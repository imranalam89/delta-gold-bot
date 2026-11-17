"""
Runner & Big-Move Exploration ($10 Quick Scalp to $1000 Monster Runner)
------------------------------------------------------------------------
Tests how extending TP2 and dynamic trailing stops impacts Net PnL,
average R, win rate, and the largest winning trades.
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

    # Pod: MARCUS (Breakout) + ARTHUR (Macro) + JACK (Vol)
    marcus_l = (chop < 53.0) & ((rpos60 <= 0.60) | (c > sh20)) & (bull_disp | b_mss | (lw >= 1.10)) & (vz >= 0.40)
    marcus_s = (chop < 53.0) & ((rpos60 >= 0.40) | (c < sl20)) & (bear_disp | s_mss | (uw >= 1.10)) & (vz >= 0.40)
    jack_l = (stop_b | (vz >= 0.70))
    jack_s = (stop_s | (vz >= 0.70))

    pod_breakout_l = gate_l & marcus_l & jack_l
    pod_breakout_s = gate_s & marcus_s & jack_s

    # Pod: SMC + L2 + Fib
    nina_l = (bull_fvg | (l <= sl20 * 1.002) | (lw >= 1.15) | b_mss) & (vz >= 0.45)
    nina_s = (bear_fvg | (h >= sh20 * 0.998) | (uw >= 1.15) | s_mss) & (vz >= 0.45)
    sam_l = ((l_liq >= 36.0) | (u_liq >= 38.0) | l_grab) & (vz >= 0.45)
    sam_s = ((u_liq >= 36.0) | (l_liq >= 38.0) | u_grab) & (vz >= 0.45)
    kai_l = ((fib240_l >= 0.54) | (fib60_l >= 0.58)) & (vz >= 0.40)
    kai_s = ((fib240_s >= 0.54) | (fib60_s >= 0.58)) & (vz >= 0.40)

    pod_smc_l = gate_l & nina_l & (sam_l | kai_l)
    pod_smc_s = gate_s & nina_s & (sam_s | kai_s)

    # Fast simulation engine
    def run_sim(m_l, m_s, tp1_r=1.80, tp2_r=3.50, trail_trig=2.10, trail_dist=1.05, max_hold=180):
        sig_idxs = np.where(m_l | m_s)[0]
        sig_idxs = sig_idxs[(sig_idxs >= 2000) & (sig_idxs < len(c) - max_hold - 5)]

        trades_pnl = []
        rs = []
        last_exit = -999
        eq = 100.0
        peak_eq = 100.0
        max_dd = 0.0
        max_win = 0.0

        for idx in sig_idxs:
            if idx < last_exit + 8:
                continue
            is_long = m_l[idx]
            entry = float(c[idx])
            rk = float(np.clip(1.35 * atr[idx], 3.8, 11.0))
            qty = 5.0 / rk

            sl_init = entry - rk if is_long else entry + rk
            cur_sl = sl_init
            be_px = entry + 1.05 * rk if is_long else entry - 1.05 * rk
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
                    if tp2_r > 0 and h[k] >= tp2_px:
                        exit_px = tp2_px
                        exit_i = k
                        break

                    # Stall lock (+0.54R MFE -> lock +0.28R)
                    if stage == 0 and peak_r >= 0.54 and (k - peak_k >= 6 or (s_mss[k] and d5[k] < 0)):
                        if c[k] >= entry + 0.28 * rk:
                            cur_sl = max(cur_sl, entry + 0.28 * rk)
                            stage = 1
                            stall_locked = True

                    if stage == 0 and h[k] >= be_px:
                        cur_sl = max(cur_sl, entry + 0.38 * rk)
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
                    if tp2_r > 0 and l[k] <= tp2_px:
                        exit_px = tp2_px
                        exit_i = k
                        break

                    # Stall lock
                    if stage == 0 and peak_r >= 0.54 and (k - peak_k >= 6 or (b_mss[k] and d5[k] > 0)):
                        if c[k] <= entry - 0.28 * rk:
                            cur_sl = min(cur_sl, entry - 0.28 * rk)
                            stage = 1
                            stall_locked = True

                    if stage == 0 and l[k] <= be_px:
                        cur_sl = min(cur_sl, entry - 0.38 * rk)
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

            if net_usd > max_win:
                max_win = net_usd

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
            "max_win": round(max_win, 2),
        }

    print("TESTING RUNNER EXTENSIONS FOR POD: MARCUS + ARTHUR + JACK")
    for tp2 in [3.35, 4.50, 6.00, 10.00, 0.0]:
        t_label = f"TP2={tp2:.2f}R" if tp2 > 0 else "Pure Trailing (Uncapped Runner)"
        res = run_sim(pod_breakout_l, pod_breakout_s, tp1_r=1.85, tp2_r=tp2, trail_trig=2.10, trail_dist=1.05)
        print(f"  {t_label:<32} | Tr: {res['n']:3d} ({res['tpd']} tr/d) | WR: {res['wr']:5.2f}% | PF: {res['pf']:4.2f} | Net: ${res['net']:+7.2f} | EndEq: ${res['eq']:7.2f} | MaxDD: {res['max_dd']:5.2f}% | Max Single Win: ${res['max_win']:5.2f}")

    print("\nTESTING RUNNER EXTENSIONS FOR POD: NINA + SAM + KAI")
    for tp2 in [3.35, 4.50, 6.00, 10.00, 0.0]:
        t_label = f"TP2={tp2:.2f}R" if tp2 > 0 else "Pure Trailing (Uncapped Runner)"
        res = run_sim(pod_smc_l, pod_smc_s, tp1_r=1.80, tp2_r=tp2, trail_trig=2.10, trail_dist=1.05)
        print(f"  {t_label:<32} | Tr: {res['n']:3d} ({res['tpd']} tr/d) | WR: {res['wr']:5.2f}% | PF: {res['pf']:4.2f} | Net: ${res['net']:+7.2f} | EndEq: ${res['eq']:7.2f} | MaxDD: {res['max_dd']:5.2f}% | Max Single Win: ${res['max_win']:5.2f}")

if __name__ == "__main__":
    main()
