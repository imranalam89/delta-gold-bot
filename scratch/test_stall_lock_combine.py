import os
import json
import numpy as np
import pandas as pd
from backtest_runner import load_config, CONFIG_PATH, load_dataset, STRATEGY_PROFILES
from src.agents.syndicate_agents import precompute_features

cfg = load_config(CONFIG_PATH)
raw_df = load_dataset()
df = precompute_features(raw_df, cfg)

# Let's inspect test with ORACLE Stall Lock at +0.65R MFE
# (When MFE >= 0.65R and price retraces to +0.20R, lock SL to +0.15R)
prof = STRATEGY_PROFILES[0].copy()
prof["be_trigger_r"] = 0.95
prof["be_lock_r"] = 0.25

from backtest_runner import simulate_profile
# We can test by running a modified simulation
print("Testing with ORACLE Stall Lock...")
