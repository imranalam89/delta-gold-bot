import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone

parquet_path = os.path.join("data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
print("Loading 2-Year Parquet dataset...")
df = pd.read_parquet(parquet_path)
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

print(f"Total 1m bars: {len(df)}")
print(f"Date range: {df.index.min()} to {df.index.max()}")

times = df.index.to_numpy()
opens = df['open'].to_numpy(dtype=np.float32)
highs = df['high'].to_numpy(dtype=np.float32)
lows  = df['low'].to_numpy(dtype=np.float32)
closes= df['close'].to_numpy(dtype=np.float32)
volumes = df['volume'].to_numpy(dtype=np.float32)
n = len(closes)

print(f"Extracted {n} bars successfully.")
