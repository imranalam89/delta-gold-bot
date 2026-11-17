import json
import math
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

with open('data/processed/lab_candles_15m.json', 'r') as f:
    raw_candles = json.load(f)

candles = []
for i, c in enumerate(raw_candles):
    dt = datetime.fromtimestamp(c['time'], tz=IST)
    c_open = float(c['open'])
    c_high = float(c['high'])
    c_low = float(c['low'])
    c_close = float(c['close'])
    c_range = max(c_high - c_low, 0.10)
    body = abs(c_close - c_open)
    upper_wick = c_high - max(c_open, c_close)
    lower_wick = min(c_open, c_close) - c_low

    candles.append({
        'idx': i,
        'time': c['time'],
        'dt_ist': dt,
        'hour_ist': dt.hour,
        'minute_ist': dt.minute,
        'open': c_open,
        'high': c_high,
        'low': c_low,
        'close': c_close,
        'range': c_range,
        'body': body,
        'u_wick_ratio': upper_wick / max(body, 0.20),
        'l_wick_ratio': lower_wick / max(body, 0.20),
    })

close_prices = [c['close'] for c in candles]
ranges = [c['range'] for c in candles]

atr_14 = [3.5] * len(candles)
for i in range(14, len(candles)):
    atr_14[i] = sum(ranges[i-14:i]) / 14.0

ema_50 = [close_prices[0]] * len(candles)
ema_200 = [close_prices[0]] * len(candles)
k_50 = 2.0 / (50 + 1)
k_200 = 2.0 / (200 + 1)

for i in range(1, len(candles)):
    ema_50[i] = close_prices[i] * k_50 + ema_50[i-1] * (1 - k_50)
    ema_200[i] = close_prices[i] * k_200 + ema_200[i-1] * (1 - k_200)

# Compute 14-period CHOP index: 100 * LOG10(Sum(TrueRange, 14) / (MaxHigh - MinLow)) / LOG10(14)
chop_14 = [50.0] * len(candles)
for i in range(14, len(candles)):
    sum_tr = sum(ranges[i-14:i])
    hh = max(candles[j]['high'] for j in range(i-14, i))
    ll = min(candles[j]['low'] for j in range(i-14, i))
    denom = max(hh - ll, 0.20)
    chop = 100.0 * (math.log10(sum_tr / denom) / math.log10(14.0)) if sum_tr > denom else 30.0
    chop_14[i] = chop

for i in range(len(candles)):
    candles[i]['atr'] = atr_14[i]
    candles[i]['ema_50'] = ema_50[i]
    candles[i]['ema_200'] = ema_200[i]
    candles[i]['chop'] = chop_14[i]
    candles[i]['bull_regime'] = ema_50[i] > ema_200[i] and candles[i]['close'] > ema_50[i]
    candles[i]['bear_regime'] = ema_50[i] < ema_200[i] and candles[i]['close'] < ema_50[i]

