import json
import base64
import numpy as np
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

print("[DECODER] Loading continuous 1m bars from dashboard_payload.json...")
with open('data/processed/dashboard_payload.json', 'r') as f:
    payload = json.load(f)

c1m = payload['continuous_1m']
n = c1m['n']
start_ts = c1m['start_ts_min'] * 60
start_open = c1m['start_open_d']

dt_u16 = np.frombuffer(base64.b64decode(c1m['dt']), dtype="<u2")
do_i16 = np.frombuffer(base64.b64decode(c1m['do']), dtype="<i2")
dh_u16 = np.frombuffer(base64.b64decode(c1m['dh']), dtype="<u2")
dl_u16 = np.frombuffer(base64.b64decode(c1m['dl']), dtype="<u2")
dc_i16 = np.frombuffer(base64.b64decode(c1m['dc']), dtype="<i2")
v_u16 = np.frombuffer(base64.b64decode(c1m['v']), dtype="<u2")

# Reconstruct 1m OHLCV arrays
ts_arr = np.empty(n, dtype=np.int64)
ts_arr[0] = start_ts
for i in range(1, n):
    ts_arr[i] = ts_arr[i-1] + int(dt_u16[i]) * 60

o_arr = np.cumsum(do_i16) / 10.0
h_arr = (o_arr * 10.0 + dh_u16) / 10.0
l_arr = (o_arr * 10.0 - dl_u16) / 10.0
c_arr = (o_arr * 10.0 + dc_i16) / 10.0
v_arr = v_u16.astype(float)

print(f"[DECODER] Successfully decoded {n:,} 1m candles.")
t_start = datetime.fromtimestamp(ts_arr[0], tz=IST)
t_end = datetime.fromtimestamp(ts_arr[-1], tz=IST)
print(f"Time Range: {t_start.strftime('%Y-%m-%d %H:%M')} to {t_end.strftime('%Y-%m-%d %H:%M')} IST")
print(f"Price Range: ${l_arr.min():.1f} to ${h_arr.max():.1f}")
