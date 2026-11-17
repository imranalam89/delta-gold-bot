"""
Syndicate Alpha — Local & Cloud MBP-10 Preprocessor
---------------------------------------------------
Reads raw Databento `.dbn.zst` (MBP-10 Level 2 order book depth & 1M OHLCV) files
directly from `data/raw/` on your PC (or Google Drive) in memory-safe 250,000-tick
chunks and distills them into a compact 1-Minute Enriched Institutional Parquet dataset:
  - Standard OHLCV (Open, High, Low, Close, Volume)
  - SAM (Level 2 DOM): 10-Level Bid/Ask Imbalance Ratio, Max Bid/Ask Walls, Spread
  - OMAR (Order Flow): Bar Delta (Market Buy Vol - Market Sell Vol) & CVD
  - JACK (VSA): Volume Z-Score & Stopping Volume Wick Absorption flags
"""

import glob
import os
import databento as db
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
LOCAL_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def process_single_mbp10_file(dbn_path: str) -> pd.DataFrame:
    """Streams one .dbn.zst MBP-10 file in 250k-tick chunks into 1-minute institutional bars."""
    print(f"Processing Level-2 book depth & tape: {os.path.basename(dbn_path)} ...")
    store = db.DBNStore.from_file(dbn_path)
    chunk_bars = []

    for df in store.to_df(count=250_000):
        if df.empty:
            continue

        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)

        # 1. Sum 10 levels of Bid Depth and Ask Depth (SAM's MBP-10 DOM metric)
        bid_sz_cols = [f"bid_sz_0{i}" for i in range(10) if f"bid_sz_0{i}" in df.columns]
        ask_sz_cols = [f"ask_sz_0{i}" for i in range(10) if f"ask_sz_0{i}" in df.columns]

        df["bid_depth_10"] = df[bid_sz_cols].sum(axis=1)
        df["ask_depth_10"] = df[ask_sz_cols].sum(axis=1)
        df["l2_ratio"] = (df["bid_depth_10"] + 1.0) / (df["ask_depth_10"] + 1.0)
        df["spread_pts"] = (df["ask_px_00"] - df["bid_px_00"]).clip(lower=0)

        # 2. Separate trade executions (action == 'T') for OHLCV & OMAR's Delta
        trades = df[df["action"] == "T"].copy() if "action" in df.columns else df.copy()
        if trades.empty:
            continue

        signed_sz = trades["size"].astype(np.int64)
        trades["delta"] = np.where(
            trades["side"] == "B",
            signed_sz,
            np.where(trades["side"] == "A", -signed_sz, 0),
        )

        # 3. Resample chunk to 1-Minute Bars with L2 & Order Flow features
        b1m = trades["price"].resample("1min").ohlc()
        b1m["volume"] = trades["size"].resample("1min").sum()
        b1m["bar_delta"] = trades["delta"].resample("1min").sum()
        b1m["l2_bid_ask_ratio_mean"] = df["l2_ratio"].resample("1min").mean()
        b1m["l2_bid_ask_ratio_max"] = df["l2_ratio"].resample("1min").max()
        b1m["max_bid_wall_10"] = df["bid_depth_10"].resample("1min").max()
        b1m["max_ask_wall_10"] = df["ask_depth_10"].resample("1min").max()
        b1m["avg_spread_pts"] = df["spread_pts"].resample("1min").mean()

        chunk_bars.append(b1m.dropna(subset=["close"]))

    if not chunk_bars:
        return pd.DataFrame()

    wk_df = pd.concat(chunk_bars).sort_index()
    wk_df = wk_df[~wk_df.index.duplicated(keep="last")]
    return wk_df


def build_master_parquet():
    os.makedirs(LOCAL_RAW_DIR, exist_ok=True)
    os.makedirs(LOCAL_PROCESSED_DIR, exist_ok=True)

    # 1. Check for any 1M OHLCV files in data/raw
    ohlcv_files = sorted(glob.glob(os.path.join(LOCAL_RAW_DIR, "**/*ohlcv*.dbn.zst"), recursive=True))
    master_ohlcv = pd.DataFrame()
    if ohlcv_files:
        print(f"Loading 2-Year OHLCV from: {os.path.basename(ohlcv_files[0])}")
        store_ohlcv = db.DBNStore.from_file(ohlcv_files[0])
        df_ohlcv = store_ohlcv.to_df()
        if not isinstance(df_ohlcv.index, pd.DatetimeIndex):
            df_ohlcv.index = pd.to_datetime(df_ohlcv.index, utc=True)
        master_ohlcv = df_ohlcv.loc["2024-11-01":"2026-11-01"][["open", "high", "low", "close", "volume"]]
        print(f"Loaded {len(master_ohlcv):,} 1M OHLCV bars.")

    # 2. Check for MBP-10 files in data/raw
    mbp_files = sorted(glob.glob(os.path.join(LOCAL_RAW_DIR, "**/*mbp-10*.dbn.zst"), recursive=True))
    if not mbp_files:
        print(f"No *mbp-10*.dbn.zst files found in {LOCAL_RAW_DIR}")
        return

    all_chunks = []
    for f in mbp_files:
        chunk_df = process_single_mbp10_file(f)
        if not chunk_df.empty:
            all_chunks.append(chunk_df)

    master_l2 = pd.concat(all_chunks).sort_index()
    master_l2 = master_l2[~master_l2.index.duplicated(keep="last")]
    master_l2["cvd"] = master_l2["bar_delta"].cumsum()

    final_df = master_ohlcv.combine_first(master_l2) if not master_ohlcv.empty else master_l2
    vol_mean = final_df["volume"].rolling(60, min_periods=10).mean()
    vol_std = final_df["volume"].rolling(60, min_periods=10).std().replace(0, 1)
    final_df["vol_z_score"] = (final_df["volume"] - vol_mean) / vol_std

    out_file = os.path.join(LOCAL_PROCESSED_DIR, "GC_v0_2Year_L2_OrderFlow_Master.parquet")
    final_df.to_parquet(out_file, compression="zstd")
    print(f"\n[DONE] Saved Master L2 + OrderFlow dataset to:\n  -> {out_file}")
    print(f"Total 1M bars: {len(final_df):,}")


if __name__ == "__main__":
    build_master_parquet()
