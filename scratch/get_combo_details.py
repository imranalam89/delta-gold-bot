import csv

with open('data/processed/mtf_100s_combinations_results.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

target_ids = ['707', '869']
for r in rows:
    if r['combo_id'] in target_ids:
        print(f"\n=== COMBO {r['combo_id']} CONFIGURATION ===")
        for k, v in r.items():
            print(f"  {k}: {v}")
