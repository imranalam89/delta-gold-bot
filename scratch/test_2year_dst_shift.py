import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
import zoneinfo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, "data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
BUNDLE_PATH = os.path.join(BASE_DIR, "data", "processed", "all_11_agents_2year_bundle.json")

print("[1/3] Loading 2-Year Bundle and Parquet...")
with open(BUNDLE_PATH, "r", encoding="utf-8") as f:
    bundle = json.load(f)

df = pd.read_parquet(PARQUET_PATH)
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

ny_tz = zoneinfo.ZoneInfo("America/New_York")
times = df.index.to_numpy()
time_to_idx = {ts: idx for idx, ts in enumerate(times)}

c = df["close"].to_numpy(dtype=np.float32)
h = df["high"].to_numpy(dtype=np.float32)
l = df["low"].to_numpy(dtype=np.float32)

n_bars = len(df)
n_15 = n_bars // 15
h_15 = np.zeros(n_15, dtype=np.float32)
l_15 = np.zeros(n_15, dtype=np.float32)
for j in range(n_15):
    s = j * 15
    e = s + 15
    h_15[j] = np.max(h[s:e])
    l_15[j] = np.min(l[s:e])

PLAYBOOK_MAP = {
    "2:MAYA": ("5:LEO", "LEO_SWEEP_TRAP", 5),
    "6:SOPHIA": ("5:LEO", "LEO_KILLZONE_SWEEP", 4),
    "9:SAM": ("5:LEO", "LEO_LIQUIDITY_TRAP", 3),
    "7:DEREK": ("6:KAI", "KAI_SMC_OTE_TREND", 5),
    "4:NINA": ("6:KAI", "KAI_FVG_BOS_RETEST", 4),
    "8:ELENA": ("9:ELENA", "ELENA_VWAP_WICK_REV", 5),
    "11:LIAM": ("9:ELENA", "ELENA_VWAP_VSA_POCKET", 4),
    "5:MAX": ("7:NINA", "NINA_RANGE_BOX_FADE", 4),
    "3:MARCUS": ("8:MAX", "MAX_BOX_BREAKOUT", 4),
    "10:OMAR": ("8:MAX", "MAX_DELTA_MOMENTUM", 4),
    "1:ALEX": ("8:MAX", "MAX_TREND_PULLBACK", 3),
}

raw_candidates = []
for aid, data in bundle.items():
    pb_agent, pb_name, prio = PLAYBOOK_MAP.get(aid, ("6:KAI", "KAI_SMC_OTE_TREND", 3))
    if pb_name == "LEO_LIQUIDITY_TRAP":
        continue

    for tf_label in ["5m", "15m", "1h"]:
        tf_trades = data.get("timeframes", {}).get(tf_label, {}).get("trades", [])
        for t in tf_trades:
            entry_dt = pd.to_datetime(t["entry_time"], utc=True)
            if entry_dt.weekday() not in (0, 1, 2, 3, 4):
                continue

            entry_ny = entry_dt.astimezone(ny_tz)
            if entry_dt in time_to_idx:
                idx = time_to_idx[entry_dt]
                raw_candidates.append({
                    "idx": idx,
                    "entry_time": t["entry_time"],
                    "entry_ts": int(entry_dt.timestamp()),
                    "utc_hour": entry_dt.hour,
                    "ny_hour": entry_ny.hour,
                    "is_dst": bool(entry_ny.dst()),
                    "direction": t["direction"],
                    "agent": aid,
                    "tf": tf_label,
                    "playbook": pb_name,
                    "prio": prio,
                    "sl_dist": float(t["sl_dist"]),
                })

print(f"Total Base Candidates: {len(raw_candidates)}")

