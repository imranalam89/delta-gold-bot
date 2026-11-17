import json
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

with open('data/processed/lab_candles_15m.json', 'r') as f:
    candles = json.load(f)

print(f"Loaded {len(candles)} 15m candles")

# Let's inspect all sustained moves >= $20 (measured from swing pivot to subsequent high/low within 24 candles / 6h)
# Excluding 1-candle freak spikes (news) where range > $20
events = []
lookback = 8 # 2 hours lookback to establish local pivot

for i in range(lookback, len(candles) - 24):
    c = candles[i]
    dt_ist = datetime.fromtimestamp(c['time'], tz=IST)
    minute_of_day = dt_ist.hour * 60 + dt_ist.minute
    
    # Check if single candle is an extreme news spike
    c_range = c['high'] - c['low']
    if c_range >= 20.0:
        continue

    prior_candles = candles[i-lookback:i]
    prior_high = max(p['high'] for p in prior_candles)
    prior_low = min(p['low'] for p in prior_candles)
    prev = candles[i-1]

    # Future 24 bars (6 hours)
    future = candles[i+1:i+25]
    if any(fc['high'] - fc['low'] >= 22.0 for fc in future):
        continue # skip news spike

    max_future_high = max(fc['high'] for fc in future)
    min_future_low = min(fc['low'] for fc in future)

    # 1. Bearish Reversal: swept high, closed lower
    if c['high'] >= prior_high and c['close'] < c['open']:
        is_bear_engulf = (c['close'] <= prev['low'] and c['open'] >= prev['close'])
        is_bear_reject = ((c['high'] - max(c['open'], c['close'])) >= 1.2 * abs(c['close'] - c['open']))
        move = c['close'] - min_future_low
        adverse = max(fc['high'] for fc in future) - c['close']
        sl = c['high'] + 1.5 - c['close']
        
        events.append({
            'time_ist': dt_ist.strftime('%Y-%m-%d %H:%M'),
            'hour': dt_ist.hour,
            'direction': 'SHORT',
            'pattern': 'ENGULF' if is_bear_engulf else ('REJECT' if is_bear_reject else 'RED_BAR'),
            'risk_sl': round(sl, 2),
            'mfe': round(move, 2),
            'stopped': adverse > sl,
            'hit_20': move >= 20.0 and adverse <= sl
        })

    # 2. Bullish Reversal: swept low, closed higher
    if c['low'] <= prior_low and c['close'] > c['open']:
        is_bull_engulf = (c['close'] >= prev['high'] and c['open'] <= prev['close'])
        is_bull_reject = ((min(c['open'], c['close']) - c['low']) >= 1.2 * abs(c['close'] - c['open']))
        move = max_future_high - c['close']
        adverse = c['close'] - min(fc['low'] for fc in future)
        sl = c['close'] - (c['low'] - 1.5)
        
        events.append({
            'time_ist': dt_ist.strftime('%Y-%m-%d %H:%M'),
            'hour': dt_ist.hour,
            'direction': 'LONG',
            'pattern': 'ENGULF' if is_bull_engulf else ('REJECT' if is_bull_reject else 'GREEN_BAR'),
            'risk_sl': round(sl, 2),
            'mfe': round(move, 2),
            'stopped': adverse > sl,
            'hit_20': move >= 20.0 and adverse <= sl
        })

print(f"Total swing reversal attempts detected: {len(events)}")

# Filter for the 05:00 - 09:30 window
morning_events = [e for e in events if 5 <= e['hour'] <= 9]
print(f"Morning IST (05:00 - 09:30) reversal attempts: {len(morning_events)}")

engulf_events = [e for e in morning_events if e['pattern'] == 'ENGULF']
print(f"Morning Engulfing patterns: {len(engulf_events)}")

engulf_hit_20 = [e for e in engulf_events if e['hit_20']]
print(f"Morning Engulfing that captured >= $20 without hitting SL: {len(engulf_hit_20)}")

# Distribution of MFE (Maximum Favorable Excursion) for Engulfing
mfe_values = [e['mfe'] for e in engulf_events]
if mfe_values:
    print(f"Avg MFE for morning engulfing: {sum(mfe_values)/len(mfe_values):.2f}")
    print(f"Trades with MFE >= $10: {len([m for m in mfe_values if m >= 10])} / {len(mfe_values)}")
    print(f"Trades with MFE >= $15: {len([m for m in mfe_values if m >= 15])} / {len(mfe_values)}")
    print(f"Trades with MFE >= $20: {len([m for m in mfe_values if m >= 20])} / {len(mfe_values)}")

# Check what percentage got stopped out with standard SL vs trailed SL
stopped = [e for e in engulf_events if e['stopped']]
print(f"Stopped out with structural SL (wick + 1.5): {len(stopped)} ({len(stopped)/len(engulf_events)*100:.1f}%)")

# Show examples of successful $20+ morning runners
print("\n--- Top Examples of >= $20 Morning Runners ---")
for e in engulf_hit_20[:8]:
    print(f"Time: {e['time_ist']} IST | {e['direction']} | SL: ${e['risk_sl']} | MFE: ${e['mfe']}")
