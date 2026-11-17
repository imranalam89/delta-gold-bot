import json
import pandas as pd
import numpy as np

with open('data/processed/dashboard_payload.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data['profiles']['MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL']['trades']
df = pd.DataFrame(trades)
df['is_win'] = df['net_pnl_usd'] > 0
df['is_loss'] = ~df['is_win']

# Check all numerical columns
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
num_cols = [c for c in num_cols if c not in ['id', 'entry_ts', 'exit_ts', 'entry_idx', 'exit_idx', 'pnl_pts', 'r_multiple', 'gross_pnl_usd', 'delta_fee_usd', 'net_pnl_usd', 'equity_after', 'is_win', 'is_loss', 'is_oos']]

corrs = {}
for c in num_cols:
    val = df[c].dropna()
    if len(val) == len(df) and val.std() > 0:
        corrs[c] = df[c].corr(df['is_win'])

s_corr = pd.Series(corrs).sort_values(ascending=False)
print("Correlation with IS_WIN:")
print(s_corr)

print("\n--- DETAILED FEATURE DISTRIBUTIONS: WINS vs LOSSES ---")
for feat in ['adx_15m', 'chop_15m', 'atr_15m', 'vol_z', 'l2_ratio', 'spread_pts', 'init_risk_pts', 'consensus_score', 'confirming_count', 'fib_240_pct', 'wick_ratio']:
    if feat in df.columns:
        w = df[df['is_win']][feat]
        l = df[~df['is_win']][feat]
        print(f"\nFeature: {feat}")
        print(f"  Wins:   mean={w.mean():.3f}, std={w.std():.3f}, min={w.min():.2f}, 25%={w.quantile(0.25):.2f}, 50%={w.median():.2f}, 75%={w.quantile(0.75):.2f}, max={w.max():.2f}")
        print(f"  Losses: mean={l.mean():.3f}, std={l.std():.3f}, min={l.min():.2f}, 25%={l.quantile(0.25):.2f}, 50%={l.median():.2f}, 75%={l.quantile(0.75):.2f}, max={l.max():.2f}")
