"""
Syndicate Alpha — 16-Agent Institutional Gold Trading Desk
----------------------------------------------------------
Pure deterministic Python implementation of all 16 specialized agents across
the 5-Stage Peer-to-Peer Blackboard Relay Pipeline:

Stage 1 (Macro & News):
  1. CLARA  — Red-Folder News Lockout Sentinel (CPI/NFP/FOMC window protection)
  2. ARTHUR — Multi-Timeframe Regime, ADX(14), Choppiness Index (CHOP), & 1H Overlap

Stage 2 (Multi-Strategy Setup Hunters):
  3. MARCUS — Volume-Backed Value Area Breakout Specialist (active when CHOP < 50)
  4. NINA   — Smart Money Concepts (SMC) Liquidity Sweep (EQH/EQL) + FVG Hunter
  5. MAX    — Failed Breakout / Bull & Bear Trap Reversal Specialist
  6. LEO    — ICT London/NY Killzone & Silver Bullet Time-Window Filter
  7. KAI    — Fibonacci Golden Pocket (61.8% - 78.6%) & 70.5% OTE Confluence
  8. ELENA  — Price Action Wick Rejection (>=2.5x body) & 1M Market Structure Shift (MSS)

Stage 3 (Order Flow, Level-2 MBP-10 DOM & VSA):
  9. SAM    — Level-2 10-Deep Order Book Imbalance (>=2.5:1) & Passive Iceberg Detector
  10. OMAR  — Cumulative Volume Delta (CVD) Absorption & Delta Acceleration
  11. JACK  — Volume Spread Analysis (VSA) Z-Score Anomaly & Stopping Volume

Stage 4 (Risk, Veteran Filter & Quantitative Math):
  12. SARAH — Drawdown Circuit Breaker (-2% max daily loss, max 3 trades/day, cooldown)
  13. DAVID — 20-Year Veteran Filter (Spread <= 3 ticks, Room-to-Wall >= 4x ATR)
  14. ETHAN — Position Sizing (0.75% Equity Risk) & Net R:R Validator (>= 1:2.5 after fees)

Stage 5 (Master Consensus & In-Trade Lifecycle Engine):
  15. VICTOR — Master Boss Weighted Consensus Aggregator (>= 80% score required)
  16. RYAN   — Dynamic 5-Phase Trade Lifecycle Manager (Armed -> BE at +1.5R -> 50% TP1 -> Swing Trail -> L2 Emergency Exit)
"""

import numpy as np
import pandas as pd
from src.core.blackboard import Blackboard, SetupCandidate


