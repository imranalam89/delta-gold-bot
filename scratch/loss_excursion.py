import json
import numpy as np
import pandas as pd

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
df = pd.DataFrame(trades)
df['is_win'] = df['net_pnl_usd'] > 0

losses = df[~df['is_win']]
wins = df[df['is_win']]

print("=== LOSSES (99 TRADES) EXCURSION STATS ===")
print("peak_r in losses:")
print(losses['peak_r'].describe())

print("\nLosses peak_r distribution:")
print(f"peak_r < 0.2R (Instant adverse plunge): {len(losses[losses['peak_r'] < 0.2])} ({len(losses[losses['peak_r'] < 0.2])/len(losses)*100:.1f}%)")
print(f"0.2R <= peak_r < 0.5R (Minor poke, then die): {len(losses[(losses['peak_r'] >= 0.2) & (losses['peak_r'] < 0.5)])} ({len(losses[(losses['peak_r'] >= 0.2) & (losses['peak_r'] < 0.5)])/len(losses)*100:.1f}%)")
print(f"0.5R <= peak_r < 1.0R (Substantial move, but reversed): {len(losses[(losses['peak_r'] >= 0.5) & (losses['peak_r'] < 1.0)])} ({len(losses[(losses['peak_r'] >= 0.5) & (losses['peak_r'] < 1.0)])/len(losses)*100:.1f}%)")
print(f"peak_r >= 1.0R (Reached +1R or more!): {len(losses[losses['peak_r'] >= 1.0])} ({len(losses[losses['peak_r'] >= 1.0])/len(losses)*100:.1f}%)")

print("\n=== WINS (166 TRADES) EXCURSION STATS ===")
print("peak_r in wins:")
print(wins['peak_r'].describe())

print("\n=== HOLD MINS STATS ===")
print("Wins hold_mins median:", wins['hold_mins'].median(), "mean:", wins['hold_mins'].mean())
print("Losses hold_mins median:", losses['hold_mins'].median(), "mean:", losses['hold_mins'].mean())

print("\n=== EXIT REASONS IN LOSSES ===")
print(losses['exit_reason'].value_counts())

print("\n=== EXIT REASONS IN WINS ===")
print(wins['exit_reason'].value_counts())
