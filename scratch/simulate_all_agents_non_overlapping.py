"""
Simulate All 11 Agents from agent_lab_dashboard.html Non-Overlapping Book
"""

import json
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_PATH = os.path.join(BASE_DIR, "data", "processed", "all_11_agents_lab_bundle.json")

def main():
    with open(BUNDLE_PATH, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    all_trades = []
    for ag, data in bundle.items():
        champ = data.get("generations", {}).get("v3.0_ORACLE_CHAMPION", {})
        trades = champ.get("trades", [])
        for t in trades:
            t_copy = dict(t)
            t_copy["source_agent"] = ag
            all_trades.append(t_copy)

    print(f"Total raw trades across all 11 agents: {len(all_trades):,}")

    # Sort strictly by entry timestamp, with a tie-breaker if same second
    all_trades.sort(key=lambda x: (x["entry_ts"], -x.get("net_pnl", 0)))

    # Apply Non-Overlapping Filter:
    # A new trade can only be taken if entry_ts >= previous trade's exit_ts (or exit_ts + buffer)
    for buffer_sec in [0, 60, 300]:
        filtered_trades = []
        last_exit_ts = -1
        eq = 100.0
        peak_eq = 100.0
        max_dd = 0.0

        for t in all_trades:
            if t["entry_ts"] >= last_exit_ts + buffer_sec:
                filtered_trades.append(t)
                last_exit_ts = t["exit_ts"]

        # Recalculate equity progression and stats on filtered stream
        nets = []
        for t in filtered_trades:
            pnl = float(t["net_pnl"])
            nets.append(pnl)
            eq += pnl
            if eq > peak_eq:
                peak_eq = eq
            dd = (eq - peak_eq) / peak_eq * 100.0
            if dd < max_dd:
                max_dd = dd

        n = len(filtered_trades)
        wins = sum(1 for x in nets if x > 0)
        wr = wins / n * 100.0
        gw = sum(x for x in nets if x > 0)
        gl = abs(sum(x for x in nets if x <= 0))
        pf = gw / gl if gl > 0 else 99.0
        tot_net = sum(nets)

        print(f"\n--- Buffer = {buffer_sec}s ---")
        print(f"Non-Overlapping Trades: {n} ({n/110.0:.2f} trades/day)")
        print(f"Win Rate: {wr:.2f}% ({wins}W / {n-wins}L)")
        print(f"Profit Factor: {pf:.2f}")
        print(f"Total Net PnL: ${tot_net:+.2f}")
        print(f"Ending Equity: ${eq:.2f} (from $100.00 start)")
        print(f"Max Drawdown: {max_dd:.2f}%")

        # Breakdown by which agents took the trades
        ag_counts = {}
        for t in filtered_trades:
            ag = t["source_agent"]
            ag_counts[ag] = ag_counts.get(ag, 0) + 1
        print("Trade distribution by agent:", ag_counts)

if __name__ == "__main__":
    main()
