import csv
import pandas as pd

df = pd.read_parquet('data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet')
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

trades = []
with open('data/processed/trades_100PCT_VERIFIED_CHAMPION.csv', 'r') as f:
    trades = list(csv.DictReader(f))

for i, t in enumerate(trades):
    ent_t = pd.to_datetime(t['entry_time'])
    ext_t = pd.to_datetime(t['exit_time'])
    bars_t = df.loc[ent_t:ext_t]
    if len(bars_t) == 0: continue
    if t['exit_reason'] != 'SL':
        sl = float(t['sl_price'])
        if t['direction'] == 'LONG':
            min_l = bars_t['low'].min()
            if min_l < sl:
                print(f"Trade #{i+1} [LONG]: min_low={min_l} < sl={sl} at {bars_t[bars_t['low'] < sl].index[0]}")
        else:
            max_h = bars_t['high'].max()
            if max_h > sl:
                print(f"Trade #{i+1} [SHORT]: max_high={max_h} > sl={sl} at {bars_t[bars_t['high'] > sl].index[0]}")
