import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path: sys.path.insert(0, BASE_DIR)
import pandas as pd
import numpy as np
from scripts.exit_rule_lab import load, stats, run

sets = {
    '46d (Oct1-Nov15)': load('data/processed/trades_DELTA_GOLD_MERGED_SUPER_CHAMPIONS.csv', 'data/processed/xautusd_delta_oct1_to_now_1m.parquet'),
    '1-YEAR (Oct2025-Nov2026)': load('data/processed/trades_DELTA_GOLD_1YEAR_MERGED_SUPER_CHAMPIONS.csv', 'data/processed/xautusd_delta_1year_1m.parquet')
}

p_base = dict(max_hold=180, stall=(0.54, 6, 0.33), be=(1.05, 0.45), trail=('r', 2.10, 0.85))
p_notime = dict(max_hold=100000, stall=(0.54, 6, 0.33), be=(1.05, 0.45), trail=('r', 2.10, 0.85))

for name, (ents, O, H, Lo, C) in sets.items():
    print(f"\n==========================================")
    print(f"       DATASET: {name}")
    print(f"==========================================")
    r_base = run(ents, O, H, Lo, C, p_base)
    s_base = stats(r_base)
    r_notime = run(ents, O, H, Lo, C, p_notime)
    s_notime = stats(r_notime)
    
    print(f"WITH Time Exit (180m):    Trades: {s_base['n']:4d} | WR: {s_base['wr']:5.1f}% | Net: ${s_base['net']:8.2f} | PF: {s_base['pf']:4.2f} | Max DD: -{s_base['dd']:4.1f}%")
    print(f"WITHOUT Time Exit (Inf):  Trades: {s_notime['n']:4d} | WR: {s_notime['wr']:5.1f}% | Net: ${s_notime['net']:8.2f} | PF: {s_notime['pf']:4.2f} | Max DD: -{s_notime['dd']:4.1f}%")
    print(f"Net Difference:           ${s_notime['net'] - s_base['net']:8.2f}")
    print(f"Trades Blocked/Lost:      {s_base['n'] - s_notime['n']} trades missed due to holding positions open longer")
