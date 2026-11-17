import json

with open("data/processed/dashboard_payload.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for prof_name, prof in d['profiles'].items():
    for t in prof['trades']:
        if t.get('entry_time') == '2026-06-24 07:35 UTC':
            print(f"Profile: {prof_name} -> Trade #{t.get('id')}: pnl_pts={t.get('pnl_pts')}, r_mult={t.get('r_multiple')}, ent={t.get('entry_price')}, ext={t.get('exit_price')}, gross={t.get('gross_pnl_usd')}")
            break
