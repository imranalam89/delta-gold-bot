import json

with open("data/processed/dashboard_payload.json", "r", encoding="utf-8") as f:
    d = json.load(f)

p2_trades = d['profiles']['MUX_085SL_NEWS_SHIELD_ELITE']['trades']
t30 = p2_trades[29]
orig_id = t30['orig_id']
print(f"Trade #30 has orig_id = {orig_id}")

p1_trades = d['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
t_p1 = [t for t in p1_trades if t['id'] == orig_id][0]

print("Fields in P1 trade:")
for k in ['id', 'entry_time', 'exit_time', 'direction', 'entry_price', 'exit_price', 'pnl_pts', 'r_multiple', 'qty_oz', 'gross_pnl_usd', 'delta_fee_usd', 'net_pnl_usd', 'init_risk_pts', 'exit_reason']:
    print(f"  {k}: {t_p1.get(k)}")
