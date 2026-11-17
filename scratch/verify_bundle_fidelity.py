import json
import pandas as pd
import numpy as np

# Load bundle
with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

# Load parquet 1M bars
df = pd.read_parquet('data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet')
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

print(f"Parquet loaded: {len(df)} bars")

checked = 0
discrepancies = 0

for ag, data in bundle.items():
    champ = data.get('generations', {}).get('v3.0_ORACLE_CHAMPION', {})
    trades = champ.get('trades', [])
    for t in trades[:15]: # check 15 per agent
        ent_time = pd.to_datetime(t['entry_time'], utc=True)
        ext_time = pd.to_datetime(t['exit_time'], utc=True)
        direction = t['direction']
        ent_px = t['entry_price']
        sl_px = t['sl_price']
        ext_px = t['exit_price']
        reason = t['exit_reason']

        bars = df.loc[ent_time:ext_time]
        if len(bars) == 0:
            continue
        checked += 1

        actual_ent_close = round(float(bars.iloc[0]['close']), 2)
        if abs(actual_ent_close - ent_px) > 0.05:
            print(f"[{ag}] Entry mismatch: actual={actual_ent_close}, record={ent_px} at {ent_time}")
            discrepancies += 1

        exit_bar = bars.iloc[-1]
        if reason == 'SL':
            if direction == 'LONG' and exit_bar['low'] > sl_px + 0.10:
                print(f"[{ag}] SL not touched: low={exit_bar['low']:.2f}, sl={sl_px:.2f} at {ext_time}")
                discrepancies += 1
            elif direction == 'SHORT' and exit_bar['high'] < sl_px - 0.10:
                print(f"[{ag}] SL not touched: high={exit_bar['high']:.2f}, sl={sl_px:.2f} at {ext_time}")
                discrepancies += 1

print(f"\nChecked {checked} trades from original lab bundle. Discrepancies: {discrepancies}")
