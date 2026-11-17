import json
import pandas as pd

with open('data/processed/all_11_agents_lab_bundle.json') as f:
    bundle = json.load(f)

# Let's inspect trade durations of the 2,692 trades
all_trades = []
for ag, data in bundle.items():
    champ = data.get('generations', {}).get('v3.0_ORACLE_CHAMPION', {})
    for t in champ.get('trades', []):
        t_copy = dict(t)
        t_copy['source_agent'] = ag
        ent = pd.to_datetime(t['entry_time'])
        ext = pd.to_datetime(t['exit_time'])
        t_copy['duration_mins'] = (ext - ent).total_seconds() / 60.0
        all_trades.append(t_copy)

df_all = pd.DataFrame(all_trades)
print("Average trade duration:", df_all['duration_mins'].mean(), "mins")
print("Median trade duration:", df_all['duration_mins'].median(), "mins")
print("Min duration:", df_all['duration_mins'].min(), "mins")
print("Max duration:", df_all['duration_mins'].max(), "mins")

# What if we look at the 296 non-overlapping trades?
all_trades.sort(key=lambda x: (x['entry_ts'], -x.get('net_pnl', 0)))
single_slot = []
cur_exit = None
for t in all_trades:
    if cur_exit is None or t['entry_ts'] >= cur_exit:
        single_slot.append(t)
        cur_exit = t['exit_ts']

df_ss = pd.DataFrame(single_slot)
print("\nIn the 296 non-overlapping trades:")
print("Average duration:", df_ss['duration_mins'].mean(), "mins")
print("Median duration:", df_ss['duration_mins'].median(), "mins")
