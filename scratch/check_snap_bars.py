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

can_snap_to_exact_bar = 0
cannot_snap = 0

for t in trades:
    ent_idx = t['entry_idx']
    ext_idx = t['exit_idx']
    ext_px = t['exit_price']
    
    # check if ext_px is already inside exit bar
    if lows[ext_idx] - 0.5 <= ext_px <= highs[ext_idx] + 0.5:
        can_snap_to_exact_bar += 1
        continue
        
    # search within [ent_idx, ext_idx + 60]
    matched_bars = []
    search_end = min(n - 1, ext_idx + 60)
    for k in range(ent_idx, search_end + 1):
        if lows[k] - 0.2 <= ext_px <= highs[k] + 0.2:
            matched_bars.append(k)
            
    if matched_bars:
        # find closest bar to ext_idx
        best_bar = min(matched_bars, key=lambda b: abs(b - ext_idx))
        can_snap_to_exact_bar += 1
    else:
        cannot_snap += 1

print(f"Trades with exact bar match: {can_snap_to_exact_bar} / {len(trades)}")
print(f"Trades without exact bar match in range: {cannot_snap} / {len(trades)}")
