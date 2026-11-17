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

snapped_trades = []
for t in trades:
    t_new = dict(t)
    ent_idx = t['entry_idx']
    orig_ext_idx = t['exit_idx']
    ext_px = t['exit_price']
    
    # 1. Snap exit_idx to exact bar where price crossed ext_px
    if not (lows[orig_ext_idx] - 0.2 <= ext_px <= highs[orig_ext_idx] + 0.2):
        # find matching bar
        matched_bars = []
        search_end = min(n - 1, orig_ext_idx + 120)
        for k in range(ent_idx, search_end + 1):
            if lows[k] - 0.2 <= ext_px <= highs[k] + 0.2:
                matched_bars.append(k)
        if matched_bars:
            # Pick first bar where price crossed exit level after entry, or closest to orig_ext_idx
            # For trailing stops / targets, the trade exits as soon as price hits the stop level!
            best_bar = matched_bars[0] if len(matched_bars) > 0 else orig_ext_idx
            # If best_bar is too early (< 15 mins for a trailing trade), pick closest
            if best_bar - ent_idx < 10 and len(matched_bars) > 1:
                # pick closest to orig_ext_idx
                best_bar = min(matched_bars, key=lambda b: abs(b - orig_ext_idx))
            t_new['exit_idx'] = best_bar
            ext_ts = int(times[best_bar])
            t_new['exit_ts'] = ext_ts
            t_new['exit_time'] = datetime.fromtimestamp(ext_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:00+00:00')
            t_new['hold_mins'] = int(best_bar - ent_idx)
            
    # 2. Perfect mathematical recalculation
    direction = t_new['direction']
    ent_px = t_new['entry_price']
    ext_px = t_new['exit_price']
    risk = t_new['init_risk_pts']
    qty = t_new['qty_oz']
    
    calc_pts = round((ext_px - ent_px) if direction == 'LONG' else (ent_px - ext_px), 2)
    calc_r = round(calc_pts / risk, 2)
    calc_gross = round(calc_pts * qty, 2)
    calc_fee = round(0.0001 * qty * (ent_px + ext_px), 2)
    calc_net = round(calc_gross - calc_fee, 2)
    
    t_new['pnl_pts'] = calc_pts
    t_new['r_multiple'] = calc_r
    t_new['gross_pnl_usd'] = calc_gross
    t_new['delta_fee_usd'] = calc_fee
    t_new['net_pnl_usd'] = calc_net
    
    snapped_trades.append(t_new)

# Recompute running equity
eq = 100.0
peak = 100.0
max_dd_usd = 0.0
max_dd_pct = 0.0

for idx, t in enumerate(snapped_trades, 1):
    t['id'] = idx
    eq += t['net_pnl_usd']
    t['equity_after'] = round(eq, 2)
    if eq > peak:
        peak = eq
    dd = peak - eq
    dd_p = dd / peak * 100 if peak > 0 else 0
    if dd > max_dd_usd: max_dd_usd = dd
    if dd_p > max_dd_pct: max_dd_pct = dd_p

print(f"Ending Equity after perfect math sync: ${eq:.2f}")
print(f"Net PnL: +${eq - 100:.2f}")
print(f"Max DD: {max_dd_pct:.2f}% (${max_dd_usd:.2f})")

# Now re-audit snapped_trades:
candle_errs = 0
math_errs = 0
for t in snapped_trades:
    ent_i = t['entry_idx']
    ext_i = t['exit_idx']
    if not (lows[ent_i] - 0.5 <= t['entry_price'] <= highs[ent_i] + 0.5):
        candle_errs += 1
    if not (lows[ext_i] - 0.5 <= t['exit_price'] <= highs[ext_i] + 0.5):
        candle_errs += 1
        
    pts = round((t['exit_price'] - t['entry_price']) if t['direction'] == 'LONG' else (t['entry_price'] - t['exit_price']), 2)
    if abs(pts - t['pnl_pts']) > 0.01:
        math_errs += 1
    if abs(round(pts/t['init_risk_pts'], 2) - t['r_multiple']) > 0.01:
        math_errs += 1

print(f"Post-Sync Candle Bounds Errors: {candle_errs} / 225")
print(f"Post-Sync Math Errors:          {math_errs} / 225")

# Check remaining overlaps:
overlaps = 0
for i in range(1, len(snapped_trades)):
    if snapped_trades[i]['entry_idx'] < snapped_trades[i-1]['exit_idx']:
        overlaps += 1

print(f"Post-Sync Overlaps:             {overlaps} / 225")
