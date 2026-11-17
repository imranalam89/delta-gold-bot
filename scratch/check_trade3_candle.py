import json
import struct, base64
import numpy as np

PAYLOAD_PATH = "data/processed/dashboard_payload.json"
with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
    payload = json.load(f)

c = payload['continuous_1m']
n = c['n']
dt = struct.unpack(f'<{n}H', base64.b64decode(c['dt']))
do = struct.unpack(f'<{n}h', base64.b64decode(c['do']))
dh = struct.unpack(f'<{n}H', base64.b64decode(c['dh']))
dl = struct.unpack(f'<{n}L', base64.b64decode(c['dl'])) if 'dl' in c and len(base64.b64decode(c['dl'])) == 4*n else struct.unpack(f'<{n}H', base64.b64decode(c['dl']))
dc = struct.unpack(f'<{n}h', base64.b64decode(c['dc']))

cur_min = c['start_ts_min']
cur_open = c['start_open_d']
highs = np.zeros(n, dtype=np.float32)
lows  = np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)

trades = payload['profiles']['MUX_085SL_NEWS_SHIELD_ELITE']['trades']
t3 = trades[2]

print("Trade #3 details:")
for k in ['id', 'direction', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'sl_price', 'pnl_pts', 'r_multiple', 'exit_reason', 'hold_mins', 'entry_idx', 'exit_idx']:
    print(f"  {k}: {t3.get(k)}")

ext_idx = t3['exit_idx']
print(f"\nBars around exit_idx ({ext_idx}):")
for j in range(max(0, ext_idx - 5), min(n, ext_idx + 6)):
    print(f"  idx {j}: Low={lows[j]}, High={highs[j]} {'<-- EXIT BAR' if j == ext_idx else ''}")

# Let's find where price touched exit_price (4515.66)
found_idx = []
for j in range(t3['entry_idx'], min(n, t3['entry_idx'] + 300)):
    if lows[j] <= 4515.66 <= highs[j]:
        found_idx.append(j)
print(f"Bars where price touched 4515.66 within 300 mins: {found_idx[:5]}")
