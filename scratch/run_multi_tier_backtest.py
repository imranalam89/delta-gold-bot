import json
import math
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

print("[BACKTEST] Loading 15m institutional candles...")
with open('data/processed/lab_candles_15m.json', 'r') as f:
    raw_candles = json.load(f)

print(f"[BACKTEST] Loaded {len(raw_candles)} candles. Computing indicators...")

# Precompute technical indicators
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

# Compute 14-period ATR and 50/200 EMAs
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

for i in range(len(candles)):
    candles[i]['atr'] = atr_14[i]
    candles[i]['ema_50'] = ema_50[i]
    candles[i]['ema_200'] = ema_200[i]
    # Trend regime
    candles[i]['bull_regime'] = ema_50[i] > ema_200[i] and candles[i]['close'] > ema_50[i]
    candles[i]['bear_regime'] = ema_50[i] < ema_200[i] and candles[i]['close'] < ema_50[i]


# -------------------------------------------------------------
# SIMULATOR FUNCTION
# -------------------------------------------------------------
def run_simulation(strategy_name, params):
    trades = []
    active_trade = None
    account_equity = 100.0  # Starting $100
    risk_usd_per_trade = 5.0 # Fixed $5 risk per trade
    fee_rate = 0.0001        # 0.01% Delta Exchange fee per leg
    lookback = 12

    for i in range(lookback, len(candles)):
        c = candles[i]
        prev = candles[i-1]
        
        # 1. Manage Active Trade
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
            tier = t['tier']

            exit_price = None
            exit_reason = None

            # Skip single-candle news spikes > $22 from affecting clean fills
            if c['range'] >= 25.0:
                continue

            if direction == 'LONG':
                mfe = high - entry
                # Check Stop Loss
                if low <= sl:
                    exit_price = sl
                    exit_reason = "STOP_LOSS"
                elif t['rem_weight'] == 0:
                    exit_price = high
                    exit_reason = "ALL_TPS_HIT"
                else:
                    # Breakeven Lock
                    if params['use_be'] and mfe >= params['be_trigger_r'] * init_risk and t['stage'] == 'ARMED':
                        t['sl_price'] = max(t['sl_price'], entry + params['be_lock_r'] * init_risk)
                        t['stage'] = 'BREAKEVEN'

                    # Tier 1/2 TP1 Hit
                    if mfe >= t['tp1_dist'] and t['tp1_open']:
                        t['banked_pts'] += t['tp1_pct'] * t['tp1_dist']
                        t['rem_weight'] -= t['tp1_pct']
                        t['tp1_open'] = False
                        t['sl_price'] = max(t['sl_price'], entry + 0.5 * init_risk)
                        t['stage'] = 'TP1_BANKED'

                    # TP2 Hit
                    if mfe >= t['tp2_dist'] and t['tp2_open']:
                        t['banked_pts'] += t['tp2_pct'] * t['tp2_dist']
                        t['rem_weight'] -= t['tp2_pct']
                        t['tp2_open'] = False
                        t['sl_price'] = max(t['sl_price'], entry + 1.5 * init_risk)
                        t['stage'] = 'TP2_BANKED'

                    # Trailing Stop for Moonbag Runner
                    if t['stage'] in ('TP1_BANKED', 'TP2_BANKED') and t['rem_weight'] > 0:
                        trail_px = close - params['trail_dist_pts']
                        if trail_px > t['sl_price']:
                            t['sl_price'] = trail_px

                    # Max Hold time exit
                    if bars_held >= params['max_hold_bars'] and exit_price is None:
                        exit_price = close
                        exit_reason = "TIME_EXIT"

            else: # SHORT
                mfe = entry - low
                if high >= sl:
                    exit_price = sl
                    exit_reason = "STOP_LOSS"
                elif t['rem_weight'] == 0:
                    exit_price = low
                    exit_reason = "ALL_TPS_HIT"
                else:
                    if params['use_be'] and mfe >= params['be_trigger_r'] * init_risk and t['stage'] == 'ARMED':
                        t['sl_price'] = min(t['sl_price'], entry - params['be_lock_r'] * init_risk)
                        t['stage'] = 'BREAKEVEN'

                    if mfe >= t['tp1_dist'] and t['tp1_open']:
                        t['banked_pts'] += t['tp1_pct'] * t['tp1_dist']
                        t['rem_weight'] -= t['tp1_pct']
                        t['tp1_open'] = False
                        t['sl_price'] = min(t['sl_price'], entry - 0.5 * init_risk)
                        t['stage'] = 'TP1_BANKED'

                    if mfe >= t['tp2_dist'] and t['tp2_open']:
                        t['banked_pts'] += t['tp2_pct'] * t['tp2_dist']
                        t['rem_weight'] -= t['tp2_pct']
                        t['tp2_open'] = False
                        t['sl_price'] = min(t['sl_price'], entry - 1.5 * init_risk)
                        t['stage'] = 'TP2_BANKED'

                    if t['stage'] in ('TP1_BANKED', 'TP2_BANKED') and t['rem_weight'] > 0:
                        trail_px = close + params['trail_dist_pts']
                        if trail_px < t['sl_price']:
                            t['sl_price'] = trail_px

                    if bars_held >= params['max_hold_bars'] and exit_price is None:
                        exit_price = close
                        exit_reason = "TIME_EXIT"

            if exit_price is not None:
                rem_pts = (exit_price - entry) if direction == 'LONG' else (entry - exit_price)
                total_pts = t['banked_pts'] + t['rem_weight'] * rem_pts
                max_pts_reached = mfe
                r_mult = total_pts / max(init_risk, 0.50)
                qty_oz = risk_usd_per_trade / max(init_risk, 0.50) # position size based on $5 risk
                gross_usd = total_pts * qty_oz
                fee_usd = fee_rate * (qty_oz * entry + qty_oz * exit_price)
                net_usd = gross_usd - fee_usd
                account_equity += net_usd

                trades.append({
                    'entry_time': t['entry_time'],
                    'exit_time': c['dt_ist'].strftime('%Y-%m-%d %H:%M'),
                    'direction': direction,
                    'tier': tier,
                    'entry': entry,
                    'exit': round(exit_price, 2),
                    'total_pts': round(total_pts, 2),
                    'max_pts': round(max_pts_reached, 2),
                    'init_risk': round(init_risk, 2),
                    'r_mult': round(r_mult, 2),
                    'net_usd': round(net_usd, 2),
                    'equity': round(account_equity, 2),
                    'exit_reason': exit_reason,
                    'win': net_usd > 0
                })
                active_trade = None
                continue

        # 2. Check New Trade Signals (if not in trade)
        if active_trade is None and i < len(candles) - 1:
            # Check market conditions
            prior_window = candles[i-lookback:i]
            prior_high = max(p['high'] for p in prior_window)
            prior_low = min(p['low'] for p in prior_window)

            is_asia = (5 <= c['hour_ist'] <= 9) or (c['hour_ist'] == 9 and c['minute_ist'] <= 30)
            is_london = (12 <= c['hour_ist'] <= 16)
            is_ny = (18 <= c['hour_ist'] <= 22)
            
            allowed_session = is_london or is_ny or (params['allow_asia'] and is_asia)
            if not allowed_session:
                continue

            # Engulfing / Rejection patterns
            is_bull_engulf = (c['close'] > c['open'] and prev['close'] < prev['open'] and 
                              c['close'] >= prev['high'] and c['open'] <= prev['close'])
            is_bear_engulf = (c['close'] < c['open'] and prev['close'] > prev['open'] and 
                              c['close'] <= prev['low'] and c['open'] >= prev['close'])

            is_bull_sweep = c['low'] <= prior_low and (c['l_wick_ratio'] >= 1.8 or is_bull_engulf) and c['close'] > c['open']
            is_bear_sweep = c['high'] >= prior_high and (c['u_wick_ratio'] >= 1.8 or is_bear_engulf) and c['close'] < c['open']

            is_bull_breakout = c['close'] > prior_high and c['close'] > c['open'] and c['range'] >= 1.4 * c['atr']
            is_bear_breakout = c['close'] < prior_low and c['close'] < c['open'] and c['range'] >= 1.4 * c['atr']

            trade_signal = None

            # Check Tier 3 (Megatrend Runner)
            if params['enable_tier_3'] and (c['bull_regime'] and is_bull_breakout):
                trade_signal = ('LONG', 'TIER_3_MEGATREND', params['sl_tier_3'], params['tp1_tier_3'], params['tp2_tier_3'])
            elif params['enable_tier_3'] and (c['bear_regime'] and is_bear_breakout):
                trade_signal = ('SHORT', 'TIER_3_MEGATREND', params['sl_tier_3'], params['tp1_tier_3'], params['tp2_tier_3'])

            # Check Tier 2 (Expansion Breakout)
            elif params['enable_tier_2'] and is_bull_breakout:
                trade_signal = ('LONG', 'TIER_2_EXPANSION', params['sl_tier_2'], params['tp1_tier_2'], params['tp2_tier_2'])
            elif params['enable_tier_2'] and is_bear_breakout:
                trade_signal = ('SHORT', 'TIER_2_EXPANSION', params['sl_tier_2'], params['tp1_tier_2'], params['tp2_tier_2'])

            # Check Tier 1 (Tactical Sweep & Engulfing Reversal)
            elif is_bull_sweep:
                trade_signal = ('LONG', 'TIER_1_SNIPER', params['sl_tier_1'], params['tp1_tier_1'], params['tp2_tier_1'])
            elif is_bear_sweep:
                trade_signal = ('SHORT', 'TIER_1_SNIPER', params['sl_tier_1'], params['tp1_tier_1'], params['tp2_tier_1'])

            if trade_signal:
                direction, tier, sl_pts, tp1_pts, tp2_pts = trade_signal
                entry_px = c['close']
                init_risk = sl_pts
                sl_px = (entry_px - sl_pts) if direction == 'LONG' else (entry_px + sl_pts)
                
                active_trade = {
                    'entry_idx': i,
                    'entry_time': c['dt_ist'].strftime('%Y-%m-%d %H:%M'),
                    'direction': direction,
                    'tier': tier,
                    'entry_price': entry_px,
                    'sl_price': sl_px,
                    'init_risk': init_risk,
                    'tp1_dist': tp1_pts,
                    'tp2_dist': tp2_pts,
                    'tp1_pct': params['tp1_weight'],
                    'tp2_pct': params['tp2_weight'],
                    'tp1_open': True,
                    'tp2_open': True,
                    'banked_pts': 0.0,
                    'rem_weight': 1.0,
                    'stage': 'ARMED'
                }

    return trades

