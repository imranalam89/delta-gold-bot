import pandas as pd

bars = pd.read_parquet('data/processed/xautusd_delta_oct1_to_now_1m.parquet')
if 'timestamp' in bars.columns:
    bars.set_index('timestamp', inplace=True)
elif 'time' in bars.columns:
    bars.set_index('time', inplace=True)

sub = bars.loc['2026-11-15 09:15:00':'2026-11-15 11:15:00'].copy()

entry_p = 3829.36
sl_p = 3835.60
risk = 6.24
lowest_p = entry_p

print("=== TRADE #108 1-MINUTE EXECUTION TIMELINE ===")
print(f"Entry: 09:16 UTC @ {entry_p} (SHORT)")
print(f"Initial SL: {sl_p} (Risk = {risk} pts)")

for ts, row in sub.iterrows():
    if row['low'] < lowest_p:
        lowest_p = row['low']
        pts = entry_p - lowest_p
        r = pts / risk
        print(f"[{ts}] New Low: {lowest_p:.2f} (Max Favorable: +{pts:.2f} pts / +{r:.2f}R)")

print("\n=== EXIT BARS (Around 11:00 - 11:05 UTC) ===")
for ts, row in sub.loc['2026-11-15 10:55:00':'2026-11-15 11:08:00'].iterrows():
    print(f"[{ts}] O={row['open']:.2f}  H={row['high']:.2f}  L={row['low']:.2f}  C={row['close']:.2f}")
