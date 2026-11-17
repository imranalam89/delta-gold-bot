"""
Syndicate Alpha — 2-Year Comprehensive Backtest of Champion Model 2
(November 2024 to October 2026 — 699,702 1-Minute Bars)
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print("[1/3] Loading Full 2-Year Parquet Dataset (699,702 1m bars)...")
parquet_path = os.path.join(BASE_DIR, "data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
df = pd.read_parquet(parquet_path)
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

print(f"Loaded {len(df)} bars from {df.index.min()} to {df.index.max()}")
print("Dataset size in memory:", round(df.memory_usage().sum() / 1024 / 1024, 2), "MB")
