"""
Syndicate Alpha — 2-Year Specialist Bundle Generator
Runs all 11 Field Specialists across 699,702 1m bars for 2 full years (Nov 1, 2024 to Oct 30, 2026).
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backtest_runner import load_config, CONFIG_PATH
from src.agents.syndicate_agents import precompute_features
from scripts.backtest_agent_2_maya_lab import compute_maya_indicators
from scripts.backtest_all_11_agents_lab import simulate_specialist_fast

OUT_2Y_BUNDLE = os.path.join(BASE_DIR, "data", "processed", "all_11_agents_2year_bundle.json")

def generate_2year_bundle():
    t0 = time.time()
    cfg = load_config(CONFIG_PATH)
    parquet_path = os.path.join(BASE_DIR, "data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
    print(f"[1/3] Loading Full 2-Year Parquet Dataset: {parquet_path}...")
    raw_df = pd.read_parquet(parquet_path)
    if not raw_df.index.tz:
        raw_df.index = raw_df.index.tz_localize('UTC')
    else:
        raw_df.index = raw_df.index.tz_convert('UTC')

    print(f"Loaded {len(raw_df):,} bars from {raw_df.index[0]} to {raw_df.index[-1]}")
    print("[2/3] Precomputing features across 699,702 bars...")
    df = precompute_features(raw_df, cfg)
    A = compute_maya_indicators(df)

    c, h, l, o = A["c"], A["h"], A["l"], A["o"]
    ema9, ema15, ema21, ema50, ema200, emad, emam = (
        A["ema9"], A["ema15"], A["ema21"], A["ema50"], A["ema200"], A["emad"], A["emam"]
    )
    rsi5, vz, lw, uw, b_mss, s_mss = A["rsi5"], A["vz"], A["lw"], A["uw"], A["b_mss"], A["s_mss"]
    bull_disp, bear_disp = A["bull_disp"], A["bear_disp"]
    fib60_l = df["fib_retracement_long"].to_numpy()
    fib60_s = df["fib_retracement_short"].to_numpy()
    fib240_l, fib240_s, chop, adx, atr, d5 = A["fib240_l"], A["fib240_s"], A["chop"], A["adx"], A["atr"], A["d5"]
    in_session, news_lock, spread = A["in_session"], A["news_lock"], A["spread"]
    room_h60, room_l60 = A["room_h60"], A["room_l60"]
    room_h240, room_l240 = A["room_h240"], A["room_l240"]
    sess_arr = A["sess"]
    is_london = sess_arr == "LONDON"
    est_hr = (df.index.hour - 5) % 24
    mins = df.index.minute.to_numpy()

    poc60 = df["poc_60"].to_numpy()
    rpos60 = df["range_pos_60"].to_numpy()
    sh20, sl20 = A["sh20"], A["sl20"]
    bull_fvg = df["bull_fvg"].rolling(10, min_periods=1).max().to_numpy() > 0
    bear_fvg = df["bear_fvg"].rolling(10, min_periods=1).max().to_numpy() > 0
    u_liq, l_liq = A["u_liq"], A["l_liq"]
    u_grab = df["upper_liq_grabbed"].rolling(10, min_periods=1).max().to_numpy() > 0
    l_grab = df["lower_liq_grabbed"].rolling(10, min_periods=1).max().to_numpy() > 0
    b_abs = df["bull_absorption"].rolling(8, min_periods=1).max().to_numpy() > 0
    s_abs = df["bear_absorption"].rolling(8, min_periods=1).max().to_numpy() > 0
    stop_b = df["stopping_vol_bull"].rolling(10, min_periods=1).max().to_numpy() > 0
    stop_s = df["stopping_vol_bear"].rolling(10, min_periods=1).max().to_numpy() > 0
    sb_win = df["silver_bullet"].to_numpy()
    kz_win = df["in_killzone"].to_numpy()

    ema12_5m = df["close"].ewm(span=60, adjust=False).mean()
    ema26_5m = df["close"].ewm(span=130, adjust=False).mean()
    macd_l = ema12_5m - ema26_5m
    macd_s = macd_l.ewm(span=45, adjust=False).mean()
    macd_h = (macd_l - macd_s).to_numpy()
    macd_up = macd_h > np.roll(macd_h, 3)
    macd_dn = macd_h < np.roll(macd_h, 3)

    prime_hrs = np.isin(est_hr, [2, 3, 4, 5, 8, 10, 11, 12, 18, 20, 21])
    base_gate = (~news_lock) & prime_hrs & (spread <= 0.65)
    macro_gate = (~news_lock) & in_session & (spread <= 0.65)
    rk_base = np.clip(1.25 * atr, 3.8, 11.0)
    rm_l = (room_h240 >= 1.10 * rk_base) | (room_h60 >= 1.00 * rk_base)
    rm_s = (room_l240 >= 1.10 * rk_base) | (room_l60 >= 1.00 * rk_base)

    htf_bull = ((c > emam) & (ema200 > emad)) | ((c > emad) & (ema50 > ema200) & (chop < 52.5)) | ((c > ema200) & (ema15 > ema50) & (chop < 50.0) & (d5 > 0))
    htf_bear = ((c < emam) & (ema50 < ema200)) | ((c < emad) & (ema50 < ema200) & (chop < 53.5)) | ((c < ema200) & (ema15 < ema50) & (chop < 51.0) & (d5 < 0))

    sarah_l = (~is_london) & (chop < 53.5) & (rsi5 >= 35) & (rsi5 <= 66) & rm_l
    sarah_s = (rsi5 <= 66) & (rsi5 >= 32) & rm_s
    disc_l = (fib240_l >= 0.50) | (fib60_l >= 0.54)
    prem_s = (fib240_s >= 0.50) | (fib60_s >= 0.54)
    htf_disc_l = (fib240_l >= 0.57) | (fib60_l >= 0.61)
    htf_prem_s = (fib240_s >= 0.57) | (fib60_s >= 0.61)

    is_5m = (mins % 5) == 0
    is_15m = (mins % 15) == 0

    macro_bull_1h = (~news_lock) & in_session & (~is_london) & (c > emam) & (ema200 > emad) & (c > ema15) & (chop < 53.2) & (rsi5 <= 65) & rm_l
    macro_bear_1h = (~news_lock) & in_session & (c < emam) & (ema50 < ema200) & (c < ema15) & (rsi5 >= 33) & rm_s

    specialists = [
        {
            "id": "1:ALEX", "slug": "agent_1_alex", "role": "Technical Indicators",
            "tl": (macd_up | (rsi5 >= 43)) & ((c > ema9) | (d5 > 0)) & (vz >= 0.50),
            "ts": (macd_dn | (rsi5 <= 57)) & ((c < ema9) | (d5 < 0)) & (vz >= 0.50),
            "tl1h": (fib240_l >= 0.56) & (macd_up | (rsi5 >= 40) | (d5 > 0)),
            "ts1h": (fib240_s >= 0.56) & (macd_dn | (rsi5 <= 60) | (d5 < 0)),
            "params": (1.35, 1.80, 3.35, 110, 0.54, 6, 8),
        },
        {
            "id": "2:MAYA", "slug": "agent_2_maya", "role": "Price Action + Psych",
            "tl": ((lw >= 1.15) | b_mss | bull_disp) & (vz >= 0.48),
            "ts": ((uw >= 1.15) | s_mss | bear_disp) & (vz >= 0.48),
            "tl1h": (fib240_l >= 0.56) & ((lw >= 1.12) | b_mss | (d5 > 0)),
            "ts1h": (fib240_s >= 0.56) & ((uw >= 1.12) | s_mss | (d5 < 0)),
            "params": (1.35, 1.80, 3.35, 105, 0.54, 6, 6),
        },
        {
            "id": "3:MARCUS", "slug": "agent_3_marcus", "role": "Box Breakouts",
            "tl": (chop < 52.8) & ((rpos60 <= 0.64) | (fib240_l >= 0.50)) & ((lw >= 1.05) | b_mss | bull_disp | (d5 > 0)) & (vz >= 0.44),
            "ts": (chop < 53.4) & ((rpos60 >= 0.36) | (fib240_s >= 0.50)) & ((uw >= 1.05) | s_mss | bear_disp | (d5 < 0)) & (vz >= 0.44),
            "tl1h": (fib240_l >= 0.53) & (chop < 52.5) & ((rpos60 <= 0.58) | (d5 > 0)),
            "ts1h": (fib240_s >= 0.53) & (chop < 53.0) & ((rpos60 >= 0.42) | (d5 < 0)),
            "params": (1.36, 1.80, 3.35, 110, 0.54, 6, 7),
        },
        {
            "id": "4:NINA", "slug": "agent_4_nina", "role": "SMC / FVG",
            "tl": (bull_fvg | (l <= sl20 * 1.0018) | (lw >= 1.18) | b_mss) & (vz >= 0.58),
            "ts": (bear_fvg | (h >= sh20 * 0.9982) | (uw >= 1.18) | s_mss) & (vz >= 0.58),
            "tl1h": (fib240_l >= 0.55) & (bull_fvg | (l <= sl20 * 1.002) | b_mss | (d5 > 0)),
            "ts1h": (fib240_s >= 0.55) & (bear_fvg | (h >= sh20 * 0.998) | s_mss | (d5 < 0)),
            "params": (1.34, 1.80, 3.35, 110, 0.54, 6, 8),
        },
        {
            "id": "5:MAX", "slug": "agent_5_max", "role": "Sideways / Traps",
            "tl": ((rpos60 <= 0.58) | l_grab | (fib240_l >= 0.52)) & ((lw >= 1.10) | b_mss | (d5 > 0)) & (vz >= 0.64),
            "ts": ((rpos60 >= 0.42) | u_grab | (fib240_s >= 0.52)) & ((uw >= 1.10) | s_mss | (d5 < 0)) & (vz >= 0.64),
            "tl1h": (fib240_l >= 0.55) & ((rpos60 <= 0.52) | l_grab | (lw >= 1.10) | (d5 > 0)),
            "ts1h": (fib240_s >= 0.55) & ((rpos60 >= 0.48) | u_grab | (uw >= 1.10) | (d5 < 0)),
            "params": (1.35, 1.80, 3.35, 108, 0.54, 6, 9),
        },
        {
            "id": "6:SOPHIA", "slug": "agent_6_sophia", "role": "Macro / Killzone",
            "tl": (kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42),
            "ts": (kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42),
            "tl1h": (fib240_l >= 0.57) & (kz_win | sb_win | (est_hr >= 18)) & ((lw >= 1.08) | b_mss | (d5 > 0)),
            "ts1h": (fib240_s >= 0.57) & (kz_win | sb_win | (est_hr >= 18)) & ((uw >= 1.08) | s_mss | (d5 < 0)),
            "params": (1.35, 1.80, 3.35, 105, 0.54, 6, 5),
        },
        {
            "id": "7:DEREK", "slug": "agent_7_derek", "role": "Fib OTE / Vol",
            "tl": ((fib240_l >= 0.53) | (fib60_l >= 0.57)) & (fib240_l <= 0.86) & (vz >= 0.52),
            "ts": ((fib240_s >= 0.53) | (fib60_s >= 0.57)) & (fib240_s <= 0.86) & (vz >= 0.52),
            "tl1h": (fib240_l >= 0.58) & (fib240_l <= 0.85) & ((lw >= 1.05) | (d5 > 0)),
            "ts1h": (fib240_s >= 0.58) & (fib240_s <= 0.85) & ((uw >= 1.05) | (d5 < 0)),
            "params": (1.36, 1.85, 3.40, 118, 0.55, 6, 7),
        },
        {
            "id": "8:ELENA", "slug": "agent_8_elena", "role": "1m Fast Scalper",
            "tl": (c > ema9) & (b_mss | (lw >= 1.12)) & (vz >= 0.32),
            "ts": (c < ema9) & (s_mss | (uw >= 1.12)) & (vz >= 0.32),
            "tl1h": (fib240_l >= 0.57) & (c > ema9) & (b_mss | (lw >= 1.12) | (d5 > 0)),
            "ts1h": (fib240_s >= 0.57) & (c < ema9) & (s_mss | (uw >= 1.12) | (d5 < 0)),
            "params": (1.32, 1.75, 3.25, 95, 0.52, 5, 5),
        },
        {
            "id": "9:SAM", "slug": "agent_9_sam", "role": "Liquidity >40",
            "tl": ((l_liq >= 35.5) | (u_liq >= 37.5) | l_grab) & (vz >= 0.56),
            "ts": ((u_liq >= 35.5) | (l_liq >= 37.5) | u_grab) & (vz >= 0.56),
            "tl1h": (fib240_l >= 0.54) & ((l_liq >= 36.0) | (u_liq >= 38.0) | l_grab) & (d5 > 0),
            "ts1h": (fib240_s >= 0.54) & ((u_liq >= 36.0) | (l_liq >= 38.0) | u_grab) & (d5 < 0),
            "params": (1.35, 1.80, 3.35, 110, 0.54, 6, 8),
        },
        {
            "id": "10:OMAR", "slug": "agent_10_omar", "role": "CVD Order Flow",
            "tl": (((d5 > 0)) | b_abs) & (vz >= 0.62),
            "ts": (((d5 < 0)) | s_abs) & (vz >= 0.62),
            "tl1h": (fib240_l >= 0.56) & (((d5 > 0)) | b_abs | (lw >= 1.15)),
            "ts1h": (fib240_s >= 0.56) & (((d5 < 0)) | s_abs | (uw >= 1.15)),
            "params": (1.35, 1.80, 3.35, 115, 0.55, 6, 8),
        },
        {
            "id": "11:LIAM", "slug": "agent_11_liam", "role": "VSA / VWAP",
            "tl": (stop_b | (vz >= 0.80)) & (vz >= 0.70),
            "ts": (stop_s | (vz >= 0.80)) & (vz >= 0.70),
            "tl1h": (fib240_l >= 0.55) & (stop_b | (vz >= 0.45) | (c <= poc60)) & ((lw >= 1.10) | b_mss | (d5 > 0)),
            "ts1h": (fib240_s >= 0.55) & (stop_s | (vz >= 0.45) | (c >= poc60)) & ((uw >= 1.10) | s_mss | (d5 < 0)),
            "params": (1.35, 1.80, 3.35, 115, 0.55, 6, 9),
        },
    ]

    bundle = {}
    print("\n[3/3] Generating multi-TF trades across 11 specialists for 2 FULL YEARS...")

    for spec in specialists:
        aid = spec["id"]
        sl_m, tp1_r, tp2_r, mh, st_t, st_b, cd = spec["params"]
        tl, ts = spec["tl"], spec["ts"]
        tl1h, ts1h = spec["tl1h"], spec["ts1h"]

        v3_l = base_gate & htf_bull & sarah_l & (c > ema15) & disc_l & tl
        v3_s = base_gate & htf_bear & sarah_s & (c < ema15) & prem_s & ts

        m5_l = is_5m & base_gate & htf_bull & sarah_l & (c > ema15) & htf_disc_l & tl
        m5_s = is_5m & base_gate & htf_bear & sarah_s & (c < ema15) & htf_prem_s & ts

        m15_l = is_15m & base_gate & htf_bull & sarah_l & (c > ema15) & htf_disc_l & tl
        m15_s = is_15m & base_gate & htf_bear & sarah_s & (c < ema15) & htf_prem_s & ts

        m1h_l = macro_bull_1h & tl1h
        m1h_s = macro_bear_1h & ts1h

        # Multi-timeframe execution with record_trades=True
        tf_breakdown = {
            "5m": simulate_specialist_fast(
                A, m5_l, m5_s, tf_mod=1, sl_mult=sl_m, tp1_r=tp1_r, tp2_r=tp2_r, max_hold=mh,
                be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=0.45,
                stall_trig_r=st_t, stall_bars=st_b, cooldown=cd, use_rev_exit=True,
                record_trades=True, agent_id=aid, agent_focus=spec["role"], tf_label="5m"
            ),
            "15m": simulate_specialist_fast(
                A, m15_l, m15_s, tf_mod=1, sl_mult=sl_m, tp1_r=tp1_r, tp2_r=tp2_r, max_hold=mh + 30,
                be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=0.45,
                stall_trig_r=st_t, stall_bars=st_b, cooldown=cd + 5, use_rev_exit=True,
                record_trades=True, agent_id=aid, agent_focus=spec["role"], tf_label="15m"
            ),
            "1h": simulate_specialist_fast(
                A, m1h_l, m1h_s, tf_mod=60, sl_mult=sl_m, tp1_r=tp1_r, tp2_r=tp2_r, max_hold=mh + 60,
                be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=0.45,
                stall_trig_r=st_t + 0.10, stall_bars=st_b + 2, cooldown=cd + 15, use_rev_exit=True,
                record_trades=True, agent_id=aid, agent_focus=spec["role"], tf_label="1h"
            ),
        }

        bundle[aid] = {"timeframes": tf_breakdown}
        t5 = tf_breakdown["5m"]
        print(f"  {aid:10s} | 5m: {t5['trades_count']:3d}t ({t5['win_rate']:5.1f}% WR, ${t5['net_pnl']:+7.2f})")

    with open(OUT_2Y_BUNDLE, "w", encoding="utf-8") as f:
        json.dump(bundle, f)

    print(f"\n[DONE] Saved 2-Year Multi-TF Bundle to {OUT_2Y_BUNDLE} in {time.time() - t0:.1f}s!")

if __name__ == "__main__":
    generate_2year_bundle()
