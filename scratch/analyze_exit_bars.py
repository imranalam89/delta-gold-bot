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
closes= np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)
    closes[i]= round((cur_open + dc[i]) * 0.1, 2)

trades = payload['profiles']['MUX_085SL_NEWS_SHIELD_ELITE']['trades']

outside_bars = []
for t in trades:
    ext_idx = t['exit_idx']
    ext_px = t['exit_price']
    l = lows[ext_idx]
    h = highs[ext_idx]
    if ext_px < (l - 0.5) or ext_px > (h + 0.5):
        outside_bars.append((t, l, h))

print(f"Total trades where exit_px is outside [low, high] of exit_idx bar: {len(outside_bars)}")

# Group by exit reason
reasons = {}
for t, l, h in outside_bars:
    r = t['exit_reason']
    reasons[r] = reasons.get(r, 0) + 1

print("\nDistribution of exit reasons for outside_bars:")
for r, count in sorted(reasons.items(), key=lambda x: -x[1]):
    print(f"  {r}: {count}")

print("\nSample 5 trades:")
for t, l, h in outside_bars[:5]:
    print(f"Trade #{t['id']} ({t['direction']}) Exit Reason: {t['exit_reason']}")
    print(f"  Entry: {t['entry_time']} @ {t['entry_price']} | Exit: {t['exit_time']} @ {t['exit_price']}")
    print(f"  Exit bar (idx {t['exit_idx']}): Low={l}, High={h}")
    # Check if exit_px was within the high-low of any bar between entry and exit
    trade_high = np.max(highs[t['entry_idx']:t['exit_idx']+1])
    trade_low = np.min(lows[t['entry_idx']:t['exit_idx']+1])
    print(f"  Entire Trade Range: Low={trade_low:.2f}, High={trade_high:.2f}")
    print(f"  Is exit_price within Entire Trade Range? {trade_low <= t['exit_price'] <= trade_high}\n")
