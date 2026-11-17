import json

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

print("Keys:", list(payload.keys()))
for k in payload.keys():
    if isinstance(payload[k], list):
        print(k, len(payload[k]))
    elif isinstance(payload[k], dict):
        print(k, list(payload[k].keys())[:5])
