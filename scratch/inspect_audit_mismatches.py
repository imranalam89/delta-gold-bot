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
dl = struct.unpack(f'<{n}H', base64.b64decode(c['dl']))
dc = struct.unpack(f'<{n}h', base64.b64decode(c['dc']))

cur_min = c['start_ts_min']
cur_open = c['start_open_d']
times = np.zeros(n, dtype=np.int64)
opens = np.zeros(n, dtype=np.float32)
highs = np.zeros(n, dtype=np.float32)
lows  = np.zeros(n, dtype=np.float32)
closes= np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    times[i] = cur_min * 60
    opens[i] = round(cur_open * 0.1, 2)
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)
    closes[i]= round((cur_open + dc[i]) * 0.1, 2)

trades = payload['profiles']['MUX_085SL_NEWS_SHIELD_ELITE']['trades']

print("--- INSPECTING TRADE #30 ---")
t30 = trades[29] # 0-indexed
for k, v in t30.items():
    print(f"  {k}: {v}")

print(f"\nEntry bar (idx={t30['entry_idx']}): O={opens[t30['entry_idx']]}, H={highs[t30['entry_idx']]}, L={lows[t30['entry_idx']]}, C={closes[t30['entry_idx']]}")
print(f"Exit bar (idx={t30['exit_idx']}): O={opens[t30['exit_idx']]}, H={highs[t30['exit_idx']]}, L={lows[t30['exit_idx']]}, C={closes[t30['exit_idx']]}")

print("\n--- INSPECTING TRADE #3 (Candle bounds error) ---")
t3 = trades[2]
for k, v in t3.items():
    print(f"  {k}: {v}")
print(f"Entry bar (idx={t3['entry_idx']}): O={opens[t3['entry_idx']]}, H={highs[t3['entry_idx']]}, L={lows[t3['entry_idx']]}, C={closes[t3['entry_idx']]}")
print(f"Exit bar (idx={t3['exit_idx']}): O={opens[t3['exit_idx']]}, H={highs[t3['exit_idx']]}, L={lows[t3['exit_idx']]}, C={closes[t3['exit_idx']]}")

print("\n--- INSPECTING OVERLAP ERRORS (9 trades) ---")
prev_ext = -1
for t in trades:
    if t['entry_idx'] < prev_ext:
        print(f"Trade #{t['id']} (orig #{t.get('orig_id')}): entry_idx={t['entry_idx']} ({t['entry_time']}) < prev_exit_idx={prev_ext}")
    prev_ext = t['exit_idx']
