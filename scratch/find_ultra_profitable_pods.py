"""
Ultra High-Performance Pod & Strategy Optimizer
-----------------------------------------------
Scans hundreds of 2-agent, 3-agent, and specialist pod combinations to find
the highest Win Rate (>65-72%), highest Profit Factor (>1.45-1.80),
highest Net Profit (+$180 to +$250+), and lowest Drawdown (<12-15%)
while strictly maintaining 2 to 3 trades per active day (~220-330 trades).
"""

import os
import sys
import itertools
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
    print(f"[SCANNER] Loaded 5-month data: {len(df_raw):,} 1m bars")

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

    prime_hrs = np.isin(est_hr, [2, 3, 4, 5, 8, 9, 10, 11, 12, 18, 19, 20, 21])
    base_gate = (~news_lock) & prime_hrs & (spread <= 0.65)
    rk_base = np.clip(1.25 * atr, 3.8, 11.0)
    rm_l = (room_h240 >= 1.05 * rk_base) | (room_h60 >= 0.95 * rk_base)
    rm_s = (room_l240 >= 1.05 * rk_base) | (room_l60 >= 0.95 * rk_base)

    htf_bull = ((c > emam) & (ema200 > emad)) | ((c > emad) & (ema50 > ema200) & (chop < 52.5)) | ((c > ema200) & (ema15 > ema50) & (chop < 50.0) & (d5 > 0))
    htf_bear = ((c < emam) & (ema50 < ema200)) | ((c < emad) & (ema50 < ema200) & (chop < 53.5)) | ((c < ema200) & (ema15 < ema50) & (chop < 51.0) & (d5 < 0))

    sarah_l = (~is_london) & (chop < 53.5) & (rsi5 >= 35) & (rsi5 <= 66) & rm_l
    sarah_s = (rsi5 <= 66) & (rsi5 >= 32) & rm_s

    disc_l = (fib240_l >= 0.50) | (fib60_l >= 0.54)
    prem_s = (fib240_s >= 0.50) | (fib60_s >= 0.54)

    gate_l = base_gate & htf_bull & sarah_l & (c > ema15) & disc_l
    gate_s = base_gate & htf_bear & sarah_s & (c < ema15) & prem_s

    # Specialist core signals
    specs = {
        "1:ALEX": (
            (rsi5 >= 43) & ((c > ema9) | (d5 > 0)) & (vz >= 0.50),
            (rsi5 <= 57) & ((c < ema9) | (d5 < 0)) & (vz >= 0.50),
        ),
        "2:MAYA": (
            ((lw >= 1.15) | b_mss | bull_disp) & (vz >= 0.48),
            ((uw >= 1.15) | s_mss | bear_disp) & (vz >= 0.48),
        ),
        "3:MARCUS": (
            (chop < 52.8) & ((rpos60 <= 0.64) | (fib240_l >= 0.50)) & ((lw >= 1.05) | b_mss | bull_disp | (d5 > 0)) & (vz >= 0.44),
            (chop < 53.4) & ((rpos60 >= 0.36) | (fib240_s >= 0.50)) & ((uw >= 1.05) | s_mss | bear_disp | (d5 < 0)) & (vz >= 0.44),
        ),
        "4:NINA": (
            (bull_fvg | (l <= sl20 * 1.0018) | (lw >= 1.18) | b_mss) & (vz >= 0.58),
            (bear_fvg | (h >= sh20 * 0.9982) | (uw >= 1.18) | s_mss) & (vz >= 0.58),
        ),
        "5:MAX": (
            ((rpos60 <= 0.58) | l_grab | (fib240_l >= 0.52)) & ((lw >= 1.10) | b_mss | (d5 > 0)) & (vz >= 0.64),
            ((rpos60 >= 0.42) | u_grab | (fib240_s >= 0.52)) & ((uw >= 1.10) | s_mss | (d5 < 0)) & (vz >= 0.64),
        ),
        "6:SOPHIA": (
            (kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42),
            (kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42),
        ),
        "7:DEREK": (
            ((fib240_l >= 0.53) | (fib60_l >= 0.57)) & (fib240_l <= 0.86) & (vz >= 0.52),
            ((fib240_s >= 0.53) | (fib60_s >= 0.57)) & (fib240_s <= 0.86) & (vz >= 0.52),
        ),
        "8:ELENA": (
            (c > ema9) & (b_mss | (lw >= 1.12)) & (vz >= 0.32),
            (c < ema9) & (s_mss | (uw >= 1.12)) & (vz >= 0.32),
        ),
        "9:SAM": (
            ((l_liq >= 35.5) | (u_liq >= 37.5) | l_grab) & (vz >= 0.56),
            ((u_liq >= 35.5) | (l_liq >= 37.5) | u_grab) & (vz >= 0.56),
        ),
        "10:OMAR": (
            (((d5 > 0) & (d15 > 0)) | b_abs) & (vz >= 0.62),
            (((d5 < 0) & (d15 < 0)) | s_abs) & (vz >= 0.62),
        ),
        "11:LIAM": (
            (stop_b | (vz >= 0.80)) & (vz >= 0.70),
            (stop_s | (vz >= 0.80)) & (vz >= 0.70),
        ),
    }

    # Fast simulation engine
    def run_sim(m_l, m_s, sl_mult=1.35, tp1_r=1.80, tp2_r=3.35, be_trig=1.05, be_lock=0.38, trail_trig=2.10, trail_dist=1.05, stall_trig=0.54, stall_bars=6, stall_lock=0.28, cooldown=7, max_hold=110):
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
        return {
            "n": n,
            "tpd": round(n / 110.0, 2),
            "wr": round(wr, 2),
            "pf": round(pf, 2),
            "net": round(sum(trades_pnl), 2),
            "eq": round(eq, 2),
            "avg_r": round(float(np.mean(rs)), 2),
            "max_dd": round(max_dd, 2),
        }

    results = []

    # 1. Test all 2-agent pairs:
    # A) Pair Confirmation (Both Agent A AND Agent B agree)
    # B) Pod Synergy (Agent A OR Agent B agree inside HTF + Sarah gate)
    agent_names = list(specs.keys())

    print("\n--- Scanning 2-Agent and 3-Agent Pod Synergies ---")
    for a1, a2 in itertools.combinations(agent_names, 2):
        l1, s1 = specs[a1]
        l2, s2 = specs[a2]

        # OR synergy: (A1 or A2) inside gate
        ml_or = gate_l & (l1 | l2)
        ms_or = gate_s & (s1 | s2)
        res_or = run_sim(ml_or, ms_or, tp1_r=1.80, tp2_r=3.35, cooldown=7)
        if res_or and 200 <= res_or["n"] <= 350 and res_or["net"] > 140:
            results.append((f"{a1} + {a2} (Synergy OR)", res_or))

        # AND confirmation: (A1 and A2) inside gate
        ml_and = gate_l & l1 & l2
        ms_and = gate_s & s1 & s2
        res_and = run_sim(ml_and, ms_and, tp1_r=1.80, tp2_r=3.35, cooldown=5)
        if res_and and 180 <= res_and["n"] <= 350 and res_and["net"] > 140:
            results.append((f"{a1} & {a2} (Confirm AND)", res_and))

    # 2. Test 3-agent pods: (A1 or (A2 and A3))
    for a1, a2, a3 in itertools.combinations(agent_names, 3):
        l1, s1 = specs[a1]
        l2, s2 = specs[a2]
        l3, s3 = specs[a3]

        ml_pod = gate_l & (l1 | (l2 & l3))
        ms_pod = gate_s & (s1 | (s2 & s3))
        res = run_sim(ml_pod, ms_pod, tp1_r=1.80, tp2_r=3.35, cooldown=7)
        if res and 220 <= res["n"] <= 330 and res["net"] > 160:
            results.append((f"{a1} + ({a2} & {a3})", res))

    results.sort(key=lambda x: x[1]["net"], reverse=True)

    print(f"\nTOP {min(20, len(results))} HIGHEST PROFIT PODS IDENTIFIED:")
    print(f"{'Pod Combination':<40} | {'Trades':>6} | {'Tr/Day':>6} | {'WinRate':>7} | {'PF':>5} | {'Net PnL':>10} | {'End Eq':>9} | {'Max DD':>7}")
    print("-" * 105)
    for name, r in results[:20]:
        print(f"{name:<40} | {r['n']:6d} | {r['tpd']:6.2f} | {r['wr']:6.2f}% | {r['pf']:5.2f} | ${r['net']:+9.2f} | ${r['eq']:8.2f} | {r['max_dd']:6.2f}%")

if __name__ == "__main__":
    main()
