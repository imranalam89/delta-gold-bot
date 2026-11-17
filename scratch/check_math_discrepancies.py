import json

with open("data/processed/dashboard_payload.json", "r", encoding="utf-8") as f:
    d = json.load(f)

trades = d['profiles']['MUX_085SL_NEWS_SHIELD_ELITE']['trades']

print("Auditing math across all 225 trades:")
discrepancies = []

eq = 100.0
for idx, t in enumerate(trades, 1):
    direction = t['direction']
    ent = t['entry_price']
    ext = t['exit_price']
    risk = t['init_risk_pts']
    qty = t['qty_oz']
    
    # 1. PnL points
    calc_pts = round((ext - ent) if direction == 'LONG' else (ent - ext), 2)
    stated_pts = t['pnl_pts']
    
    # 2. R multiple
    calc_r = round(calc_pts / risk, 2)
    stated_r = t['r_multiple']
    
    # 3. Gross PnL
    calc_gross = round(calc_pts * qty, 2)
    stated_gross = t['gross_pnl_usd']
    
    # 4. Fee
    calc_fee = round(0.0001 * qty * (ent + ext), 2)
    stated_fee = t['delta_fee_usd']
    
    # 5. Net PnL
    calc_net = round(calc_gross - calc_fee, 2)
    stated_net = t['net_pnl_usd']
    
    eq += stated_net
    calc_eq = round(eq, 2)
    stated_eq = t['equity_after']
    
    if abs(calc_pts - stated_pts) > 0.05 or abs(calc_r - stated_r) > 0.05:
        discrepancies.append({
            'id': t['id'],
            'direction': direction,
            'ent': ent,
            'ext': ext,
            'calc_pts': calc_pts,
            'stated_pts': stated_pts,
            'calc_r': calc_r,
            'stated_r': stated_r,
            'calc_gross': calc_gross,
            'stated_gross': stated_gross,
            'calc_net': calc_net,
            'stated_net': stated_net
        })

print(f"Total trades with pnl_pts or r_multiple cosmetic discrepancy: {len(discrepancies)}")
for disc in discrepancies[:10]:
    print(disc)
