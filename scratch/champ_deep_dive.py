import json
import sys
sys.path.insert(0, '.')

from scratch.optimize_multi_agent_desk import simulate_combination

# Run Combo #297 (Champion Ultra-Low Drawdown + 66% Win Rate)
champ_res = simulate_combination(
    sniper_sl_pts=3.80,
    struct_sl_mult=1.25,
    be_trig_r=1.05,
    be_lock_r=0.38,
    trail_trig_r=2.50,
    trail_dist_r=1.05,
    use_reversal_exit=True,
    consensus_continuation=True,
    max_slots=1
)

trades = champ_res['trades']
print(f"Total Trades: {len(trades)}")
print(f"Win Rate: {champ_res['win_rate']:.2f}%")
print(f"Net Profit: +${champ_res['net_pnl']:.2f}")
print(f"Profit Factor: {champ_res['profit_factor']:.2f}")
print(f"Max Drawdown: {champ_res['max_dd_pct']:.2f}%")

reasons = {}
for t in trades:
    r = t['exit_reason']
    reasons[r] = reasons.get(r, 0) + 1
print("Exit Reasons Distribution:", reasons)

# Agent breakdown
agent_wins = {}
agent_counts = {}
for t in trades:
    ag = t['agent']
    agent_counts[ag] = agent_counts.get(ag, 0) + 1
    if t['win']:
        agent_wins[ag] = agent_wins.get(ag, 0) + 1

print("\nPerformance by Initiating Agent:")
for ag in sorted(agent_counts.keys()):
    w = agent_wins.get(ag, 0)
    tot = agent_counts[ag]
    print(f"  {ag:11s} | Trades: {tot:3d} | WR: {w/tot*100:5.1f}%")
