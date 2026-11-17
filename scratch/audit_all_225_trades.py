import json
import struct, base64
import numpy as np
from datetime import datetime, timezone

PAYLOAD_PATH = "data/processed/dashboard_payload.json"
print("Loading dashboard payload...")
with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
    payload = json.load(f)

# 1. Decode continuous 1m bars
c = payload['continuous_1m']
n = c['n']
dt = struct.unpack(f'<{n}H', base64.b64decode(c['dt']))
do = struct.unpack(f'<{n}h', base64.b64decode(c['do']))
dh = struct.unpack(f'<{n}H', base64.b64decode(c['dh']))
dl = struct.unpack(f'<{n}H', base64.b64decode(c['dl']))
dc = struct.unpack(f'<{n}h', base64.b64decode(c['dc']))
v  = struct.unpack(f'<{n}H', base64.b64decode(c['v']))

cur_min = c['start_ts_min']
cur_open = c['start_open_d']
times = np.zeros(n, dtype=np.int64)
opens = np.zeros(n, dtype=np.float32)
highs = np.zeros(n, dtype=np.float32)
lows  = np.zeros(n, dtype=np.float32)
closes= np.zeros(n, dtype=np.float32)
vols  = np.zeros(n, dtype=np.float32)

for i in range(n):
    if i > 0:
        cur_min += dt[i]
        cur_open += do[i]
    times[i] = cur_min * 60
    opens[i] = round(cur_open * 0.1, 2)
    highs[i] = round((cur_open + dh[i]) * 0.1, 2)
    lows[i]  = round((cur_open - dl[i]) * 0.1, 2)
    closes[i]= round((cur_open + dc[i]) * 0.1, 2)
    vols[i]  = float(v[i])

print(f"Decoded {n} 1m bars.")

# 2. Get Model 2 Trades
profile = payload['profiles']['MUX_085SL_NEWS_SHIELD_ELITE']
trades = profile['trades']
print(f"Validating {len(trades)} trades in MUX_085SL_NEWS_SHIELD_ELITE...")

# Audit Containers
math_errors = []
timing_errors = []
candle_bounds_errors = []
overlap_errors = []
equity_errors = []
holding_time_errors = []

running_eq = 100.0
prev_exit_idx = -1