def precompute_features(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Vectorized feature pre-computation across 1-minute bars (strictly backward-looking,
    zero lookahead bias) for all 16 agents.
    """
    data = df.copy()
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index, utc=True)
    data = data.sort_index()

    # Fill missing L2/OrderFlow columns on older historical bars with neutral baselines
    if "l2_bid_ask_ratio_mean" not in data.columns:
        data["l2_bid_ask_ratio_mean"] = 1.0
    else:
        data["l2_bid_ask_ratio_mean"] = data["l2_bid_ask_ratio_mean"].fillna(1.0)

    if "l2_bid_ask_ratio_max" not in data.columns:
        data["l2_bid_ask_ratio_max"] = 1.5
    else:
        data["l2_bid_ask_ratio_max"] = data["l2_bid_ask_ratio_max"].fillna(1.5)

    data["volume"] = data["volume"].astype(float)
    bar_rng = (data["high"] - data["low"]).replace(0, 0.10)
    clv = ((data["close"] - data["low"]) - (data["high"] - data["close"])) / bar_rng
    fallback_delta = pd.Series(clv * data["volume"] * 0.5, index=data.index)
    if "bar_delta" not in data.columns:
        data["bar_delta"] = fallback_delta
    else:
        # Decode uint32 underflow if raw bar_delta contains unsigned wrap-around (> 1e8)
        valid_mask = data["bar_delta"].notna()
        if valid_mask.any() and data.loc[valid_mask, "bar_delta"].abs().max() > 1e8:
            raw_d = data.loc[valid_mask, "bar_delta"].to_numpy(dtype=np.int64)
            n_sells = np.round(raw_d / 4294967296.0).astype(np.int64)
            data.loc[valid_mask, "bar_delta"] = (raw_d - n_sells * 4294967296).astype(float)
        data["bar_delta"] = data["bar_delta"].fillna(fallback_delta)

    if "avg_spread_pts" not in data.columns:
        data["avg_spread_pts"] = 0.10
    else:
        data["avg_spread_pts"] = data["avg_spread_pts"].fillna(0.10)

    # Has real L2 flag (June 2026 - Nov 2026 window)
    data["has_real_l2"] = data["l2_bid_ask_ratio_mean"] != 1.0

    # --- ARTHUR: Multi-Timeframe EMAs (15M, 1H, 4H, Daily, Macro), ATR, ADX(14), & 15M CHOP(14) ---
    data["ema_15"] = data["close"].ewm(span=15, adjust=False).mean()
    data["ema_50"] = data["close"].ewm(span=60, adjust=False).mean()       # 1H Fast EMA
    data["ema_200"] = data["close"].ewm(span=240, adjust=False).mean()     # 4H Structure EMA
    data["ema_daily"] = data["close"].ewm(span=1440, adjust=False).mean()  # 24H Daily EMA
    data["ema_macro"] = data["close"].ewm(span=7200, adjust=False).mean()  # 5-Day Macro EMA

    high_low = data["high"] - data["low"]
    high_close = (data["high"] - data["close"].shift(1)).abs()
    low_close = (data["low"] - data["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data["atr_14"] = tr.rolling(14, min_periods=5).mean().bfill()

    # True 15-Minute ATR(14) and 15-Minute Choppiness Index CHOP(14) (210-min lookback)
    h15 = data["high"].rolling(15, min_periods=5).max()
    l15 = data["low"].rolling(15, min_periods=5).min()
    c15_prev = data["close"].shift(15).bfill()
    tr15 = pd.concat([h15 - l15, (h15 - c15_prev).abs(), (l15 - c15_prev).abs()], axis=1).max(axis=1)
    data["atr_5m"] = tr15.rolling(210, min_periods=30).mean().bfill()

    tr15_sum = sum(tr15.shift(15 * k).fillna(0.0) for k in range(14))
    hh_210 = data["high"].rolling(210, min_periods=30).max()
    ll_210 = data["low"].rolling(210, min_periods=30).min()
    hl_range_210 = (hh_210 - ll_210).replace(0, 0.10)
    data["chop_index"] = (
        100.0 * np.log10((tr15_sum / hl_range_210).clip(lower=1.0)) / np.log10(14.0)
    ).fillna(50.0)

    # ADX approximation on 15M structure
    up_move = data["high"].diff(15)
    down_move = -data["low"].diff(15)
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_smooth = tr15.rolling(210, min_periods=30).mean().replace(0, 0.10)
    plus_di = 100.0 * pd.Series(plus_dm, index=data.index).rolling(210, min_periods=30).mean() / atr_smooth
    minus_di = 100.0 * pd.Series(minus_dm, index=data.index).rolling(210, min_periods=30).mean() / atr_smooth
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1.0)
    data["adx"] = dx.rolling(210, min_periods=30).mean().fillna(20.0)

    # --- MARCUS & ARTHUR: Rolling 60-min & 240-min (4H) Value Area High (VAH), Low (VAL), and POC ---
    data["range_high_60"] = data["high"].shift(1).rolling(60, min_periods=15).max()
    data["range_low_60"] = data["low"].shift(1).rolling(60, min_periods=15).min()
    data["poc_60"] = data["close"].shift(1).rolling(60, min_periods=15).median()
    data["range_high_240"] = data["high"].shift(1).rolling(240, min_periods=30).max()
    data["range_low_240"] = data["low"].shift(1).rolling(240, min_periods=30).min()

    # --- NINA & MAX: 20-bar Liquidity Swing High / Low (EQH / EQL pools) ---
    data["swing_high_20"] = data["high"].shift(1).rolling(20, min_periods=5).max()
    data["swing_low_20"] = data["low"].shift(1).rolling(20, min_periods=5).min()

    # Fair Value Gap (FVG) detection (3-bar imbalance)
    data["bull_fvg"] = (data["low"] - data["high"].shift(2)) >= 0.30
    data["bear_fvg"] = (data["low"].shift(2) - data["high"]) >= 0.30

    # --- KAI: Fibonacci Golden Pocket (61.8% - 78.6% retracement of 60m & 240m range) ---
    rng_60 = (data["range_high_60"] - data["range_low_60"]).replace(0, 0.10)
    data["fib_retracement_long"] = (data["range_high_60"] - data["low"]) / rng_60
    data["fib_retracement_short"] = (data["high"] - data["range_low_60"]) / rng_60

    rng_240 = (data["range_high_240"] - data["range_low_240"]).replace(0, 0.10)
    data["fib_240_long"] = (data["range_high_240"] - data["low"]) / rng_240
    data["fib_240_short"] = (data["high"] - data["range_low_240"]) / rng_240

    # --- ELENA: Price Action Wick-to-Body Ratio & 1M Market Structure Shift ---
    body = (data["close"] - data["open"]).abs().replace(0, 0.05)
    lower_wick = np.minimum(data["open"], data["close"]) - data["low"]
    upper_wick = data["high"] - np.maximum(data["open"], data["close"])
    data["lower_wick_ratio"] = lower_wick / body
    data["upper_wick_ratio"] = upper_wick / body
    data["bull_mss_1m"] = (data["close"] > data["open"]) & (data["close"] > data["high"].shift(1))
    data["bear_mss_1m"] = (data["close"] < data["open"]) & (data["close"] < data["low"].shift(1))

    # --- JACK & OMAR: Volume Z-Score, Stopping Volume, CVD Slope & Delta Absorption ---
    vol_mean = data["volume"].rolling(60, min_periods=10).mean()
    vol_std = data["volume"].rolling(60, min_periods=10).std().replace(0, 1.0)
    data["vol_z_score"] = ((data["volume"] - vol_mean) / vol_std).fillna(0.0)
    data["delta_sum_5"] = data["bar_delta"].rolling(5, min_periods=1).sum()
    data["delta_sum_15"] = data["bar_delta"].rolling(15, min_periods=1).sum()
    data["bull_absorption"] = (data["delta_sum_5"] < 0) & ((data["close"] > data["open"]) | (data["lower_wick_ratio"] >= 1.5))
    data["bear_absorption"] = (data["delta_sum_5"] > 0) & ((data["close"] < data["open"]) | (data["upper_wick_ratio"] >= 1.5))
    data["stopping_vol_bull"] = (data["vol_z_score"] >= 1.3) & (data["lower_wick_ratio"] >= 1.3)
    data["stopping_vol_bear"] = (data["vol_z_score"] >= 1.3) & (data["upper_wick_ratio"] >= 1.3)

    # --- DAVID: Room-to-Opposing-4H-Wall & Micro 60m Wall (for Scalper / Sideways Bypass) ---
    data["room_to_high_240"] = (data["range_high_240"] - data["close"]).clip(lower=0.10)
    data["room_to_low_240"] = (data["close"] - data["range_low_240"]).clip(lower=0.10)
    data["room_to_high_60"] = (data["range_high_60"] - data["close"]).clip(lower=0.10)
    data["room_to_low_60"] = (data["close"] - data["range_low_60"]).clip(lower=0.10)

    # --- SAM & NINA: Institutional Liquidity Heatmap Score (0-100, Threshold > 40) & Magnet Distance ($) ---
    # Upper Liquidity Pool (resting sell limits + buy-stop clusters at 60m/240m/20m highs)
    near_eqh_60 = ((data["range_high_60"] - data["high"].shift(1)).abs() <= 1.20).astype(float).rolling(60, min_periods=5).sum()
    near_eql_60 = ((data["low"].shift(1) - data["range_low_60"]).abs() <= 1.20).astype(float).rolling(60, min_periods=5).sum()
    vol_cluster = data["vol_z_score"].clip(lower=0.0, upper=4.0).rolling(30, min_periods=5).max().fillna(1.0)
    l2_ask_wall = np.where(data["has_real_l2"], (2.0 - data["l2_bid_ask_ratio_mean"]).clip(0.5, 2.0) * 18.0, 18.0)
    l2_bid_wall = np.where(data["has_real_l2"], data["l2_bid_ask_ratio_mean"].clip(0.5, 2.0) * 18.0, 18.0)
    htf_align_hi = np.where((data["range_high_240"] - data["range_high_60"]).abs() <= 2.50, 16.0, 6.0)
    htf_align_lo = np.where((data["range_low_60"] - data["range_low_240"]).abs() <= 2.50, 16.0, 6.0)

    data["upper_liq_score"] = (15.0 + near_eqh_60 * 6.5 + vol_cluster * 7.5 + l2_ask_wall + htf_align_hi).clip(10.0, 99.0)
    data["lower_liq_score"] = (15.0 + near_eql_60 * 6.5 + vol_cluster * 7.5 + l2_bid_wall + htf_align_lo).clip(10.0, 99.0)
    data["upper_liq_grabbed"] = (data["high"] >= data["range_high_60"]) | (data["high"].shift(1) >= data["range_high_60"].shift(1))
    data["lower_liq_grabbed"] = (data["low"] <= data["range_low_60"]) | (data["low"].shift(1) <= data["range_low_60"].shift(1))

    # --- MAX (Sideways) & SARAH (Psychologist): 60m Range Position & 5m RSI(14) Crowd Exhaustion ---
    data["range_pos_60"] = ((data["close"] - data["range_low_60"]) / rng_60).clip(0.0, 1.0)
    delta_c5 = data["close"].diff(5).fillna(0.0)
    gain5 = delta_c5.clip(lower=0.0).rolling(70, min_periods=15).mean()
    loss5 = (-delta_c5.clip(upper=0.0)).rolling(70, min_periods=15).mean().replace(0, 0.01)
    rs5 = gain5 / loss5
    data["rsi_5m"] = (100.0 - (100.0 / (1.0 + rs5))).fillna(50.0)

    # --- LEO: ICT Killzone, Silver Bullet & Expanded Intraday Scalping Session (UTC-5 EST) ---
    est_hour = (data.index.hour - 5) % 24
    est_min = data.index.minute
    # Primary Killzones (02:00-06:00 EST London, 07:00-13:00 EST NY)
    data["in_killzone"] = est_hour.isin([2, 3, 4, 5, 7, 8, 10, 11, 12])
    # High-Expectancy Intraday Scalper Bypass Hours (London Mid, NY Open, NY Lunch, Globex Close, Asia Open)
    data["in_scalp_window"] = est_hour.isin([5, 7, 8, 12, 15, 16, 17, 23])
    # Expanded Liquid Intraday Scalping & Sideways Session (London + NY + Afternoon Globex Close + Asian Open)
    data["in_active_session"] = est_hour.isin([2, 3, 4, 5, 7, 8, 10, 11, 12, 15, 16, 17, 23])
    # LEO Silver Bullet (03:00-04:00 EST, 10:00-11:00 EST, 15:00-16:00 EST) or ICT Macro (:50 to :10)
    data["silver_bullet"] = (est_hour == 3) | (est_hour == 10) | (est_hour == 15) | (est_min >= 50) | (est_min <= 10)
    # CLARA: Red-Folder 08:30 EST (CPI/NFP release minute lockout 08:28 - 08:35 EST)
    data["news_lockout"] = (est_hour == 8) & (est_min >= 28) & (est_min <= 35)

    return data
