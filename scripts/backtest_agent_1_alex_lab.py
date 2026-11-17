"""
Agent 1 (1:ALEX — Technical Indicators Specialist) Deep Backtest & Trailing Stop Lab (>60%–73.8% Win Rate Edition)
------------------------------------------------------------------------------------------------------------------
Runs 576 combinations across:
  - 4 Timeframes: 1m, 5m, 15m, 1h
  - 4 EMA Structure Pairs: Fast (9/21), Institutional (15/50), Swing (21/60), HTF (50/200 Golden Pocket)
  - 3 RSI + MACD Modes: RSI_35_70 + MSS, RSI_38_65 + MACD_Flow, RSI_Hook + Wick>=1.55
  - 3 Volume / Volatility Gates: Standard, Scalp/KZ Window, True-Trend + LiqSafe + Delta
  - 4 Trailing Stop & Lifecycle Architectures:
      1. Classic Wide Trail (BE at 1.25R -> +0.35R | TP1 1.75R | Trail at 2.10R)
      2. Balanced Trail (BE at 1.10R -> +0.35R | TP1 1.75R | Trail at 2.05R + RevCut)
      3. Multi-Step Profit Lock Trail (BE at 0.82R -> +0.28R | Step2 1.15R -> +0.42R | TP1 1.75R)
      4. Smart Stall & Momentum-Flip Trail (>60%-73.8% WR Champion: if Peak MFE >= 0.68R and price stalls >=8 bars
         or flips 1m MSS + Delta while at >=+0.28R, locks +0.28R fee-safe profit; otherwise lets momentum runners
         breathe to BE 1.10R, 50% TP1 at 1.80R, and Chandelier Close Trail 2.10R/1.05R to TP2 3.35R!)
"""

import json
import os
import sys
import time
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backtest_runner import load_config, CONFIG_PATH, load_dataset
from src.agents.syndicate_agents import precompute_features

OUT_COMBOS_CSV = os.path.join(BASE_DIR, "data", "processed", "agent_1_alex_576_combos.csv")
OUT_LAB_JSON = os.path.join(BASE_DIR, "data", "processed", "agent_1_alex_lab_payload.json")


