import json

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

profiles = payload.get('profiles', {})
first_k = list(profiles.keys())[0]
first_prof = profiles[first_k]

print("Profile meta keys:", list(first_prof['meta'].keys()))
print("Meta values:")
for k, v in first_prof['meta'].items():
    if k != 'label':
        print(f"  {k}: {v}")
    else:
        print(f"  label length: {len(v)}")

sample_t = first_prof['trades'][0]
print("\nSample trade keys:", list(sample_t.keys()))
print("Sample trade fields:")
for k, v in sample_t.items():
    if k not in ('candles', 'mfe_mae'):
        print(f"  {k}: {v}")
