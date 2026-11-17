import json
import struct, base64
import numpy as np
from datetime import datetime, timezone

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
times = np.zeros(n, dtype=np.int64)
highs = np.zeros(n, dtype=np.float32)
lows  = np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    times[i] = cur_min * 60
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)

trades = payload['profiles']['MUX_085SL_NEWS_SHIELD_ELITE']['trades']

snapped = []
for t in trades:
    t_new = dict(t)
    ent_idx = t['entry_idx']
    orig_ext = t['exit_idx']
    ext_px = t['exit_price']
    if not (lows[orig_ext] - 0.2 <= ext_px <= highs[orig_ext] + 0.2):
        matched = [k for k in range(ent_idx, min(n - 1, orig_ext + 120)) if lows[k] - 0.2 <= ext_px <= highs[k] + 0.2]
        if matched:
            best = min(matched, key=lambda b: abs(b - orig_ext))
            t_new['exit_idx'] = best
            t_new['exit_ts'] = int(times[best])
            t_new['exit_time'] = datetime.fromtimestamp(int(times[best]), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:00+00:00')
            t_new['hold_mins'] = int(best - ent_idx)
    snapped.append(t_new)

for i in range(1, len(snapped)):
    prev = snapped[i-1]
    curr = snapped[i]
    if curr['entry_idx'] < prev['exit_idx']:
        print(f"Overlap between #{prev['id']} (exit_idx={prev['exit_idx']}) and #{curr['id']} (entry_idx={curr['entry_idx']}):")
        print(f"  Prev: #{prev['id']} [{prev['direction']}] {prev['entry_time']} -> {prev['exit_time']} | Reason: {prev['exit_reason']}")
        print(f"  Curr: #{curr['id']} [{curr['direction']}] {curr['entry_time']} -> {curr['exit_time']} | Reason: {curr['exit_reason']}\n")
