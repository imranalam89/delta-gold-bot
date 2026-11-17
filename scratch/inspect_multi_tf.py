import json

with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    b = json.load(f)

print(f"{'Agent':<10} | {'1m (WR / Trades / Net)':<24} | {'5m (WR / Trades / Net)':<24} | {'15m (WR / Trades / Net)':<24} | {'1h (WR / Trades / Net)':<24}")
print("-" * 115)

for ag, data in b.items():
    tf = data.get('timeframes', {})
    def fmt(k):
        t = tf.get(k, {})
        return f"{t.get('win_rate', 0):.1f}% | {t.get('trades_count', 0)}T | ${t.get('net_pnl', 0):.1f}"
    print(f"{ag:<10} | {fmt('1m'):<24} | {fmt('5m'):<24} | {fmt('15m'):<24} | {fmt('1h'):<24}")