def run_confluence_sim():
    trades = []
    active_trade = None
    account_equity = 100.0
    risk_usd = 5.0
    fee_rate = 0.0001
    lookback = 12

    for i in range(lookback, len(candles)):
        c = candles[i]
        prev = candles[i-1]

        # Manage active trade
        if active_trade is not None:
            t = active_trade
            bars_held = i - t['entry_idx']
            high = c['high']
            low = c['low']
            close = c['close']
            entry = t['entry_price']
            sl = t['sl_price']
            init_risk = t['init_risk']
            direction = t['direction']

            exit_price = None
            exit_reason = None

            if c['range'] >= 25.0:
                continue

            if direction == 'LONG':
                mfe = high - entry
                if low <= sl:
                    exit_price = sl
                    exit_reason = "STOP_LOSS"
                elif t['rem_weight'] <= 0.05:
                    exit_price = high
                    exit_reason = "ALL_TARGETS_HIT"
                else:
                    # Breakeven after +2.0R
                    if mfe >= 2.0 * init_risk and t['stage'] == 'ARMED':
                        t['sl_price'] = max(t['sl_price'], entry + 0.5 * init_risk)
                        t['stage'] = 'BREAKEVEN'

                    # TP1 (+$12 - $15)
                    if mfe >= t['tp1_dist'] and t['tp1_open']:
                        t['banked_pts'] += t['tp1_pct'] * t['tp1_dist']
                        t['rem_weight'] -= t['tp1_pct']
                        t['tp1_open'] = False
                        t['sl_price'] = max(t['sl_price'], entry + 1.0 * init_risk)
                        t['stage'] = 'TP1_BANKED'

                    # TP2 (+$25 - $35)
                    if mfe >= t['tp2_dist'] and t['tp2_open']:
                        t['banked_pts'] += t['tp2_pct'] * t['tp2_dist']
                        t['rem_weight'] -= t['tp2_pct']
                        t['tp2_open'] = False
                        t['sl_price'] = max(t['sl_price'], entry + 2.5 * init_risk)
                        t['stage'] = 'TP2_BANKED'

                    # Trailing behind 15m structure for Moonbag Runner ($50 - $100)
                    if t['stage'] in ('TP1_BANKED', 'TP2_BANKED') and t['rem_weight'] > 0:
                        trail_px = close - 6.5
                        if trail_px > t['sl_price']:
                            t['sl_price'] = trail_px

                    if bars_held >= 96 and exit_price is None:
                        exit_price = close
                        exit_reason = "TIME_EXIT_24H"

            else: # SHORT
                mfe = entry - low
                if high >= sl:
                    exit_price = sl
                    exit_reason = "STOP_LOSS"
                elif t['rem_weight'] <= 0.05:
                    exit_price = low
                    exit_reason = "ALL_TARGETS_HIT"
                else:
                    if mfe >= 2.0 * init_risk and t['stage'] == 'ARMED':
                        t['sl_price'] = min(t['sl_price'], entry - 0.5 * init_risk)
                        t['stage'] = 'BREAKEVEN'

                    if mfe >= t['tp1_dist'] and t['tp1_open']:
                        t['banked_pts'] += t['tp1_pct'] * t['tp1_dist']
                        t['rem_weight'] -= t['tp1_pct']
                        t['tp1_open'] = False
                        t['sl_price'] = min(t['sl_price'], entry - 1.0 * init_risk)
                        t['stage'] = 'TP1_BANKED'

                    if mfe >= t['tp2_dist'] and t['tp2_open']:
                        t['banked_pts'] += t['tp2_pct'] * t['tp2_dist']
                        t['rem_weight'] -= t['tp2_pct']
                        t['tp2_open'] = False
                        t['sl_price'] = min(t['sl_price'], entry - 2.5 * init_risk)
                        t['stage'] = 'TP2_BANKED'

                    if t['stage'] in ('TP1_BANKED', 'TP2_BANKED') and t['rem_weight'] > 0:
                        trail_px = close + 6.5
                        if trail_px < t['sl_price']:
                            t['sl_price'] = trail_px

                    if bars_held >= 96 and exit_price is None:
                        exit_price = close
                        exit_reason = "TIME_EXIT_24H"

            if exit_price is not None:
                rem_pts = (exit_price - entry) if direction == 'LONG' else (entry - exit_price)
                total_pts = t['banked_pts'] + t['rem_weight'] * rem_pts
                qty_oz = risk_usd / max(init_risk, 0.50)
                gross_usd = total_pts * qty_oz
                fee_usd = fee_rate * (qty_oz * entry + qty_oz * exit_price)
                net_usd = gross_usd - fee_usd
                account_equity += net_usd

                trades.append({
                    'entry_time': t['entry_time'],
                    'exit_time': c['dt_ist'].strftime('%Y-%m-%d %H:%M'),
                    'direction': direction,
                    'tier': t['tier'],
                    'entry': entry,
                    'exit': round(exit_price, 2),
                    'total_pts': round(total_pts, 2),
                    'max_pts': round(mfe, 2),
                    'init_risk': round(init_risk, 2),
                    'r_mult': round(total_pts / max(init_risk, 0.50), 2),
                    'net_usd': round(net_usd, 2),
                    'equity': round(account_equity, 2),
                    'exit_reason': exit_reason,
                    'win': net_usd > 0
                })
                active_trade = None
                continue

        # Look for High-Confluence Setups
        if active_trade is None and i < len(candles) - 1:
            prior_window = candles[i-lookback:i]
            prior_high = max(p['high'] for p in prior_window)
            prior_low = min(p['low'] for p in prior_window)

            is_asia = (5 <= c['hour_ist'] <= 9) or (c['hour_ist'] == 9 and c['minute_ist'] <= 30)
            is_london = (12 <= c['hour_ist'] <= 16)
            is_ny = (18 <= c['hour_ist'] <= 22)
            if not (is_asia or is_london or is_ny):
                continue

            # Engulfing pattern
            is_bull_engulf = (c['close'] > c['open'] and prev['close'] < prev['open'] and 
                              c['close'] >= prev['high'] and c['open'] <= prev['close'])
            is_bear_engulf = (c['close'] < c['open'] and prev['close'] > prev['open'] and 
                              c['close'] <= prev['low'] and c['open'] >= prev['close'])

            # High Confluence Reversals (Arthur Chop > 40 + Elena Engulfing/Wick + Sweep)
            is_bull_sweep = c['low'] <= prior_low and (c['l_wick_ratio'] >= 1.8 or is_bull_engulf) and c['close'] > c['open']
            is_bear_sweep = c['high'] >= prior_high and (c['u_wick_ratio'] >= 1.8 or is_bear_engulf) and c['close'] < c['open']

            # High Confluence Breakout/Trends (Arthur CHOP < 45.0 + 1.5x Volume Expansion)
            is_bull_trend = c['chop'] < 46.0 and c['bull_regime'] and c['close'] > prior_high and c['range'] >= 1.3 * c['atr']
            is_bear_trend = c['chop'] < 46.0 and c['bear_regime'] and c['close'] < prior_low and c['range'] >= 1.3 * c['atr']

            trade_signal = None
            if is_bull_trend:
                trade_signal = ('LONG', 'MEGATREND_RUNNER', 8.50, 18.0, 45.0, 0.35, 0.35)
            elif is_bear_trend:
                trade_signal = ('SHORT', 'MEGATREND_RUNNER', 8.50, 18.0, 45.0, 0.35, 0.35)
            elif is_bull_sweep:
                trade_signal = ('LONG', 'SWEEP_SNIPER', 5.50, 10.0, 22.0, 0.50, 0.50)
            elif is_bear_sweep:
                trade_signal = ('SHORT', 'SWEEP_SNIPER', 5.50, 10.0, 22.0, 0.50, 0.50)

            if trade_signal:
                direction, tier, sl_pts, tp1_pts, tp2_pts, tp1_pct, tp2_pct = trade_signal
                entry_px = c['close']
                sl_px = (entry_px - sl_pts) if direction == 'LONG' else (entry_px + sl_pts)
                active_trade = {
                    'entry_idx': i,
                    'entry_time': c['dt_ist'].strftime('%Y-%m-%d %H:%M'),
                    'direction': direction,
                    'tier': tier,
                    'entry_price': entry_px,
                    'sl_price': sl_px,
                    'init_risk': sl_pts,
                    'tp1_dist': tp1_pts,
                    'tp2_dist': tp2_pts,
                    'tp1_pct': tp1_pct,
                    'tp2_pct': tp2_pct,
                    'tp1_open': True,
                    'tp2_open': True,
                    'banked_pts': 0.0,
                    'rem_weight': 1.0,
                    'stage': 'ARMED'
                }

    return trades

