import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest_runner import load_config, CONFIG_PATH, load_dataset, STRATEGY_PROFILES, simulate_profile
from src.agents.syndicate_agents import precompute_features

cfg = load_config(CONFIG_PATH)
raw_df = load_dataset()
df = precompute_features(raw_df, cfg)

# Test with modified profile
prof = STRATEGY_PROFILES[0].copy()
prof["be_trigger_r"] = 1.05
prof["be_lock_r"] = 0.30

# Let's run and see
t_df = simulate_profile(df, cfg, prof)
wins = t_df[t_df["net_pnl_usd"] > 0]
n = len(t_df)
wr = len(wins) / n * 100
pnl = t_df["net_pnl_usd"].sum()
print(f"Results: {n} trades | Win Rate: {wr:.2f}% | Net PnL: ${pnl:.2f}")
