import pandas as pd

p3 = pd.read_csv('data/processed/trades_3_SCALPER_DENSITY_1115_TRADES_QUAD_SLOT.csv')
p3['entry_ts'] = pd.to_datetime(p3['entry_time']).astype('int64') // 10**9
p3['exit_ts'] = pd.to_datetime(p3['exit_time']).astype('int64') // 10**9
p3 = p3.sort_values(by='entry_ts').reset_index(drop=True)

# Test strict 1 position non-overlapping from p3
last_exit = -1
executed_1 = []
for idx, row in p3.iterrows():
    if row['entry_ts'] >= last_exit:
        executed_1.append(row)
        last_exit = row['exit_ts']

print(f"P3 strict 1-slot non-overlapping: {len(executed_1)} trades")
df1 = pd.DataFrame(executed_1)
wins1 = (df1['net_pnl_usd'] > 0).sum()
net1 = df1['net_pnl_usd'].sum()
print(f"WR: {wins1/len(df1)*100:.2f}%, Net: ${net1:.2f}")

# What if max 2 slots from p3?
for slots in [2, 3, 4]:
    active = []
    executed = []
    for idx, row in p3.iterrows():
        active = [e for e in active if e > row['entry_ts']]
        if len(active) < slots:
            active.append(row['exit_ts'])
            executed.append(row)
    df = pd.DataFrame(executed)
    wins = (df['net_pnl_usd'] > 0).sum()
    net = df['net_pnl_usd'].sum()
    print(f"P3 max {slots} slots: {len(df)} trades, WR: {wins/len(df)*100:.2f}%, Net: ${net:.2f}")
