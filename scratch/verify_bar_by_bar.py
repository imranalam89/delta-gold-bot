import pandas as pd
import numpy as np
import csv

# Load the trades
trades = []
with open('data/processed/trades_MTF_APEX_CHAMPION_707.csv', 'r', encoding='utf-8') as f:
    trades = list(csv.DictReader(f))

print(f"Loaded {len(trades)} trades from trades_MTF_APEX_CHAMPION_707.csv")

# Load parquet 1M bars
df = pd.read_parquet('data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet')
print(f"Loaded {len(df)} 1M bars from parquet. Index: {df.index[0]} to {df.index[-1]}")

# Check first 10 trades against real bars
issues = 0
for i, t in enumerate(trades[:20]):
    ent_time = pd.to_datetime(t['entry_time'])
    ext_time = pd.to_datetime(t['exit_time'])
    direction = t['direction']
    ent_px = float(t['entry_price'])
    sl_px = float(t['sl_price'])
    tp1_px = float(t['tp1_price'])
    exit_px = float(t['exit_price'])

    # Slice the actual 1M bars between entry and exit
    bars = df.loc[ent_time:ext_time]
    if len(bars) == 0:
        print(f"Trade {i+1}: Cannot find bars for {ent_time} to {ext_time}")
        continue

    # Check if entry price matches
    bar0 = bars.iloc[0]
    bar_end = bars.iloc[-1]
    
    # Check if SL was breached before exit
    if direction == 'LONG':
        min_l = bars['low'].min()
        if min_l < sl_px and t['exit_reason'] != 'SL':
            first_breach = bars[bars['low'] < sl_px].index[0]
            if first_breach < ext_time:
                print(f"Trade {i+1} [LONG]: SL breached at {first_breach} (Low: {bars.loc[first_breach, 'low']:.2f} < SL: {sl_px:.2f}), but exit was recorded at {ext_time} with reason {t['exit_reason']}")
                issues += 1
    else:
        max_h = bars['high'].max()
        if max_h > sl_px and t['exit_reason'] != 'SL':
            first_breach = bars[bars['high'] > sl_px].index[0]
            if first_breach < ext_time:
                print(f"Trade {i+1} [SHORT]: SL breached at {first_breach} (High: {bars.loc[first_breach, 'high']:.2f} > SL: {sl_px:.2f}), but exit was recorded at {ext_time} with reason {t['exit_reason']}")
                issues += 1

print(f"\nTotal potential issues in first 20 trades: {issues}")
