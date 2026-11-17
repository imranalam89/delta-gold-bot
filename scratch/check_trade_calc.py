import json

with open("data/processed/dashboard_payload.json", "r", encoding="utf-8") as f:
    d = json.load(f)

# Check baseline profile
p1_trades = d['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
print("P1 trades total:", len(p1_trades))

t30_p1 = None
for t in p1_trades:
    if t.get('orig_id') == 36 or t.get('id') == 36 or (t['entry_time'] == '2026-06-24 07:35 UTC'):
        t30_p1 = t
        break

if t30_p1:
    print("Found Trade in P1:")
    for k in ['id', 'direction', 'entry_price', 'exit_price', 'pnl_pts', 'r_multiple', 'qty_oz', 'gross_pnl_usd', 'delta_fee_usd', 'net_pnl_usd', 'init_risk_pts']:
        print(f"  {k}: {t30_p1.get(k)}")
    ent = t30_p1['entry_price']
    ext = t30_p1['exit_price']
    print(f"  ent - ext = {ent - ext:.2f}")
    print(f"  (ent - ext)/init_risk_pts = {(ent - ext)/t30_p1['init_risk_pts']:.2f}")
    print(f"  (ent - ext) * qty_oz = {(ent - ext)*t30_p1['qty_oz']:.2f}")
