import json
import base64
import numpy as np
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

print("[SNIPER BACKTEST] Loading 5-month continuous 1m dataset from dashboard_payload.json...")
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

o_d = np.cumsum(do_i16.astype(np.int64)) + start_open
h_d = o_d + dh_u16
l_d = o_d - dl_u16
c_d = o_d + dc_i16

opens = o_d / 10.0
highs = h_d / 10.0
lows = l_d / 10.0
closes = c_d / 10.0

ts_arr = np.empty(n, dtype=np.int64)
ts_arr[0] = start_ts
for i in range(1, n):
    ts_arr[i] = ts_arr[i-1] + int(dt_u16[i]) * 60

print(f"[SNIPER BACKTEST] Loaded {n:,} 1m candles. Running simulation...")

# Backtest engine for Sniper Entries
def run_sniper_simulation(sl_pts, name, entry_retest_pct=0.50):
    trades = []
    active_trade = None
    account_equity = 100.0  # $100 starting capital
    risk_usd = 5.0          # $5 fixed risk per trade
    fee_rate = 0.0001       # 0.01% fee per leg
    
    # 60-bar (1 hour) lookback to identify session liquidity pools
    lookback = 60
    
    # Skip single-candle news anomalies (1m candle range >= $18)
    candle_ranges = highs - lows

    # We step through 1m bars
    i = lookback
    while i < n - 60:
        if candle_ranges[i] >= 18.0:
            i += 1
            continue

        # 1. Manage Active Trade
        if active_trade is not None:
            t = active_trade
            bars_held = i - t['entry_idx']
            h = highs[i]
            l = lows[i]
            c = closes[i]
            entry = t['entry']
            sl = t['sl']
            init_risk = t['init_risk']
            direction = t['dir']

            exit_px = None
            exit_reason = None

            if direction == 'LONG':
                mfe = h - entry
                if l <= sl:
                    exit_px = sl
                    exit_reason = "STOP_LOSS"
                elif t['rem_weight'] <= 0.05:
                    exit_px = h
                    exit_reason = "ALL_TPS_HIT"
                else:
                    # Breakeven Lock at +2.5R
                    if mfe >= 2.5 * init_risk and t['stage'] == 'ARMED':
                        t['sl'] = max(t['sl'], entry + 0.5 * init_risk)
                        t['stage'] = 'BREAKEVEN'

                    # TP1 at +4.0R (Bank 40%)
                    if mfe >= t['tp1_dist'] and t['tp1_open']:
                        t['banked_pts'] += 0.40 * t['tp1_dist']
                        t['rem_weight'] -= 0.40
                        t['tp1_open'] = False
                        t['sl'] = max(t['sl'], entry + 1.0 * init_risk)
                        t['stage'] = 'TP1_HIT'

                    # TP2 at +10.0R (Bank 35%)
                    if mfe >= t['tp2_dist'] and t['tp2_open']:
                        t['banked_pts'] += 0.35 * t['tp2_dist']
                        t['rem_weight'] -= 0.35
                        t['tp2_open'] = False
                        t['sl'] = max(t['sl'], entry + 4.0 * init_risk)
                        t['stage'] = 'TP2_HIT'

                    # Trailing Stop for 25% Runner (trails behind 15m swings)
                    if t['stage'] in ('TP1_HIT', 'TP2_HIT') and t['rem_weight'] > 0:
                        trail_px = c - max(3.5, 2.0 * init_risk)
                        if trail_px > t['sl']:
                            t['sl'] = trail_px

                    # Max hold time: 480 mins (8 hours)
                    if bars_held >= 480 and exit_px is None:
                        exit_px = c
                        exit_reason = "TIME_EXIT_8H"

            else: # SHORT
                mfe = entry - l
                if h >= sl:
                    exit_px = sl
                    exit_reason = "STOP_LOSS"
                elif t['rem_weight'] <= 0.05:
                    exit_px = l
                    exit_reason = "ALL_TPS_HIT"
                else:
                    if mfe >= 2.5 * init_risk and t['stage'] == 'ARMED':
                        t['sl'] = min(t['sl'], entry - 0.5 * init_risk)
                        t['stage'] = 'BREAKEVEN'

                    if mfe >= t['tp1_dist'] and t['tp1_open']:
                        t['banked_pts'] += 0.40 * t['tp1_dist']
                        t['rem_weight'] -= 0.40
                        t['tp1_open'] = False
                        t['sl'] = min(t['sl'], entry - 1.0 * init_risk)
                        t['stage'] = 'TP1_HIT'

                    if mfe >= t['tp2_dist'] and t['tp2_open']:
                        t['banked_pts'] += 0.35 * t['tp2_dist']
                        t['rem_weight'] -= 0.35
                        t['tp2_open'] = False
                        t['sl'] = min(t['sl'], entry - 4.0 * init_risk)
                        t['stage'] = 'TP2_HIT'

                    if t['stage'] in ('TP1_HIT', 'TP2_HIT') and t['rem_weight'] > 0:
                        trail_px = c + max(3.5, 2.0 * init_risk)
                        if trail_px < t['sl']:
                            t['sl'] = trail_px

                    if bars_held >= 480 and exit_px is None:
                        exit_px = c
                        exit_reason = "TIME_EXIT_8H"

            if exit_px is not None:
                rem_pts = (exit_px - entry) if direction == 'LONG' else (entry - exit_px)
                total_pts = t['banked_pts'] + t['rem_weight'] * rem_pts
                qty_oz = risk_usd / max(init_risk, 0.50)
                gross_usd = total_pts * qty_oz
                fee_usd = fee_rate * (qty_oz * entry + qty_oz * exit_px)
                net_usd = gross_usd - fee_usd
                account_equity += net_usd

                r_achieved = total_pts / max(init_risk, 0.50)

                dt_ent = datetime.fromtimestamp(ts_arr[t['entry_idx']], tz=IST)
                dt_ext = datetime.fromtimestamp(ts_arr[i], tz=IST)

                trades.append({
                    'entry_time': dt_ent.strftime('%Y-%m-%d %H:%M'),
                    'exit_time': dt_ext.strftime('%Y-%m-%d %H:%M'),
                    'dir': direction,
                    'entry': round(entry, 2),
                    'exit': round(exit_px, 2),
                    'sl_pts': round(init_risk, 2),
                    'total_pts': round(total_pts, 2),
                    'max_pts': round(mfe, 2),
                    'r_mult': round(r_achieved, 2),
                    'net_usd': round(net_usd, 2),
                    'equity': round(account_equity, 2),
                    'exit_reason': exit_reason,
                    'win': net_usd > 0
                })
                active_trade = None
                i += 5 # 5 min cooldown after trade closes
                continue

        # 2. Sniper Signal Detection (when no active trade)
        if active_trade is None:
            # Check session time: Focus on Asia (05:00-09:30 IST), London (12:30-16:30 IST), NY (18:00-22:30 IST)
            cur_dt = datetime.fromtimestamp(ts_arr[i], tz=IST)
            hr = cur_dt.hour
            mn = cur_dt.minute

            in_active_window = (5 <= hr <= 9) or (12 <= hr <= 16) or (18 <= hr <= 22)
            if not in_active_window:
                i += 1
                continue

            # Lookback window for 1H high/low
            prior_h = highs[i-lookback:i].max()
            prior_l = lows[i-lookback:i].min()

            c_now = closes[i]
            o_now = opens[i]
            h_now = highs[i]
            l_now = lows[i]

            # Bullish Sniper Setup:
            # 1. Price swept prior 1-hour low (l_now <= prior_l)
            # 2. Quick displacement up (close > open, strong green candle)
            # 3. Limit / Retest entry near the sweep extreme
            if l_now <= prior_l and c_now > o_now and (c_now - l_now) >= 1.2:
                # Sniper entry at 50% discount of displacement candle
                sniper_entry = round(l_now + entry_retest_pct * (c_now - l_now), 2)
                sniper_sl = round(l_now - 0.50, 2) # 5 ticks below wick low
                actual_sl_dist = round(sniper_entry - sniper_sl, 2)

                if actual_sl_dist <= sl_pts: # Only take if risk fits sniper limit
                    active_trade = {
                        'entry_idx': i,
                        'dir': 'LONG',
                        'entry': sniper_entry,
                        'sl': sniper_sl,
                        'init_risk': actual_sl_dist,
                        'tp1_dist': 4.0 * actual_sl_dist,  # 4R TP1
                        'tp2_dist': 10.0 * actual_sl_dist, # 10R TP2
                        'tp1_open': True,
                        'tp2_open': True,
                        'banked_pts': 0.0,
                        'rem_weight': 1.0,
                        'stage': 'ARMED'
                    }

            # Bearish Sniper Setup:
            # 1. Price swept prior 1-hour high (h_now >= prior_h)
            # 2. Quick displacement down (close < open)
            elif h_now >= prior_h and c_now < o_now and (h_now - c_now) >= 1.2:
                sniper_entry = round(h_now - entry_retest_pct * (h_now - c_now), 2)
                sniper_sl = round(h_now + 0.50, 2)
                actual_sl_dist = round(sniper_sl - sniper_entry, 2)

                if actual_sl_dist <= sl_pts:
                    active_trade = {
                        'entry_idx': i,
                        'dir': 'SHORT',
                        'entry': sniper_entry,
                        'sl': sniper_sl,
                        'init_risk': actual_sl_dist,
                        'tp1_dist': 4.0 * actual_sl_dist,  # 4R TP1
                        'tp2_dist': 10.0 * actual_sl_dist, # 10R TP2
                        'tp1_open': True,
                        'tp2_open': True,
                        'banked_pts': 0.0,
                        'rem_weight': 1.0,
                        'stage': 'ARMED'
                    }

        i += 1

    return trades

