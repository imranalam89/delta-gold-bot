import json

with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    b = json.load(f)

total_by_tf = {}
for tf in ['1m', '5m', '15m', '1h']:
    count = sum(len(b[ag]['timeframes'][tf].get('trades', [])) for ag in b)
    total_by_tf[tf] = count
    print(f"Total trades across all 11 agents in {tf}: {count}")

print(f"Total candidate trades across ALL 4 timeframes: {sum(total_by_tf.values())}")
