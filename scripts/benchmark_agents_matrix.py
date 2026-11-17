import json
import os
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backtest_runner import load_config, CONFIG_PATH, load_dataset
from src.agents.syndicate_agents import precompute_features

OUT_CSV = os.path.join(BASE_DIR, "data", "processed", "agent_benchmark_matrix.csv")
OUT_JSON = os.path.join(BASE_DIR, "data", "processed", "agent_trust_weights.json")


def run_agent_benchmark():
    cfg = load_config(CONFIG_PATH)
    raw_df = load_dataset()
    print(f"[BENCHMARK] Precomputing features on {len(raw_df):,} bars across 1m, 5m, 15m, 1h...")
    df = precompute_features(raw_df, cfg)

    c = df["close"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    o = df["open"].to_numpy()
    atr = df["atr_5m"].to_numpy()
    chop = df["chop_index"].to_numpy()
    adx = df["adx"].to_numpy()
    ema15 = df["ema_15"].to_numpy()
    ema50 = df["ema_50"].to_numpy()
    ema200 = df["ema_200"].to_numpy()
    emad = df["ema_daily"].to_numpy()
    emam = df["ema_macro"].to_numpy()
    rl60 = df["range_low_60"].to_numpy()
    rh60 = df["range_high_60"].to_numpy()
    rl240 = df["range_low_240"].to_numpy()
    rh240 = df["range_high_240"].to_numpy()
    sl20 = df["swing_low_20"].to_numpy()
    sh20 = df["swing_high_20"].to_numpy()
    fib60_l = df["fib_retracement_long"].to_numpy()
    fib60_s = df["fib_retracement_short"].to_numpy()
    fib240_l = df["fib_240_long"].to_numpy()
    fib240_s = df["fib_240_short"].to_numpy()
    lw = df["lower_wick_ratio"].to_numpy()
    uw = df["upper_wick_ratio"].to_numpy()
    vz = df["vol_z_score"].to_numpy()
    b_mss = df["bull_mss_1m"].to_numpy()
    s_mss = df["bear_mss_1m"].to_numpy()
    b_fvg = df["bull_fvg"].to_numpy()
    s_fvg = df["bear_fvg"].to_numpy()
    d5 = df["delta_sum_5"].to_numpy()
    d15 = df["delta_sum_15"].to_numpy()
    b_abs = df["bull_absorption"].to_numpy()
    s_abs = df["bear_absorption"].to_numpy()
    stop_b = df["stopping_vol_bull"].to_numpy()
    stop_s = df["stopping_vol_bear"].to_numpy()
    room_h240 = df["room_to_high_240"].to_numpy()
    room_l240 = df["room_to_low_240"].to_numpy()
    room_h60 = df["room_to_high_60"].to_numpy()
    room_l60 = df["room_to_low_60"].to_numpy()
    rpos60 = df["range_pos_60"].to_numpy()
    rsi5 = df["rsi_5m"].to_numpy()
    u_liq = df["upper_liq_score"].to_numpy()
    l_liq = df["lower_liq_score"].to_numpy()
    u_grab = df["upper_liq_grabbed"].to_numpy()
    l_grab = df["lower_liq_grabbed"].to_numpy()
    l2m = df["l2_bid_ask_ratio_mean"].to_numpy()
    has_l2 = df["has_real_l2"].to_numpy()
    sb = df["silver_bullet"].to_numpy()

    est_hr = (df.index.hour - 5) % 24
    # Sessions: ASIA (18-01 EST), LONDON (02-07 EST), NEW_YORK (08-17 EST)
    sess_arr = np.where(
        np.isin(est_hr, [18, 19, 20, 21, 22, 23, 0, 1]),
        "ASIA",
        np.where(np.isin(est_hr, [2, 3, 4, 5, 6, 7]), "LONDON", "NEW_YORK"),
    )
    # Market Regime: TRENDING vs SIDEWAYS
    mkt_arr = np.where((chop < 52.5) & (adx >= 20.0), "TRENDING", "SIDEWAYS")

    macro_bull = c > emam
    macro_bear = c < emam
    rk_base = np.clip(1.20 * atr, 3.8, 11.0)
    rm_l = room_h240 >= 1.30 * rk_base
    rm_s = room_l240 >= 1.30 * rk_base

    # Define Individual Agent Signals & Multi-Agent Combination Signals
    agent_signals = {
        "2:ARTHUR (HTF Trend)": (
            macro_bull & (ema200 > emad) & (adx >= 20.0) & (c > ema50) & b_mss & (vz >= 1.1) & rm_l,
            macro_bear & (ema200 < emad) & (adx >= 20.0) & (c < ema50) & s_mss & (vz >= 1.1) & rm_s,
        ),
        "3:MARCUS (Breakout)": (
            macro_bull & (c > sh20) & (c > ema15) & (vz >= 1.35) & (d5 > 0) & rm_l,
            macro_bear & (c < sl20) & (c < ema15) & (vz >= 1.35) & (d5 < 0) & rm_s,
        ),
        "4:NINA (SMC Sweep/FVG)": (
            macro_bull & ((l <= sl20) | b_fvg) & (c > ema15) & (lw >= 1.45) & (vz >= 1.2) & rm_l,
            macro_bear & ((h >= sh20) | s_fvg) & (c < ema15) & (uw >= 1.45) & (vz >= 1.2) & rm_s,
        ),
        "5:MAX (Sideways Trap)": (
            macro_bull & (l < rl60) & (c > rl60) & (c > o) & ((lw >= 1.4) | b_mss) & (vz >= 1.35) & rm_l,
            macro_bear & (h > rh60) & (c < rh60) & (c < o) & ((uw >= 1.4) | s_mss) & (vz >= 1.35) & rm_s,
        ),
        "6:LEO (Killzone/SB)": (
            sb & macro_bull & (ema200 > emad) & (fib240_l >= 0.55) & b_mss & (vz >= 1.15) & rm_l,
            sb & macro_bear & (ema50 < ema200) & (fib240_s >= 0.55) & s_mss & (vz >= 1.15) & rm_s,
        ),
        "7:KAI (Fib OTE 61.8-78.6%)": (
            macro_bull & (ema200 > emad) & (fib240_l >= 0.618) & (fib240_l <= 0.786) & (lw >= 1.6) & (vz >= 1.15) & rm_l,
            macro_bear & (ema50 < ema200) & (fib240_s >= 0.618) & (fib240_s <= 0.786) & s_mss & (vz >= 1.1) & rm_s,
        ),
        "8:ELENA (Price Action Scalper)": (
            macro_bull & (ema200 > emad) & (fib240_l >= 0.55) & ((lw >= 1.45) | b_mss) & (vz >= 1.15) & (d5 > 0) & rm_l,
            macro_bear & (ema50 < ema200) & (fib240_s >= 0.55) & ((uw >= 1.45) | s_mss) & (vz >= 1.15) & (d5 < 0) & rm_s,
        ),
        "9:SAM (Liquidity Heatmap >40)": (
            macro_bull & (u_liq >= 42.0) & (room_h60 >= 4.5) & (room_h60 <= 9.5) & b_mss & (d5 > 0) & (~has_l2 | (l2m >= 1.02)),
            macro_bear & (l_liq >= 42.0) & (room_l60 >= 4.5) & (room_l60 <= 9.5) & s_mss & (d5 < 0) & (~has_l2 | (l2m <= 0.98)),
        ),
        "10:OMAR (CVD Order Flow)": (
            macro_bull & ((d5 > 10) & (d15 > 15) | b_abs) & (fib240_l >= 0.55) & b_mss & (vz >= 1.15) & rm_l,
            macro_bear & ((d5 < -10) & (d15 < -15) | s_abs) & (fib240_s >= 0.55) & s_mss & (vz >= 1.15) & rm_s,
        ),
        "11:JACK (VSA Stopping Vol)": (
            macro_bull & stop_b & (fib240_l >= 0.55) & (c > o) & rm_l,
            macro_bear & stop_s & (fib240_s >= 0.55) & (c < o) & rm_s,
        ),
        "12:SARAH (Psychology Trap)": (
            macro_bull & (rsi5 <= 42.0) & b_mss & (lw >= 1.4) & (d5 > 0) & rm_l,
            macro_bear & (rsi5 >= 58.0) & s_mss & (uw >= 1.4) & (d5 < 0) & rm_s,
        ),
        # --- MULTI-AGENT SYNERGY COMBINATIONS ---
        "COMBO: ELENA + OMAR (PA + OrderFlow)": (
            macro_bull & (ema200 > emad) & (fib240_l >= 0.56) & ((lw >= 1.5) | b_mss) & (d5 > 0) & (d15 > 0) & (vz >= 1.2) & rm_l,
            macro_bear & (ema50 < ema200) & (fib240_s >= 0.58) & ((uw >= 1.5) | s_mss) & (d5 < 0) & (d15 < 0) & (vz >= 1.2) & rm_s,
        ),
        "COMBO: NINA + SAM + SARAH (Liq Grab >40)": (
            macro_bull & (l_liq >= 40.0) & l_grab & (c > rl60) & ((lw >= 1.45) | b_mss) & (d5 > 0) & (rsi5 < 68.0) & rm_l,
            macro_bear & (u_liq >= 40.0) & u_grab & (c < rh60) & ((uw >= 1.45) | s_mss) & (d5 < 0) & (rsi5 > 32.0) & rm_s,
        ),
        "COMBO: MARCUS + OMAR + JACK (True Box Breakout)": (
            macro_bull & (c > rh60) & (c > sh20) & (vz >= 1.45) & (d5 > 0) & (d15 > 0) & (u_liq >= 40.0) & rm_l,
            macro_bear & (c < rl60) & (c < sl20) & (vz >= 1.45) & (d5 < 0) & (d15 < 0) & (l_liq >= 40.0) & rm_s,
        ),
        "COMBO: ELENA + SAM ($5 Liquidity Magnet Scalp)": (
            macro_bull & (u_liq >= 42.0) & (room_h60 >= 4.5) & (room_h60 <= 9.5) & (ema200 > emad) & b_mss & (d5 > 0) & (vz >= 1.15),
            macro_bear & (l_liq >= 42.0) & (room_l60 >= 4.5) & (room_l60 <= 9.5) & (ema50 < ema200) & s_mss & (d5 < 0) & (vz >= 1.15),
        ),
        "COMBO: KAI + ELENA + OMAR (Golden Pocket + CVD)": (
            macro_bull & (ema200 > emad) & (fib240_l >= 0.618) & (fib240_l <= 0.786) & (lw >= 1.7) & (d5 > 0) & (vz >= 1.2) & rm_l,
            macro_bear & (ema50 < ema200) & (fib240_s >= 0.618) & (fib240_s <= 0.786) & s_mss & (d5 < 0) & (vz >= 1.1) & rm_s,
        ),
    }

    # Timeframe horizon parameters: (tf_name, bar_mod, sl_mult, tp1_r, tp2_r, max_hold_bars)
    timeframes = [
        ("1m", 1, 1.15, 1.65, 3.00, 150),
        ("5m", 5, 1.20, 1.75, 3.25, 210),
        ("15m", 15, 1.22, 1.80, 3.35, 240),
        ("1h", 60, 1.28, 1.85, 3.50, 300),
    ]

    # Precompute forward 240-bar high/low matrices using fast stride evaluation
    rows = []
    for tf_name, tf_mod, sl_m, tp1_r, tp2_r, hold_b in timeframes:
        tf_mask = (np.arange(len(c)) % tf_mod) == 0
        for ag_name, (m_l, m_s) in agent_signals.items():
            sig_idxs = np.where((m_l | m_s) & tf_mask)[0]
            sig_idxs = sig_idxs[(sig_idxs >= 2000) & (sig_idxs < len(c) - 320)]
            if len(sig_idxs) == 0:
                continue

            # De-cluster signals (minimum 45 mins apart)
            clean_idxs = []
            last_i = -999
            for idx in sig_idxs:
                if idx - last_i >= 45:
                    clean_idxs.append(idx)
                    last_i = idx

            # Simulate outcomes for each clean signal
            for sess in ["ASIA", "LONDON", "NEW_YORK"]:
                for mkt in ["TRENDING", "SIDEWAYS"]:
                    cell_idxs = [idx for idx in clean_idxs if sess_arr[idx] == sess and mkt_arr[idx] == mkt]
                    if not cell_idxs:
                        continue

                    nets = []
                    rs = []
                    for idx in cell_idxs:
                        direction = "LONG" if m_l[idx] else "SHORT"
                        entry = c[idx]
                        rk = float(np.clip(sl_m * atr[idx], 3.8, 11.0))
                        # If Liquidity Magnet Scalp, target the $5-$9 liquidity zone!
                        is_mag = "Magnet" in ag_name or "9:SAM" in ag_name
                        tp1 = entry + (1.45 if is_mag else tp1_r) * rk if direction == "LONG" else entry - (1.45 if is_mag else tp1_r) * rk
                        tp2 = entry + (2.50 if is_mag else tp2_r) * rk if direction == "LONG" else entry - (2.50 if is_mag else tp2_r) * rk
                        sl = entry - rk if direction == "LONG" else entry + rk
                        be_t = entry + 1.25 * rk if direction == "LONG" else entry - 1.25 * rk

                        cur_sl = sl
                        stage = 0
                        banked = 0.0
                        rem = 1.0
                        exit_px = None
                        end_k = min(len(c), idx + hold_b + 1)

                        for k in range(idx + 1, end_k):
                            if direction == "LONG":
                                if l[k] <= cur_sl:
                                    exit_px = cur_sl
                                    break
                                if h[k] >= tp2:
                                    exit_px = tp2
                                    break
                                if stage == 0 and h[k] >= be_t:
                                    cur_sl = entry + 0.35 * rk
                                    stage = 1
                                if stage <= 1 and h[k] >= tp1:
                                    banked += 0.5 * (tp1 - entry)
                                    rem = 0.5
                                    cur_sl = entry + 0.40 * rk
                                    stage = 2
                            else:
                                if h[k] >= cur_sl:
                                    exit_px = cur_sl
                                    break
                                if l[k] <= tp2:
                                    exit_px = tp2
                                    break
                                if stage == 0 and l[k] <= be_t:
                                    cur_sl = entry - 0.35 * rk
                                    stage = 1
                                if stage <= 1 and l[k] <= tp1:
                                    banked += 0.5 * (entry - tp1)
                                    rem = 0.5
                                    cur_sl = entry - 0.40 * rk
                                    stage = 2

                        if exit_px is None:
                            exit_px = c[end_k - 1]

                        pts = (exit_px - entry) if direction == "LONG" else (entry - exit_px)
                        tot_pts = banked + rem * pts
                        r_m = tot_pts / rk
                        gross = r_m * 5.0
                        qty = 5.0 / rk
                        fee = 0.0001 * qty * (entry + exit_px)
                        net = gross - fee
                        nets.append(net)
                        rs.append(r_m)

                    n_tr = len(nets)
                    wins = [x for x in nets if x > 0]
                    losses = [x for x in nets if x <= 0]
                    wr = (len(wins) / n_tr) * 100.0
                    pf = sum(wins) / max(0.50, abs(sum(losses)))
                    avg_r = float(np.mean(rs))
                    net_sum = float(sum(nets))

                    # Calibrate Dynamic Trust Voting Weight (0.65x to 2.25x) based on WR, PF, and Avg R
                    edge_score = (wr - 45.0) * 0.035 + (pf - 1.0) * 0.65 + avg_r * 0.85
                    trust_weight = float(np.clip(1.0 + edge_score, 0.65, 2.25))

                    rows.append({
                        "agent_or_combo": ag_name,
                        "is_combo": ag_name.startswith("COMBO:"),
                        "timeframe": tf_name,
                        "session": sess,
                        "market_condition": mkt,
                        "trades": n_tr,
                        "win_rate": round(wr, 2),
                        "profit_factor": round(pf, 2),
                        "avg_r": round(avg_r, 3),
                        "net_pnl_usd": round(net_sum, 2),
                        "trust_weight": round(trust_weight, 2),
                    })

    res_df = pd.DataFrame(rows)
    res_df.to_csv(OUT_CSV, index=False)
    print(f"[BENCHMARK] Saved {len(res_df)} multi-dimensional benchmark rows to {OUT_CSV}")

    # Build structured lookup table for Agent #17 LUCAS (The Analyser)
    # Keyed by: session -> market_condition -> agent_id_prefix -> weight (averaged across active TFs with sample weighting)
    trust_map = {}
    best_by_context = {}

    for sess in ["ASIA", "LONDON", "NEW_YORK"]:
        trust_map[sess] = {}
        best_by_context[sess] = {}
        for mkt in ["TRENDING", "SIDEWAYS"]:
            trust_map[sess][mkt] = {}
            sub = res_df[(res_df["session"] == sess) & (res_df["market_condition"] == mkt) & (~res_df["is_combo"])]
            for ag_name, grp in sub.groupby("agent_or_combo"):
                ag_key = ag_name.split(" ")[0]  # e.g. "8:ELENA"
                # Weighted average across timeframes + best timeframe weight
                best_tf_row = grp.sort_values(by=["net_pnl_usd", "profit_factor"], ascending=False).iloc[0]
                w_avg = float(np.clip(grp["trust_weight"].max() * 0.65 + grp["trust_weight"].mean() * 0.35, 0.70, 2.25))
                trust_map[sess][mkt][ag_key] = {
                    "weight": round(w_avg, 2),
                    "best_tf": str(best_tf_row["timeframe"]),
                    "win_rate": float(best_tf_row["win_rate"]),
                    "pf": float(best_tf_row["profit_factor"]),
                    "net_pnl": float(best_tf_row["net_pnl_usd"]),
                    "trades": int(grp["trades"].sum()),
                }

            # Rank top individual agents & top combos for this (session, market_condition)
            top_ind = sub.sort_values(by=["net_pnl_usd", "profit_factor"], ascending=False).head(4)
            sub_combo = res_df[(res_df["session"] == sess) & (res_df["market_condition"] == mkt) & (res_df["is_combo"])]
            top_cmb = sub_combo.sort_values(by=["net_pnl_usd", "profit_factor"], ascending=False).head(3)
            best_by_context[sess][mkt] = {
                "top_individual": top_ind.to_dict(orient="records"),
                "top_combos": top_cmb.to_dict(orient="records"),
            }

    out_payload = {
        "trust_weights": trust_map,
        "best_by_context": best_by_context,
        "all_rows": rows,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"[BENCHMARK] Saved Dynamic Trust Weights for 17:LUCAS to {OUT_JSON}\n")

    # Print Executive Summary Table
    print("=" * 115)
    print("   MULTI-TIMEFRAME (1m, 5m, 15m, 1h) × SESSION × REGIME AGENT BENCHMARK — TOP CHAMPIONS & VOTING WEIGHTS")
    print("=" * 115)
    for sess in ["ASIA", "LONDON", "NEW_YORK"]:
        for mkt in ["TRENDING", "SIDEWAYS"]:
            info = best_by_context[sess][mkt]
            print(f"\n>>> CONTEXT: {sess} SESSION | {mkt} MARKET <<<")
            for r in info["top_individual"][:3]:
                print(
                    f"  [INDIVIDUAL] {r['agent_or_combo']:<32} | Best TF: {r['timeframe']:<3} | Trades: {r['trades']:4d} | "
                    f"WR: {r['win_rate']:5.1f}% | PF: {r['profit_factor']:4.2f} | Net: ${r['net_pnl_usd']:+8.2f} | Trust Weight: {r['trust_weight']:.2f}x"
                )
            for r in info["top_combos"][:2]:
                print(
                    f"  [SYNERGY   ] {r['agent_or_combo']:<32} | Best TF: {r['timeframe']:<3} | Trades: {r['trades']:4d} | "
                    f"WR: {r['win_rate']:5.1f}% | PF: {r['profit_factor']:4.2f} | Net: ${r['net_pnl_usd']:+8.2f} | Trust Weight: {r['trust_weight']:.2f}x"
                )
    print("=" * 115)


if __name__ == "__main__":
    run_agent_benchmark()
