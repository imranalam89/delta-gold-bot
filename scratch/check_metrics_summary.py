import json

with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print(f"{'AGENT':12} | {'1m Timeframe':26} | {'5m Timeframe':24} | {'15m Timeframe':24} | {'1h Timeframe':24}")
print("-" * 118)
for aid, data in d.items():
    tfs = data['timeframes']
    t1m = f"{tfs['1m']['trades_count']}t ({tfs['1m']['win_rate']:.1f}%, ${tfs['1m']['net_pnl']:+.1f})"
    t5m = f"{tfs['5m']['trades_count']}t ({tfs['5m']['win_rate']:.1f}%, ${tfs['5m']['net_pnl']:+.1f})"
    t15m = f"{tfs['15m']['trades_count']}t ({tfs['15m']['win_rate']:.1f}%, ${tfs['15m']['net_pnl']:+.1f})"
    t1h = f"{tfs['1h']['trades_count']}t ({tfs['1h']['win_rate']:.1f}%, ${tfs['1h']['net_pnl']:+.1f})"
    print(f"{aid:12} | {t1m:26} | {t5m:24} | {t15m:24} | {t1h:24}")
