"""
Multi-Agent Pod Combinatorial Optimization Engine
-------------------------------------------------
Simulates dozens of 2-to-3 agent pod combinations and multi-pod desks
across the 5-month Gold dataset to identify settings that maximize
Win Rate (>62-68%), Net Profit, and maintain 2 to 3 trades/day.
"""

import os
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backtest_runner import load_config, CONFIG_PATH
from src.agents.syndicate_agents import precompute_features
from scripts.backtest_agent_2_maya_lab import compute_maya_indicators

def main():
    cfg = load_config(CONFIG_PATH)
    raw_df = pd.read_parquet(os.path.join(BASE_DIR, "data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet"))
    cutoff = raw_df.index[-1] - pd.Timedelta(days=155)
    df_raw = raw_df[raw_df.index >= cutoff].copy()
    print(f"[OPTIMIZER] Loaded 5-month data: {len(df_raw):,} 1m bars")

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

    prime_hrs = np.isin(est_hr, [2, 3, 4, 5, 8, 9, 10, 11, 12, 18, 19, 20, 21])
    base_gate = (~news_lock) & prime_hrs & (spread <= 0.65)
    rk_base = np.clip(1.25 * atr, 3.8, 11.0)
    rm_l = (room_h240 >= 1.05 * rk_base) | (room_h60 >= 0.95 * rk_base)
    rm_s = (room_l240 >= 1.05 * rk_base) | (room_l60 >= 0.95 * rk_base)

    htf_bull = ((c > emam) & (ema200 > emad)) | ((c > emad) & (ema50 > ema200) & (chop < 53.0)) | ((c > ema200) & (ema15 > ema50) & (chop < 51.0) & (d5 > 0))
    htf_bear = ((c < emam) & (ema50 < ema200)) | ((c < emad) & (ema50 < ema200) & (chop < 53.5)) | ((c < ema200) & (ema15 < ema50) & (chop < 51.0) & (d5 < 0))

    sarah_l = (~is_london) & (chop < 54.0) & (rsi5 >= 35) & (rsi5 <= 66) & rm_l
    sarah_s = (rsi5 <= 66) & (rsi5 >= 32) & rm_s

    disc_l = (fib240_l >= 0.48) | (fib60_l >= 0.52)
    prem_s = (fib240_s >= 0.48) | (fib60_s >= 0.52)

    # -------------------------------------------------------------
    # Define Pod Signal Triggers (2-3 Agents Collaborating per Pod)
    # -------------------------------------------------------------
    # POD 1: Scalper & Order Flow Trio: ELENA (Price Action) + OMAR (CVD) + JACK (VSA)
    pod1_long = base_gate & htf_bull & sarah_l & (c > ema15) & disc_l & (
        (c > ema9) & (b_mss | (lw >= 1.12)) & (((d5 > 0) & (d15 > 0)) | b_abs | (vz >= 0.65))
    )
    pod1_short = base_gate & htf_bear & sarah_s & (c < ema15) & prem_s & (
        (c < ema9) & (s_mss | (uw >= 1.12)) & (((d5 < 0) & (d15 < 0)) | s_abs | (vz >= 0.65))
    )

    # POD 2: Institutional SMC Trio: NINA (Sweep/FVG) + SAM (L2 Liquidity) + KAI (Fib OTE)
    pod2_long = base_gate & htf_bull & sarah_l & (c > ema15) & (fib240_l >= 0.52) & (
        (bull_fvg | (l <= sl20 * 1.0018) | l_grab | (u_liq >= 37.0)) & ((lw >= 1.10) | b_mss | (d5 > 0)) & (vz >= 0.52)
    )
    pod2_short = base_gate & htf_bear & sarah_s & (c < ema15) & (fib240_s >= 0.52) & (
        (bear_fvg | (h >= sh20 * 0.9982) | u_grab | (l_liq >= 37.0)) & ((uw >= 1.10) | s_mss | (d5 < 0)) & (vz >= 0.52)
    )

    # POD 3: High-R:R Breakout Trio: MARCUS (Box Breakout) + ARTHUR (Macro Trend) + JACK (Volume Surge)
    pod3_long = base_gate & (c > emam) & (ema200 > emad) & sarah_l & (c > ema15) & (chop < 52.0) & (
        ((rpos60 <= 0.65) | (c > sh20)) & (bull_disp | b_mss | (lw >= 1.15)) & (vz >= 0.85)
    )
    pod3_short = base_gate & (c < emam) & (ema50 < ema200) & sarah_s & (c < ema15) & (chop < 52.5) & (
        ((rpos60 >= 0.35) | (c < sl20)) & (bear_disp | s_mss | (uw >= 1.15)) & (vz >= 0.85)
    )

    # POD 4: Range Extremes & Boundary Trap Trio: MAX (Range Trap) + ELENA (Wick) + SAM (L2 Wall)
    pod4_long = base_gate & sarah_l & (chop >= 48.0) & (
        ((rpos60 <= 0.40) | l_grab) & ((lw >= 1.25) | b_mss) & (vz >= 0.60)
    )
    pod4_short = base_gate & sarah_s & (chop >= 48.0) & (
        ((rpos60 >= 0.60) | u_grab) & ((uw >= 1.25) | s_mss) & (vz >= 0.60)
    )

    # POD 5: Multi-Pod Unified Desk (Rotates between best pod depending on market conditions)
    pod5_long = pod1_long | (pod2_long & (vz >= 0.60)) | (pod3_long & (chop < 50.0)) | (pod4_long & (chop >= 52.0))
    pod5_short = pod1_short | (pod2_short & (vz >= 0.60)) | (pod3_short & (chop < 50.0)) | (pod4_short & (chop >= 52.0))

    pods = [
        ("POD_1_SCALPER_TRIO", "ELENA (PA) + OMAR (CVD) + JACK (VSA)", pod1_long, pod1_short),
        ("POD_2_SMC_DEPTH_TRIO", "NINA (SMC) + SAM (L2) + KAI (Fib OTE)", pod2_long, pod2_short),
        ("POD_3_BREAKOUT_RUNNER_TRIO", "MARCUS (Box) + ARTHUR (Macro) + JACK (Vol)", pod3_long, pod3_short),
        ("POD_4_RANGE_TRAP_TRIO", "MAX (Range) + ELENA (Wick) + SAM (L2 Wall)", pod4_long, pod4_short),
        ("POD_5_UNIFIED_DESK", "Dynamic Floor Multi-Pod Relay (16 Agents)", pod5_long, pod5_short),
    ]

    print("\n" + "=" * 115)
    print("RUNNING GRID SEARCH ACROSS 2-3 AGENT PODS AND TRAILING/TARGET SETTINGS")
    print("=" * 115)

    # Fast simulation engine
    def run_sim(m_l, m_s, sl_mult, tp1_r, tp2_r, be_trig, be_lock, trail_trig, trail_dist, stall_trig, stall_bars, stall_lock, cooldown, max_hold=110):
        sig_idxs = np.where(m_l | m_s)[0]
        sig_idxs = sig_idxs[(sig_idxs >= 2000) & (sig_idxs < len(c) - max_hold - 5)]

        trades_pnl = []
        rs = []
        last_exit = -999
        eq = 100.0
        peak_eq = 100.0
        max_dd = 0.0

        for idx in sig_idxs:
            if idx < last_exit + cooldown:
                continue
            is_long = m_l[idx]
            entry = float(c[idx])
            rk = float(np.clip(sl_mult * atr[idx], 3.8, 11.0))
            qty = 5.0 / rk

            sl_init = entry - rk if is_long else entry + rk
            cur_sl = sl_init
            be_px = entry + be_trig * rk if is_long else entry - be_trig * rk
            tp1_px = entry + tp1_r * rk if is_long else entry - tp1_r * rk
            tp2_px = entry + tp2_r * rk if is_long else entry - tp2_r * rk

            stage = 0
            stall_locked = False
            banked_pts = 0.0
            rem_weight = 1.0
            peak_r = 0.0
            peak_k = idx
            exit_px = None
            exit_i = idx + max_hold

            end_k = min(len(c), idx + max_hold + 1)
            for k in range(idx + 1, end_k):
                bars_held = k - idx
                if is_long:
                    cur_mfe = (h[k] - entry) / rk
                    cur_r = (c[k] - entry) / rk
                    if cur_mfe > peak_r:
                        peak_r = cur_mfe
                        peak_k = k

                    if l[k] <= cur_sl:
                        exit_px = cur_sl
                        exit_i = k
                        break
                    if h[k] >= tp2_px:
                        exit_px = tp2_px
                        exit_i = k
                        break

                    # Stall lock
                    if stage == 0 and stall_trig > 0 and peak_r >= stall_trig and (k - peak_k >= stall_bars or (s_mss[k] and d5[k] < 0)):
                        if c[k] >= entry + stall_lock * rk:
                            cur_sl = max(cur_sl, entry + stall_lock * rk)
                            stage = 1
                            stall_locked = True

                    if stage == 0 and h[k] >= be_px:
                        cur_sl = max(cur_sl, entry + be_lock * rk)
                        stage = 1

                    if stage <= 1 and h[k] >= tp1_px:
                        banked_pts += 0.50 * (tp1_px - entry)
                        rem_weight = 0.50
                        cur_sl = max(cur_sl, entry + 0.45 * rk)
                        stage = 2
                    elif stage == 2 and cur_mfe >= trail_trig:
                        cand = c[k] - trail_dist * rk
                        if cand > cur_sl:
                            cur_sl = cand

                    # Reversal exit
                    if bars_held >= 10 and s_mss[k] and c[k] < ema15[k] and d5[k] < 0 and vz[k] >= 1.45:
                        if stage >= 1 and peak_r >= 1.10 and cur_r >= 0.45 and (peak_r - cur_r) >= 0.55:
                            exit_px = float(c[k])
                            exit_i = k
                            break
                        elif stage == 0 and bars_held >= 18 and peak_r < 0.35 and (-0.78 <= cur_r <= -0.42) and c[k] < sl20[k] and vz[k] >= 1.55:
                            exit_px = float(c[k])
                            exit_i = k
                            break
                else:
                    cur_mfe = (entry - l[k]) / rk
                    cur_r = (entry - c[k]) / rk
                    if cur_mfe > peak_r:
                        peak_r = cur_mfe
                        peak_k = k

                    if h[k] >= cur_sl:
                        exit_px = cur_sl
                        exit_i = k
                        break
                    if l[k] <= tp2_px:
                        exit_px = tp2_px
                        exit_i = k
                        break

                    # Stall lock
                    if stage == 0 and stall_trig > 0 and peak_r >= stall_trig and (k - peak_k >= stall_bars or (b_mss[k] and d5[k] > 0)):
                        if c[k] <= entry - stall_lock * rk:
                            cur_sl = min(cur_sl, entry - stall_lock * rk)
                            stage = 1
                            stall_locked = True

                    if stage == 0 and l[k] <= be_px:
                        cur_sl = min(cur_sl, entry - be_lock * rk)
                        stage = 1

                    if stage <= 1 and l[k] <= tp1_px:
                        banked_pts += 0.50 * (entry - tp1_px)
                        rem_weight = 0.50
                        cur_sl = min(cur_sl, entry - 0.45 * rk)
                        stage = 2
                    elif stage == 2 and cur_mfe >= trail_trig:
                        cand = c[k] + trail_dist * rk
                        if cand < cur_sl:
                            cur_sl = cand

                    # Reversal exit
                    if bars_held >= 10 and b_mss[k] and c[k] > ema15[k] and d5[k] > 0 and vz[k] >= 1.45:
                        if stage >= 1 and peak_r >= 1.10 and cur_r >= 0.45 and (peak_r - cur_r) >= 0.55:
                            exit_px = float(c[k])
                            exit_i = k
                            break
                        elif stage == 0 and bars_held >= 18 and peak_r < 0.35 and (-0.78 <= cur_r <= -0.42) and c[k] > sh20[k] and vz[k] >= 1.55:
                            exit_px = float(c[k])
                            exit_i = k
                            break

            if exit_px is None:
                exit_px = float(c[exit_i])

            rem_pts = (exit_px - entry) if is_long else (entry - exit_px)
            tot_pts = banked_pts + rem_weight * rem_pts
            r_mult = tot_pts / rk
            gross_usd = r_mult * 5.0

            # Delta fee
            entry_notional = qty * entry
            exit_notional = qty * (0.50 * tp1_px + 0.50 * exit_px if rem_weight < 1.0 else exit_px)
            fee = 0.0001 * (entry_notional + exit_notional)
            net_usd = gross_usd - fee

            eq += net_usd
            if eq > peak_eq:
                peak_eq = eq
            dd = (eq - peak_eq) / peak_eq * 100.0
            if dd < max_dd:
                max_dd = dd

            trades_pnl.append(net_usd)
            rs.append(r_mult)
            last_exit = exit_i

        n = len(trades_pnl)
        if n == 0:
            return None
        wins = sum(1 for x in trades_pnl if x > 0)
        wr = (wins / n) * 100.0
        gw = sum(x for x in trades_pnl if x > 0)
        gl = abs(sum(x for x in trades_pnl if x <= 0))
        pf = (gw / gl) if gl > 0 else 99.0
        net = sum(trades_pnl)
        return {
            "n": n,
            "tpd": round(n / 110.0, 2),
            "wr": round(wr, 2),
            "pf": round(pf, 2),
            "net": round(net, 2),
            "eq": round(eq, 2),
            "avg_r": round(float(np.mean(rs)), 2),
            "max_dd": round(max_dd, 2),
        }

    # Test parameter variations across the pods
    test_params = [
        # sl_m, tp1_r, tp2_r, be_trig, be_lock, trail_trig, trail_dist, stall_trig, stall_bars, stall_lock, cd
        ("Standard Trail (TP1 1.75R | TP2 3.35R | Stall +0.54R->+0.28R)", 1.35, 1.75, 3.35, 1.05, 0.38, 2.10, 1.05, 0.54, 6, 0.28, 6),
        ("Extended Runner (TP1 1.85R | TP2 4.25R | Stall +0.55R->+0.30R)", 1.35, 1.85, 4.25, 1.05, 0.38, 2.20, 1.10, 0.55, 6, 0.30, 6),
        ("High-Reward Swing (TP1 1.95R | TP2 5.50R | Stall +0.56R->+0.32R)", 1.35, 1.95, 5.50, 1.10, 0.40, 2.30, 1.15, 0.56, 6, 0.32, 6),
        ("Quick Lock Scalper (TP1 1.65R | TP2 3.10R | Stall +0.50R->+0.26R)", 1.30, 1.65, 3.10, 1.00, 0.35, 1.95, 1.00, 0.50, 5, 0.26, 5),
    ]

    for p_name, p_label, ml, ms in pods:
        print(f"\n--- {p_name}: {p_label} ---")
        for desc, sm, t1, t2, bet, bel, trt, trd, stt, stb, stl, cd in test_params:
            res = run_sim(ml, ms, sm, t1, t2, bet, bel, trt, trd, stt, stb, stl, cd)
            if res:
                print(
                    f"  [{res['n']:3d} tr | {res['tpd']} tr/d] WR: {res['wr']:5.2f}% | PF: {res['pf']:4.2f} | "
                    f"AvgR: {res['avg_r']:+5.2f}R | Net: ${res['net']:+7.2f} | EndEq: ${res['eq']:7.2f} | "
                    f"DD: {res['max_dd']:5.2f}% | {desc[:48]}"
                )

if __name__ == "__main__":
    main()