# -------------------------------------------------------------
# RUN COMPARATIVE BACKTESTS
# -------------------------------------------------------------

# Strategy A: OLD Baseline (Tight SL, premature 0.95R BE, 4h time limit, No Asia KZ)
params_baseline = {
    'allow_asia': False,
    'enable_tier_2': False,
    'enable_tier_3': False,
    'sl_tier_1': 3.80, # tight 1.15x ATR
    'tp1_tier_1': 6.00,
    'tp2_tier_1': 10.00,
    'tp1_weight': 0.50,
    'tp2_weight': 0.50,
    'use_be': True,
    'be_trigger_r': 0.95,
    'be_lock_r': 0.25,
    'trail_dist_pts': 3.5,
    'max_hold_bars': 16 # 4 hours (240 mins)
}

# Strategy B: NEW Calibrated 3-Tier Multi-Horizon Desk
params_calibrated = {
    'allow_asia': True,
    'enable_tier_2': True,
    'enable_tier_3': True,
    # Tier 1 Snipers (Elena & Leo)
    'sl_tier_1': 5.50,
    'tp1_tier_1': 10.00,
    'tp2_tier_1': 20.00,
    # Tier 2 Expansion (Marcus & Max)
    'sl_tier_2': 7.50,
    'tp1_tier_2': 15.00,
    'tp2_tier_2': 35.00,
    # Tier 3 Megatrend (Arthur & Ryan Moonbag)
    'sl_tier_3': 10.00,
    'tp1_tier_3': 22.00,
    'tp2_tier_3': 55.00, # 30% Moonbag runner trails to $100+
    'tp1_weight': 0.35,
    'tp2_weight': 0.35,
    'use_be': True,
    'be_trigger_r': 2.20,
    'be_lock_r': 0.50,
    'trail_dist_pts': 6.5,
    'max_hold_bars': 96 # 24 hours (1440 mins)
}