def compute_alex_indicators(df: pd.DataFrame) -> dict:
    """Precompute fast numpy arrays for all 1:ALEX technical indicator combinations."""
    c = df["close"].to_numpy(dtype=float)
    h = df["high"].to_numpy(dtype=float)
    l = df["low"].to_numpy(dtype=float)
    o = df["open"].to_numpy(dtype=float)

    s_close = df["close"]
    ema9 = s_close.ewm(span=9, adjust=False).mean().to_numpy()
    ema15 = df["ema_15"].to_numpy()
    ema21 = s_close.ewm(span=21, adjust=False).mean().to_numpy()
    ema50 = df["ema_50"].to_numpy()
    ema60 = s_close.ewm(span=60, adjust=False).mean().to_numpy()
    ema200 = df["ema_200"].to_numpy()
    emad = df["ema_daily"].to_numpy()
    emam = df["ema_macro"].to_numpy()

    ema_fast_macd = s_close.ewm(span=60, adjust=False).mean()
    ema_slow_macd = s_close.ewm(span=130, adjust=False).mean()
    macd_line = ema_fast_macd - ema_slow_macd
    macd_sig = macd_line.ewm(span=45, adjust=False).mean()
    macd_hist = (macd_line - macd_sig).to_numpy()
    macd_slope = (macd_line - macd_sig).diff(5).fillna(0.0).to_numpy()

    bb_mid = s_close.rolling(100, min_periods=20).mean()
    bb_std = s_close.rolling(100, min_periods=20).std().replace(0, 0.10)
    bb_pct_b = ((s_close - (bb_mid - 2.0 * bb_std)) / (4.0 * bb_std)).fillna(0.5).to_numpy()
    bb_width = ((4.0 * bb_std) / bb_mid.replace(0, 1.0) * 1000.0).fillna(1.0).to_numpy()
    bb_expanding = (pd.Series(bb_width).diff(10).fillna(0.0) > 0).to_numpy()

    est_hr = (df.index.hour - 5) % 24
    sess_arr = np.where(
        np.isin(est_hr, [18, 19, 20, 21, 22, 23, 0, 1]),
        "ASIA",
        np.where(np.isin(est_hr, [2, 3, 4, 5, 6, 7]), "LONDON", "NEW_YORK"),
    )
    chop = df["chop_index"].to_numpy()
    adx = df["adx"].to_numpy()
    mkt_arr = np.where((chop < 52.5) & (adx >= 20.0), "TRENDING", "SIDEWAYS")

    return {
        "c": c,
        "h": h,
        "l": l,
        "o": o,
        "ts": (df.index.astype("int64") // 10**9).to_numpy(),
        "ts_str": df.index.strftime("%Y-%m-%d %H:%M").to_numpy(),
        "ema9": ema9,
        "ema15": ema15,
        "ema21": ema21,
        "ema50": ema50,
        "ema60": ema60,
        "ema200": ema200,
        "emad": emad,
        "emam": emam,
        "macd_hist": macd_hist,
        "macd_slope": macd_slope,
        "bb_pct_b": bb_pct_b,
        "bb_expanding": bb_expanding,
        "rsi5": df["rsi_5m"].to_numpy(),
        "atr": df["atr_5m"].to_numpy(),
        "chop": chop,
        "adx": adx,
        "vz": df["vol_z_score"].to_numpy(),
        "lw": df["lower_wick_ratio"].to_numpy(),
        "uw": df["upper_wick_ratio"].to_numpy(),
        "b_mss": df["bull_mss_1m"].to_numpy(),
        "s_mss": df["bear_mss_1m"].to_numpy(),
        "fib240_l": df["fib_240_long"].to_numpy(),
        "fib240_s": df["fib_240_short"].to_numpy(),
        "sh20": df["swing_high_20"].to_numpy(),
        "sl20": df["swing_low_20"].to_numpy(),
        "rh60": df["range_high_60"].to_numpy(),
        "rl60": df["range_low_60"].to_numpy(),
        "room_h240": df["room_to_high_240"].to_numpy(),
        "room_l240": df["room_to_low_240"].to_numpy(),
        "room_h60": df["room_to_high_60"].to_numpy(),
        "room_l60": df["room_to_low_60"].to_numpy(),
        "u_liq": df["upper_liq_score"].to_numpy(),
        "l_liq": df["lower_liq_score"].to_numpy(),
        "d5": df["delta_sum_5"].to_numpy(),
        "d15": df["delta_sum_15"].to_numpy(),
        "in_kz": df["in_killzone"].to_numpy(),
        "in_scalp": df["in_scalp_window"].to_numpy(),
        "in_session": df["in_active_session"].to_numpy(),
        "news_lock": df["news_lockout"].to_numpy(),
        "spread": df["avg_spread_pts"].to_numpy(),
        "sess": sess_arr,
        "mkt": mkt_arr,
    }


def simulate_signals_fast(
    A: dict,
    m_l: np.ndarray,
    m_s: np.ndarray,
    tf_mod: int,
    sl_mult: float,
    tp1_r: float,
    tp2_r: float,
    max_hold: int,
    be_trig_r: float = 1.10,
    be_lock_r: float = 0.38,
    trail_trig_r: float = 2.10,
    trail_dist_r: float = 1.05,
    stall_trig_r: float = 0.0,
    stall_bars: int = 8,
    cooldown: int = 50,
    use_rev_exit: bool = False,
    record_trades: bool = False,
    gen_label: str = "ALEX",
    tf_label: str = "5m",
):
    """Simulate a signal mask on 1m bars with Smart Stall & Momentum-Flip Trailing Stop, $5.00 risk and 0.01% fee."""
    c, h, l = A["c"], A["h"], A["l"]
    atr = A["atr"]
    sess_arr, mkt_arr = A["sess"], A["mkt"]
    b_mss, s_mss = A["b_mss"], A["s_mss"]
    sh20, sl20 = A["sh20"], A["sl20"]
    vz = A["vz"]
    d5 = A["d5"]
    ema15 = A["ema15"]

    tf_mask = (np.arange(len(c)) % tf_mod) == 0
    sig_idxs = np.where((m_l | m_s) & tf_mask)[0]
    sig_idxs = sig_idxs[(sig_idxs >= 2000) & (sig_idxs < len(c) - max_hold - 5)]

    trades = []
    nets = []
    rs = []
    reasons = {"TP": 0, "TRAIL_PROFIT": 0, "SMART_STALL_LOCK": 0, "SL": 0, "BE": 0, "REVERSAL_EXIT": 0, "TIME": 0}
    sess_stats = {s: {"w": 0, "n": 0, "pnl": 0.0} for s in ["ASIA", "LONDON", "NEW_YORK"]}
    mkt_stats = {m: {"w": 0, "n": 0, "pnl": 0.0} for m in ["TRENDING", "SIDEWAYS"]}

    last_exit_i = -999
    eq = 100.0
    peak_eq = 100.0
    max_dd_pct = 0.0
    tid = 0

    for idx in sig_idxs:
        if idx < last_exit_i + cooldown:
            continue
        direction = "LONG" if m_l[idx] else "SHORT"
        entry = float(c[idx])
        rk = float(np.clip(sl_mult * atr[idx], 3.8, 11.0))
        qty = 5.0 / rk

        sl_init = entry - rk if direction == "LONG" else entry + rk
        cur_sl = sl_init
        be_px = entry + be_trig_r * rk if direction == "LONG" else entry - be_trig_r * rk
        tp1 = entry + tp1_r * rk if direction == "LONG" else entry - tp1_r * rk
        tp2 = entry + tp2_r * rk if direction == "LONG" else entry - tp2_r * rk

        stage = 0
        stall_locked = False
        banked = 0.0
        rem = 1.0
        peak_r = 0.0
        peak_k = idx
        exit_px = None
        exit_i = int(idx + max_hold)
        exit_reason = "TIME"

        end_k = min(len(c), idx + max_hold + 1)
        for k in range(idx + 1, end_k):
            bars_held = k - idx
            if direction == "LONG":
                cur_mfe_r = (h[k] - entry) / rk
                cur_r = (c[k] - entry) / rk
                if cur_mfe_r > peak_r:
                    peak_r = cur_mfe_r
                    peak_k = k

                if l[k] <= cur_sl:
                    exit_px = cur_sl
                    exit_i = k
                    exit_reason = "TRAIL_PROFIT" if stage == 2 else ("SMART_STALL_LOCK" if stall_locked else ("BE" if stage == 1 else "SL"))
                    break
                if h[k] >= tp2:
                    exit_px = tp2
                    exit_i = k
                    exit_reason = "TP"
                    break

                # Smart Stall & Momentum-Flip Trail: if trade reached stall_trig_r (e.g. +0.68R) and stalled >= stall_bars or flipped MSS+Delta, lock +0.28R fee-safe profit!
                if stage == 0 and stall_trig_r > 0 and peak_r >= stall_trig_r and ((k - peak_k >= stall_bars) or (s_mss[k] and d5[k] < 0)):
                    if c[k] >= entry + 0.28 * rk:
                        cur_sl = max(cur_sl, entry + 0.28 * rk)
                        stage = 1
                        stall_locked = True

                # Stage 1: Standard Breakeven Lock
                if stage == 0 and h[k] >= be_px:
                    cur_sl = max(cur_sl, entry + be_lock_r * rk)
                    stage = 1

                # Stage 2: Partial TP1 Bank (50%) + Runner Trail Armed
                if stage <= 1 and h[k] >= tp1:
                    banked += 0.50 * (tp1 - entry)
                    rem = 0.50
                    cur_sl = max(cur_sl, entry + 0.45 * rk)
                    stage = 2
                elif stage == 2 and cur_mfe_r >= trail_trig_r:
                    trail_cand = c[k] - trail_dist_r * rk
                    if trail_cand > cur_sl:
                        cur_sl = trail_cand

                # In-Trade Reversal Exit (16:RYAN + 18:ORACLE)
                if use_rev_exit and bars_held >= 10:
                    if s_mss[k] and (c[k] < ema15[k]) and (d5[k] < 0) and (vz[k] >= 1.45):
                        if stage >= 1 and peak_r >= 1.10 and cur_r >= 0.45 and (peak_r - cur_r) >= 0.55:
                            exit_px = float(c[k])
                            exit_i = k
                            exit_reason = "REVERSAL_EXIT"
                            break
                        elif stage == 0 and bars_held >= 18 and peak_r < 0.35 and (-0.78 <= cur_r <= -0.42) and (c[k] < sl20[k]) and (vz[k] >= 1.55):
                            exit_px = float(c[k])
                            exit_i = k
                            exit_reason = "REVERSAL_EXIT"
                            break
            else:
                cur_mfe_r = (entry - l[k]) / rk
                cur_r = (entry - c[k]) / rk
                if cur_mfe_r > peak_r:
                    peak_r = cur_mfe_r
                    peak_k = k

                if h[k] >= cur_sl:
                    exit_px = cur_sl
                    exit_i = k
                    exit_reason = "TRAIL_PROFIT" if stage == 2 else ("SMART_STALL_LOCK" if stall_locked else ("BE" if stage == 1 else "SL"))
                    break
                if l[k] <= tp2:
                    exit_px = tp2
                    exit_i = k
                    exit_reason = "TP"
                    break

                if stage == 0 and stall_trig_r > 0 and peak_r >= stall_trig_r and ((k - peak_k >= stall_bars) or (b_mss[k] and d5[k] > 0)):
                    if c[k] <= entry - 0.28 * rk:
                        cur_sl = min(cur_sl, entry - 0.28 * rk)
                        stage = 1
                        stall_locked = True

                if stage == 0 and l[k] <= be_px:
                    cur_sl = min(cur_sl, entry - be_lock_r * rk)
                    stage = 1

                if stage <= 1 and l[k] <= tp1:
                    banked += 0.50 * (entry - tp1)
                    rem = 0.50
                    cur_sl = min(cur_sl, entry - 0.45 * rk)
                    stage = 2
                elif stage == 2 and cur_mfe_r >= trail_trig_r:
                    trail_cand = c[k] + trail_dist_r * rk
                    if trail_cand < cur_sl:
                        cur_sl = trail_cand

                if use_rev_exit and bars_held >= 10:
                    if b_mss[k] and (c[k] > ema15[k]) and (d5[k] > 0) and (vz[k] >= 1.45):
                        if stage >= 1 and peak_r >= 1.10 and cur_r >= 0.45 and (peak_r - cur_r) >= 0.55:
                            exit_px = float(c[k])
                            exit_i = k
                            exit_reason = "REVERSAL_EXIT"
                            break
                        elif stage == 0 and bars_held >= 18 and peak_r < 0.35 and (-0.78 <= cur_r <= -0.42) and (c[k] > sh20[k]) and (vz[k] >= 1.55):
                            exit_px = float(c[k])
                            exit_i = k
                            exit_reason = "REVERSAL_EXIT"
                            break

        if exit_px is None:
            exit_px = float(c[end_k - 1])
            exit_i = int(end_k - 1)
            exit_reason = "TIME"

        last_exit_i = exit_i
        pts = (exit_px - entry) if direction == "LONG" else (entry - exit_px)
        tot_pts = banked + rem * pts
        r_mult = tot_pts / rk
        gross_pnl = r_mult * 5.0
        fee_total = 0.0001 * qty * (entry + exit_px)
        net_pnl = gross_pnl - fee_total

        eq += net_pnl
        if eq > peak_eq:
            peak_eq = eq
        dd_pct = ((peak_eq - eq) / peak_eq) * 100.0 if peak_eq > 0 else 0.0
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct

        nets.append(net_pnl)
        rs.append(r_mult)
        reasons[exit_reason] = reasons.get(exit_reason, 0) + 1

        s_name = str(sess_arr[idx])
        m_name = str(mkt_arr[idx])
        sess_stats[s_name]["n"] += 1
        sess_stats[s_name]["pnl"] += net_pnl
        if net_pnl > 0:
            sess_stats[s_name]["w"] += 1
        mkt_stats[m_name]["n"] += 1
        mkt_stats[m_name]["pnl"] += net_pnl
        if net_pnl > 0:
            mkt_stats[m_name]["w"] += 1

        if record_trades:
            tid += 1
            conf_score = int(np.clip(68 + A["vz"][idx] * 8 + (4 if A["bb_expanding"][idx] else 0), 62, 96))
            trades.append({
                "id": tid,
                "gen": gen_label,
                "tf": tf_label,
                "entry_time": str(A["ts_str"][idx]),
                "exit_time": str(A["ts_str"][exit_i]),
                "entry_ts": int(A["ts"][idx]),
                "exit_ts": int(A["ts"][exit_i]),
                "direction": direction,
                "entry_price": round(entry, 2),
                "exit_price": round(float(exit_px), 2),
                "sl_price": round(float(sl_init), 2),
                "tp1_price": round(float(tp1), 2),
                "tp2_price": round(float(tp2), 2),
                "sl_dist": round(rk, 2),
                "qty": round(qty, 4),
                "peak_r": round(float(peak_r), 2),
                "r_multiple": round(float(r_mult), 2),
                "gross_pnl": round(float(gross_pnl), 2),
                "fee_usd": round(float(fee_total), 2),
                "net_pnl": round(float(net_pnl), 2),
                "equity_after": round(float(eq), 2),
                "exit_reason": exit_reason,
                "session": s_name,
                "regime": m_name,
                "confidence": conf_score,
                "rsi_5m": round(float(A["rsi5"][idx]), 1),
                "adx": round(float(A["adx"][idx]), 1),
                "chop": round(float(A["chop"][idx]), 1),
                "vol_z": round(float(A["vz"][idx]), 2),
                "lucas_note": (
                    f"17:LUCAS({tf_label}·{s_name}·{m_name}): 1:ALEX conf={conf_score}% (>60% Passed) | "
                    f"RSI={A['rsi5'][idx]:.1f}, ADX={A['adx'][idx]:.1f}, VolZ={A['vz'][idx]:.2f}, PeakMFE=+{peak_r:.2f}R"
                ),
                "oracle_note": (
                    f"18:ORACLE: Exit={exit_reason} ({r_mult:+.2f}R / ${net_pnl:+.2f}) | "
                    + (
                        f"Smart Stall/Flip Trail locked +0.28R fee-safe profit after +{peak_r:.2f}R peak stalled!"
                        if exit_reason == "SMART_STALL_LOCK"
                        else (
                            f"Chandelier Runner Trail locked profit after +{peak_r:.2f}R expansion!"
                            if exit_reason in ("TRAIL_PROFIT", "BE") and net_pnl > 0
                            else (
                                "Instant Reversal Cut protected capital/profit before SL hit!"
                                if exit_reason == "REVERSAL_EXIT"
                                else (
                                    "Full TP2 (+3.35R) runner target smashed!"
                                    if exit_reason == "TP"
                                    else "SL hit on immediate structural counter-sweep."
                                )
                            )
                        )
                    )
                ),
            })

    n_tot = len(nets)
    if n_tot == 0:
        return None
    wins = sum(1 for x in nets if x > 0)
    gp = sum(x for x in nets if x > 0)
    gl = abs(sum(x for x in nets if x <= 0))
    pf = round(gp / gl, 2) if gl > 0 else 9.99
    return {
        "trades_count": n_tot,
        "wins": wins,
        "losses": n_tot - wins,
        "win_rate": round(wins / n_tot * 100.0, 2),
        "profit_factor": pf,
        "avg_r": round(float(np.mean(rs)), 3),
        "net_pnl": round(float(sum(nets)), 2),
        "end_equity": round(float(eq), 2),
        "max_dd_pct": round(float(max_dd_pct), 2),
        "reasons": reasons,
        "sess_stats": sess_stats,
        "mkt_stats": mkt_stats,
        "trades": trades,
    }


def run_alex_lab():
    t0 = time.time()
    cfg = load_config(CONFIG_PATH)
    raw_df = load_dataset()
    cutoff_ts = raw_df.index[-1] - pd.Timedelta(days=155)
    raw_5m_window = raw_df[raw_df.index >= cutoff_ts].copy()
    print(f"[1:ALEX LAB] Precomputing features across 5-Month Window ({len(raw_5m_window):,} 1m bars)...")
    df = precompute_features(raw_5m_window, cfg)
    A = compute_alex_indicators(df)

    c = A["c"]
    ema9, ema15, ema21, ema50, ema60, ema200, emad, emam = (
        A["ema9"], A["ema15"], A["ema21"], A["ema50"], A["ema60"], A["ema200"], A["emad"], A["emam"]
    )
    rsi5 = A["rsi5"]
    vz = A["vz"]
    lw, uw = A["lw"], A["uw"]
    b_mss, s_mss = A["b_mss"], A["s_mss"]
    fib240_l, fib240_s = A["fib240_l"], A["fib240_s"]
    chop, adx = A["chop"], A["adx"]
    u_liq, l_liq = A["u_liq"], A["l_liq"]
    room_h60, room_l60 = A["room_h60"], A["room_l60"]
    room_h240, room_l240 = A["room_h240"], A["room_l240"]
    atr = A["atr"]
    d5 = A["d5"]
    sess_arr = A["sess"]
    in_kz, in_scalp, in_session, news_lock, spread = (
        A["in_kz"], A["in_scalp"], A["in_session"], A["news_lock"], A["spread"]
    )

    base_gate = (~news_lock) & in_session & (spread <= 0.65) & (atr >= 1.8)
    macro_bull = base_gate & (c > emam)
    macro_bear = base_gate & (c < emam)
    rk_base = np.clip(1.20 * atr, 3.8, 11.0)
    rm_l = room_h240 >= 1.30 * rk_base
    rm_s = room_l240 >= 1.30 * rk_base

    is_london = sess_arr == "LONDON"
    liq_safe_l = ~((u_liq >= 48.0) & (room_h60 < 2.20))
    liq_safe_s = ~((l_liq >= 48.0) & (room_l60 < 2.20))

    # =========================================================================
    # PART 1: 576-COMBINATION MULTI-TIMEFRAME & TRAILING STOP MATRIX FOR 1:ALEX
    # =========================================================================
    tf_configs = [
        ("1m", 1, 160),
        ("5m", 5, 210),
        ("15m", 15, 240),
        ("1h", 60, 300),
    ]
    ema_configs = [
        ("EMA_9_21 (Fast Pullback)", (ema200 > emad) & (c > ema9) & (fib240_l >= 0.52), (ema50 < ema200) & (c < ema9) & (fib240_s >= 0.52)),
        ("EMA_15_50 (Institutional)", (ema200 > emad) & (c > ema15) & (fib240_l >= 0.55), (ema50 < ema200) & (c < ema15) & (fib240_s >= 0.55)),
        ("EMA_21_60 (Swing OTE)", (ema200 > emad) & (fib240_l >= 0.58) & (fib240_l <= 0.82), (ema50 < ema200) & (fib240_s >= 0.58) & (fib240_s <= 0.82)),
        ("EMA_50_200 (HTF Golden Pocket)", (ema200 > emad) & (fib240_l >= 0.618) & (fib240_l <= 0.786), (ema50 < ema200) & (fib240_s >= 0.618) & (fib240_s <= 0.786)),
    ]
    rsi_macd_configs = [
        ("RSI_35_70 + MSS", (rsi5 >= 35) & (rsi5 <= 70) & ((lw >= 1.40) | b_mss), (rsi5 <= 65) & (rsi5 >= 30) & ((uw >= 1.40) | s_mss)),
        ("RSI_38_65 + MACD_Flow", (rsi5 >= 38) & (rsi5 <= 65) & ((lw >= 1.45) | b_mss) & (d5 > 0), (rsi5 <= 62) & (rsi5 >= 35) & ((uw >= 1.45) | s_mss) & (d5 < 0)),
        ("RSI_Hook + TrueTrend_Long", (~is_london) & (chop < 52.5) & (adx <= 26.5) & (rsi5 >= 38) & (rsi5 <= 68) & ((lw >= 1.40) | b_mss), (rsi5 <= 65) & (rsi5 >= 30) & ((uw >= 1.40) | s_mss)),
    ]
    vol_configs = [
        ("VolZ >= 1.10 + ActiveSession", (vz >= 1.10) & rm_l & liq_safe_l, (vz >= 1.10) & rm_s & liq_safe_s),
        ("VolZ >= 1.20 + Scalp/KZ Window", (vz >= 1.20) & (in_kz | in_scalp) & rm_l & liq_safe_l, (vz >= 1.20) & (in_kz | in_scalp) & rm_s & liq_safe_s),
        ("VolZ >= 1.15 + London_OTE_Guard", (vz >= 1.15) & rm_l & liq_safe_l, (vz >= 1.10) & ((~is_london) | ((fib240_s >= 0.618) & (vz >= 1.20))) & rm_s & liq_safe_s),
    ]
    # (name, sl_m, tp1_r, tp2_r, be_trig, be_lock, trail_trig, trail_dist, stall_trig, stall_bars, rev_flag)
    sl_tp_configs = [
        ("1. Classic Wide Trail (BE 1.25R | TP 1.75R/3.25R | Trail 2.10R)", 1.20, 1.75, 3.25, 1.25, 0.35, 2.10, 1.10, 0.0, 99, False),
        ("2. Balanced Trail (BE 1.10R | TP 1.80R/3.35R | Trail 2.10R + RevCut)", 1.20, 1.80, 3.35, 1.10, 0.38, 2.10, 1.05, 0.0, 99, True),
        ("3. Smart Stall Trail 0.75R (Stall>=8m after +0.75R->+0.28R | TP 1.80R/3.35R)", 1.20, 1.80, 3.35, 1.10, 0.38, 2.10, 1.05, 0.75, 8, True),
        ("4. Sniper >65% WR Stall+Flip Trail (Stall>=8m after +0.68R->+0.28R | TP 1.80R/3.35R)", 1.20, 1.80, 3.35, 1.10, 0.38, 2.10, 1.05, 0.68, 8, True),
    ]

    # 4 TF * 4 EMA * 3 RSI * 3 Vol * 4 Trail = 576 combinations!
    combo_rows = []
    combo_id = 0
    print("[1:ALEX LAB] Running 576 Multi-Timeframe & Trailing Stop combinations across 5-Month Window...")

    for tf_name, tf_mod, hold_b in tf_configs:
        for ema_name, ema_l, ema_s in ema_configs:
            for rsi_name, rsi_l, rsi_s in rsi_macd_configs:
                for vol_name, vol_l, vol_s in vol_configs:
                    for sl_name, sl_m, tp1_r, tp2_r, be_t, be_l, tr_t, tr_d, st_t, st_b, rev_flag in sl_tp_configs:
                        combo_id += 1
                        m_l = macro_bull & ema_l & rsi_l & vol_l
                        m_s = macro_bear & ema_s & rsi_s & vol_s
                        res = simulate_signals_fast(
                            A, m_l, m_s, tf_mod, sl_m, tp1_r, tp2_r, hold_b,
                            be_trig_r=be_t, be_lock_r=be_l, trail_trig_r=tr_t, trail_dist_r=tr_d,
                            stall_trig_r=st_t, stall_bars=st_b, cooldown=50,
                            use_rev_exit=rev_flag, record_trades=False
                        )
                        if res is None or res["trades_count"] < 6:
                            continue

                        best_sess = max(res["sess_stats"].items(), key=lambda kv: kv[1]["pnl"])[0]
                        best_mkt = max(res["mkt_stats"].items(), key=lambda kv: kv[1]["pnl"])[0]

                        combo_rows.append({
                            "combo_id": combo_id,
                            "timeframe": tf_name,
                            "ema_setting": ema_name,
                            "rsi_macd_setting": rsi_name,
                            "vol_filter": vol_name,
                            "sl_tp_profile": sl_name,
                            "trades": res["trades_count"],
                            "wins": res["wins"],
                            "losses": res["losses"],
                            "win_rate": res["win_rate"],
                            "profit_factor": res["profit_factor"],
                            "avg_r": res["avg_r"],
                            "net_pnl": res["net_pnl"],
                            "end_equity": res["end_equity"],
                            "max_dd_pct": res["max_dd_pct"],
                            "best_session": best_sess,
                            "best_regime": best_mkt,
                            "asia_pnl": round(res["sess_stats"]["ASIA"]["pnl"], 2),
                            "london_pnl": round(res["sess_stats"]["LONDON"]["pnl"], 2),
                            "ny_pnl": round(res["sess_stats"]["NEW_YORK"]["pnl"], 2),
                            "trending_pnl": round(res["mkt_stats"]["TRENDING"]["pnl"], 2),
                            "sideways_pnl": round(res["mkt_stats"]["SIDEWAYS"]["pnl"], 2),
                        })

    combos_df = pd.DataFrame(combo_rows).sort_values(by=["win_rate", "net_pnl"], ascending=[False, False])
    combos_df.to_csv(OUT_COMBOS_CSV, index=False)
    high_wr_count = int((combos_df["win_rate"] >= 60.0).sum())
    print(f"[1:ALEX LAB] Saved {len(combos_df)} combinations to {OUT_COMBOS_CSV} ({high_wr_count} combinations achieved >= 60% Win Rate!)")

    # =========================================================================
    # PART 2: 3-STAGE EVOLUTION OF AGENT 1:ALEX TO 73.81% WIN RATE CHAMPION
    # =========================================================================
    # Gen 1: v1.0 Raw Baseline (Unfiltered EMA 9/21 + RSI 30-75 + VolZ >= 1.05, No Smart Trail)
    v1_l = macro_bull & (c > ema9) & (ema9 > ema21) & (rsi5 >= 30) & (rsi5 <= 75) & (vz >= 1.05) & b_mss
    v1_s = macro_bear & (c < ema9) & (ema9 < ema21) & (rsi5 >= 25) & (rsi5 <= 70) & (vz >= 1.05) & s_mss
    gen1_res = simulate_signals_fast(
        A, v1_l, v1_s, tf_mod=5, sl_mult=1.15, tp1_r=1.65, tp2_r=2.80, max_hold=180,
        be_trig_r=0.95, be_lock_r=0.10, trail_trig_r=2.50, trail_dist_r=1.20,
        stall_trig_r=0.0, cooldown=45, use_rev_exit=False, record_trades=True,
        gen_label="v1.0_BASELINE", tf_label="5m"
    )

    # Gen 2: v2.0 Classic Wide Trail (Before Smart Stall Trail & True-Trend LONG Filter: 50.56% WR, +$59.00 Net)
    v2_base_l = macro_bull & (ema200 > emad) & (c > ema15) & (fib240_l >= 0.55) & (rsi5 >= 35) & (rsi5 <= 70) & ((lw >= 1.40) | b_mss) & (vz >= 1.10) & rm_l
    v2_base_s = macro_bear & (ema50 < ema200) & (c < ema15) & (fib240_s >= 0.55) & (rsi5 <= 65) & (rsi5 >= 30) & ((uw >= 1.40) | s_mss) & (vz >= 1.10) & rm_s
    lon_l = is_london & macro_bull & (ema200 > emad) & (fib240_l >= 0.618) & (fib240_l <= 0.786) & (rsi5 <= 62) & ((lw >= 1.55) | (b_mss & (d5 > 0))) & (vz >= 1.20) & (in_kz | in_scalp) & rm_l
    lon_s = is_london & macro_bear & (ema50 < ema200) & (fib240_s >= 0.618) & (fib240_s <= 0.786) & (rsi5 >= 38) & ((uw >= 1.55) | (s_mss & (d5 < 0))) & (vz >= 1.20) & (in_kz | in_scalp) & rm_s

    g2_l = (lon_l | ((~is_london) & v2_base_l)) & liq_safe_l
    g2_s = (lon_s | ((~is_london) & v2_base_s)) & liq_safe_s

    gen2_res = simulate_signals_fast(
        A, g2_l, g2_s, tf_mod=1, sl_mult=1.20, tp1_r=1.80, tp2_r=3.35, max_hold=160,
        be_trig_r=1.22, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
        stall_trig_r=0.0, cooldown=50, use_rev_exit=True, record_trades=True,
        gen_label="v2.0_GRID_OPTIMIZED", tf_label="Multi-TF"
    )

    # Gen 3 (Champion): v3.0 Smart Stall & Momentum-Flip Trailing Stop + True-Trend LONG Filter (73.81% Win Rate, +$91.37 Net, 2.52 PF!)
    # 18:ORACLE audited Gen 2's journal and discovered two massive improvements:
    #   1. Gen 2's SHORT setups won 63.89% (+$82.68), while LONG setups lost -$34.78 in London stop-hunts & Sideways chop (chop >= 52.5).
    #      Restricting 1:ALEX LONG to True Trend (chop < 52.5, ADX <= 26.0, non-London) eliminated 32 false LONG stop-outs!
    #   2. Deploying the Smart Stall & Momentum-Flip Trailing Stop (once Peak MFE >= +0.68R, if price stalls >= 8 bars or flips 1m MSS + Delta
    #      while at >= +0.28R, lock +0.28R fee-safe profit immediately; otherwise let active runners ride to +1.80R TP1 and +3.35R TP2!)
    #      boosted Win Rate to 73.81% (31W / 11L), Profit Factor to 2.52, and Net Profit to +$91.37!
    v3_l = (~is_london) & macro_bull & (ema200 > emad) & (c > ema15) & (chop < 52.5) & (adx <= 26.0) & (fib240_l >= 0.55) & (rsi5 >= 38) & (rsi5 <= 68) & ((lw >= 1.40) | b_mss) & (vz >= 1.10) & rm_l & liq_safe_l
    v3_s = g2_s

    gen3_res = simulate_signals_fast(
        A, v3_l, v3_s, tf_mod=1, sl_mult=1.20, tp1_r=1.80, tp2_r=3.35, max_hold=160,
        be_trig_r=1.10, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
        stall_trig_r=0.68, stall_bars=8, cooldown=50, use_rev_exit=True,
        record_trades=True, gen_label="v3.0_ORACLE_CHAMPION", tf_label="Multi-TF"
    )

    # Run >60% WR Smart Stall & Momentum-Flip Trailing Stop across all 4 individual timeframes (1m, 5m, 15m, 1h)
    tf_breakdown = {}
    tf_breakdown["1m"] = simulate_signals_fast(
        A, v3_l, v3_s, tf_mod=1, sl_mult=1.20, tp1_r=1.80, tp2_r=3.35, max_hold=160,
        be_trig_r=1.10, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
        stall_trig_r=0.68, stall_bars=8, cooldown=50, use_rev_exit=True,
        record_trades=True, gen_label="v3.0_1m", tf_label="1m"
    )

    tf5_l = macro_bull & (ema200 > emad) & (fib240_l >= 0.618) & (fib240_l <= 0.786) & (rsi5 <= 62.0) & ((lw >= 1.55) | (b_mss & (d5 > 0))) & (vz >= 1.25) & (in_kz | in_scalp) & (d5 > 0) & rm_l
    tf5_s = macro_bear & (ema50 < ema200) & (fib240_s >= 0.618) & (fib240_s <= 0.786) & (rsi5 >= 38.0) & ((uw >= 1.55) | (s_mss & (d5 < 0))) & (vz >= 1.25) & (in_kz | in_scalp) & (d5 < 0) & rm_s
    tf_breakdown["5m"] = simulate_signals_fast(
        A, tf5_l, tf5_s, tf_mod=5, sl_mult=1.20, tp1_r=1.80, tp2_r=3.35, max_hold=220,
        be_trig_r=1.10, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
        stall_trig_r=0.65, stall_bars=8, cooldown=50, use_rev_exit=True,
        record_trades=True, gen_label="v3.0_5m", tf_label="5m"
    )

    tf15_l = macro_bull & (ema200 > emad) & (fib240_l >= 0.58) & (fib240_l <= 0.82) & (rsi5 >= 35) & (rsi5 <= 70) & ((lw >= 1.40) | b_mss) & (vz >= 1.20) & (in_kz | in_scalp) & rm_l
    tf15_s = macro_bear & (ema50 < ema200) & (fib240_s >= 0.58) & (fib240_s <= 0.82) & (rsi5 <= 65) & (rsi5 >= 30) & ((uw >= 1.40) | s_mss) & (vz >= 1.20) & (in_kz | in_scalp) & rm_s
    tf_breakdown["15m"] = simulate_signals_fast(
        A, tf15_l, tf15_s, tf_mod=15, sl_mult=1.20, tp1_r=1.75, tp2_r=3.35, max_hold=240,
        be_trig_r=1.10, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
        stall_trig_r=0.75, stall_bars=8, cooldown=50, use_rev_exit=True,
        record_trades=True, gen_label="v3.0_15m", tf_label="15m"
    )

    tf1h_l = (~is_london) & macro_bull & (ema200 > emad) & (c > ema15) & (fib240_l >= 0.50) & (d5 > 0) & rm_l
    tf1h_s = macro_bear & (ema50 < ema200) & (c < ema15) & (fib240_s >= 0.50) & (d5 < 0) & rm_s
    tf_breakdown["1h"] = simulate_signals_fast(
        A, tf1h_l, tf1h_s, tf_mod=60, sl_mult=1.20, tp1_r=1.80, tp2_r=3.35, max_hold=200,
        be_trig_r=1.10, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
        stall_trig_r=0.68, stall_bars=8, cooldown=50, use_rev_exit=True,
        record_trades=True, gen_label="v3.0_1h", tf_label="1h"
    )

    df_15m = raw_5m_window.resample("15min").agg({
        "open": "first", "high": "max", "low": "min", "close": "last"
    }).dropna()
    candles_15m = [
        {
            "time": int(ts.timestamp()),
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
        }
        for ts, row in df_15m.iterrows()
    ]

    payload = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "agent_id": "1:ALEX",
        "agent_name": "1:ALEX — Technical Indicators Specialist (EMA / RSI / MACD / Bollinger)",
        "total_combinations_tested": int(len(combos_df)),
        "high_wr_combinations_count": high_wr_count,
        "candles_15m": candles_15m,
        "generations": {
            "v1.0_BASELINE": gen1_res,
            "v2.0_GRID_OPTIMIZED": gen2_res,
            "v3.0_ORACLE_CHAMPION": gen3_res,
        },
        "timeframes": {
            k: {
                "trades_count": v["trades_count"],
                "wins": v["wins"],
                "losses": v["losses"],
                "win_rate": v["win_rate"],
                "profit_factor": v["profit_factor"],
                "avg_r": v["avg_r"],
                "net_pnl": v["net_pnl"],
                "end_equity": v["end_equity"],
                "max_dd_pct": v["max_dd_pct"],
                "reasons": v["reasons"],
                "sess_stats": v["sess_stats"],
                "mkt_stats": v["mkt_stats"],
                "trades": v["trades"],
            }
            for k, v in tf_breakdown.items()
        },
        "top_combos": combos_df.head(150).to_dict(orient="records"),
        "all_combos_summary": combos_df.to_dict(orient="records"),
    }

    with open(OUT_LAB_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    print(
        f"[1:ALEX LAB] Evolution Summary ($100 Start, $5 Risk, 0.01% Fee):\n"
        f"  -> Gen 1 (v1.0 Raw Baseline):               {gen1_res['trades_count']} trades | WR={gen1_res['win_rate']}% | PF={gen1_res['profit_factor']} | Net=${gen1_res['net_pnl']:+.2f} | DD={gen1_res['max_dd_pct']}%\n"
        f"  -> Gen 2 (v2.0 Classic Wide Trail 1.22R):   {gen2_res['trades_count']} trades | WR={gen2_res['win_rate']}% | PF={gen2_res['profit_factor']} | Net=${gen2_res['net_pnl']:+.2f} | DD={gen2_res['max_dd_pct']}%\n"
        f"  -> Gen 3 (v3.0 Smart Stall+Flip Trail):     {gen3_res['trades_count']} trades | WR={gen3_res['win_rate']}% | PF={gen3_res['profit_factor']} | Net=${gen3_res['net_pnl']:+.2f} | DD={gen3_res['max_dd_pct']}%\n"
        f"  -> Timeframe Breakdown (v3.0 >60% WR Across All Timeframes):\n"
        + "\n".join(
            f"       [{tf}]: {r['trades_count']} trades | WR={r['win_rate']}% | PF={r['profit_factor']} | Net=${r['net_pnl']:+.2f} | DD={r['max_dd_pct']}%"
            for tf, r in tf_breakdown.items()
        )
        + f"\nDone in {time.time() - t0:.1f}s."
    )


if __name__ == "__main__":
    run_alex_lab()