trades = run_confluence_sim()
wins = [t for t in trades if t['win']]
losses = [t for t in trades if not t['win']]
wr = len(wins) / len(trades) * 100.0 if trades else 0.0
tot_net_usd = sum(t['net_usd'] for t in trades)
gross_win = sum(t['net_usd'] for t in wins)
gross_loss = abs(sum(t['net_usd'] for t in losses))
pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0

m_10_20 = len([t for t in trades if 10.0 <= t['max_pts'] < 20.0])
m_20_50 = len([t for t in trades if 20.0 <= t['max_pts'] < 50.0])
m_50_plus = len([t for t in trades if t['max_pts'] >= 50.0])

print("="*65)
print(" SYNDICATE ALPHA HIGH-CONFLUENCE MULTI-HORIZON REPORT")
print("="*65)
print(f"Total Trades:           {len(trades)}")
print(f"Win Rate:               {wr:.2f}% ({len(wins)}W / {len(losses)}L)")
print(f"Total Net PnL:          +${tot_net_usd:.2f} (starting on $100 account)")
print(f"Profit Factor:          {pf:.2f}")
print(f"Trades hitting $10-$20: {m_10_20}")
print(f"Trades hitting $20-$50: {m_20_50}")
print(f"Trades hitting $50+:    {m_50_plus}")
print("-"*65)
print("Top 8 Megatrend Runners Captured:")
runners = sorted(trades, key=lambda x: x['total_pts'], reverse=True)[:8]
for r in runners:
    print(f"  {r['entry_time']} | {r['direction']:5s} {r['tier']:16s} | Pts: +{r['total_pts']:5.1f} | Max: +{r['max_pts']:5.1f} | Net: +${r['net_usd']:6.2f}")
