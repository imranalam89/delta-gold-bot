import json
import pandas as pd

with open('data/processed/all_11_agents_lab_bundle.json') as f:
    bundle = json.load(f)

all_trades = []
for ag, data in bundle.items():
    champ = data.get('generations', {}).get('v3.0_ORACLE_CHAMPION', {})
    for t in champ.get('trades', []):
        t_copy = dict(t)
        t_copy['source_agent'] = ag
        all_trades.append(t_copy)

all_trades.sort(key=lambda x: (x['entry_ts'], -x.get('net_pnl', 0)))

print(f"Total Raw Trades from all 11 Agents: {len(all_trades)}")

# What happens with different slot counts?
for slots in [1, 2, 3, 4]:
    active_positions = []
    executed = []
    overlaps_skipped = 0
    for t in all_trades:
        ent = t['entry_ts']
        ext = t['exit_ts']
        active_positions = [e for e in active_positions if e > ent]
        if len(active_positions) < slots:
            active_positions.append(ext)
            executed.append(t)
        else:
            overlaps_skipped += 1
    
    n = len(executed)
    wins = sum(1 for t in executed if t['net_pnl'] > 0)
    wr = wins / n * 100 if n else 0
    gross = sum(t['gross_pnl'] for t in executed)
    fee = sum(t['fee_usd'] for t in executed)
    net = sum(t['net_pnl'] for t in executed)
    
    # Calculate drawdown
    eq = 100.0
    peak = 100.0
    max_dd = 0.0
    for t in executed:
        eq += t['net_pnl']
        if eq > peak:
            peak = eq
        dd = (peak - eq) / peak * 100.0
        if dd > max_dd:
            max_dd = dd
            
    print(f"\nSlots = {slots} (Max concurrent open positions = {slots}):")
    print(f"  Executed Trades: {n} trades ({n/110.0:.2f}/day)")
    print(f"  Overlapping Trades Skipped: {overlaps_skipped}")
    print(f"  Win Rate: {wr:.2f}% ({wins}W / {n - wins}L)")
    print(f"  Gross PnL: ${gross:.2f} | Fees: ${fee:.2f} | Net PnL: ${net:.2f}")
    print(f"  Ending Equity ($100 start): ${eq:.2f} ({eq/100:.2f}X)")
    print(f"  Max Drawdown: -{max_dd:.2f}%")