def run_backtest_with_filter(name, filter_fn):
    # Group by bar
    bar_to_cands = {}
    for cand in raw_candidates:
        if filter_fn(cand):
            continue
        bar_to_cands.setdefault(cand["idx"], []).append(cand)

    filtered = []
    for idx in sorted(bar_to_cands.keys()):
        c_list = bar_to_cands[idx]
        longs = [x for x in c_list if x["direction"] == "LONG"]
        shorts = [x for x in c_list if x["direction"] == "SHORT"]
        chosen = None
        if len(longs) >= len(shorts) and len(longs) >= 1:
            longs.sort(key=lambda x: -x["prio"])
            chosen = longs[0]
        elif len(shorts) > len(longs) and len(shorts) >= 1:
            shorts.sort(key=lambda x: -x["prio"])
            chosen = shorts[0]
        if chosen:
            filtered.append(chosen)

    # Single-slot execution
    fee_rate = 0.0001
    executed = []
    busy_until = 0

    for cand in filtered:
        idx = cand["idx"]
        if idx < busy_until:
            continue

        direction = cand["direction"]
        ent_px = round(float(c[idx]), 2)
        sl_dist = round(cand["sl_dist"] * (0.85 / 1.35), 2)
        sl_dist = max(3.5, sl_dist)
        qty = round(5.0 / sl_dist, 4)

        cur_sl = round(ent_px - sl_dist if direction == "LONG" else ent_px + sl_dist, 2)
        stage = 0
        peak_fav = 0.0
        peak_k = idx
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
                if l[k] <= cur_sl:
                    exit_px = cur_sl
                    exit_k = k
                    exit_reason = "STOP_LOSS" if stage == 0 else "TRAIL"
                    break
                if stage == 0 and cur_r >= 0.54 and (k - peak_k >= 6):
                    cur_sl = max(cur_sl, round(ent_px + 0.28 * sl_dist, 2))
                    stage = 1
                if stage == 0 and cur_r >= 1.05:
                    cur_sl = max(cur_sl, round(ent_px + 0.38 * sl_dist, 2))
                    stage = 1
                if cur_r >= 2.10:
                    stage = 2
                    recent_l = float(np.min(l_15[max(0, j_15 - 2):j_15 + 1]))
                    cand_sl = round(recent_l - 0.35 * sl_dist, 2)
                    if cand_sl > cur_sl:
                        cur_sl = cand_sl
            else:
                fav = ent_px - l[k]
                if fav > peak_fav:
                    peak_fav = fav
                    peak_k = k
                cur_r = fav / sl_dist
                if h[k] >= cur_sl:
                    exit_px = cur_sl
                    exit_k = k
                    exit_reason = "STOP_LOSS" if stage == 0 else "TRAIL"
                    break
                if stage == 0 and cur_r >= 0.54 and (k - peak_k >= 6):
                    cur_sl = min(cur_sl, round(ent_px - 0.28 * sl_dist, 2))
                    stage = 1
                if stage == 0 and cur_r >= 1.05:
                    cur_sl = min(cur_sl, round(ent_px - 0.38 * sl_dist, 2))
                    stage = 1
                if cur_r >= 2.10:
                    stage = 2
                    recent_h = float(np.max(h_15[max(0, j_15 - 2):j_15 + 1]))
                    cand_sl = round(recent_h + 0.35 * sl_dist, 2)
                    if cand_sl < cur_sl:
                        cur_sl = cand_sl

        if exit_px is None:
            exit_px = float(c[end_k - 1])
            exit_k = end_k - 1
            exit_reason = "TIME"

        busy_until = exit_k + 1
        pts = (exit_px - ent_px) if direction == "LONG" else (ent_px - exit_px)
        r_mult = round(pts / sl_dist, 2)
        gross = round(pts * qty, 2)
        fee = round(fee_rate * qty * (ent_px + exit_px), 2)
        net = round(gross - fee, 2)

        executed.append({
            "entry_time": str(times[idx]),
            "net_pnl": net,
            "year": str(times[idx])[:4]
        })

    wins = sum(1 for t in executed if t["net_pnl"] > 0)
    tot = len(executed)
    wr = wins / tot * 100 if tot > 0 else 0
    net_tot = sum(t["net_pnl"] for t in executed)
    w_sum = sum(t["net_pnl"] for t in executed if t["net_pnl"] > 0)
    l_sum = abs(sum(t["net_pnl"] for t in executed if t["net_pnl"] < 0))
    pf = w_sum / l_sum if l_sum > 0 else 99.0

    print(f"\n{name}:")
    print(f"  Total Trades: {tot} | WR: {wr:.2f}% | Net: ${net_tot:+.2f} | PF: {pf:.2f}")
    df_e = pd.DataFrame(executed)
    for yr, sub in df_e.groupby("year"):
        w_y = (sub["net_pnl"] > 0).sum()
        net_y = sub["net_pnl"].sum()
        w_s = sub[sub["net_pnl"] > 0]["net_pnl"].sum()
        l_s = abs(sub[sub["net_pnl"] < 0]["net_pnl"].sum())
        pf_y = w_s / l_s if l_s > 0 else 99.0
        print(f"    Year {yr}: {len(sub):3d}t | WR: {w_y/len(sub)*100:5.2f}% | Net: ${net_y:+7.2f} | PF: {pf_y:4.2f}")

print("\n--- TESTING TIME-SHIELD CONFIGURATIONS OVER 2 FULL YEARS ---")

# Config 1: Fixed UTC 13:00-13:59
run_backtest_with_filter("Config 1: Fixed UTC 13:00 Shield", lambda c: c["utc_hour"] == 13)

# Config 2: Fixed UTC 14:00-14:59 (Shifted 1 hour later in UTC)
run_backtest_with_filter("Config 2: Shifted 1hr Later (UTC 14:00 Shield)", lambda c: c["utc_hour"] == 14)

# Config 3: Dynamic NY Local 9:00 AM - 9:59 AM (Automatically shifts UTC hour with NY DST!)
# (In Summer EDT = 13:00 UTC, in Winter EST = 14:00 UTC)
run_backtest_with_filter("Config 3: Dynamic NY Local 9:00 AM Open Shield (Auto DST Shift)", lambda c: c["ny_hour"] == 9)

# Config 4: Dynamic NY Local 8:00 AM - 8:59 AM (8:30 AM Economic News Release)
# (In Summer EDT = 12:00 UTC, in Winter EST = 13:00 UTC)
run_backtest_with_filter("Config 4: Dynamic NY Local 8:00 AM News Shield (8:30 Release)", lambda c: c["ny_hour"] == 8)

# Config 5: Full Dynamic NY 8:00-9:59 AM Shield (Both 8:30 News + 9:30 Equity Open)
run_backtest_with_filter("Config 5: Full NY Macro Shield (8:00-9:59 AM NY Local)", lambda c: c["ny_hour"] in (8, 9))
