import csv
from collections import defaultdict
import numpy as np

trades = []
with open('data/processed/trades_CHAMPION_B_MAX_PROFIT.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        trades.append(r)

print(f"Total Trades in Journal: {len(trades)}")

# 1. Performance by Setup Agent
agent_stats = defaultdict(lambda: {"w": 0, "l": 0, "net": 0.0, "gross_win": 0.0, "gross_loss": 0.0, "trades": 0})
for t in trades:
    ag = t["setup_agent"]
    net = float(t["net_pnl_usd"])
    agent_stats[ag]["trades"] += 1
    agent_stats[ag]["net"] += net
    if net > 0:
        agent_stats[ag]["w"] += 1
        agent_stats[ag]["gross_win"] += net
    else:
        agent_stats[ag]["l"] += 1
        agent_stats[ag]["gross_loss"] += abs(net)

print("\n=== 1. CHAMPION B JOURNAL: BREAKDOWN BY AGENT ===")
print(f"{'Agent':<12} | {'Trades':<6} | {'Win Rate':<8} | {'Net PnL':<10} | {'Profit Factor':<13} | {'Avg PnL':<8}")
print("-" * 75)
for ag, s in sorted(agent_stats.items(), key=lambda x: -x[1]["net"]):
    wr = s["w"] / s["trades"] * 100.0 if s["trades"] else 0.0
    pf = s["gross_win"] / s["gross_loss"] if s["gross_loss"] > 0 else 99.0
    avg_p = s["net"] / s["trades"] if s["trades"] else 0.0
    print(f"{ag:<12} | {s['trades']:<6} | {wr:<7.1f}% | ${s['net']:<9.2f} | {pf:<13.2f} | ${avg_p:<7.2f}")

# 2. Performance by Session
sess_stats = defaultdict(lambda: {"w": 0, "l": 0, "net": 0.0, "trades": 0})
for t in trades:
    s = t["session"]
    net = float(t["net_pnl_usd"])
    sess_stats[s]["trades"] += 1
    sess_stats[s]["net"] += net
    if net > 0:
        sess_stats[s]["w"] += 1
    else:
        sess_stats[s]["l"] += 1

print("\n=== 2. CHAMPION B JOURNAL: BREAKDOWN BY SESSION ===")
print(f"{'Session':<32} | {'Trades':<6} | {'Win Rate':<8} | {'Net PnL':<10}")
print("-" * 65)
for s, st in sorted(sess_stats.items(), key=lambda x: -x[1]["net"]):
    wr = st["w"] / st["trades"] * 100.0 if st["trades"] else 0.0
    print(f"{s:<32} | {st['trades']:<6} | {wr:<7.1f}% | ${st['net']:<9.2f}")

# 3. Breakdown by Exit Reason
exit_stats = defaultdict(lambda: {"count": 0, "net": 0.0})
for t in trades:
    reason = t["exit_reason"]
    net = float(t["net_pnl_usd"])
    exit_stats[reason]["count"] += 1
    exit_stats[reason]["net"] += net

print("\n=== 3. CHAMPION B JOURNAL: BREAKDOWN BY EXIT REASON ===")
print(f"{'Exit Reason':<20} | {'Count':<6} | {'Total Net PnL':<13} | {'Avg Net PnL':<10}")
print("-" * 55)
for r, st in sorted(exit_stats.items(), key=lambda x: -x[1]["net"]):
    avg_p = st["net"] / st["count"] if st["count"] else 0.0
    print(f"{r:<20} | {st['count']:<6} | ${st['net']:<12.2f} | ${avg_p:<9.2f}")

# 4. Consecutive Loss Distribution
streak = 0
max_streak = 0
streaks = defaultdict(int)
for t in trades:
    net = float(t["net_pnl_usd"])
    if net < 0:
        streak += 1
        max_streak = max(max_streak, streak)
    else:
        if streak > 0:
            streaks[streak] += 1
        streak = 0
if streak > 0:
    streaks[streak] += 1

print("\n=== 4. CHAMPION B JOURNAL: LOSING STREAK ANALYSIS ===")
print(f"Max Consecutive Losses: {max_streak}")
print(f"Losing streak frequencies: {dict(sorted(streaks.items()))}")
