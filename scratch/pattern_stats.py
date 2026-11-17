import json
import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime, timezone

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']

df = pd.DataFrame(trades)

# Parse hour of entry
df['entry_dt'] = pd.to_datetime(df['entry_ts'], unit='s', utc=True)
df['entry_hour'] = df['entry_dt'].dt.hour
df['is_win'] = df['net_pnl_usd'] > 0

print("=== 1. BY SETUP AGENT ===")
agent_stats = df.groupby('setup_agent').agg(
    total=('id', 'count'),
    wins=('is_win', 'sum'),
    net_pnl=('net_pnl_usd', 'sum')
)
agent_stats['wr'] = (agent_stats['wins'] / agent_stats['total'] * 100).round(1)
agent_stats['losses'] = agent_stats['total'] - agent_stats['wins']
agent_stats['loss_rate'] = (agent_stats['losses'] / agent_stats['total'] * 100).round(1)
print(agent_stats.sort_values(by='total', ascending=False).to_string())

print("\n=== 2. BY PLAYBOOK ===")
pb_stats = df.groupby('playbook').agg(
    total=('id', 'count'),
    wins=('is_win', 'sum'),
    net_pnl=('net_pnl_usd', 'sum')
)
pb_stats['wr'] = (pb_stats['wins'] / pb_stats['total'] * 100).round(1)
pb_stats['losses'] = pb_stats['total'] - pb_stats['wins']
pb_stats['loss_rate'] = (pb_stats['losses'] / pb_stats['total'] * 100).round(1)
print(pb_stats.sort_values(by='losses', ascending=False).head(15).to_string())

print("\n=== 3. BY SESSION ===")
sess_stats = df.groupby('session').agg(
    total=('id', 'count'),
    wins=('is_win', 'sum'),
    net_pnl=('net_pnl_usd', 'sum')
)
sess_stats['wr'] = (sess_stats['wins'] / sess_stats['total'] * 100).round(1)
sess_stats['losses'] = sess_stats['total'] - sess_stats['wins']
print(sess_stats.to_string())

print("\n=== 4. BY ENTRY HOUR (UTC) ===")
hour_stats = df.groupby('entry_hour').agg(
    total=('id', 'count'),
    wins=('is_win', 'sum'),
    net_pnl=('net_pnl_usd', 'sum')
)
hour_stats['wr'] = (hour_stats['wins'] / hour_stats['total'] * 100).round(1)
hour_stats['losses'] = hour_stats['total'] - hour_stats['wins']
print(hour_stats.sort_values(by='entry_hour').to_string())

print("\n=== 5. BY DAY OF WEEK ===")
day_stats = df.groupby('day_of_week').agg(
    total=('id', 'count'),
    wins=('is_win', 'sum'),
    net_pnl=('net_pnl_usd', 'sum')
)
day_stats['wr'] = (day_stats['wins'] / day_stats['total'] * 100).round(1)
day_stats['losses'] = day_stats['total'] - day_stats['wins']
print(day_stats.to_string())

print("\n=== 6. BY REGIME ===")
reg_stats = df.groupby('regime').agg(
    total=('id', 'count'),
    wins=('is_win', 'sum'),
    net_pnl=('net_pnl_usd', 'sum')
)
reg_stats['wr'] = (reg_stats['wins'] / reg_stats['total'] * 100).round(1)
reg_stats['losses'] = reg_stats['total'] - reg_stats['wins']
print(reg_stats.to_string())

print("\n=== 7. NUMERICAL INDICATOR COMPARISON (WINS VS LOSSES) ===")
num_cols = ['consensus_score', 'confirming_count', 'adx_15m', 'atr_15m', 'vol_z', 'l2_ratio', 'init_risk_pts', 'chop_15m', 'wick_ratio']
for col in num_cols:
    if col in df.columns:
        w_mean = df[df['is_win']][col].mean()
        l_mean = df[~df['is_win']][col].mean()
        w_med = df[df['is_win']][col].median()
        l_med = df[~df['is_win']][col].median()
        print(f"{col:18} -> Wins: mean={w_mean:.2f}, med={w_med:.2f} | Losses: mean={l_mean:.2f}, med={l_med:.2f}")

print("\n=== 8. BY DIRECTION ===")
dir_stats = df.groupby('direction').agg(
    total=('id', 'count'),
    wins=('is_win', 'sum'),
    net_pnl=('net_pnl_usd', 'sum')
)
dir_stats['wr'] = (dir_stats['wins'] / dir_stats['total'] * 100).round(1)
print(dir_stats.to_string())

print("\n=== 9. MISTAKE CODES ON LOSSES ===")
loss_df = df[~df['is_win']]
print(loss_df['mistake_code'].value_counts().to_string())
