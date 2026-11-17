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

trades = payload['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
print(f"Auditing Baseline MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL ({len(trades)} trades)...")

timing_errs = 0
candle_errs = 0
math_errs = 0
eq_errs = 0
running_eq = 100.0

for t in trades:
    ent_i = t['entry_idx']
    ext_i = t['exit_idx']
    if abs(times[ent_i] - t['entry_ts']) > 60 or abs(times[ext_i] - t['exit_ts']) > 60:
        timing_errs += 1
    if not (lows[ent_i] - 0.5 <= t['entry_price'] <= highs[ent_i] + 0.5):
        candle_errs += 1
    if not (lows[ext_i] - 0.5 <= t['exit_price'] <= highs[ext_i] + 0.5):
        candle_errs += 1
        
    pts = round((t['exit_price'] - t['entry_price']) if t['direction'] == 'LONG' else (t['entry_price'] - t['exit_price']), 2)
    if abs(pts - t['pnl_pts']) > 0.01:
        math_errs += 1
    if abs(round(pts/t['init_risk_pts'], 2) - t['r_multiple']) > 0.01:
        math_errs += 1
        
    running_eq += t['net_pnl_usd']
    if abs(round(running_eq, 2) - t['equity_after']) > 0.05:
        eq_errs += 1

print(f"Baseline Timing Errors:         {timing_errs}")
print(f"Baseline Candle Bounds Errors:  {candle_errs}")
print(f"Baseline Math Errors:           {math_errs}")
print(f"Baseline Equity Errors:         {eq_errs}")
print(f"Baseline Stated Ending Equity:  ${trades[-1]['equity_after']:.2f}")
print(f"Baseline Calculated Equity:     ${running_eq:.2f}")
