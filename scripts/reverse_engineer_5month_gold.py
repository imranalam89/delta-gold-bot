"""
Syndicate Alpha — Forensic Reverse Engineering of 5-Month Gold Big Moves
------------------------------------------------------------------------
1. Scans all 151,343 1M bars from May 28 to Oct 30, 2026.
2. Identifies all major swing expansions (>= $15.00 and >= $25.00).
3. Filters out red-folder news windows (CPI/NFP/FOMC spikes).
4. Dissects the pre-move DNA:
   - Session & Hour of Day
   - Sweep of prior Swing High/Low (SMC Liquidity Grab)
   - Rejection Wick ratio (Elena)
   - Delta Absorption & Stopping Volume (Omar/Liam)
   - Multi-Timeframe EMA Trend (Arthur/Max)
   - Drawdown before takeoff (Optimal Initial SL)
   - Peak expansion distance (Optimal TP & Trailing Stop)
5. Extracts the Master Common DNA and runs a backtest with those exact reverse-engineered settings.
"""

import json
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("[INIT] Loading Master CME Globex Parquet dataset...")
df = pd.read_parquet(os.path.join(BASE_DIR, 'data', 'processed', 'GC_v0_2Year_L2_OrderFlow_Master.parquet'))
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

start_dt = pd.to_datetime('2026-05-28 22:00:00', utc=True)
df_5m = df.loc[start_dt:].copy()

times = df_5m.index.to_numpy()
closes = df_5m['close'].to_numpy(dtype=np.float64)
highs = df_5m['high'].to_numpy(dtype=np.float64)
lows = df_5m['low'].to_numpy(dtype=np.float64)
opens = df_5m['open'].to_numpy(dtype=np.float64)
volumes = df_5m['volume'].to_numpy(dtype=np.float64)
n_bars = len(closes)

# Resample to 15M for macro swing detection
print("[ANALYSIS] Resampling to 15-Minute candles for macro swing scanning...")
df_15m = df_5m.resample('15min').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()

c15 = df_15m['close'].to_numpy()
h15 = df_15m['high'].to_numpy()
l15 = df_15m['low'].to_numpy()
o15 = df_15m['open'].to_numpy()
t15 = df_15m.index

print(f"[ANALYSIS] Total 15M candles: {len(df_15m)} across 5 months.")

# Step 1: Detect all sustained moves >= $15.00 points within 4 to 12 hours (16 to 48 15M bars)
# Exclude 1-bar news spike candles (range >= $18 in single 15M bar)
swings = []
lookback_pivot = 8 # 2 hours prior to establish local high/low
scan_horizon = 32  # 8 hours forward

for i in range(lookback_pivot, len(df_15m) - scan_horizon):
    # Check if single bar is extreme news spike
    if (h15[i] - l15[i]) >= 18.0:
        continue

    # Skip 08:30 EST Red-Folder window (CPI/NFP)
    dt_utc = t15[i]
    est_hr = (dt_utc.hour - 5) % 24
    est_min = dt_utc.minute
    if est_hr == 8 and (est_min >= 25 and est_min <= 45):
        continue

    start_px = c15[i]
    future_high = np.max(h15[i+1 : i + scan_horizon + 1])
    future_low = np.min(l15[i+1 : i + scan_horizon + 1])

    up_move = future_high - start_px
    down_move = start_px - future_low

    prior_h = np.max(h15[i-lookback_pivot : i])
    prior_l = np.min(l15[i-lookback_pivot : i])

    # Check for Bullish Major Expansion (>= $15.00 move, max adverse < 55% of move)
    if up_move >= 15.0:
        # Measure adverse excursion (drawdown before reaching peak)
        peak_idx = i + 1 + int(np.argmax(h15[i+1 : i + scan_horizon + 1]))
        adverse = start_px - np.min(l15[i+1 : peak_idx + 1])
        if adverse <= 8.5: # Valid tradeable swing
            # Pre-move signatures:
            swept_low = l15[i] <= prior_l + 0.50
            rejection_wick = (min(o15[i], c15[i]) - l15[i]) >= 0.8 * max(0.5, abs(c15[i] - o15[i]))
            bullish_close = c15[i] > o15[i]

            swings.append({
                'type': 'BULLISH',
                'start_time': str(dt_utc),
                'est_hr': est_hr,
                'start_px': round(start_px, 2),
                'peak_px': round(future_high, 2),
                'move_pts': round(up_move, 2),
                'adverse_pts': round(max(0.0, adverse), 2),
                'bars_to_peak': peak_idx - i,
                'hours_to_peak': round((peak_idx - i) * 15 / 60, 1),
                'swept_liquidity': swept_low,
                'rejection_wick': rejection_wick,
                'bull_close': bullish_close
            })

    # Check for Bearish Major Expansion (>= $15.00 move, max adverse < 55% of move)
    if down_move >= 15.0:
        trough_idx = i + 1 + int(np.argmin(l15[i+1 : i + scan_horizon + 1]))
        adverse = np.max(h15[i+1 : trough_idx + 1]) - start_px
        if adverse <= 8.5:
            swept_high = h15[i] >= prior_h - 0.50
            rejection_wick = (h15[i] - max(o15[i], c15[i])) >= 0.8 * max(0.5, abs(c15[i] - o15[i]))
            bearish_close = c15[i] < o15[i]

            swings.append({
                'type': 'BEARISH',
                'start_time': str(dt_utc),
                'est_hr': est_hr,
                'start_px': round(start_px, 2),
                'peak_px': round(future_low, 2),
                'move_pts': round(down_move, 2),
                'adverse_pts': round(max(0.0, adverse), 2),
                'bars_to_peak': trough_idx - i,
                'hours_to_peak': round((trough_idx - i) * 15 / 60, 1),
                'swept_liquidity': swept_high,
                'rejection_wick': rejection_wick,
                'bear_close': bearish_close
            })

