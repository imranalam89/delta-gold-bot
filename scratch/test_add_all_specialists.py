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
print("Dataset ready, testing adding Alex, Maya, Liam triggers...")