trades_base = run_simulation("Baseline", params_baseline)
trades_calib = run_simulation("Calibrated_Desk", params_calibrated)

def print_metrics(name, trades):
    if not trades:
        print(f"[{name}] No trades executed.")
        return
    wins = [t for t in trades if t['win']]
    losses = [t for t in trades if not t['win']]
    wr = len(wins) / len(trades) * 100.0
    tot_net_usd = sum(t['net_usd'] for t in trades)
    gross_win = sum(t['net_usd'] for t in wins)
    gross_loss = abs(sum(t['net_usd'] for t in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    
    # Analyze move milestones achieved
    m_10_20 = len([t for t in trades if 10.0 <= t['max_pts'] < 20.0])
    m_20_50 = len([t for t in trades if 20.0 <= t['max_pts'] < 50.0])
    m_50_plus = len([t for t in trades if t['max_pts'] >= 50.0])

    print("="*65)
    print(f" PERFORMANCE REPORT: {name}")
    print("="*65)
    print(f"Total Trades:           {len(trades)}")
    print(f"Win Rate:               {wr:.2f}% ({len(wins)}W / {len(losses)}L)")
    print(f"Total Net PnL:          ${tot_net_usd:+.2f} (on $100 base account)")
    print(f"Profit Factor:          {pf:.2f}")
    print(f"Trades hitting $10-$20: {m_10_20}")
    print(f"Trades hitting $20-$50: {m_20_50}")
    print(f"Trades hitting $50+:    {m_50_plus}")
    print("-"*65)
    print("Sample Top Megatrend Trades:")
    runners = sorted(trades, key=lambda x: x['total_pts'], reverse=True)[:5]
    for r in runners:
        print(f"  {r['entry_time']} | {r['direction']} {r['tier']} | Pts: +{r['total_pts']} | Max: +{r['max_pts']} | Net: +${r['net_usd']:.2f}")

print_metrics("OLD BASELINE (Single Scalper / No Asia)", trades_base)
print_metrics("NEW CALIBRATED 3-TIER MULTI-HORIZON DESK", trades_calib)
