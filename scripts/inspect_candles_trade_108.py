import pandas as pd

bars = pd.read_parquet('data/processed/xautusd_delta_oct1_to_now_1m.parquet')
if 'timestamp' in bars.columns:
    bars.set_index('timestamp', inplace=True)
elif 'time' in bars.columns:
    bars.set_index('time', inplace=True)

# 5m resample
bars_5m = bars.resample('5min').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last'
}).dropna()

sub_5m = bars_5m.loc['2026-11-15 09:10:00':'2026-11-15 11:30:00']
print("=== 5-MINUTE CANDLES (09:10 to 11:30 UTC) ===")
for ts, r in sub_5m.iterrows():
    print(f"{ts} | O: {r['open']:.2f} | H: {r['high']:.2f} | L: {r['low']:.2f} | C: {r['close']:.2f}")

print("\n=== 1-MINUTE CANDLES (10:45 to 11:15 UTC) ===")
sub_1m = bars.loc['2026-11-15 10:45:00':'2026-11-15 11:15:00']
for ts, r in sub_1m.iterrows():
    print(f"{ts} | O: {r['open']:.2f} | H: {r['high']:.2f} | L: {r['low']:.2f} | C: {r['close']:.2f}")
