import json
import base64
import numpy as np
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

with open('data/processed/dashboard_payload.json', 'r') as f:
    payload = json.load(f)

c1m = payload['continuous_1m']
n = c1m['n']
start_ts = c1m['start_ts_min'] * 60
start_open = c1m['start_open_d']

do_i16 = np.frombuffer(base64.b64decode(c1m['do']), dtype="<i2")
dh_u16 = np.frombuffer(base64.b64decode(c1m['dh']), dtype="<u2")
dl_u16 = np.frombuffer(base64.b64decode(c1m['dl']), dtype="<u2")
dc_i16 = np.frombuffer(base64.b64decode(c1m['dc']), dtype="<i2")
dt_u16 = np.frombuffer(base64.b64decode(c1m['dt']), dtype="<u2")

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

# 50 EMA and 200 EMA on 1m
ema_50 = np.empty(n, dtype=float)
ema_200 = np.empty(n, dtype=float)
ema_50[0] = closes[0]
ema_200[0] = closes[0]
k50 = 2.0 / 51.0
k200 = 2.0 / 201.0

for i in range(1, n):
    ema_50[i] = closes[i] * k50 + ema_50[i-1] * (1.0 - k50)
    ema_200[i] = closes[i] * k200 + ema_200[i-1] * (1.0 - k200)

def run_filtered_sniper(sl_max=2.80):
    trades = []
    active_trade = None
    account_equity = 100.0
    risk_usd = 5.0
    fee_rate = 0.0001
    lookback = 60
    candle_ranges = highs - lows

    i = lookback
    while i < n - 60:
        if candle_ranges[i] >= 18.0:
            i += 1
            continue

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
                    if mfe >= 2.0 * init_risk and t['stage'] == 'ARMED':
                        t['sl'] = max(t['sl'], entry + 0.3 * init_risk)
                        t['stage'] = 'BREAKEVEN'

                    if mfe >= t['tp1_dist'] and t['tp1_open']:
                        t['banked_pts'] += 0.40 * t['tp1_dist']
                        t['rem_weight'] -= 0.40
                        t['tp1_open'] = False
                        t['sl'] = max(t['sl'], entry + 1.0 * init_risk)
                        t['stage'] = 'TP1_HIT'

                    if mfe >= t['tp2_dist'] and t['tp2_open']:
                        t['banked_pts'] += 0.35 * t['tp2_dist']
                        t['rem_weight'] -= 0.35
                        t['tp2_open'] = False
                        t['sl'] = max(t['sl'], entry + 3.0 * init_risk)
                        t['stage'] = 'TP2_HIT'

                    if t['stage'] in ('TP1_HIT', 'TP2_HIT') and t['rem_weight'] > 0:
                        trail_px = c - max(3.0, 2.0 * init_risk)
                        if trail_px > t['sl']:
                            t['sl'] = trail_px

                    if bars_held >= 360 and exit_px is None:
                        exit_px = c
                        exit_reason = "TIME_EXIT_6H"

            else: # SHORT
                mfe = entry - l
                if h >= sl:
                    exit_px = sl
                    exit_reason = "STOP_LOSS"
                elif t['rem_weight'] <= 0.05:
                    exit_px = l
                    exit_reason = "ALL_TPS_HIT"
                else:
                    if mfe >= 2.0 * init_risk and t['stage'] == 'ARMED':
                        t['sl'] = min(t['sl'], entry - 0.3 * init_risk)
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
                        t['sl'] = min(t['sl'], entry - 3.0 * init_risk)
                        t['stage'] = 'TP2_HIT'

                    if t['stage'] in ('TP1_HIT', 'TP2_HIT') and t['rem_weight'] > 0:
                        trail_px = c + max(3.0, 2.0 * init_risk)
                        if trail_px < t['sl']:
                            t['sl'] = trail_px

                    if bars_held >= 360 and exit_px is None:
                        exit_px = c
                        exit_reason = "TIME_EXIT_6H"

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
                trades.append({
                    'time': dt_ent.strftime('%Y-%m-%d %H:%M'),
                    'dir': direction,
                    'entry': round(entry, 2),
                    'sl': round(init_risk, 2),
                    'pts': round(total_pts, 2),
                    'max_pts': round(mfe, 2),
                    'r_mult': round(r_achieved, 2),
                    'net_usd': round(net_usd, 2),
                    'equity': round(account_equity, 2),
                    'win': net_usd > 0
                })
                active_trade = None
                i += 10 # 10 min spacing between trades
                continue

        if active_trade is None:
            cur_dt = datetime.fromtimestamp(ts_arr[i], tz=IST)
            hr = cur_dt.hour
            in_session = (5 <= hr <= 9) or (12 <= hr <= 16) or (18 <= hr <= 22)
            if not in_session:
                i += 1
                continue

            prior_h = highs[i-lookback:i].max()
            prior_l = lows[i-lookback:i].min()

            c_now = closes[i]
            o_now = opens[i]
            h_now = highs[i]
            l_now = lows[i]

            # Long with Trend / Sweep Filter
            if l_now <= prior_l and c_now > o_now and (c_now - l_now) >= 1.2:
                sniper_entry = round(l_now + 0.50 * (c_now - l_now), 2)
                sniper_sl = round(l_now - 0.40, 2)
                risk = round(sniper_entry - sniper_sl, 2)

                if risk <= sl_max and c_now > ema_50[i]:
                    active_trade = {
                        'entry_idx': i,
                        'dir': 'LONG',
                        'entry': sniper_entry,
                        'sl': sniper_sl,
                        'init_risk': risk,
                        'tp1_dist': 3.5 * risk,
                        'tp2_dist': 8.0 * risk,
                        'tp1_open': True,
                        'tp2_open': True,
                        'banked_pts': 0.0,
                        'rem_weight': 1.0,
                        'stage': 'ARMED'
                    }

            elif h_now >= prior_h and c_now < o_now and (h_now - c_now) >= 1.2:
                sniper_entry = round(h_now - 0.50 * (h_now - c_now), 2)
                sniper_sl = round(h_now + 0.40, 2)
                risk = round(sniper_sl - sniper_entry, 2)

                if risk <= sl_max and c_now < ema_50[i]:
                    active_trade = {
                        'entry_idx': i,
                        'dir': 'SHORT',
                        'entry': sniper_entry,
                        'sl': sniper_sl,
                        'init_risk': risk,
                        'tp1_dist': 3.5 * risk,
                        'tp2_dist': 8.0 * risk,
                        'tp1_open': True,
                        'tp2_open': True,
                        'banked_pts': 0.0,
                        'rem_weight': 1.0,
                        'stage': 'ARMED'
                    }
        i += 1

    return trades

