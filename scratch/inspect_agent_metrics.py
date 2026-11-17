import json

with open('data/processed/all_11_agents_lab_bundle.json', 'r') as f:
    bundle = json.load(f)

print("Agent       | Trades | WinRate | Net Profit | PF   | Max DD")
print("-" * 55)
for k in list(bundle.keys()):
    champ = bundle[k]['generations']['v3.0_ORACLE_CHAMPION']
    trades = champ.get('trades_count', len(champ.get('trades', [])))
    wr = champ.get('win_rate', 0.0)
    net = champ.get('net_pnl', 0.0)
    pf = champ.get('profit_factor', 0.0)
    dd = champ.get('max_dd_pct', 0.0)
    print(f"{k:11s} | {trades:6d} | {wr:6.1f}% | ${net:9.2f} | {pf:4.2f} | {dd:5.2f}%")
