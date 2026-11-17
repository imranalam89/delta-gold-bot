import pandas as pd

p1 = pd.read_csv('data/processed/trades_1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT.csv')
p2 = pd.read_csv('data/processed/trades_2_HIGH_FREQUENCY_847_TRADES_TRI_SLOT.csv')
p3 = pd.read_csv('data/processed/trades_3_SCALPER_DENSITY_1115_TRADES_QUAD_SLOT.csv')

print(f"Strategy 1 trades: {len(p1)}")
print(f"Strategy 2 trades: {len(p2)}")
print(f"Strategy 3 trades: {len(p3)}")
print(f"Sum total raw trades: {len(p1) + len(p2) + len(p3)}")

# Combine all 3 into one dataframe
p1['source_strategy'] = 'Strategy 1 (Dual-Slot)'
p2['source_strategy'] = 'Strategy 2 (Tri-Slot)'
p3['source_strategy'] = 'Strategy 3 (Quad-Slot)'

all_combined = pd.concat([p1, p2, p3], ignore_index=True)
all_combined['entry_dt'] = pd.to_datetime(all_combined['entry_time'])
all_combined = all_combined.sort_values(by='entry_dt').reset_index(drop=True)

# 1. Deduplicate identical trade entries (exact same trade taken by multiple strategies)
dedup_trades = all_combined.drop_duplicates(subset=['entry_time', 'direction', 'setup_agent', 'entry_price']).copy()
print(f"\n--- Combined 1, 2, 3 (Skipping Duplicate Trade Overlaps) ---")
print(f"Total Unique Trades: {len(dedup_trades)}")
wins = (dedup_trades['net_pnl_usd'] > 0).sum()
wr = wins / len(dedup_trades) * 100
net = dedup_trades['net_pnl_usd'].sum()
gross = dedup_trades['gross_pnl_usd'].sum()
fees = dedup_trades['delta_fee_usd'].sum()
print(f"Win Rate: {wr:.2f}% ({wins}W / {len(dedup_trades) - wins}L)")
print(f"Gross PnL: ${gross:.2f}")
print(f"Delta Fees: ${fees:.2f}")
print(f"Net Profit: ${net:.2f}")
print(f"Ending Equity ($100 start): ${100.0 + net:.2f}")

# 2. What if we also skip TIME OVERLAPPING trades so only 1 position is open at a time?
dedup_trades['entry_ts'] = pd.to_datetime(dedup_trades['entry_time']).astype('int64') // 10**9
dedup_trades['exit_ts'] = pd.to_datetime(dedup_trades['exit_time']).astype('int64') // 10**9
dedup_trades = dedup_trades.sort_values(by=['entry_ts', 'net_pnl_usd'], ascending=[True, False]).reset_index(drop=True)

for max_concurrent in [1, 2, 3, 4]:
    active = []
    executed = []
    eq = 100.0
    peak = 100.0
    max_dd = 0.0
    for idx, t in dedup_trades.iterrows():
        active = [e for e in active if e > t['entry_ts']]
        if len(active) < max_concurrent:
            active.append(t['exit_ts'])
            executed.append(t)
            eq += t['net_pnl_usd']
            if eq > peak: peak = eq
            dd = (peak - eq) / peak * 100
            if dd > max_dd: max_dd = dd
    df_exec = pd.DataFrame(executed)
    w = (df_exec['net_pnl_usd'] > 0).sum()
    n_exec = len(df_exec)
    net_pnl = df_exec['net_pnl_usd'].sum()
    print(f"\nMax Concurrent Positions = {max_concurrent}:")
    print(f"  Executed Trades: {n_exec} ({n_exec/110:.2f}/day)")
    print(f"  Win Rate: {w/n_exec*100:.2f}% ({w}W / {n_exec-w}L)")
    print(f"  Net Profit: ${net_pnl:.2f} (End Eq: ${eq:.2f}, {eq/100:.2f}X)")
    print(f"  Max Drawdown: -{max_dd:.2f}%")
