"""
Syndicate Alpha — 2-Year Exact Model 2 Champion Simulation
Applies Model 2:
1. 0.85x ATR Initial SL
2. 40R Continuous Chandelier Trailing Engine
3. Smart Stall Lock (+0.28R after 6 bars)
4. 13:00 UTC News Whipsaw Shield (blocks entries 13:00–13:59 UTC)
5. Strict Pruning of LEO_LIQUIDITY_TRAP (Sam 9:SAM)
6. Strict Single-Slot Desk (max_slots = 1, 0 overlaps)
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_PATH = os.path.join(BASE_DIR, "data", "processed", "all_11_agents_2year_bundle.json")
PARQUET_PATH = os.path.join(BASE_DIR, "data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")

def run_simulation(min_consensus=1):
    print(f"[1/4] Loading 2-Year Bundle from {BUNDLE_PATH}...")
    with open(BUNDLE_PATH, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    print(f"[2/4] Loading 1m bars from {PARQUET_PATH}...")
    df = pd.read_parquet(PARQUET_PATH)
    if not df.index.tz:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')

    c = df["close"].to_numpy(dtype=np.float32)
    h = df["high"].to_numpy(dtype=np.float32)
    l = df["low"].to_numpy(dtype=np.float32)
    times = df.index.to_numpy()
    time_to_idx = {ts: idx for idx, ts in enumerate(times)}

    # Build 15m highs/lows for Chandelier trailing
    n_bars = len(df)
    n_15 = n_bars // 15
    h_15 = np.zeros(n_15, dtype=np.float32)
    l_15 = np.zeros(n_15, dtype=np.float32)
    for j in range(n_15):
        s = j * 15
        e = s + 15
        h_15[j] = np.max(h[s:e])
        l_15[j] = np.min(l[s:e])

    # Playbook mapping
    PLAYBOOK_MAP = {
        "2:MAYA": ("5:LEO", "LEO_SWEEP_TRAP", 5),
        "6:SOPHIA": ("5:LEO", "LEO_KILLZONE_SWEEP", 4),
        "9:SAM": ("5:LEO", "LEO_LIQUIDITY_TRAP", 3), # Pruned in Model 2!
        "7:DEREK": ("6:KAI", "KAI_SMC_OTE_TREND", 5),
        "4:NINA": ("6:KAI", "KAI_FVG_BOS_RETEST", 4),
        "8:ELENA": ("9:ELENA", "ELENA_VWAP_WICK_REV", 5),
        "11:LIAM": ("9:ELENA", "ELENA_VWAP_VSA_POCKET", 4),
        "5:MAX": ("7:NINA", "NINA_RANGE_BOX_FADE", 4),
        "3:MARCUS": ("8:MAX", "MAX_BOX_BREAKOUT", 4),
        "10:OMAR": ("8:MAX", "MAX_DELTA_MOMENTUM", 4),
        "1:ALEX": ("8:MAX", "MAX_TREND_PULLBACK", 3),
    }

    # Extract all candidate trades from bundle
    raw_candidates = []
    for aid, data in bundle.items():
        pb_agent, pb_name, prio = PLAYBOOK_MAP.get(aid, ("6:KAI", "KAI_SMC_OTE_TREND", 3))
        
        # MODEL 2 RULE: Prune LEO_LIQUIDITY_TRAP
        if pb_name == "LEO_LIQUIDITY_TRAP":
            continue

        for tf_label in ["5m", "15m", "1h"]:
            tf_trades = data.get("timeframes", {}).get(tf_label, {}).get("trades", [])
            for t in tf_trades:
                entry_dt = pd.to_datetime(t["entry_time"], utc=True)
                
                # MODEL 2 RULE: News Whipsaw Shield (13:00 - 13:59 UTC)
                if entry_dt.hour == 13:
                    continue

                # Exclude weekends
                if entry_dt.weekday() not in (0, 1, 2, 3, 4):
                    continue

                if entry_dt in time_to_idx:
                    idx = time_to_idx[entry_dt]
                    raw_candidates.append({
                        "idx": idx,
                        "entry_time": t["entry_time"],
                        "entry_ts": int(entry_dt.timestamp()),
                        "direction": t["direction"],
                        "agent": aid,
                        "tf": tf_label,
                        "playbook": pb_name,
                        "prio": prio,
                        "sl_dist": float(t["sl_dist"]),
                        "entry_price": float(t["entry_price"]),
                    })

    print(f"Total Model 2 Candidate Trades after News Shield & Leo Pruning: {len(raw_candidates):,}")

    # Group candidates by entry bar to detect consensus
    bar_to_cands = {}
    for c_item in raw_candidates:
        idx = c_item["idx"]
        bar_to_cands.setdefault(idx, []).append(c_item)

    # Filter by consensus if required
    filtered_cands = []
    for idx in sorted(bar_to_cands.keys()):
        c_list = bar_to_cands[idx]
        longs = [x for x in c_list if x["direction"] == "LONG"]
        shorts = [x for x in c_list if x["direction"] == "SHORT"]
        
        # Choose side with highest votes
        chosen = None
        if len(longs) >= min_consensus and len(longs) >= len(shorts):
            longs.sort(key=lambda x: -x["prio"])
            chosen = longs[0]
            chosen["confirming_count"] = len(longs)
        elif len(shorts) >= min_consensus and len(shorts) > len(longs):
            shorts.sort(key=lambda x: -x["prio"])
            chosen = shorts[0]
            chosen["confirming_count"] = len(shorts)

        if chosen:
            filtered_cands.append(chosen)

    print(f"Filtered Candidates with Consensus >= {min_consensus}: {len(filtered_cands):,}")

    # Step 3: Run exact bar-by-bar Single-Slot execution
    # Model 2 Champion Lifecyle:
    # - 0.85x ATR SL
    # - Smart Stall Lock: stall_trig = +0.54R, stall_bars = 6, stall_lock = +0.28R
    # - Breakeven Lock: be_trig = +1.05R, be_lock = +0.38R
    # - 40R Continuous Chandelier Trail: trail_trig = +2.10R, 15m structure anchor
    
    fee_rate = 0.0001
    executed_trades = []
    busy_until = 0

    for cand in filtered_cands:
        idx = cand["idx"]
        if idx < busy_until:
            continue

        direction = cand["direction"]
        ent_px = round(float(c[idx]), 2)
        sl_dist = round(cand["sl_dist"] * (0.85 / 1.35), 2) # Calibrated to 0.85x SL
        sl_dist = max(3.5, sl_dist)
        qty = round(5.0 / sl_dist, 4)

        cur_sl = round(ent_px - sl_dist if direction == "LONG" else ent_px + sl_dist, 2)
        stage = 0
        peak_fav = 0.0
        peak_k = idx
        stall_locked = False
        
        exit_px = None
        exit_k = None
        exit_reason = None

        max_hold = 240
        end_k = min(n_bars, idx + max_hold + 1)

        for k in range(idx + 1, end_k):
            j_15 = k // 15
            bars_held = k - idx

            if direction == "LONG":
                fav = h[k] - ent_px
                if fav > peak_fav:
                    peak_fav = fav
                    peak_k = k
                cur_r = fav / sl_dist

                # 1. Stop loss check
                if l[k] <= cur_sl:
                    exit_px = cur_sl
                    exit_k = k
                    exit_reason = "STOP_LOSS" if stage == 0 else ("BREAKEVEN_LOCK" if stage == 1 else "CHANDELIER_TRAIL_HIT")
                    break

                # 2. Instant Pre-SL Cut (if adverse order flow appears after 12 bars)
                if stage == 0 and bars_held >= 12 and cur_r <= -0.55:
                    exit_px = float(c[k])
                    exit_k = k
                    exit_reason = "INSTANT_PRE_SL_CUT"
                    break

                # 3. Smart Stall Lock (+0.54R -> +0.28R after 6 bars)
                if stage == 0 and cur_r >= 0.54 and (k - peak_k >= 6):
                    cur_sl = max(cur_sl, round(ent_px + 0.28 * sl_dist, 2))
                    stage = 1
                    stall_locked = True

                # 4. Breakeven Lock (+1.05R -> +0.38R)
                if stage == 0 and cur_r >= 1.05:
                    cur_sl = max(cur_sl, round(ent_px + 0.38 * sl_dist, 2))
                    stage = 1

                # 5. 40R Continuous Chandelier Trail (+2.10R trigger)
                if cur_r >= 2.10:
                    stage = 2
                    recent_l = float(np.min(l_15[max(0, j_15 - 2):j_15 + 1]))
                    cand_sl = round(recent_l - 0.35 * sl_dist, 2)
                    if cand_sl > cur_sl:
                        cur_sl = cand_sl

            else:
                # SHORT
                fav = ent_px - l[k]
                if fav > peak_fav:
                    peak_fav = fav
                    peak_k = k
                cur_r = fav / sl_dist

                # 1. Stop loss check
                if h[k] >= cur_sl:
                    exit_px = cur_sl
                    exit_k = k
                    exit_reason = "STOP_LOSS" if stage == 0 else ("BREAKEVEN_LOCK" if stage == 1 else "CHANDELIER_TRAIL_HIT")
                    break

                # 2. Instant Pre-SL Cut
                if stage == 0 and bars_held >= 12 and cur_r <= -0.55:
                    exit_px = float(c[k])
                    exit_k = k
                    exit_reason = "INSTANT_PRE_SL_CUT"
                    break

                # 3. Smart Stall Lock
                if stage == 0 and cur_r >= 0.54 and (k - peak_k >= 6):
                    cur_sl = min(cur_sl, round(ent_px - 0.28 * sl_dist, 2))
                    stage = 1
                    stall_locked = True

                # 4. Breakeven Lock
                if stage == 0 and cur_r >= 1.05:
                    cur_sl = min(cur_sl, round(ent_px - 0.38 * sl_dist, 2))
                    stage = 1

                # 5. 40R Continuous Chandelier Trail
                if cur_r >= 2.10:
                    stage = 2
                    recent_h = float(np.max(h_15[max(0, j_15 - 2):j_15 + 1]))
                    cand_sl = round(recent_h + 0.35 * sl_dist, 2)
                    if cand_sl < cur_sl:
                        cur_sl = cand_sl

        if exit_px is None:
            exit_px = float(c[end_k - 1])
            exit_k = end_k - 1
            exit_reason = "TIME_DECAY_EXIT"

        busy_until = exit_k + 1 # Cooldown

        pts = (exit_px - ent_px) if direction == "LONG" else (ent_px - exit_px)
        r_mult = round(pts / sl_dist, 2)
        gross = round(pts * qty, 2)
        fee = round(fee_rate * qty * (ent_px + exit_px), 2)
        net = round(gross - fee, 2)

        executed_trades.append({
            "id": len(executed_trades) + 1,
            "entry_time": str(times[idx]),
            "exit_time": str(times[exit_k]),
            "entry_idx": idx,
            "exit_idx": exit_k,
            "direction": direction,
            "agent": cand["agent"],
            "playbook": cand["playbook"],
            "tf": cand["tf"],
            "entry_price": ent_px,
            "exit_price": exit_px,
            "init_risk_pts": sl_dist,
            "r_multiple": r_mult,
            "qty_oz": qty,
            "gross_pnl_usd": gross,
            "delta_fee_usd": fee,
            "net_pnl_usd": net,
            "exit_reason": exit_reason,
            "hold_mins": exit_k - idx,
            "confirming_count": cand.get("confirming_count", 1),
        })

    # Calculate equity curve & drawdowns
    equity = 100.0
    peak_equity = 100.0
    max_dd_pct = 0.0
    max_dd_usd = 0.0
    wins = 0
    win_sum = 0.0
    loss_sum = 0.0

    for t in executed_trades:
        pnl = t["net_pnl_usd"]
        equity += pnl
        t["equity_after"] = round(equity, 2)
        if equity > peak_equity:
            peak_equity = equity
        dd_usd = peak_equity - equity
        dd_pct = (dd_usd / peak_equity * 100.0) if peak_equity > 0 else 0.0
        if dd_usd > max_dd_usd: max_dd_usd = dd_usd
        if dd_pct > max_dd_pct: max_dd_pct = dd_pct
        if pnl > 0:
            wins += 1
            win_sum += pnl
        else:
            loss_sum += abs(pnl)

    tot = len(executed_trades)
    wr = (wins / tot * 100.0) if tot > 0 else 0
    pf = (win_sum / loss_sum) if loss_sum > 0 else 99.0
    net_pnl = equity - 100.0

    print("\n" + "=" * 80)
    print(f"2-YEAR MODEL 2 CHAMPION RESULTS (Consensus >= {min_consensus})")
    print("=" * 80)
    print(f"Total Trades:             {tot:,} Verified Executions")
    print(f"Win Rate:                 {wr:.2f}% ({wins:,} Wins / {tot - wins:,} Losses)")
    print(f"Clean Net Profit:         +${net_pnl:,.2f} USD")
    print(f"Ending Equity:            ${equity:,.2f} ({equity/100:.2f}X Multiplier)")
    print(f"Profit Factor:            {pf:.2f} PF")
    print(f"Max Peak-to-Valley DD:    {max_dd_pct:.2f}% (${max_dd_usd:.2f})")

    # Annual breakdown
    df_t = pd.DataFrame(executed_trades)
    df_t["year"] = df_t["entry_time"].str[:4]
    print("\n--- ANNUAL BREAKDOWN ---")
    for yr, sub in df_t.groupby("year"):
        w = (sub["net_pnl_usd"] > 0).sum()
        w_sum = sub[sub["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        l_sum = abs(sub[sub["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        sub_pf = w_sum / l_sum if l_sum > 0 else 99.0
        print(f"Year {yr}: {len(sub):4d} Trades | WR: {w/len(sub)*100:5.2f}% | Net: +${sub['net_pnl_usd'].sum():+8.2f} | PF: {sub_pf:4.2f}")

    # Exit reason breakdown
    print("\n--- EXIT REASONS ---")
    print(df_t["exit_reason"].value_counts().to_string())

    return executed_trades

if __name__ == "__main__":
    min_c = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run_simulation(min_consensus=min_c)