for idx, t in enumerate(trades):
    t_id = t['id']
    direction = t['direction']
    ent_idx = t['entry_idx']
    ext_idx = t['exit_idx']
    ent_px = t['entry_price']
    ext_px = t['exit_price']
    sl_px = t['sl_price']
    init_risk = t['init_risk_pts']
    pnl_pts = t['pnl_pts']
    r_mult = t['r_multiple']
    qty = t['qty_oz']
    notional = t.get('notional_usd', 0)
    gross = t['gross_pnl_usd']
    fee = t['delta_fee_usd']
    net = t['net_pnl_usd']
    eq_after = t['equity_after']
    hold_mins = t['hold_mins']
    ent_ts = t['entry_ts']
    ext_ts = t['exit_ts']

    # --- A. Timing & Index Verification ---
    if ent_idx < 0 or ent_idx >= n:
        timing_errors.append(f"Trade #{t_id}: entry_idx {ent_idx} out of range [0, {n-1}]")
    if ext_idx < 0 or ext_idx >= n:
        timing_errors.append(f"Trade #{t_id}: exit_idx {ext_idx} out of range [0, {n-1}]")
    if ext_idx < ent_idx:
        timing_errors.append(f"Trade #{t_id}: exit_idx {ext_idx} < entry_idx {ent_idx}")
    
    # Check timestamp match
    if abs(times[ent_idx] - ent_ts) > 60:
        timing_errors.append(f"Trade #{t_id}: entry_ts mismatch (bar={times[ent_idx]}, trade={ent_ts})")
    if abs(times[ext_idx] - ext_ts) > 60:
        timing_errors.append(f"Trade #{t_id}: exit_ts mismatch (bar={times[ext_idx]}, trade={ext_ts})")
        
    # Check hold_mins
    calc_hold = ext_idx - ent_idx
    if abs(calc_hold - hold_mins) > 2:
        holding_time_errors.append(f"Trade #{t_id}: hold_mins mismatch (calc={calc_hold}, stated={hold_mins})")

    # --- B. Single-Slot Overlap Check ---
    if ent_idx < prev_exit_idx:
        overlap_errors.append(f"Trade #{t_id}: overlaps with previous trade! (ent={ent_idx}, prev_exit={prev_exit_idx})")
    prev_exit_idx = ext_idx

    # --- C. Candle Price Bounds Verification ---
    ent_bar_l = lows[ent_idx]
    ent_bar_h = highs[ent_idx]
    # Entry price should be within or within spread of bar
    if ent_px < (ent_bar_l - 0.5) or ent_px > (ent_bar_h + 0.5):
        candle_bounds_errors.append(f"Trade #{t_id}: entry_px {ent_px} outside bar [{ent_bar_l}, {ent_bar_h}] at idx {ent_idx}")
        
    ext_bar_l = lows[ext_idx]
    ext_bar_h = highs[ext_idx]
    # Exit price should be within or within spread/gap of exit bar
    if ext_px < (ext_bar_l - 1.5) or ext_px > (ext_bar_h + 1.5):
        candle_bounds_errors.append(f"Trade #{t_id}: exit_px {ext_px} outside bar [{ext_bar_l}, {ext_bar_h}] at idx {ext_idx}")

    # --- D. Mathematical Calculations Verification ---
    # Expected pnl_pts
    expected_pts = round((ext_px - ent_px) if direction == 'LONG' else (ent_px - ext_px), 2)
    if abs(expected_pts - pnl_pts) > 0.05:
        math_errors.append(f"Trade #{t_id}: pnl_pts mismatch (calc={expected_pts}, trade={pnl_pts})")

    # Expected r_multiple
    expected_r = round(pnl_pts / init_risk, 2)
    if abs(expected_r - r_mult) > 0.05:
        math_errors.append(f"Trade #{t_id}: r_multiple mismatch (calc={expected_r}, trade={r_mult})")

    # Expected gross pnl
    expected_gross = round(pnl_pts * qty, 2)
    if abs(expected_gross - gross) > 0.10:
        math_errors.append(f"Trade #{t_id}: gross_pnl mismatch (calc={expected_gross}, trade={gross})")

    # Expected fees (0.01% on notional entry + exit)
    expected_fee = round(0.0001 * (qty * ent_px + qty * ext_px), 2)
    if abs(expected_fee - fee) > 0.15:
        math_errors.append(f"Trade #{t_id}: delta_fee mismatch (calc={expected_fee}, trade={fee})")

    # Expected net pnl
    expected_net = round(gross - fee, 2)
    if abs(expected_net - net) > 0.10:
        math_errors.append(f"Trade #{t_id}: net_pnl mismatch (calc={expected_net}, trade={net})")

    # Expected running equity
    running_eq += net
    expected_eq_after = round(running_eq, 2)
    if abs(expected_eq_after - eq_after) > 0.15:
        equity_errors.append(f"Trade #{t_id}: equity_after mismatch (calc={expected_eq_after}, trade={eq_after})")

print("\n" + "="*70)
print("AUDIT & VERIFICATION SUMMARY FOR ALL 225 TRADES:")
print("="*70)
print(f"1. Timing & Index Errors:       {len(timing_errors)}")
print(f"2. Single-Slot Overlap Errors:  {len(overlap_errors)}")
print(f"3. Candle Price Bounds Errors:  {len(candle_bounds_errors)}")
print(f"4. Hold Mins Errors:            {len(holding_time_errors)}")
print(f"5. PnL & R-Multiple Math Errors:{len(math_errors)}")
print(f"6. Running Equity Curve Errors: {len(equity_errors)}")

if timing_errors:
    print("\nTiming errors sample:", timing_errors[:3])
if overlap_errors:
    print("\nOverlap errors sample:", overlap_errors[:3])
if candle_bounds_errors:
    print("\nCandle bounds errors sample:", candle_bounds_errors[:3])
if math_errors:
    print("\nMath errors sample:", math_errors[:3])
if equity_errors:
    print("\nEquity errors sample:", equity_errors[:3])

print("\nMaster Final Equity Check:")
print(f"  Calculated Ending Master Equity: ${running_eq:.2f}")
print(f"  Profile Stated Master Equity:    ${trades[-1]['equity_after']:.2f}")
print(f"  Total Clean Net Profit:          +${running_eq - 100.0:.2f}")
