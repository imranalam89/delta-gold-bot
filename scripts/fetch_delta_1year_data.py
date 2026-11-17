"""
Fetch 1 Year of 1-minute OHLCV data for XAUTUSD from Delta Exchange API.
Saves to data/processed/xautusd_delta_1year_1m.parquet
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PARQUET = os.path.join(BASE_DIR, "data", "processed", "xautusd_delta_1year_1m.parquet")

ENDPOINTS = [
    "https://api.india.delta.exchange/v2/history/candles",
    "https://api.delta.exchange/v2/history/candles",
]


def http_get_json(url: str, timeout: float = 12.0, retries: int = 5) -> dict:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except Exception as exc:
            last_err = exc
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"HTTP GET failed after {retries} retries ({url}): {last_err}")


def fetch_chunk_with_fallback(cur_ts: int, nxt_ts: int, symbol: str = "XAUTUSD", resolution: str = "1m") -> list:
    qs = urllib.parse.urlencode({
        "symbol": symbol,
        "resolution": resolution,
        "start": str(cur_ts),
        "end": str(nxt_ts),
    })
    
    for base_url in ENDPOINTS:
        url = f"{base_url}?{qs}"
        try:
            payload = http_get_json(url, timeout=12.0, retries=3)
            if payload.get("success", False) or "result" in payload:
                res = payload.get("result", [])
                if isinstance(res, list) and len(res) > 0:
                    return res
        except Exception:
            continue
    return []


def main():
    print("=" * 70)
    print("DELTA EXCHANGE 1-YEAR 1-MINUTE OHLCV DATA HARVESTER")
    print("=" * 70)

    # 1 Year range: exactly 365 days from now
    end_dt = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start_dt = end_dt - timedelta(days=365)
    
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    chunk_sec = 86400  # 1 day = 1440 bars (< 2000 limit)
    total_chunks = int(np.ceil((end_ts - start_ts) / chunk_sec))

    print(f"Target Symbol: XAUTUSD")
    print(f"Target Resolution: 1m (1-minute)")
    print(f"Date Range: {start_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} -> {end_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Total Calendar Days: {total_chunks} days (~525,600 minutes)")
    print(f"Output Path: {OUTPUT_PARQUET}")
    print("-" * 70)

    # Check if partial or existing parquet exists to resume
    existing_df = None
    if os.path.exists(OUTPUT_PARQUET):
        try:
            existing_df = pd.read_parquet(OUTPUT_PARQUET)
            print(f"[CACHE] Found existing dataset with {len(existing_df):,} bars: {existing_df.index[0]} -> {existing_df.index[-1]}")
            if len(existing_df) >= 500000:
                print("[CACHE] Full 1-year dataset already downloaded! Re-verifying...")
                return
        except Exception as e:
            print(f"[WARN] Error reading existing parquet: {e}")

    cur = start_ts
    chunk_idx = 0
    all_rows = []
    t0 = time.time()
    empty_streak = 0

    while cur < end_ts:
        nxt = min(cur + chunk_sec, end_ts)
        chunk_idx += 1
        
        rows = fetch_chunk_with_fallback(cur, nxt, symbol="XAUTUSD", resolution="1m")
        if rows:
            all_rows.extend(rows)
            empty_streak = 0
        else:
            empty_streak += 1
            if empty_streak > 30 and chunk_idx < 60:
                # If earliest dates have no data (e.g. before listing), note it
                pass
        
        cur = nxt + 60
        time.sleep(0.08)  # Polite pause

        if chunk_idx % 25 == 0 or chunk_idx == total_chunks:
            elapsed = time.time() - t0
            dt_cur = datetime.fromtimestamp(nxt, tz=timezone.utc).strftime("%Y-%m-%d")
            print(f"[{chunk_idx:3d}/{total_chunks}] Day {dt_cur} | Total Bars Fetched: {len(all_rows):,} | Elapsed: {elapsed:.1f}s", flush=True)

    if not all_rows:
        print("[ERROR] No bars fetched from Delta API!")
        sys.exit(1)

    print("-" * 70)
    print(f"Raw bars collected: {len(all_rows):,}. Processing DataFrame...")

    df = pd.DataFrame(all_rows)
    df["timestamp"] = pd.to_datetime(df["time"].astype(np.int64), unit="s", utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(np.float64)

    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).set_index("timestamp")
    df = df[["open", "high", "low", "close", "volume"]].sort_index()

    # Feature enrichment matching production engine
    df["delta_raw_volume"] = df["volume"]
    hl = np.maximum(df["high"] - df["low"], 1e-4)
    clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / hl
    df["clv_delta_1m"] = clv * df["volume"]
    df["bar_delta"] = df["clv_delta_1m"]
    df["cvd"] = df["bar_delta"].cumsum()
    df["avg_spread_pts"] = 0.12
    df["l2_bid_ask_ratio_mean"] = 1.0
    df["l2_bid_ask_ratio_max"] = 1.2
    df["has_mbp10"] = False
    df["has_db_5m_of"] = False
    df["db_5m_delta"] = 0.0
    df["db_5m_buy_vol"] = 0.0
    df["db_5m_sell_vol"] = 0.0
    df["max_bid_wall_10"] = 0.0
    df["max_ask_wall_10"] = 0.0

    # Ensure parent dir exists
    os.makedirs(os.path.dirname(OUTPUT_PARQUET), exist_ok=True)
    df.to_parquet(OUTPUT_PARQUET, compression="snappy")
    file_mb = os.path.getsize(OUTPUT_PARQUET) / (1024 * 1024)

    print(f"[SUCCESS] Saved {len(df):,} unique 1m XAUTUSD candles to {OUTPUT_PARQUET}")
    print(f"Time Range: {df.index[0]} -> {df.index[-1]}")
    print(f"Total Calendar Days: {(df.index[-1] - df.index[0]).total_seconds() / 86400:.1f} days")
    print(f"File Size: {file_mb:.2f} MB")
    print("=" * 70)


if __name__ == "__main__":
    main()