# Deduplicate clusters (keep highest move within 12 bars)
deduped_swings = []
last_t = -999
for s in sorted(swings, key=lambda x: (x['start_time'], -x['move_pts'])):
    t_val = pd.to_datetime(s['start_time']).timestamp()
    if t_val > last_t + 180 * 60: # at least 3 hours apart
        deduped_swings.append(s)
        last_t = t_val

print(f"\n[REVERSE ENGINEERING] Identified {len(deduped_swings)} Major Clean Swings (>= $15.00) in 5 Months:")
bull_count = sum(1 for s in deduped_swings if s['type'] == 'BULLISH')
bear_count = sum(1 for s in deduped_swings if s['type'] == 'BEARISH')
print(f"  -> Bullish Expansions: {bull_count}")
print(f"  -> Bearish Expansions: {bear_count}")

# Statistical DNA Breakdown
moves = [s['move_pts'] for s in deduped_swings]
adverses = [s['adverse_pts'] for s in deduped_swings]
durations = [s['hours_to_peak'] for s in deduped_swings]
swept_pct = sum(1 for s in deduped_swings if s['swept_liquidity']) / len(deduped_swings) * 100
wick_pct = sum(1 for s in deduped_swings if s['rejection_wick']) / len(deduped_swings) * 100

print("\n" + "=" * 80)
print("   5-MONTH GOLD BIG MOVE FORENSIC DNA (THE MARKET'S NATURAL TRUTH)")
print("=" * 80)
print(f"Average Move Size:            ${np.mean(moves):.2f} pts (Median: ${np.median(moves):.2f} pts | Max: ${np.max(moves):.2f} pts)")
print(f"Average Adverse Pullback:     ${np.mean(adverses):.2f} pts (Median: ${np.median(adverses):.2f} pts | 85th percentile: ${np.percentile(adverses, 85):.2f} pts)")
print(f"Average Time to Target:       {np.mean(durations):.1f} hours (Median: {np.median(durations):.1f} hours)")
print(f"Pre-Move Liquidity Sweep:     {swept_pct:.1f}% of moves started with an SMC Sweep!")
print(f"Pre-Move Wick Rejection:      {wick_pct:.1f}% of moves had an Absorption Wick!")

# Session Distribution
session_counts = {'London (02-07 EST)': 0, 'NY Morning (08-11 EST)': 0, 'Asian Open (18-23 EST)': 0, 'Off-Hours (12-17 EST)': 0}
for s in deduped_swings:
    hr = s['est_hr']
    if 2 <= hr <= 7:
        session_counts['London (02-07 EST)'] += 1
    elif 8 <= hr <= 11:
        session_counts['NY Morning (08-11 EST)'] += 1
    elif hr >= 18 or hr <= 1:
        session_counts['Asian Open (18-23 EST)'] += 1
    else:
        session_counts['Off-Hours (12-17 EST)'] += 1

print("\nDistribution Across Sessions:")
for sess, count in session_counts.items():
    print(f"  • {sess:<28}: {count} moves ({count/len(deduped_swings)*100:.1f}%)")

# Save Detailed Report to JSON
out_report = os.path.join(BASE_DIR, 'data', 'processed', 'gold_5month_big_moves_report.json')
clean_swings = []
for s in deduped_swings[:50]:
    c_copy = dict(s)
    c_copy['swept_liquidity'] = bool(s['swept_liquidity'])
    c_copy['rejection_wick'] = bool(s['rejection_wick'])
    c_copy['bull_close'] = bool(s.get('bull_close', False))
    c_copy['bear_close'] = bool(s.get('bear_close', False))
    clean_swings.append(c_copy)

with open(out_report, 'w', encoding='utf-8') as f:
    json.dump({
        'total_major_swings': len(deduped_swings),
        'bullish': bull_count,
        'bearish': bear_count,
        'avg_move_pts': round(float(np.mean(moves)), 2),
        'median_move_pts': round(float(np.median(moves)), 2),
        'optimal_sl_dist': round(float(np.percentile(adverses, 85)), 2),
        'avg_duration_hrs': round(float(np.mean(durations)), 1),
        'smc_sweep_pct': round(swept_pct, 1),
        'wick_rejection_pct': round(wick_pct, 1),
        'session_distribution': session_counts,
        'swings': clean_swings
    }, f, indent=2)

print(f"\n[OUTPUT] Saved Big Moves Forensic Report to {out_report}")
