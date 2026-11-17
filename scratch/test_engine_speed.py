import json
import time
import pandas as pd
import numpy as np

# Load Parquet
print("[INIT] Loading Parquet dataset...")
t0 = time.time()
df = pd.read_parquet('data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet')
if not df.index.tz:
    df.index = df.index.tz_localize('UTC')
else:
    df.index = df.index.tz_convert('UTC')

start_dt = pd.to_datetime('2026-05-28 22:00:00', utc=True)
df_5m = df.loc[start_dt:].copy()

times = df_5m.index.to_numpy()
closes = df_5m['close'].to_numpy(dtype=np.float64)
highs = df_5m['high'].to_numpy(dtype=np.float64)
lows = df_5m['low'].to_numpy(dtype=np.float64)
opens = df_5m['open'].to_numpy(dtype=np.float64)
atrs = df_5m['atr_14'].to_numpy(dtype=np.float64) if 'atr_14' in df_5m.columns else np.full(len(closes), 4.5)
est_hours = ((df_5m.index.hour - 5) % 24).to_numpy(dtype=np.int32)
n_bars = len(closes)

time_to_idx = {ts: idx for idx, ts in enumerate(times)}

# Load bundle candidate signals
with open('data/processed/all_11_agents_lab_bundle.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

signals = []
for ag, data in bundle.items():
    tf_data = data.get('timeframes', {})
    for tf_label in ['1m', '5m', '15m', '1h']:
        trades = tf_data.get(tf_label, {}).get('trades', [])
        for t in trades:
            dt_ts = pd.to_datetime(t['entry_time'], utc=True)
            if dt_ts in time_to_idx:
                idx = time_to_idx[dt_ts]
                signals.append({
                    'idx': idx,
                    'ts': int(t['entry_ts']),
                    'agent': ag,
                    'direction': t['direction'],
                    'tf': tf_label,
                    'tf_rank': {'1h': 4, '15m': 3, '5m': 2, '1m': 1}[tf_label],
                    'orig_sl_dist': float(t['sl_dist'])
                })

signals.sort(key=lambda x: (x['ts'], -x['tf_rank']))
print(f"[INIT] Loaded {len(signals)} valid signals. Setup time: {time.time()-t0:.2f}s")
