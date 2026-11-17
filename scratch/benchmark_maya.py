import os
import sys
import time
import pandas as pd

sys.path.insert(0, '.')
from backtest_runner import load_config, CONFIG_PATH
from src.agents.syndicate_agents import precompute_features
from scripts.backtest_agent_2_maya_lab import compute_maya_indicators

parquet_path = os.path.join("data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
df_raw = pd.read_parquet(parquet_path)
cfg = load_config(CONFIG_PATH)
df_feats = precompute_features(df_raw, cfg)

t0 = time.time()
print("Starting compute_maya_indicators on 699,702 bars...")
A = compute_maya_indicators(df_feats)
t1 = time.time()
print(f"compute_maya_indicators finished in {t1 - t0:.2f} seconds!")
print("Indicators generated successfully.")
