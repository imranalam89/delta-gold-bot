"""
Test Priority-Sorted Non-Overlapping Book
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_PATH = os.path.join(BASE_DIR, "data", "processed", "all_11_agents_lab_bundle.json")

def main():
    with open(BUNDLE_PATH, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    # Edge ranking based on agent_lab_dashboard.html Net PnL & Win Rate:
    # 11:LIAM (+$175.92, 65.52%), 6:SOPHIA (+$175.92, 65.42%), 2:MAYA (+$175.20, 64.78%),
    # 9:SAM (+$167.63, 64.09%), 3:MARCUS (+$156.13, 65.30%), 10:OMAR (+$146.06, 62.95%),
    # 4:NINA (+$145.08, 63.28%), 8:ELENA (+$141.07, 65.68%), 7:DEREK (+$126.05, 63.18%),
    # 5:MAX (+$124.25, 62.56%), 1:ALEX (+$106.12, 64.54%)
    priority_map = {
        "11:LIAM": 11,
        "6:SOPHIA": 10,
        "2:MAYA": 9,
        "9:SAM": 8,
        "3:MARCUS": 7,
        "8:ELENA": 6,
        "10:OMAR": 5,
        "4:NINA": 4,
        "7:DEREK": 3,
        "5:MAX": 2,
        "1:ALEX": 1,
    }

    all_trades = []
    for ag, data in bundle.items():
        champ = data.get("generations", {}).get("v3.0_ORACLE_CHAMPION", {})
        trades = champ.get("trades", [])
        for t in trades:
            t_copy = dict(t)
            t_copy["source_agent"] = ag
            t_copy["priority"] = priority_map.get(ag, 0)
            all_trades.append(t_copy)

    # Test two ways of resolving simultaneous / close signals:
    # 1. Natural chronological order
    # 2. Priority-aware: at any given entry minute, take the highest priority agent's trade

    # Group by entry_ts
    by_ts = {}
    for t in all_trades:
        ts = t["entry_ts"]
        by_ts.setdefault(ts, []).append(t)

    sorted_entry_timestamps = sorted(by_ts.keys())

    # Strategy A: Chronological with highest priority on exact tie
    trades_stream = []
    for ts in sorted_entry_timestamps:
        candidates = by_ts[ts]
        # pick highest priority
        candidates.sort(key=lambda x: x["priority"], reverse=True)
        trades_stream.append(candidates[0])

    # Now filter overlapping
    filtered = []
    last_exit_ts = -1
    eq = 100.0
    peak_eq = 100.0
    max_dd = 0.0
    nets = []

    for t in trades_stream:
        if t["entry_ts"] >= last_exit_ts:
            filtered.append(t)
            last_exit_ts = t["exit_ts"]
            pnl = float(t["net_pnl"])
            nets.append(pnl)
            eq += pnl
            if eq > peak_eq:
                peak_eq = eq
            dd = (eq - peak_eq) / peak_eq * 100.0
            if dd < max_dd:
                max_dd = dd

    n = len(filtered)
    wins = sum(1 for x in nets if x > 0)
    wr = wins / n * 100.0
    gw = sum(x for x in nets if x > 0)
    gl = abs(sum(x for x in nets if x <= 0))
    pf = gw / gl if gl > 0 else 99.0
    tot_net = sum(nets)

    print("--- Priority-Tied Non-Overlapping Book ---")
    print(f"Non-Overlapping Trades: {n} ({n/110.0:.2f} trades/day)")
    print(f"Win Rate: {wr:.2f}% ({wins}W / {n-wins}L)")
    print(f"Profit Factor: {pf:.2f}")
    print(f"Total Net PnL: ${tot_net:+.2f}")
    print(f"Ending Equity: ${eq:.2f} (from $100.00 start)")
    print(f"Max Drawdown: {max_dd:.2f}%")

    ag_counts = {}
    for t in filtered:
        ag = t["source_agent"]
        ag_counts[ag] = ag_counts.get(ag, 0) + 1
    print("Trade distribution by agent:", ag_counts)

if __name__ == "__main__":
    main()
