import json
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

with open('data/processed/lab_candles_15m.json', 'r') as f:
    candles = json.load(f)

# Find all sustained moves >= $20 initiated in the 05:00 - 09:30 IST window
# Measure move over 16-32 candles (4 to 8 hours)
big_moves = []
i = 0
while i < len(candles) - 32:
    c = candles[i]
    dt_ist = datetime.fromtimestamp(c['time'], tz=IST)
    
    # Check if in 05:00 - 09:30 IST
    minute_of_day = dt_ist.hour * 60 + dt_ist.minute
    if not (5 * 60 <= minute_of_day <= 9 * 60 + 30):
        i += 1
        continue
        
    # Exclude news spike candle itself
    if (c['high'] - c['low']) >= 20.0:
        i += 1
        continue
        
    start_price = c['open']
    
    # Next 24 candles (6 hours)
    future = candles[i:i+25]
    if any((fc['high'] - fc['low']) >= 25.0 for fc in future):
        i += 1
        continue
        
    highest = max(fc['high'] for fc in future)
    lowest = min(fc['low'] for fc in future)
    
    up_dist = highest - start_price
    down_dist = start_price - lowest
    
    # Check prior 12 candles trend
    prior = candles[max(0, i-12):i]
    prior_high = max(p['high'] for p in prior) if prior else start_price
    prior_low = min(p['low'] for p in prior) if prior else start_price
    
    # Reversal vs Breakout classification:
    # If up_dist >= 20: did it start from sweeping prior low (Reversal) or breaking prior high (Breakout)?
    if up_dist >= 20.0 and down_dist < 10.0:
        is_reversal = (c['low'] <= prior_low + 1.0)
        is_breakout = (c['high'] >= prior_high - 1.0)
        big_moves.append({
            'time': dt_ist.strftime('%Y-%m-%d %H:%M'),
            'type': 'BULLISH',
            'move': round(up_dist, 2),
            'max_pullback': round(down_dist, 2),
            'category': 'SWEEP_REVERSAL' if is_reversal else ('BREAKOUT' if is_breakout else 'TREND_CONTINUATION')
        })
        i += 16 # skip ahead so we don't double count the same move
        continue
        
    if down_dist >= 20.0 and up_dist < 10.0:
        is_reversal = (c['high'] >= prior_high - 1.0)
        is_breakout = (c['low'] <= prior_low + 1.0)
        big_moves.append({
            'time': dt_ist.strftime('%Y-%m-%d %H:%M'),
            'type': 'BEARISH',
            'move': round(down_dist, 2),
            'max_pullback': round(up_dist, 2),
            'category': 'SWEEP_REVERSAL' if is_reversal else ('BREAKOUT' if is_breakout else 'TREND_CONTINUATION')
        })
        i += 16
        continue
        
    i += 1

print(f"Total clean $20+ moves initiated between 05:00 and 09:30 IST: {len(big_moves)}")
cats = {}
for m in big_moves:
    cats[m['category']] = cats.get(m['category'], 0) + 1
print("Categories of $20+ moves:", cats)

pullbacks = [m['max_pullback'] for m in big_moves]
print(f"Average initial adverse pullback before reaching $20+: ${sum(pullbacks)/len(pullbacks):.2f}")
print(f"Moves with initial pullback <= $3.00: {len([p for p in pullbacks if p <= 3.0])} / {len(pullbacks)}")
print(f"Moves with initial pullback <= $5.00: {len([p for p in pullbacks if p <= 5.0])} / {len(pullbacks)}")
print(f"Moves with initial pullback <= $8.00: {len([p for p in pullbacks if p <= 8.0])} / {len(pullbacks)}")

print("\nSample 10 Big Movements:")
for m in big_moves[:10]:
    print(f"{m['time']} IST | {m['type']} | Move: ${m['move']} | Pullback: ${m['max_pullback']} | {m['category']}")