# Test 3 different Sniper SL settings:
# 1. Ultra-Sniper ($1.80 SL)
# 2. Standard Sniper ($2.50 SL)
# 3. Controlled Sniper ($3.20 SL)
# 4. Standard Base ($5.50 SL)

res_180 = run_sniper_simulation(1.80, "ULTRA_SNIPER ($1.80 SL)")
res_250 = run_sniper_simulation(2.50, "STANDARD_SNIPER ($2.50 SL)")
res_320 = run_sniper_simulation(3.20, "BALANCED_SNIPER ($3.20 SL)")
res_550 = run_sniper_simulation(5.50, "WIDE_BASE ($5.50 SL)")

def print_sniper_report(title, tr_list):
    if not tr_list:
        print(f"[{title}] No trades.")
        return
    wins = [t for t in tr_list if t['win']]
    losses = [t for t in tr_list if not t['win']]
    wr = len(wins) / len(tr_list) * 100.0
    tot_pnl = sum(t['net_usd'] for t in tr_list)
    gross_win = sum(t['net_usd'] for t in wins)
    gross_loss = abs(sum(t['net_usd'] for t in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0

    r_multiples = [t['r_mult'] for t in tr_list]
    avg_win_r = sum(t['r_mult'] for t in wins) / max(len(wins), 1)

    # Count high RR achievements
    rr_5 = len([t for t in tr_list if t['r_mult'] >= 5.0])
    rr_10 = len([t for t in tr_list if t['r_mult'] >= 10.0])
    rr_15 = len([t for t in tr_list if t['r_mult'] >= 15.0])
    max_r = max(r_multiples) if r_multiples else 0.0

    print("="*68)
    print(f"  {title}")
    print("="*68)
    print(f"Total Trades:           {len(tr_list)}")
    print(f"Win Rate:               {wr:.2f}% ({len(wins)}W / {len(losses)}L)")
    print(f"Total Net PnL:          ${tot_pnl:+.2f} (from $100 starting equity)")
    print(f"Profit Factor (PF):     {pf:.2f}")
    print(f"Average Win RR:         {avg_win_r:.2f}R")
    print(f"Max Single Trade RR:    +{max_r:.2f}R")
    print(f"Trades hitting >= 5R:   {rr_5}")
    print(f"Trades hitting >= 10R:  {rr_10}")
    print(f"Trades hitting >= 15R:  {rr_15}")
    print("-"*68)
    print("Top 4 Highest RR Sniper Trades:")
    for t in sorted(tr_list, key=lambda x: x['r_mult'], reverse=True)[:4]:
        print(f"  {t['entry_time']} | {t['dir']:5s} | Entry: {t['entry']} | SL: ${t['sl_pts']} | Max: +${t['max_pts']} | RR: +{t['r_mult']}R | Net: +${t['net_usd']:.2f}")

print_sniper_report("1. ULTRA-SNIPER ($1.80 MAX SL)", res_180)
print_sniper_report("2. STANDARD SNIPER ($2.50 MAX SL)", res_250)
print_sniper_report("3. BALANCED SNIPER ($3.20 MAX SL)", res_320)
print_sniper_report("4. CONSERVATIVE BASE ($5.50 MAX SL)", res_550)
