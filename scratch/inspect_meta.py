import json

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

p = d['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']
meta = p['meta']
for k, v in meta.items():
    print(f"{k}: {repr(v).encode('ascii', errors='backslashreplace').decode('ascii')}")
