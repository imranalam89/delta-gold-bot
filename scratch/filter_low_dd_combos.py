import csv

with open('data/processed/multi_agent_100_combos_results.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for r in rows:
    r['WinRate'] = float(r['WinRate'])
    r['NetProfit'] = float(r['NetProfit'])
    r['ProfitFactor'] = float(r['ProfitFactor'])
    r['MaxDD'] = float(r['MaxDD'])
    r['Score'] = float(r['Score'])

# Filter for low drawdown: Max DD < 15%
low_dd = [r for r in rows if r['MaxDD'] <= 15.0]
# Sort by highest Net Profit & Win Rate
low_dd.sort(key=lambda x: (x['WinRate'], x['NetProfit']), reverse=True)

print(f"Total combinations with Max Drawdown <= 15%: {len(low_dd)}")
print("\n" + "="*85)
print("  TOP 5 CHAMPION SETTINGS FOR LOW DRAWDOWN (DD <= 15%) & HIGH WIN RATE")
print("="*85)

for i, c in enumerate(low_dd[:6], 1):
    print(f"Rank {i}: Combo #{int(c['ID']):03d} | Slots: {c['Slots']} | Sniper SL: ${c['SniperSL']} | Struct SL: {c['StructSL']}x")
    print(f"        Settings: BE Trig={c['BE_Trig']}R | Trail Trig={c['TrailTrig']}R | RevExit={c['ReversalExit']} | 70% Consensus Trail={c['ConsensusTrail']}")
    print(f"        RESULTS:  Win Rate: {c['WinRate']:.2f}% | Net Profit: +${c['NetProfit']:.2f} | PF: {c['ProfitFactor']:.2f} | Max DD: {c['MaxDD']:.2f}% (Ultra-Safe)")
    print("-" * 85)
