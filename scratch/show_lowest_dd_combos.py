import csv

with open('data/processed/multi_agent_100_combos_results.csv', 'r') as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r['WinRate'] = float(r['WinRate'])
    r['NetProfit'] = float(r['NetProfit'])
    r['ProfitFactor'] = float(r['ProfitFactor'])
    r['MaxDD'] = float(r['MaxDD'])
    r['Trades'] = int(r['Trades'])
    r['ID'] = int(r['ID'])

# Sort by lowest Max DD first, then highest Win Rate, then Net Profit
rows.sort(key=lambda x: (x['MaxDD'], -x['WinRate'], -x['NetProfit']))

print("="*85)
print("  TOP 5 SETTINGS RANKED STRICTLY BY LOWEST DRAWDOWN (MAX DD < 20%)")
print("="*85)
for i, c in enumerate(rows[:5], 1):
    print(f"Rank {i}: Combo #{c['ID']:03d} | Slots: {c['Slots']} | Sniper SL: ${c['SniperSL']} | Struct SL: {c['StructSL']}x")
    print(f"        Settings: BE Trig={c['BE_Trig']}R | Trail Trig={c['TrailTrig']}R | RevExit={c['ReversalExit']} | 70% Consensus Trail={c['ConsensusTrail']}")
    print(f"        RESULTS:  Win Rate: {c['WinRate']:.2f}% | Net Profit: +${c['NetProfit']:.2f} | PF: {c['ProfitFactor']:.2f} | Max DD: {c['MaxDD']:.2f}% (Lowest Risk)")
    print("-" * 85)
