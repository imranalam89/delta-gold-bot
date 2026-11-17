import json
import pandas as pd

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
df = pd.DataFrame(trades)
df['is_win'] = df['net_pnl_usd'] > 0

# Sort by net pnl descending
top_wins = df[df['is_win']].sort_values(by='net_pnl_usd', ascending=False)
print("=== TOP 20 BIGGEST WINNING TRADES ===")
cols = ['id', 'setup_agent', 'playbook', 'direction', 'session', 'day_of_week', 'consensus_score', 'hold_mins', 'r_multiple', 'net_pnl_usd', 'exit_reason']
print(top_wins[cols].head(20).to_string())

print("\n=== AGENT DISTRIBUTION IN TOP 50 WINS ===")
top_50 = top_wins.head(50)
print(top_50['setup_agent'].value_counts())

print("\n=== PLAYBOOK DISTRIBUTION IN TOP 50 WINS ===")
print(top_50['playbook'].value_counts())

print("\n=== SESSION DISTRIBUTION IN TOP 50 WINS ===")
print(top_50['session'].value_counts())

print("\n=== EXIT REASON IN TOP 50 WINS ===")
print(top_50['exit_reason'].value_counts())
