"""
Test Elite Combinations of Top Performing Specialists
"""

import os
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backtest_runner import load_config, CONFIG_PATH, load_dataset
from src.agents.syndicate_agents import precompute_features
from scripts.backtest_all_11_agents_lab import compute_maya_indicators, simulate_specialist_fast

def main():
    cfg = load_config(CONFIG_PATH)
    raw_df = load_dataset()
    cutoff = raw_df.index[-1] - pd.Timedelta(days=155)
    df_raw = raw_df[raw_df.index >= cutoff].copy()

    df = precompute_features(df_raw, cfg)
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
    d15 = df["delta_sum_15"].to_numpy()
    in_session, news_lock, spread = A["in_session"], A["news_lock"], A["spread"]
    room_h60, room_l60 = A["room_h60"], A["room_l60"]
    room_h240, room_l240 = A["room_h240"], A["room_l240"]
    sess_arr = A["sess"]
    is_london = sess_arr == "LONDON"
    est_hr = (df.index.hour - 5) % 24

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

    prime_hrs = np.isin(est_hr, [2, 3, 4, 5, 8, 10, 11, 12, 18, 20, 21])
    base_gate = (~news_lock) & prime_hrs & (spread <= 0.65)
    rk_base = np.clip(1.25 * atr, 3.8, 11.0)
    rm_l = (room_h240 >= 1.10 * rk_base) | (room_h60 >= 1.00 * rk_base)
    rm_s = (room_l240 >= 1.10 * rk_base) | (room_l60 >= 1.00 * rk_base)

    htf_bull = ((c > emam) & (ema200 > emad)) | ((c > emad) & (ema50 > ema200) & (chop < 52.5)) | ((c > ema200) & (ema15 > ema50) & (chop < 50.0) & (d5 > 0))
    htf_bear = ((c < emam) & (ema50 < ema200)) | ((c < emad) & (ema50 < ema200) & (chop < 53.5)) | ((c < ema200) & (ema15 < ema50) & (chop < 51.0) & (d5 < 0))

    sarah_l = (~is_london) & (chop < 53.5) & (rsi5 >= 35) & (rsi5 <= 66) & rm_l
    sarah_s = (rsi5 <= 66) & (rsi5 >= 32) & rm_s

    disc_l = (fib240_l >= 0.50) | (fib60_l >= 0.54)
    prem_s = (fib240_s >= 0.50) | (fib60_s >= 0.54)

    # Base gate
    gate_l = base_gate & htf_bull & sarah_l & (c > ema15) & disc_l
    gate_s = base_gate & htf_bear & sarah_s & (c < ema15) & prem_s

    # Specialists:
    # 2:MAYA
    maya_l = gate_l & (((lw >= 1.15) | b_mss | bull_disp) & (vz >= 0.48))
    maya_s = gate_s & (((uw >= 1.15) | s_mss | bear_disp) & (vz >= 0.48))

    # 11:LIAM (JACK)
    liam_l = gate_l & ((stop_b | (vz >= 0.80)) & (vz >= 0.70))
    liam_s = gate_s & ((stop_s | (vz >= 0.80)) & (vz >= 0.70))

    # 6:SOPHIA (LEO)
    sophia_l = gate_l & ((kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42))
    sophia_s = gate_s & ((kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42))

    # 9:SAM
    sam_l = gate_l & (((l_liq >= 35.5) | (u_liq >= 37.5) | l_grab) & (vz >= 0.56))
    sam_s = gate_s & (((u_liq >= 35.5) | (l_liq >= 37.5) | u_grab) & (vz >= 0.56))

    # 3:MARCUS
    marcus_l = gate_l & ((chop < 52.8) & ((rpos60 <= 0.64) | (fib240_l >= 0.50)) & ((lw >= 1.05) | b_mss | bull_disp | (d5 > 0)) & (vz >= 0.44))
    marcus_s = gate_s & ((chop < 53.4) & ((rpos60 >= 0.36) | (fib240_s >= 0.50)) & ((uw >= 1.05) | s_mss | bear_disp | (d5 < 0)) & (vz >= 0.44))

    # 8:ELENA
    elena_l = gate_l & ((c > ema9) & (b_mss | (lw >= 1.12)) & (vz >= 0.32))
    elena_s = gate_s & ((c < ema9) & (s_mss | (uw >= 1.12)) & (vz >= 0.32))

    # 10:OMAR
    omar_l = gate_l & ((((d5 > 0) & (d15 > 0)) | b_abs) & (vz >= 0.62))
    omar_s = gate_s & ((((d5 < 0) & (d15 < 0)) | s_abs) & (vz >= 0.62))

    combos = [
        ("1. MAYA + LIAM Pod (Price Action + VSA Stopping Volume)", maya_l | liam_l, maya_s | liam_s, 1.35, 1.80, 3.35, 0.54, 6, 8),
        ("2. SOPHIA + LIAM Pod (Killzone Timing + VSA Volume Surge)", sophia_l | liam_l, sophia_s | liam_s, 1.35, 1.80, 3.35, 0.54, 6, 8),
        ("3. MARCUS + SOPHIA Pod (Box Breakout + Macro Killzone Runner)", marcus_l | sophia_l, marcus_s | sophia_s, 1.36, 1.85, 4.25, 0.54, 6, 8),
        ("4. MAYA + SAM Pod (Price Action MSS + L2 DOM Liquidity)", maya_l | sam_l, maya_s | sam_s, 1.35, 1.80, 3.35, 0.54, 6, 8),
        ("5. ELENA + OMAR + LIAM Pod (Scalper + CVD Order Flow + VSA)", elena_l | omar_l | liam_l, elena_s | omar_s | liam_s, 1.34, 1.80, 3.35, 0.54, 6, 8),
        ("6. ALL-STAR COUNCIL RELAY (Maya + Liam + Sophia + Marcus + Sam)", maya_l | liam_l | sophia_l | marcus_l | sam_l, maya_s | liam_s | sophia_s | marcus_s | sam_s, 1.35, 1.80, 3.80, 0.54, 6, 8),
        # Pure individual champions:
        ("7. 11:LIAM / JACK Pure (VSA Stopping Volume & POC)", liam_l, liam_s, 1.35, 1.80, 3.35, 0.55, 6, 9),
        ("8. 2:MAYA Pure (Pinbar Wick MSS & Anti-FOMO)", maya_l, maya_s, 1.35, 1.80, 3.35, 0.54, 6, 6),
        ("9. 6:SOPHIA Pure (ICT Killzone & Silver Bullet)", sophia_l, sophia_s, 1.35, 1.80, 3.35, 0.54, 6, 5),
    ]

    print("\n" + "=" * 125)
    print(f"{'Combo / Strategy Setting':<52} | {'Trades':>6} | {'Tr/Day':>6} | {'WinRate':>7} | {'PF':>5} | {'Avg R':>7} | {'Net PnL':>10} | {'End Eq':>9} | {'Max DD':>7}")
    print("=" * 125)

    for name, ml, ms, sm, t1, t2, stt, stb, cd in combos:
        res = simulate_specialist_fast(
            A, ml, ms, tf_mod=1, sl_mult=sm, tp1_r=t1, tp2_r=t2, max_hold=110,
            be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
            stall_trig_r=stt, stall_bars=stb, cooldown=cd, use_rev_exit=True
        )
        if res:
            print(
                f"{name:<52} | {res['trades_count']:6d} | {res['trades_per_day']:6.2f} | {res['win_rate']:6.2f}% | "
                f"{res['profit_factor']:5.2f} | {res['avg_r']:+6.2f}R | ${res['net_pnl']:+9.2f} | ${res['end_equity']:8.2f} | {res['max_dd_pct']:6.2f}%"
            )

if __name__ == "__main__":
    main()
