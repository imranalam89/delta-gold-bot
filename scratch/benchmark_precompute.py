import os
import sys
import time
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath('.'))
sys.path.insert(0, '.')

from backtest_runner import load_config, CONFIG_PATH
from src.agents.syndicate_agents import precompute_features

parquet_path = os.path.join("data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
print(f"Loading {parquet_path}...")
df_raw = pd.read_parquet(parquet_path)
cfg = load_config(CONFIG_PATH)

t0 = time.time()
print("Starting precompute_features on 699,702 bars...")
df_feats = precompute_features(df_raw, cfg)
t1 = time.time()
print(f"precompute_features finished in {t1 - t0:.2f} seconds!")
print(f"Features shape: {df_feats.shape}")
