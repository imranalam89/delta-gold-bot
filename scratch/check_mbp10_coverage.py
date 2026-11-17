import os
import pandas as pd
import numpy as np

parquet_path = os.path.join("data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
print(f"Reading {parquet_path}...")
df = pd.read_parquet(parquet_path)

print(f"Total rows: {len(df)}")
print(f"Index range: {df.index.min()} to {df.index.max()}")
print("\nColumns and null counts:")
print(df.isnull().sum())

print("\nChecking non-zero / non-default values across time:")
# Split into early period (Nov 2024 - May 2026) vs late period (Jun 2026 - Oct 2026)
early_mask = df.index < '2026-05-28'
late_mask = df.index >= '2026-05-28'

print(f"Early period rows (< May 2026): {early_mask.sum()}")
print(f"Late period rows (>= May 2026):  {late_mask.sum()}")

print("\n--- EARLY PERIOD (Nov 2024 to May 2026) ---")
for col in ['bar_delta', 'cvd', 'l2_bid_ask_ratio_mean', 'max_bid_wall_10', 'avg_spread_pts']:
    if col in df.columns:
        s = df.loc[early_mask, col]
        print(f"  {col:22} -> non-zero: {(s != 0).sum()} / {len(s)} ({(s != 0).mean()*100:.1f}%), min={s.min():.2f}, mean={s.mean():.2f}, max={s.max():.2f}")

print("\n--- LATE PERIOD (May 2026 to Oct 2026) ---")
for col in ['bar_delta', 'cvd', 'l2_bid_ask_ratio_mean', 'max_bid_wall_10', 'avg_spread_pts']:
    if col in df.columns:
        s = df.loc[late_mask, col]
        print(f"  {col:22} -> non-zero: {(s != 0).sum()} / {len(s)} ({(s != 0).mean()*100:.1f}%), min={s.min():.2f}, mean={s.mean():.2f}, max={s.max():.2f}")
