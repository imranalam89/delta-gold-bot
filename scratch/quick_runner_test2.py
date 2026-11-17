import os
import sys
import json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest_runner import load_config, CONFIG_PATH, load_dataset, STRATEGY_PROFILES
from src.agents.syndicate_agents import precompute_features

cfg = load_config(CONFIG_PATH)
raw_df = load_dataset()
df = precompute_features(raw_df, cfg)

# Let's inspect modifying simulate_profile with ORACLE stall-lock
# We can copy simulate_profile and add stall-lock:
from backtest_runner import simulate_profile

prof = STRATEGY_PROFILES[0].copy()
prof["be_trigger_r"] = 0.95
prof["be_lock_r"] = 0.25
prof["tp1_r"] = 1.65
prof["tp2_r"] = 3.00

t_df = simulate_profile(df, cfg, prof)
wins = t_df[t_df["net_pnl_usd"] > 0]
n = len(t_df)
wr = len(wins) / n * 100
pnl = t_df["net_pnl_usd"].sum()
print(f"Results with be_trig=0.95: {n} trades | Win Rate: {wr:.2f}% | Net PnL: ${pnl:.2f}")