filtered_trades = run_filtered_sniper(2.80)
wins = [t for t in filtered_trades if t['win']]
losses = [t for t in filtered_trades if not t['win']]
wr = len(wins) / len(filtered_trades) * 100.0 if filtered_trades else 0
tot_pnl = sum(t['net_usd'] for t in filtered_trades)
gross_win = sum(t['net_usd'] for t in wins)
gross_loss = abs(sum(t['net_usd'] for t in losses))
pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
avg_win_r = sum(t['r_mult'] for t in wins) / max(len(wins), 1)

print("="*68)
print("  HIGH-CONFLUENCE SNIPER ENTRY PERFORMANCE (5-MONTH BACKTEST)")
print("="*68)
print(f"Total Trades:           {len(filtered_trades)}")
print(f"Win Rate:               {wr:.2f}% ({len(wins)}W / {len(losses)}L)")
print(f"Total Net PnL:          +${tot_pnl:.2f} (Starting Capital $100)")
print(f"Final Account Equity:   ${100.0 + tot_pnl:.2f}")
print(f"Profit Factor (PF):     {pf:.2f}")
print(f"Average Win RR:         {avg_win_r:.2f}R")
print(f"Trades hitting >= 5R:   {len([t for t in filtered_trades if t['r_mult'] >= 5.0])}")
print(f"Trades hitting >= 8R:   {len([t for t in filtered_trades if t['r_mult'] >= 8.0])}")
print("-"*68)
print("Top 5 Sniper Runner Trades:")
for t in sorted(filtered_trades, key=lambda x: x['r_mult'], reverse=True)[:5]:
    print(f"  {t['time']} IST | {t['dir']:5s} | Entry: {t['entry']} | SL: ${t['sl']} | Max Move: +${t['max_pts']} | RR: +{t['r_mult']}R | Net: +${t['net_usd']:.2f}")
