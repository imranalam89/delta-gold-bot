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
t8 = trades[7] # 0-indexed #8

print("Trade #8:")
print(f"Entry idx: {t8['entry_idx']} ({t8['entry_time']}) @ {t8['entry_price']}")
print(f"Exit idx:  {t8['exit_idx']} ({t8['exit_time']}) @ {t8['exit_price']}")

# Find all bars between entry and exit where High >= 4334.72
crossed_bars = []
for k in range(t8['entry_idx'], min(n, t8['entry_idx'] + 180)):
    if lows[k] <= t8['exit_price'] <= highs[k]:
        crossed_bars.append(k)

print(f"Bars crossing {t8['exit_price']}: {crossed_bars}")
