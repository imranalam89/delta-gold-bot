import json
import os
import pandas as pd

BASE_DIR = r"c:\Users\USER\OneDrive\Desktop\Agents Team"
PAYLOAD_PATH = os.path.join(BASE_DIR, "data", "processed", "dashboard_payload.json")

with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
    d = json.load(f)

profiles = d["profiles"]
print("=" * 90)
print(f"{'Profile Name':30} | {'Trades':>6} | {'Win Rate':>8} | {'Net PnL':>10} | {'Max Trades/Day':>14}")
print("=" * 90)

for pname, pdata in profiles.items():
    meta = pdata["meta"]
    trades = pdata["trades"]
    n = len(trades)
    wins = [t for t in trades if t["net_pnl_usd"] > 0]
    wr = len(wins) / n * 100 if n else 0
    pnl = sum(t["net_pnl_usd"] for t in trades)
    
    # Calculate daily trade distribution
    days = {}
    for t in trades:
        d_str = t["date"]
        days[d_str] = days.get(d_str, 0) + 1
    
    max_d = max(days.values()) if days else 0
    avg_d = n / len(days) if days else 0
    print(f"{pname:30} | {n:6} | {wr:7.2f}% | ${pnl:9.2f} | {max_d:2} (avg {avg_d:.1f}/day)")

print("=" * 90)
print("\nDaily trade frequency distribution for Profile 1 (sample):")
p1_trades = profiles["1_BALANCED_15_AGENT_CORE"]["trades"]
p1_days = {}
for t in p1_trades:
    p1_days[t["date"]] = p1_days.get(t["date"], 0) + 1

from collections import Counter
c = Counter(p1_days.values())
for count, num_days in sorted(c.items()):
    print(f"  Days with {count:2} trade(s): {num_days} days")
