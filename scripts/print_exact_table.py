import pandas as pd

bars = pd.read_parquet('data/processed/xautusd_delta_oct1_to_now_1m.parquet')
if 'timestamp' in bars.columns:
    bars.set_index('timestamp', inplace=True)
elif 'time' in bars.columns:
    bars.set_index('time', inplace=True)

sub = bars.loc['2026-11-15 10:50:00':'2026-11-15 11:05:00']

entry = 3829.36
sl = 3835.60
rk = 6.24

print("Timestamp | Open | High | Low | Close | Active SL | What Happened")
print("-" * 75)

for ts, r in sub.iterrows():
    t_str = str(ts)[11:16]
    act_sl = 3835.60 if t_str < '11:01' else 3827.61
    note = ""
    if t_str == '10:52':
        note = "<-- Trough Low reached (3825.94). Wait for 5 stall bars..."
    elif t_str == '10:59':
        note = "<-- High touched 3830.18. Active SL still 3835.60, so NOT hit!"
    elif t_str == '11:01':
        note = "<-- 5 bars passed & close <= 3827.61! Trailing SL locks at 3827.61!"
    elif t_str == '11:02':
        note = "<-- High touched 3829.21 >= 3827.61! TRAILING SL HIT & EXITED!"
    print(f"{t_str}     | {r['open']:.2f}| {r['high']:.2f}| {r['low']:.2f}| {r['close']:.2f}| {act_sl:.2f}    | {note}")
