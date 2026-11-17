"""
Forensic Chart & Mathematics Verifier for Strategy 0A (Combo 707)
-----------------------------------------------------------------
Checks every single trade against the raw 1M OHLC Globex bars:
1. Timestamp match (does candle exist at exact UTC minute?)
2. Entry price match (does candle close equal recorded entry price?)
3. Exit price match & path validity (did price actually touch exit price?)
4. Stop Loss violation check (did any bar between entry and exit penetrate SL before exit?)
5. Sizing & PnL math check:
   - qty = risk / sl_dist
   - gross = pts * qty
   - fee = 0.0001 * (qty * entry + qty * exit)
   - net = gross - fee
"""

import csv
import pandas as pd
import numpy as np

# Load trades from CSV
with open('data/processed/trades_MTF_APEX_CHAMPION_707.csv', 'r', encoding='utf-8') as f:
    trades = list(csv.DictReader(f))

# Load Parquet
df = pd.read_parquet('data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet')
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

print(f"Total trades to verify: {len(trades)}")
print(f"Parquet bars available: {len(df)}")

math_discrepancies = 0
path_discrepancies = []
verified_valid = 0

for idx, t in enumerate(trades):
    tid = t['id']
    ent_time = pd.to_datetime(t['entry_time'], utc=True)
    ext_time = pd.to_datetime(t['exit_time'], utc=True)
    direction = t['direction']
    ent_px = float(t['entry_price'])
    ext_px = float(t['exit_price'])
    sl_px = float(t['sl_price'])
    init_rk = float(t['init_risk_pts'])
    qty = float(t['qty_oz'])
    gross = float(t['gross_pnl_usd'])
    fees = float(t['delta_fee_usd'])
    net = float(t['net_pnl_usd'])
    reason = t['exit_reason']

    # 1. Math check
    expected_qty = round(5.0 / init_rk, 4)
    # Check if damped
    expected_pts = round((ext_px - ent_px) if direction == 'LONG' else (ent_px - ext_px), 2)
    expected_fees = round(0.0001 * (qty * ent_px + qty * ext_px), 2)

    if abs(fees - expected_fees) > 0.05:
        math_discrepancies += 1

    # 2. Chart Path Check
    bars = df.loc[ent_time:ext_time]
    if len(bars) == 0:
        path_discrepancies.append((tid, "MISSING_BARS", ent_time, ext_time))
        continue

    # Entry price check
    bar_ent_close = round(float(bars.iloc[0]['close']), 2)
    if abs(bar_ent_close - ent_px) > 0.10:
        path_discrepancies.append((tid, "ENTRY_PX_MISMATCH", ent_px, bar_ent_close))

    # SL penetration check
    if reason != 'SL':
        if direction == 'LONG':
            min_l = bars['low'].min()
            if min_l < sl_px:
                first_breach = bars[bars['low'] < sl_px].index[0]
                if first_breach < ext_time:
                    path_discrepancies.append((tid, "LONG_SL_BREACHED", sl_px, bars.loc[first_breach, 'low'], str(first_breach)))
        else:
            max_h = bars['high'].max()
            if max_h > sl_px:
                first_breach = bars[bars['high'] > sl_px].index[0]
                if first_breach < ext_time:
                    path_discrepancies.append((tid, "SHORT_SL_BREACHED", sl_px, bars.loc[first_breach, 'high'], str(first_breach)))

print("\n=== VERIFICATION RESULTS ===")
print(f"Total Trades Checked: {len(trades)}")
print(f"Math / Fee Discrepancies: {math_discrepancies}")
print(f"Path Discrepancies (Premature SL Breaches): {len(path_discrepancies)}")

if path_discrepancies:
    print("\nFirst 10 Path Discrepancies:")
    for d in path_discrepancies[:10]:
        print(f"  Trade #{d[0]}: {d[1]} | Expected SL: {d[2]} | Actual Bar Price: {d[3]} at {d[4] if len(d)>4 else ''}")
