import json

with open("data/processed/dashboard_payload.json", "r", encoding="utf-8") as f:
    d = json.load(f)

# Let's inspect all profiles to see the lineage of MUX_085SL
for k, v in d['profiles'].items():
    if 'MUX' in k or 'CHAMPION' in k:
        trades = v.get('trades', [])
        print(f"Profile: {k} -> {len(trades)} trades")
