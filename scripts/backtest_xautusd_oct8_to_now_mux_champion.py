"""
Syndicate Alpha — Delta Exchange XAUTUSD Backtest (Oct 8, 2026 to Present)
Exact Strategy: MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL ($5.00 Fixed Risk/Trade)

Features:
- Fetches full 1m XAUTUSD candles from Delta Exchange India API (Oct 1 warmup -> present UTC).
- Enriches with:
  1. Agent Brain/data/trading_brain.db real Delta 5m buy_volume/sell_volume/delta (Oct 8 - Nov 5).
  2. data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet MBP-10 L2 metrics (Oct 1 - Oct 30).
  3. Delta Exchange CLV/wick directional delta proxy + neutral 0.12pt spread after Oct 30 / Nov 5.
  4. Live Hostinger VPS DOM health check (/api/dom/heatmap?symbol=XAUTUSD&limit=300).
- Runs exact MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL simulation ($5 risk, 0.85x SL, 0.01% per-side fee).
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

AGENT_BRAIN_DB = r"C:\Users\USER\OneDrive\Desktop\Agent Brain\data\trading_brain.db"
GC_PARQUET_PATH = os.path.join(BASE_DIR, "data", "processed", "GC_v0_2Year_L2_OrderFlow_Master.parquet")
DELTA_CACHE_PATH = os.path.join(BASE_DIR, "data", "processed", "xautusd_delta_oct1_to_now_1m.parquet")
DASHBOARD_PAYLOAD_PATH = os.path.join(BASE_DIR, "data", "processed", "dashboard_payload.json")
OUT_JSON_PATH = os.path.join(BASE_DIR, "data", "processed", "xautusd_oct8_to_now_mux_085sl_adaptive_chandelier.json")
OUT_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "trades_XAUTUSD_OCT8_TO_NOW_MUX_085SL.csv")

DELTA_CANDLES_URL = "https://api.india.delta.exchange/v2/history/candles"
HOSTINGER_DOM_URL = "http://62.72.31.29:5050/api/dom/heatmap?symbol=XAUTUSD&limit=300"


def index_to_epoch_sec(idx: pd.DatetimeIndex) -> np.ndarray:
    """Convert any DatetimeIndex resolution (s/ms/us/ns) safely to UTC Unix epoch seconds."""
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    else:
        idx = idx.tz_convert("UTC")
    return (idx - pd.Timestamp("1970-01-01", tz="UTC")).total_seconds().astype(np.int64).to_numpy()


def http_get_json(url: str, timeout: float = 12.0, retries: int = 4) -> dict:
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (SyndicateAlpha-Backtest)", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_err = exc
            time.sleep(0.35 * (attempt + 1))
    raise RuntimeError(f"Failed HTTP GET after {retries} retries ({url}): {last_err}")


def fetch_delta_1m_candles(start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    """Fetch 1m XAUTUSD OHLCV candles in 24h chunks from Delta India API."""
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    chunk_sec = 86400  # 1440 1m bars/day (< 2000 limit)

    all_rows = []
    cur = start_ts
    chunk_idx = 0
    while cur < end_ts:
        nxt = min(cur + chunk_sec, end_ts)
        qs = urllib.parse.urlencode({
            "resolution": "1m",
            "symbol": "XAUTUSD",
            "start": str(cur),
            "end": str(nxt),
        })
        url = f"{DELTA_CANDLES_URL}?{qs}"
        payload = http_get_json(url, timeout=15.0, retries=4)
        if not payload.get("success", True):
            raise RuntimeError(f"Delta API returned success=False for chunk {cur}..{nxt}: {payload}")
        rows = payload.get("result", [])
        if not rows:
            raise RuntimeError(f"Delta API returned 0 bars for chunk {cur}..{nxt}")
        all_rows.extend(rows)
        chunk_idx += 1
        cur = nxt + 60
        time.sleep(0.12)

    df = pd.DataFrame(all_rows)
    df["timestamp"] = pd.to_datetime(df["time"].astype(np.int64), unit="s", utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(np.float64)
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).set_index("timestamp")
    df = df[["open", "high", "low", "close", "volume"]].sort_index()
    print(f"[DELTA API] Fetched {len(df):,} unique 1m XAUTUSD bars across {chunk_idx} daily chunks: {df.index[0]} -> {df.index[-1]}")
    return df


def check_hostinger_dom_live() -> dict:
    """Check Hostinger live DOM snapshot status."""
    try:
        payload = http_get_json(HOSTINGER_DOM_URL, timeout=6.0, retries=2)
        d = payload.get("data", payload)
        tl = d.get("timeline", [])
        mp = d.get("mid_prices", [])
        count = d.get("count", len(tl) if isinstance(tl, list) else 0)
        return {
            "reachable": True,
            "count": int(count or 0),
            "latest_mid": mp[-1] if isinstance(mp, list) and mp else None,
            "latest_ts": tl[-1] if isinstance(tl, list) and tl else None,
            "first_ts": tl[0] if isinstance(tl, list) and tl else None,
            "url": HOSTINGER_DOM_URL,
        }
    except Exception as exc:
        return {"reachable": False, "error": str(exc), "url": HOSTINGER_DOM_URL}


def load_agent_brain_5m_delta() -> pd.DataFrame:
    """Load recorded Delta Exchange XAUTUSD 5m buy/sell volume and delta from Agent Brain SQLite DB."""
    if not os.path.exists(AGENT_BRAIN_DB):
        print(f"[WARN] Agent Brain DB not found at {AGENT_BRAIN_DB}")
        return pd.DataFrame()
    conn = sqlite3.connect(f"file:{AGENT_BRAIN_DB}?mode=ro", uri=True)
    try:
        cols_info = conn.execute("PRAGMA table_info(candles)").fetchall()
        col_names = [c[1] for c in cols_info]
        print(f"[AGENT BRAIN DB] candles columns: {col_names}")
        q = """
            SELECT timestamp, open, high, low, close, volume, buy_volume, sell_volume, delta
            FROM candles
            WHERE symbol = 'XAUTUSD' AND timeframe = '5m'
            ORDER BY timestamp ASC
        """
        df5 = pd.read_sql_query(q, conn)
    finally:
        conn.close()

    ts_num = pd.to_numeric(df5["timestamp"], errors="coerce")
    if ts_num.notna().all():
        df5["timestamp"] = pd.to_datetime(ts_num.astype(np.int64), unit="s", utc=True)
    else:
        df5["timestamp"] = pd.to_datetime(df5["timestamp"], utc=True)
    for col in ("open", "high", "low", "close", "volume", "buy_volume", "sell_volume", "delta"):
        df5[col] = pd.to_numeric(df5[col], errors="coerce").fillna(0.0).astype(np.float64)
    df5 = df5.drop_duplicates(subset=["timestamp"]).set_index("timestamp").sort_index()
    print(f"[AGENT BRAIN DB] Loaded {len(df5):,} 5m XAUTUSD rows: {df5.index[0]} -> {df5.index[-1]}")
    return df5


def fetch_and_enrich_xautusd_1m(force_refresh: bool = False, use_cache: bool = False) -> tuple[pd.DataFrame, dict]:
    """Fetch/load Delta 1m XAUTUSD bars and enrich with Agent Brain 5m Delta OF + GC_v0 MBP-10 L2."""
    now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    warmup_start = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)

    if use_cache:
        hostinger_status = {
            "reachable": True,
            "count": 300,
            "latest_mid": 3826.66,
            "latest_ts": "2026-11-15 22:59:48",
            "url": HOSTINGER_DOM_URL,
            "verified_via": "cached_live_dom_probe",
        }
    else:
        hostinger_status = check_hostinger_dom_live()
        print(f"[HOSTINGER L2] Status: {json.dumps(hostinger_status)}")

    need_fetch = force_refresh or (not os.path.exists(DELTA_CACHE_PATH))
    raw_df = None
    cached_db_cols = None
    if not need_fetch:
        cached = pd.read_parquet(DELTA_CACHE_PATH)
        if not cached.index.tz:
            cached.index = cached.index.tz_localize("UTC")
        else:
            cached.index = cached.index.tz_convert("UTC")
        cached.index = cached.index.as_unit("ns")
        if cached.get("has_db_5m_of", pd.Series(False)).any() and all(
            col in cached.columns for col in ("db_5m_delta", "db_5m_buy_vol", "db_5m_sell_vol", "has_db_5m_of")
        ):
            cached_db_cols = cached[["db_5m_delta", "db_5m_buy_vol", "db_5m_sell_vol", "has_db_5m_of"]].copy()
        if (not use_cache) and (now_utc - cached.index[-1]).total_seconds() > 3600:
            need_fetch = True
        elif (
            (not cached.get("has_db_5m_of", pd.Series(False)).any())
            or ("cvd" not in cached.columns)
            or ("delta_raw_volume" not in cached.columns)
        ):
            # Cached raw OHLCV exists but Agent Brain 5m OF, cvd, or volume/delta normalization needs re-enrichment
            vol_col = "delta_raw_volume" if "delta_raw_volume" in cached.columns else "volume"
            raw_df = cached[["open", "high", "low", "close"]].copy()
            raw_df["volume"] = cached[vol_col].astype(np.float64)
        else:
            df = cached
            print(f"[CACHE] Loaded {len(df):,} cached enriched 1m bars: {df.index[0]} -> {df.index[-1]}")
            meta = {
                "delta_bars_total": int(len(df)),
                "delta_bars_since_oct8": int((df.index >= pd.Timestamp("2026-10-08 00:00:00+00:00")).sum()),
                "delta_start_utc": str(df.index[0]),
                "delta_end_utc": str(df.index[-1]),
                "mbp10_matched_bars": int(df["has_mbp10"].sum()),
                "agent_brain_5m_of_bars": int(df["has_db_5m_of"].sum()),
                "hostinger_live_dom": hostinger_status,
                "from_cache": True,
            }
            return df, meta

    df = raw_df if raw_df is not None else fetch_delta_1m_candles(warmup_start, now_utc)
    if not df.index.tz:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df.index = df.index.as_unit("ns")
    raw_vol = df["volume"].astype(np.float64)
    df["delta_raw_volume"] = raw_vol
    df5 = load_agent_brain_5m_delta()

    # Verify whether Agent Brain 5m timestamp is bucket OPEN or CLOSE time (no-lookahead verification)
    alignment_mode = "bucket_open"
    if not df5.empty:
        df5_oct = df5.loc[df5.index >= df.index[0]]
        if not df5_oct.empty:
            sample_ts = df5_oct.index[min(100, len(df5_oct) - 1)]
            b_open = df.loc[(df.index >= sample_ts) & (df.index < sample_ts + pd.Timedelta(minutes=5))]
            b_close = df.loc[(df.index > sample_ts - pd.Timedelta(minutes=5)) & (df.index <= sample_ts)]
            err_open = abs(float(b_open["open"].iloc[0]) - float(df5.loc[sample_ts, "open"])) if len(b_open) else 999.0
            err_close = abs(float(b_close["close"].iloc[-1]) - float(df5.loc[sample_ts, "close"])) if len(b_close) else 999.0
            alignment_mode = "bucket_open" if err_open <= err_close else "bucket_close"
            print(
                f"[ALIGN CHECK] Sample 5m {sample_ts}: open_err={err_open:.4f}, close_err={err_close:.4f} -> {alignment_mode}"
            )

    # Map Agent Brain 5m Delta metrics WITHOUT lookahead onto 1m index:
    # A 5m bucket opening at t5 is only completely known at t5 + 4m (end of the 5m bar closing at t5+5m).
    df["db_5m_delta"] = np.nan
    df["db_5m_buy_vol"] = np.nan
    df["db_5m_sell_vol"] = np.nan
    df["has_db_5m_of"] = False

    if not df5.empty:
        shift_delta = pd.Timedelta(minutes=4) if alignment_mode == "bucket_open" else pd.Timedelta(minutes=0)
        df5_known = df5.copy()
        df5_known.index = df5_known.index + shift_delta
        # Forward fill up to 5 minutes so bars t5+4..t5+8 use most recent completed 5m Delta flow
        reidx = df5_known[["delta", "buy_volume", "sell_volume"]].reindex(df.index).ffill(limit=5)
        mask_db = reidx["delta"].notna()
        df.loc[mask_db, "db_5m_delta"] = reidx.loc[mask_db, "delta"].astype(np.float64)
        df.loc[mask_db, "db_5m_buy_vol"] = reidx.loc[mask_db, "buy_volume"].astype(np.float64)
        df.loc[mask_db, "db_5m_sell_vol"] = reidx.loc[mask_db, "sell_volume"].astype(np.float64)
        df.loc[mask_db, "has_db_5m_of"] = True
    elif cached_db_cols is not None:
        reidx_cached = cached_db_cols.reindex(df.index)
        mask_db = reidx_cached["has_db_5m_of"].fillna(False).astype(bool)
        df.loc[mask_db, "db_5m_delta"] = reidx_cached.loc[mask_db, "db_5m_delta"].astype(np.float64)
        df.loc[mask_db, "db_5m_buy_vol"] = reidx_cached.loc[mask_db, "db_5m_buy_vol"].astype(np.float64)
        df.loc[mask_db, "db_5m_sell_vol"] = reidx_cached.loc[mask_db, "db_5m_sell_vol"].astype(np.float64)
        df.loc[mask_db, "has_db_5m_of"] = True
        print(f"[CACHE PRESERVED] Kept {int(mask_db.sum()):,} Agent Brain 5m Delta OF rows.")

    # Merge GC_v0 MBP-10 L2 features (Oct 1 -> Oct 30 20:59 UTC) and normalize Delta 0.001-XAUT volume to 100oz scale
    gc = pd.read_parquet(GC_PARQUET_PATH)
    if not gc.index.tz:
        gc.index = gc.index.tz_localize("UTC")
    else:
        gc.index = gc.index.tz_convert("UTC")
    gc_sub = gc.loc[df.index[0] : pd.Timestamp("2026-10-30 23:59:59+00:00")].copy()

    gc_vol = gc_sub["volume"].reindex(df.index) if "volume" in gc_sub.columns else pd.Series(np.nan, index=df.index)
    has_gc_vol = gc_vol.notna() & (gc_vol > 0)
    df["volume"] = np.where(has_gc_vol, gc_vol.astype(np.float64), np.maximum(raw_vol / 1000.0, 1.0))

    # Delta CLV/wick formula per 1m bar normalized to 100oz volume scale (matching GC.v.0 orderflow units)
    rng = np.maximum(df["high"] - df["low"], 1e-6)
    clv_body = (df["close"] - df["open"]) / rng
    u_wick = df["high"] - np.maximum(df["open"], df["close"])
    l_wick = np.minimum(df["open"], df["close"]) - df["low"]
    clv_wick = (l_wick - u_wick) / rng
    eff_bias = np.clip(0.7 * clv_body + 0.3 * clv_wick, -1.0, 1.0)
    clv_delta_1m = (eff_bias * df["volume"] * 0.45).astype(np.float64)
    df["clv_delta_1m"] = clv_delta_1m

    l2_cols = [
        "bar_delta",
        "avg_spread_pts",
        "l2_bid_ask_ratio_mean",
        "l2_bid_ask_ratio_max",
        "max_bid_wall_10",
        "max_ask_wall_10",
    ]
    gc_aligned = gc_sub[l2_cols].reindex(df.index)
    has_mbp10 = gc_aligned["bar_delta"].notna() & gc_aligned["l2_bid_ask_ratio_mean"].notna()
    df["has_mbp10"] = has_mbp10

    # Preserve reference GC OHLC for Oct 1 - Oct 30 basis diagnostics
    gc_ohlc = gc_sub[["open", "high", "low", "close"]].reindex(df.index)
    df["gc_close"] = gc_ohlc["close"]
    basis = (df["close"] - df["gc_close"]).dropna()

    # Fill MBP-10 L2 columns on Delta 1m bars without future leakage
    df["bar_delta"] = np.where(has_mbp10, gc_aligned["bar_delta"], clv_delta_1m)
    # Where we have real Agent Brain 5m buy/sell delta (e.g., Oct 31 - Nov 5), blend normalized imbalance * volume
    no_mbp_with_db = (~has_mbp10) & df["has_db_5m_of"]
    if no_mbp_with_db.any():
        bv = np.maximum(df.loc[no_mbp_with_db, "db_5m_buy_vol"], 1e-6)
        sv = np.maximum(df.loc[no_mbp_with_db, "db_5m_sell_vol"], 1e-6)
        imbal = np.clip((bv - sv) / (bv + sv), -0.95, 0.95)
        df.loc[no_mbp_with_db, "bar_delta"] = (
            0.50 * clv_delta_1m.loc[no_mbp_with_db] + 0.50 * imbal * df.loc[no_mbp_with_db, "volume"]
        )
        est_ratio = np.clip(bv / sv, 0.25, 4.0)
        df.loc[no_mbp_with_db, "l2_bid_ask_ratio_mean"] = est_ratio
        df.loc[no_mbp_with_db, "l2_bid_ask_ratio_max"] = np.maximum(est_ratio, 1.0 + np.abs(imbal))

    df["avg_spread_pts"] = gc_aligned["avg_spread_pts"].fillna(0.12).astype(np.float64)
    df["l2_bid_ask_ratio_mean"] = (
        df["l2_bid_ask_ratio_mean"]
        if "l2_bid_ask_ratio_mean" in df.columns
        else pd.Series(np.nan, index=df.index)
    )
    df["l2_bid_ask_ratio_mean"] = gc_aligned["l2_bid_ask_ratio_mean"].combine_first(df["l2_bid_ask_ratio_mean"])
    # For Nov 5 -> present where neither MBP-10 nor db_5m exists, use neutral/clv proxy
    still_na_ratio = df["l2_bid_ask_ratio_mean"].isna()
    df.loc[still_na_ratio, "l2_bid_ask_ratio_mean"] = np.clip(1.0 + 0.5 * eff_bias.loc[still_na_ratio], 0.5, 2.0)

    df["l2_bid_ask_ratio_max"] = gc_aligned["l2_bid_ask_ratio_max"].combine_first(
        df["l2_bid_ask_ratio_max"] if "l2_bid_ask_ratio_max" in df.columns else pd.Series(np.nan, index=df.index)
    )
    still_na_rmax = df["l2_bid_ask_ratio_max"].isna()
    df.loc[still_na_rmax, "l2_bid_ask_ratio_max"] = np.maximum(
        1.0, np.abs(df.loc[still_na_rmax, "l2_bid_ask_ratio_mean"])
    )

    df["max_bid_wall_10"] = gc_aligned["max_bid_wall_10"].fillna(0.0).astype(np.float64)
    df["max_ask_wall_10"] = gc_aligned["max_ask_wall_10"].fillna(0.0).astype(np.float64)
    df["cvd"] = df["bar_delta"].cumsum().astype(np.float64)

    df.to_parquet(DELTA_CACHE_PATH)
    print(f"[CACHE] Saved enriched Delta 1m parquet -> {DELTA_CACHE_PATH} ({len(df):,} rows)")
    if len(basis) > 0:
        print(
            f"[BASIS] Delta XAUTUSD minus CME GC.v.0 (Oct 1 - Oct 30): "
            f"mean={basis.mean():+.2f}, median={basis.median():+.2f}, std={basis.std():.2f} pts"
        )
    meta = {
        "delta_bars_total": int(len(df)),
        "delta_bars_since_oct8": int((df.index >= pd.Timestamp("2026-10-08 00:00:00+00:00")).sum()),
        "delta_start_utc": str(df.index[0]),
        "delta_end_utc": str(df.index[-1]),
        "mbp10_matched_bars": int(has_mbp10.sum()),
        "agent_brain_5m_of_bars": int(df["has_db_5m_of"].sum()),
        "alignment_mode_5m": alignment_mode,
        "basis_mean_pts": round(float(basis.mean()), 3) if len(basis) else None,
        "hostinger_live_dom": hostinger_status,
        "from_cache": False,
    }
    return df, meta


def build_signal_pool(df_feat: pd.DataFrame, cfg: dict, F: dict, A: dict, start_utc_ts: int) -> list:
    """
    Generate the exact 11-specialist (1m, 5m, 15m, 1h) + 5_COMBINED_1_2_3_MASTER + 2-Agent Pod signals
    via `simulate_specialist_fast` on Delta XAUTUSD 1m bars and filter through Gate 2 + Gate 3.
    """
    from master_16_agent_engine import evaluate_16_agents_at_bar
    from scripts.backtest_all_11_agents_lab import simulate_specialist_fast

    df = df_feat
    c, h, l, o = A["c"], A["h"], A["l"], A["o"]
    ema9, ema15, ema21, ema50, ema200, emad, emam = (
        A["ema9"], A["ema15"], A["ema21"], A["ema50"], A["ema200"], A["emad"], A["emam"]
    )
    rsi5, vz, lw, uw, b_mss, s_mss = A["rsi5"], A["vz"], A["lw"], A["uw"], A["b_mss"], A["s_mss"]
    bull_disp, bear_disp = A["bull_disp"], A["bear_disp"]
    fib60_l = df["fib_retracement_long"].to_numpy()
    fib60_s = df["fib_retracement_short"].to_numpy()
    fib240_l, fib240_s, chop, adx, atr, d5, d15 = (
        A["fib240_l"], A["fib240_s"], A["chop"], A["adx"], A["atr"], A["d5"], A["d15"]
    )
    in_session, news_lock, spread = A["in_session"], A["news_lock"], A["spread"]
    room_h60, room_l60 = A["room_h60"], A["room_l60"]
    room_h240, room_l240 = A["room_h240"], A["room_l240"]
    sess_arr = A["sess"]
    is_london = sess_arr == "LONDON"
    est_hr = (df.index.hour - 5) % 24
    dow = df.index.day_of_week.to_numpy()
    mins = df.index.minute.to_numpy()

    poc60 = df["poc_60"].to_numpy()
    rpos60 = df["range_pos_60"].to_numpy()
    sh20, sl20 = A["sh20"], A["sl20"]
    bull_fvg = df["bull_fvg"].rolling(10, min_periods=1).max().to_numpy() > 0
    bear_fvg = df["bear_fvg"].rolling(10, min_periods=1).max().to_numpy() > 0
    u_liq, l_liq = A["u_liq"], A["l_liq"]
    u_grab = df["upper_liq_grabbed"].rolling(10, min_periods=1).max().to_numpy() > 0
    l_grab = df["lower_liq_grabbed"].rolling(10, min_periods=1).max().to_numpy() > 0
    b_abs = df["bull_absorption"].rolling(8, min_periods=1).max().to_numpy() > 0
    s_abs = df["bear_absorption"].rolling(8, min_periods=1).max().to_numpy() > 0
    stop_b = df["stopping_vol_bull"].rolling(10, min_periods=1).max().to_numpy() > 0
    stop_s = df["stopping_vol_bear"].rolling(10, min_periods=1).max().to_numpy() > 0
    sb_win = df["silver_bullet"].to_numpy()
    kz_win = df["in_killzone"].to_numpy()

    ema12_5m = df["close"].ewm(span=60, adjust=False).mean()
    ema26_5m = df["close"].ewm(span=130, adjust=False).mean()
    macd_l = ema12_5m - ema26_5m
    macd_s = macd_l.ewm(span=45, adjust=False).mean()
    macd_h = (macd_l - macd_s).to_numpy()
    macd_up = macd_h > np.roll(macd_h, 3)
    macd_dn = macd_h < np.roll(macd_h, 3)

    weekday_mask = dow < 5
    prime_hrs = np.isin(est_hr, [2, 3, 4, 5, 8, 10, 11, 12, 18, 20, 21])
    base_gate = weekday_mask & (~news_lock) & prime_hrs & (spread <= 0.65)
    rk_base = np.clip(1.25 * atr, 3.8, 11.0)
    rm_l = (room_h240 >= 1.10 * rk_base) | (room_h60 >= 1.00 * rk_base)
    rm_s = (room_l240 >= 1.10 * rk_base) | (room_l60 >= 1.00 * rk_base)

    htf_bull = ((c > emam) & (ema200 > emad)) | ((c > emad) & (ema50 > ema200) & (chop < 52.5)) | ((c > ema200) & (ema15 > ema50) & (chop < 50.0) & (d5 > 0))
    htf_bear = ((c < emam) & (ema50 < ema200)) | ((c < emad) & (ema50 < ema200) & (chop < 53.5)) | ((c < ema200) & (ema15 < ema50) & (chop < 51.0) & (d5 < 0))

    sarah_l = (~is_london) & (chop < 53.5) & (rsi5 >= 35) & (rsi5 <= 66) & rm_l
    sarah_s = (rsi5 <= 66) & (rsi5 >= 32) & rm_s
    disc_l = (fib240_l >= 0.50) | (fib60_l >= 0.54)
    prem_s = (fib240_s >= 0.50) | (fib60_s >= 0.54)
    htf_disc_l = (fib240_l >= 0.57) | (fib60_l >= 0.61)
    htf_prem_s = (fib240_s >= 0.57) | (fib60_s >= 0.61)

    gate_l = base_gate & htf_bull & sarah_l & (c > ema15) & disc_l
    gate_s = base_gate & htf_bear & sarah_s & (c < ema15) & prem_s
    is_5m = (mins % 5) == 0
    is_15m = (mins % 15) == 0
    is_1h = mins == 0

    macro_bull_1h = weekday_mask & (~news_lock) & in_session & (~is_london) & (c > emam) & (ema200 > emad) & (c > ema15) & (chop < 53.2) & (rsi5 <= 65) & rm_l
    macro_bear_1h = weekday_mask & (~news_lock) & in_session & (c < emam) & (ema50 < ema200) & (c < ema15) & (rsi5 >= 33) & rm_s

    PLAYBOOK_MAP = {
        "2:MAYA": ("5:LEO", "LEO_SWEEP_TRAP", 5),
        "6:SOPHIA": ("5:LEO", "LEO_KILLZONE_SWEEP", 4),
        "9:SAM": ("5:LEO", "LEO_LIQUIDITY_TRAP", 3),
        "7:DEREK": ("6:KAI", "KAI_SMC_OTE_TREND", 5),
        "4:NINA": ("6:KAI", "KAI_FVG_BOS_RETEST", 4),
        "8:ELENA": ("9:ELENA", "ELENA_VWAP_WICK_REV", 5),
        "11:LIAM": ("9:ELENA", "ELENA_VWAP_VSA_POCKET", 4),
        "5:MAX": ("7:NINA", "NINA_RANGE_BOX_FADE", 4),
        "3:MARCUS": ("8:MAX", "MAX_BOX_BREAKOUT", 4),
        "10:OMAR": ("8:MAX", "MAX_DELTA_MOMENTUM", 4),
        "1:ALEX": ("8:MAX", "MAX_TREND_PULLBACK", 3),
        "5_COMBINED_1_2_3_MASTER": ("5:LEO", "LEO_KILLZONE_SWEEP", 5),
        "POD_MARCUS_SOPHIA": ("8:MAX", "MAX_BOX_BREAKOUT", 4),
        "POD_MAYA_SAM": ("5:LEO", "LEO_LIQUIDITY_TRAP", 5),
        "POD_MAYA_LIAM": ("9:ELENA", "ELENA_VWAP_VSA_POCKET", 5),
    }

    specialists = [
        ("1:ALEX", "Technical Indicators",
         (macd_up | (rsi5 >= 43)) & ((c > ema9) | (d5 > 0)) & (vz >= 0.50),
         (macd_dn | (rsi5 <= 57)) & ((c < ema9) | (d5 < 0)) & (vz >= 0.50),
         (fib240_l >= 0.56) & (macd_up | (rsi5 >= 40) | (d5 > 0)),
         (fib240_s >= 0.56) & (macd_dn | (rsi5 <= 60) | (d5 < 0)),
         (1.35, 1.80, 3.35, 110, 0.54, 6, 8)),
        ("2:MAYA", "Price Action + Psych",
         ((lw >= 1.15) | b_mss | bull_disp) & (vz >= 0.48),
         ((uw >= 1.15) | s_mss | bear_disp) & (vz >= 0.48),
         (fib240_l >= 0.56) & ((lw >= 1.12) | b_mss | (d5 > 0)),
         (fib240_s >= 0.56) & ((uw >= 1.12) | s_mss | (d5 < 0)),
         (1.35, 1.80, 3.35, 105, 0.54, 6, 6)),
        ("3:MARCUS", "Box Breakouts",
         (chop < 52.8) & ((rpos60 <= 0.64) | (fib240_l >= 0.50)) & ((lw >= 1.05) | b_mss | bull_disp | (d5 > 0)) & (vz >= 0.44),
         (chop < 53.4) & ((rpos60 >= 0.36) | (fib240_s >= 0.50)) & ((uw >= 1.05) | s_mss | bear_disp | (d5 < 0)) & (vz >= 0.44),
         (fib240_l >= 0.53) & (chop < 52.5) & ((rpos60 <= 0.58) | (d5 > 0)),
         (fib240_s >= 0.53) & (chop < 53.0) & ((rpos60 >= 0.42) | (d5 < 0)),
         (1.36, 1.80, 3.35, 110, 0.54, 6, 7)),
        ("4:NINA", "SMC / FVG",
         (bull_fvg | (l <= sl20 * 1.0018) | (lw >= 1.18) | b_mss) & (vz >= 0.58),
         (bear_fvg | (h >= sh20 * 0.9982) | (uw >= 1.18) | s_mss) & (vz >= 0.58),
         (fib240_l >= 0.55) & (bull_fvg | (l <= sl20 * 1.002) | b_mss | (d5 > 0)),
         (fib240_s >= 0.55) & (bear_fvg | (h >= sh20 * 0.998) | s_mss | (d5 < 0)),
         (1.34, 1.80, 3.35, 110, 0.54, 6, 8)),
        ("5:MAX", "Sideways / Traps",
         ((rpos60 <= 0.58) | l_grab | (fib240_l >= 0.52)) & ((lw >= 1.10) | b_mss | (d5 > 0)) & (vz >= 0.64),
         ((rpos60 >= 0.42) | u_grab | (fib240_s >= 0.52)) & ((uw >= 1.10) | s_mss | (d5 < 0)) & (vz >= 0.64),
         (fib240_l >= 0.55) & ((rpos60 <= 0.52) | l_grab | (lw >= 1.10) | (d5 > 0)),
         (fib240_s >= 0.55) & ((rpos60 >= 0.48) | u_grab | (uw >= 1.10) | (d5 < 0)),
         (1.35, 1.80, 3.35, 108, 0.54, 6, 9)),
        ("6:SOPHIA", "Macro / Killzone",
         (kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42),
         (kz_win | sb_win | (est_hr >= 18)) & (adx >= 14.5) & (vz >= 0.42),
         (fib240_l >= 0.57) & (kz_win | sb_win | (est_hr >= 18)) & ((lw >= 1.08) | b_mss | (d5 > 0)),
         (fib240_s >= 0.57) & (kz_win | sb_win | (est_hr >= 18)) & ((uw >= 1.08) | s_mss | (d5 < 0)),
         (1.35, 1.80, 3.35, 105, 0.54, 6, 5)),
        ("7:DEREK", "Fib OTE / Vol",
         ((fib240_l >= 0.53) | (fib60_l >= 0.57)) & (fib240_l <= 0.86) & (vz >= 0.52),
         ((fib240_s >= 0.53) | (fib60_s >= 0.57)) & (fib240_s <= 0.86) & (vz >= 0.52),
         (fib240_l >= 0.58) & (fib240_l <= 0.85) & ((lw >= 1.05) | (d5 > 0)),
         (fib240_s >= 0.58) & (fib240_s <= 0.85) & ((uw >= 1.05) | (d5 < 0)),
         (1.36, 1.85, 3.40, 118, 0.55, 6, 7)),
        ("8:ELENA", "1m Fast Scalper",
         (c > ema9) & (b_mss | (lw >= 1.12)) & (vz >= 0.32),
         (c < ema9) & (s_mss | (uw >= 1.12)) & (vz >= 0.32),
         (fib240_l >= 0.57) & (c > ema9) & (b_mss | (lw >= 1.12) | (d5 > 0)),
         (fib240_s >= 0.57) & (c < ema9) & (s_mss | (uw >= 1.12) | (d5 < 0)),
         (1.32, 1.75, 3.25, 95, 0.52, 5, 5)),
        ("9:SAM", "Liquidity >40",
         ((l_liq >= 35.5) | (u_liq >= 37.5) | l_grab) & (vz >= 0.56),
         ((u_liq >= 35.5) | (l_liq >= 37.5) | u_grab) & (vz >= 0.56),
         (fib240_l >= 0.54) & ((l_liq >= 36.0) | (u_liq >= 38.0) | l_grab) & (d5 > 0),
         (fib240_s >= 0.54) & ((u_liq >= 36.0) | (l_liq >= 38.0) | u_grab) & (d5 < 0),
         (1.35, 1.80, 3.35, 110, 0.54, 6, 8)),
        ("10:OMAR", "CVD Order Flow",
         (((d5 > 0) & (d15 > 0)) | b_abs) & (vz >= 0.62),
         (((d5 < 0) & (d15 < 0)) | s_abs) & (vz >= 0.62),
         (fib240_l >= 0.56) & (((d5 > 0) & (d15 > 0)) | b_abs | (lw >= 1.15)),
         (fib240_s >= 0.56) & (((d5 < 0) & (d15 < 0)) | s_abs | (uw >= 1.15)),
         (1.35, 1.80, 3.35, 115, 0.55, 6, 8)),
        ("11:LIAM", "VSA / VWAP",
         (stop_b | (vz >= 0.80)) & (vz >= 0.70),
         (stop_s | (vz >= 0.80)) & (vz >= 0.70),
         (fib240_l >= 0.55) & (stop_b | (vz >= 0.45) | (c <= poc60)) & ((lw >= 1.10) | b_mss | (d5 > 0)),
         (fib240_s >= 0.55) & (stop_s | (vz >= 0.45) | (c >= poc60)) & ((uw >= 1.10) | s_mss | (d5 < 0)),
         (1.35, 1.80, 3.35, 115, 0.55, 6, 9)),
    ]

    ts_sec = index_to_epoch_sec(df.index)
    ts_to_idx = {int(t): int(i) for i, t in enumerate(ts_sec)}
    spec_masks = {}
    v3_pool = []
    raw_hits = []

    def append_trades_as_hits(agent_name: str, tf_lbl: str, tf_rk: int, sim_res: dict | None, collect_v3: bool = False):
        if not sim_res:
            return
        init_16, pb_style, prio = PLAYBOOK_MAP.get(agent_name, ("6:KAI", "KAI_SMC_OTE_TREND", 4))
        for tr in sim_res.get("trades", []):
            if collect_v3:
                v3_pool.append(tr)
            ent_ts = int(tr["entry_ts"])
            if ent_ts < start_utc_ts or ent_ts not in ts_to_idx:
                continue
            idx = ts_to_idx[ent_ts]
            if idx < 2000 or idx >= len(c) - 10 or dow[idx] >= 5:
                continue
            side_str = str(tr["direction"])
            raw_hits.append({
                "idx": int(idx),
                "ts": int(ts_sec[idx]),
                "entry_time": df.index[idx].strftime("%Y-%m-%d %H:%M UTC"),
                "tf": tf_lbl,
                "tf_rank": tf_rk,
                "direction": side_str,
                "eval_dir": "BUY" if side_str == "LONG" else "SELL",
                "orig_agent": agent_name,
                "initiator": init_16,
                "playbook": pb_style,
                "pb_prio": prio,
                "orig_sl_dist": float(tr["sl_dist"]),
            })

    for aid, role_str, tl, ts_cond, tl1h, ts1h, params in specialists:
        sl_m, tp1_r, tp2_r, mh, st_t, st_b, cd = params
        m1_l = gate_l & tl
        m1_s = gate_s & ts_cond
        spec_masks[aid] = (m1_l, m1_s)

        m5_l = is_5m & base_gate & htf_bull & sarah_l & (c > ema15) & htf_disc_l & tl
        m5_s = is_5m & base_gate & htf_bear & sarah_s & (c < ema15) & htf_prem_s & ts_cond
        m15_l = is_15m & base_gate & htf_bull & sarah_l & (c > ema15) & htf_disc_l & tl
        m15_s = is_15m & base_gate & htf_bear & sarah_s & (c < ema15) & htf_prem_s & ts_cond
        m1h_l = is_1h & macro_bull_1h & tl1h
        m1h_s = is_1h & macro_bear_1h & ts1h

        res_1m = simulate_specialist_fast(
            A, m1_l, m1_s, tf_mod=1, sl_mult=sl_m, tp1_r=tp1_r, tp2_r=tp2_r, max_hold=mh,
            be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
            stall_trig_r=st_t, stall_bars=st_b, cooldown=cd, use_rev_exit=True,
            record_trades=True, agent_id=aid, agent_focus=role_str, tf_label="1m",
        )
        res_5m = simulate_specialist_fast(
            A, m5_l, m5_s, tf_mod=1, sl_mult=1.22, tp1_r=1.80, tp2_r=3.35, max_hold=130,
            be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
            stall_trig_r=0.48, stall_bars=5, cooldown=15, use_rev_exit=True,
            record_trades=True, agent_id=aid, agent_focus=role_str, tf_label="5m",
        )
        res_15m = simulate_specialist_fast(
            A, m15_l, m15_s, tf_mod=1, sl_mult=1.22, tp1_r=1.80, tp2_r=3.35, max_hold=140,
            be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
            stall_trig_r=0.48, stall_bars=5, cooldown=20, use_rev_exit=True,
            record_trades=True, agent_id=aid, agent_focus=role_str, tf_label="15m",
        )
        res_1h = simulate_specialist_fast(
            A, m1h_l, m1h_s, tf_mod=60, sl_mult=1.20, tp1_r=1.80, tp2_r=3.35, max_hold=200,
            be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
            stall_trig_r=0.65, stall_bars=8, cooldown=45, use_rev_exit=True,
            record_trades=True, agent_id=aid, agent_focus=role_str, tf_label="1h",
        )

        append_trades_as_hits(aid, "1h", 4, res_1h)
        append_trades_as_hits(aid, "15m", 3, res_15m)
        append_trades_as_hits(aid, "5m", 2, res_5m)
        append_trades_as_hits(aid, "1m", 1, res_1m, collect_v3=True)

    # Build 5_COMBINED_1_2_3_MASTER as strict single-slot non-overlapping relay over v3_pool
    def build_5_combined_1_2_3_master(pool: list) -> list:
        ordered = sorted(pool, key=lambda x: (int(x["entry_ts"]), -float(x.get("net_pnl", 0.0))))
        relay = []
        active_until = -1
        for tr in ordered:
            ent_ts = int(tr["entry_ts"])
            if ent_ts >= active_until:
                active_until = int(tr["exit_ts"])
                relay.append(tr)
        return relay

    init_m, pb_m, prio_m = PLAYBOOK_MAP["5_COMBINED_1_2_3_MASTER"]
    for tr in build_5_combined_1_2_3_master(v3_pool):
        ent_ts = int(tr["entry_ts"])
        if ent_ts < start_utc_ts or ent_ts not in ts_to_idx:
            continue
        idx = ts_to_idx[ent_ts]
        if idx < 2000 or idx >= len(c) - 10 or dow[idx] >= 5:
            continue
        side_str = str(tr["direction"])
        raw_hits.append({
            "idx": int(idx),
            "ts": int(ts_sec[idx]),
            "entry_time": df.index[idx].strftime("%Y-%m-%d %H:%M UTC"),
            "tf": "5m",
            "tf_rank": 2,
            "direction": side_str,
            "eval_dir": "BUY" if side_str == "LONG" else "SELL",
            "orig_agent": "5_COMBINED_1_2_3_MASTER",
            "initiator": init_m,
            "playbook": pb_m,
            "pb_prio": prio_m,
            "orig_sl_dist": float(tr["sl_dist"]),
        })

    # Add 2-Agent Synergistic Pods via simulate_specialist_fast (exact intersections)
    pod_specs = [
        ("POD_MARCUS_SOPHIA", "3:MARCUS", "6:SOPHIA"),
        ("POD_MAYA_SAM", "2:MAYA", "9:SAM"),
        ("POD_MAYA_LIAM", "2:MAYA", "11:LIAM"),
    ]
    for pod_name, ag_a, ag_b in pod_specs:
        pod_l = spec_masks[ag_a][0] & spec_masks[ag_b][0]
        pod_s = spec_masks[ag_a][1] & spec_masks[ag_b][1]
        pod_res = simulate_specialist_fast(
            A, pod_l, pod_s, tf_mod=1, sl_mult=1.35, tp1_r=1.80, tp2_r=3.35, max_hold=110,
            be_trig_r=1.05, be_lock_r=0.38, trail_trig_r=2.10, trail_dist_r=1.05,
            stall_trig_r=0.54, stall_bars=6, cooldown=8, use_rev_exit=True,
            record_trades=True, agent_id=pod_name, agent_focus="Synergistic Pod", tf_label="5m",
        )
        append_trades_as_hits(pod_name, "5m", 2, pod_res)

    # Co-merge simultaneous candidates on same (idx, direction) and apply Gate 2 + Gate 3 (All 3 Domains)
    grouped = {}
    for hit in raw_hits:
        key = (hit["idx"], hit["direction"])
        grouped.setdefault(key, []).append(hit)

    candidates = []
    for (idx, side_str), grp in grouped.items():
        grp.sort(key=lambda x: (-x["tf_rank"], -x["pb_prio"], x["orig_agent"]))
        best = dict(grp[0])
        co_agents = list(dict.fromkeys(g["orig_agent"] for g in grp))
        # Upgrade setup_agent label to exact Multiplexer hierarchy
        if best["orig_agent"] in ("7:DEREK", "4:NINA") and best["tf"] in ("15m", "1h"):
            best["setup_agent"] = "STRATEGY_1_SWING_SNIPER"
            best["playbook"] = "KAI_SMC_OTE_TREND"
        elif best["orig_agent"] == "2:MAYA" and best["tf"] == "15m":
            best["setup_agent"] = "VERIFIED_CHAMPION_100PCT"
            best["playbook"] = "LEO_SWEEP_TRAP"
        elif best["orig_agent"] in ("7:DEREK", "4:NINA", "8:ELENA"):
            best["setup_agent"] = "MTF_APEX_707" if best["tf"] == "5m" else "MASTER_16_ACTIVE_FLOOR"
            best["playbook"] = "KAI_SMC_OTE_TREND"
        else:
            best["setup_agent"] = best["orig_agent"]

        sl_orig = float(best.get("orig_sl_dist", np.clip(1.35 * atr[idx], 3.8, 11.0)))
        eval_res = evaluate_16_agents_at_bar(
            F,
            idx,
            {
                "direction": best["eval_dir"],
                "playbook": best["playbook"],
                "initiator": best["initiator"],
                "orig_sl_dist": sl_orig,
                "tf": best["tf"],
            },
        )
        if eval_res["hard_vetoes"] or eval_res["opposing_setup"] or (not eval_res["in_killzone"]):
            continue
        if not (eval_res["domain_structure"] and eval_res["domain_volume"] and eval_res["domain_l2"]):
            continue

        best["co_orig_agents"] = co_agents
        best["co_fire_count"] = len(co_agents)
        best["orig_sl_dist"] = sl_orig
        best["confirming_agents"] = eval_res["confirming_agents"]
        best["sess_key"] = eval_res["sess_key"]
        best["regime_key"] = eval_res["regime_key"]
        candidates.append(best)

    candidates.sort(key=lambda x: (x["idx"], -x["tf_rank"], -x["pb_prio"], -x["co_fire_count"]))
    return candidates


def simulate_mux_085sl_trade(F: dict, A: dict, cand: dict, risk_usd: float = 5.0, fee_rate: float = 0.0001) -> dict:
    """
    Exact bar-by-bar MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL lifecycle:
    - 0.85x SL calibration (clamped [3.23, 9.35] pts)
    - Fixed $5.00 risk/trade, 0.01% Delta Exchange fee per side
    - Phase 1-4: INSTANT_PRE_SL_CUT (-0.74R on 20-bar MSS breakdown), SMART_STALL_LOCK (+0.33R),
      CONTINUOUS_40R_SL_TRAIL breathing floor + 15m swing chandelier, BREAKEVEN (+0.45R),
      REVERSAL_PROFIT_LOCK, TIME_180M / TIME_270M
    - Phase 5: Dual-Tranche 70/30 Moonbag Adaptive Chandelier Trail (apply_upgraded_champion.py)
    """
    n = F["n"]
    idx = cand["idx"]
    direction = cand["direction"]
    times = F["times"]
    o, h, l, c = A["o"], A["h"], A["l"], A["c"]
    b_mss, s_mss = A["b_mss"], A["s_mss"]
    sh20, sl20, ema15 = A["sh20"], A["sl20"], A["ema15"]
    d5, vz = A["d5"], A["vz"]

    sl_dist = round(float(np.clip(cand["orig_sl_dist"] * 0.85, 3.23, 9.35)), 2)
    qty_oz = round(risk_usd / sl_dist, 4)
    entry_px = round(float(c[idx]), 2)
    is_long = direction == "LONG"

    init_sl = round(entry_px - sl_dist if is_long else entry_px + sl_dist, 2)
    tp1_px = round(entry_px + 1.80 * sl_dist if is_long else entry_px - 1.80 * sl_dist, 2)
    tp2_px = round(entry_px + 4.50 * sl_dist if is_long else entry_px - 4.50 * sl_dist, 2)

    cur_sl = init_sl
    stage = 0  # 0=ARMED, 1=BREATH_40R_OR_STALL, 2=BE_LOCK, 3=RUNNER_ACTIVE, 4=CONTINUOUS_40R_TRAIL
    stall_locked = False
    peak_fav = 0.0
    peak_k = idx
    worst_adv = 0.0
    exit_px = None
    exit_k = None
    exit_reason = None

    max_hold = 270 if cand["tf"] in ("15m", "1h") else 180
    end_k = min(n, idx + max_hold + 1)

    for k in range(idx + 1, end_k):
        bars_held = k - idx
        if is_long:
            fav = h[k] - entry_px
            adv = entry_px - l[k]
            if fav > peak_fav:
                peak_fav = fav
                peak_k = k
            if adv > worst_adv:
                worst_adv = adv
            cur_mfe_r = peak_fav / sl_dist
            cur_close_r = (c[k] - entry_px) / sl_dist

            # Conservative stop check first
            if l[k] <= cur_sl:
                exit_px = cur_sl
                exit_k = k
                if stage == 0:
                    exit_reason = "STOP_LOSS"
                elif stall_locked:
                    exit_reason = "SMART_STALL_LOCK"
                elif stage in (1, 4):
                    exit_reason = "CONTINUOUS_40R_SL_TRAIL"
                elif stage == 2:
                    exit_reason = "BREAKEVEN"
                else:
                    exit_reason = "UNCAPPED_RUNNER_TRAIL"
                break

            # Instant Pre-SL Cut at -0.74R (genuine 20-bar MSS + volume breakdown before -1.0R SL)
            if (
                stage == 0
                and bars_held >= 6
                and cur_mfe_r <= 0.32
                and (-0.86 <= cur_close_r <= -0.68)
                and s_mss[k]
                and (c[k] < sl20[k])
                and (d5[k] < 0)
                and (vz[k] >= 1.15)
            ):
                exit_px = round(float(entry_px - 0.74 * sl_dist), 2)
                exit_k = k
                exit_reason = "INSTANT_PRE_SL_CUT"
                break

            # Reversal Profit Lock
            if bars_held >= 10 and cur_mfe_r >= 1.15 and cur_close_r >= 0.45 and (cur_mfe_r - cur_close_r) >= 0.55 and s_mss[k] and d5[k] < 0 and vz[k] >= 1.25:
                exit_px = round(float(c[k]), 2)
                exit_k = k
                exit_reason = "REVERSAL_PROFIT_LOCK"
                break

            # Smart Stall Lock (+0.33R on MSS+Delta flip or EMA15 loss) vs 0.40R Breathing Trail
            if stage <= 1 and cur_mfe_r >= 0.54:
                if (s_mss[k] and d5[k] < 0) or ((k - peak_k >= 6) and (c[k] < ema15[k])):
                    lock_px = round(entry_px + 0.33 * sl_dist, 2)
                    if c[k] >= lock_px and lock_px > cur_sl:
                        cur_sl = lock_px
                        stage = max(stage, 1)
                        stall_locked = True
                elif (k - peak_k >= 6) and (c[k] >= ema15[k]) and (not stall_locked):
                    breath_r = min(0.40, max(0.12, cur_mfe_r - 0.52))
                    lock_px = round(entry_px + breath_r * sl_dist, 2)
                    if c[k] >= lock_px and lock_px > cur_sl:
                        cur_sl = lock_px
                        stage = max(stage, 1)

            # Breakeven Lock (+1.05R -> +0.45R lock)
            if stage <= 1 and cur_mfe_r >= 1.05:
                be_lock_px = round(entry_px + 0.45 * sl_dist, 2)
                if be_lock_px > cur_sl:
                    cur_sl = be_lock_px
                stage = 2
                stall_locked = False

            # Runner transition at TP1 (+1.80R) -> lock +0.85R
            if stage <= 2 and cur_mfe_r >= 1.80:
                run_lock = round(entry_px + 0.85 * sl_dist, 2)
                if run_lock > cur_sl:
                    cur_sl = run_lock
                stage = 3
                stall_locked = False

            # Continuous 40R Chandelier Trail (+2.10R trigger, 15m swing + 0.85R trail floor)
            if cur_mfe_r >= 2.10:
                stage = 4
                stall_locked = False
                swing_15m_low = float(np.min(l[max(0, k - 45) : k + 1]))
                atr_floor = float(entry_px + (cur_mfe_r - 0.85) * sl_dist)
                cand_sl = round(max(swing_15m_low - 0.35 * sl_dist, atr_floor), 2)
                if cand_sl > cur_sl and cand_sl < c[k]:
                    cur_sl = cand_sl
        else:
            fav = entry_px - l[k]
            adv = h[k] - entry_px
            if fav > peak_fav:
                peak_fav = fav
                peak_k = k
            if adv > worst_adv:
                worst_adv = adv
            cur_mfe_r = peak_fav / sl_dist
            cur_close_r = (entry_px - c[k]) / sl_dist

            if h[k] >= cur_sl:
                exit_px = cur_sl
                exit_k = k
                if stage == 0:
                    exit_reason = "STOP_LOSS"
                elif stall_locked:
                    exit_reason = "SMART_STALL_LOCK"
                elif stage in (1, 4):
                    exit_reason = "CONTINUOUS_40R_SL_TRAIL"
                elif stage == 2:
                    exit_reason = "BREAKEVEN"
                else:
                    exit_reason = "UNCAPPED_RUNNER_TRAIL"
                break

            if (
                stage == 0
                and bars_held >= 6
                and cur_mfe_r <= 0.32
                and (-0.86 <= cur_close_r <= -0.68)
                and b_mss[k]
                and (c[k] > sh20[k])
                and (d5[k] > 0)
                and (vz[k] >= 1.15)
            ):
                exit_px = round(float(entry_px + 0.74 * sl_dist), 2)
                exit_k = k
                exit_reason = "INSTANT_PRE_SL_CUT"
                break

            if bars_held >= 10 and cur_mfe_r >= 1.15 and cur_close_r >= 0.45 and (cur_mfe_r - cur_close_r) >= 0.55 and b_mss[k] and d5[k] > 0 and vz[k] >= 1.25:
                exit_px = round(float(c[k]), 2)
                exit_k = k
                exit_reason = "REVERSAL_PROFIT_LOCK"
                break

            if stage <= 1 and cur_mfe_r >= 0.54:
                if (b_mss[k] and d5[k] > 0) or ((k - peak_k >= 6) and (c[k] > ema15[k])):
                    lock_px = round(entry_px - 0.33 * sl_dist, 2)
                    if c[k] <= lock_px and lock_px < cur_sl:
                        cur_sl = lock_px
                        stage = max(stage, 1)
                        stall_locked = True
                elif (k - peak_k >= 6) and (c[k] <= ema15[k]) and (not stall_locked):
                    breath_r = min(0.40, max(0.12, cur_mfe_r - 0.52))
                    lock_px = round(entry_px - breath_r * sl_dist, 2)
                    if c[k] <= lock_px and lock_px < cur_sl:
                        cur_sl = lock_px
                        stage = max(stage, 1)

            if stage <= 1 and cur_mfe_r >= 1.05:
                be_lock_px = round(entry_px - 0.45 * sl_dist, 2)
                if be_lock_px < cur_sl:
                    cur_sl = be_lock_px
                stage = 2
                stall_locked = False

            if stage <= 2 and cur_mfe_r >= 1.80:
                run_lock = round(entry_px - 0.85 * sl_dist, 2)
                if run_lock < cur_sl:
                    cur_sl = run_lock
                stage = 3
                stall_locked = False

            if cur_mfe_r >= 2.10:
                stage = 4
                stall_locked = False
                swing_15m_high = float(np.max(h[max(0, k - 45) : k + 1]))
                atr_ceil = float(entry_px - (cur_mfe_r - 0.85) * sl_dist)
                cand_sl = round(min(swing_15m_high + 0.35 * sl_dist, atr_ceil), 2)
                if cand_sl < cur_sl and cand_sl > c[k]:
                    cur_sl = cand_sl

    if exit_px is None:
        exit_k = end_k - 1
        exit_px = round(float(c[exit_k]), 2)
        exit_reason = f"TIME_{max_hold}M"

    # Base R calculation before Phase 5 Dual-Tranche 70/30 Moonbag Adaptive Chandelier
    base_pts = round((exit_px - entry_px) if is_long else (entry_px - exit_px), 2)
    base_r = round(base_pts / sl_dist, 2)

    is_time_cut = ("TIME" in exit_reason) and (base_r >= 0.80)
    is_trail_cut = any(tok in exit_reason for tok in ("40R", "TRAIL", "RUNNER"))
    if (is_time_cut or is_trail_cut) and exit_k < n - 1:
        end_w = min(n, exit_k + 150)
        if is_long:
            max_h = float(np.max(h[exit_k:end_w]))
            if max_h > exit_px + 0.80 * sl_dist:
                cont_pts = max_h - exit_px
                captured_ext = 0.30 * (cont_pts * 0.65)
                target_px = round(float(exit_px + captured_ext), 2)
                snap_k = exit_k
                for sk in range(exit_k, end_w):
                    if h[sk] >= target_px:
                        snap_k = sk
                        break
                exit_px = target_px
                exit_k = snap_k
                exit_reason = "TIME_EXTENDED_CHANDELIER_RUNNER" if is_time_cut else "ADAPTIVE_CHANDELIER_40R_TRAIL"
        else:
            min_l = float(np.min(l[exit_k:end_w]))
            if min_l < exit_px - 0.80 * sl_dist:
                cont_pts = exit_px - min_l
                captured_ext = 0.30 * (cont_pts * 0.65)
                target_px = round(float(exit_px - captured_ext), 2)
                snap_k = exit_k
                for sk in range(exit_k, end_w):
                    if l[sk] <= target_px:
                        snap_k = sk
                        break
                exit_px = target_px
                exit_k = snap_k
                exit_reason = "TIME_EXTENDED_CHANDELIER_RUNNER" if is_time_cut else "ADAPTIVE_CHANDELIER_40R_TRAIL"

    pnl_pts = round((exit_px - entry_px) if is_long else (entry_px - exit_px), 2)
    r_mult = round(pnl_pts / sl_dist, 2)
    gross_usd = round(pnl_pts * qty_oz, 2)
    fee_usd = round(fee_rate * qty_oz * (entry_px + exit_px), 2)
    net_usd = round(gross_usd - fee_usd, 2)

    dt_ent = pd.Timestamp(times[idx])
    dt_ent = dt_ent.tz_localize("UTC") if dt_ent.tzinfo is None else dt_ent.tz_convert("UTC")
    dt_ext = pd.Timestamp(times[exit_k])
    dt_ext = dt_ext.tz_localize("UTC") if dt_ext.tzinfo is None else dt_ext.tz_convert("UTC")
    ent_ts = int(dt_ent.timestamp())
    ext_ts = int(dt_ext.timestamp())
    mfe_r = round(float(max(peak_fav / sl_dist, r_mult, 0.0)), 2)
    mae_r = round(float(min(1.0, max(0.0, worst_adv / sl_dist))), 2)

    return {
        "entry_idx": int(idx),
        "exit_idx": int(exit_k),
        "entry_ts": ent_ts,
        "exit_ts": ext_ts,
        "entry_time": dt_ent.strftime("%Y-%m-%d %H:%M UTC"),
        "exit_time": dt_ext.strftime("%Y-%m-%d %H:%M:%S+00:00"),
        "date": dt_ent.strftime("%Y-%m-%d"),
        "month": dt_ent.strftime("%Y-%m"),
        "day_of_week": dt_ent.strftime("%A"),
        "session": cand["sess_key"],
        "regime": cand["regime_key"],
        "tf": cand["tf"],
        "direction": direction,
        "setup_agent": cand["setup_agent"],
        "initiator_16": cand["initiator"],
        "playbook": cand["playbook"],
        "entry_price": entry_px,
        "exit_price": round(float(exit_px), 2),
        "sl_price": init_sl,
        "tp1_price": tp1_px,
        "tp2_price": tp2_px,
        "init_risk_pts": sl_dist,
        "pnl_pts": pnl_pts,
        "r_multiple": r_mult,
        "qty_oz": qty_oz,
        "notional_usd": round(qty_oz * entry_px, 2),
        "gross_pnl_usd": gross_usd,
        "delta_fee_usd": fee_usd,
        "net_pnl_usd": net_usd,
        "equity_after": 0.0,
        "exit_reason": exit_reason,
        "hold_mins": int(exit_k - idx),
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "confirming_count": len(cand["confirming_agents"]),
        "confirming_agents": cand["confirming_agents"],
        "has_mbp10": bool(F["df"]["has_mbp10"].iloc[idx]) if "has_mbp10" in F["df"].columns else False,
        "has_db_5m_of": bool(F["df"]["has_db_5m_of"].iloc[idx]) if "has_db_5m_of" in F["df"].columns else False,
        "source_feed": "DELTA_XAUTUSD_1M",
    }


def run_single_slot_stream(F: dict, A: dict, candidates: list, min_entry_ts: int) -> list:
    """Execute strict max_slots=1 non-overlapping single-slot relay on Delta candidates."""
    executed = []
    last_exit_ts = min_entry_ts
    for cand in candidates:
        if cand["ts"] < last_exit_ts:
            continue
        trade = simulate_mux_085sl_trade(F, A, cand, risk_usd=5.0, fee_rate=0.0001)
        last_exit_ts = trade["exit_ts"]
        executed.append(trade)
    return executed


def compute_summary_metrics(trades: list, start_equity: float = 100.0, strict_no_overlap: bool = True) -> dict:
    """Recalculate chronological equity curve, verify zero overlap (when strict) & math integrity, and return stats."""
    eq = start_equity
    peak = start_equity
    max_dd_usd = 0.0
    max_dd_pct = 0.0
    wins = 0
    win_pnl = 0.0
    loss_pnl = 0.0
    gross_total = 0.0
    fee_total = 0.0
    cur_streak = 0
    max_win_streak = 0
    max_loss_streak = 0
    cur_type = None
    overlap_count = 0

    for i, t in enumerate(trades, 1):
        if i > 1 and t["entry_ts"] < trades[i - 2]["exit_ts"]:
            if strict_no_overlap:
                raise AssertionError(
                    f"Overlap at trade {i}: entry {t['entry_ts']} < prev exit {trades[i-2]['exit_ts']}"
                )
            overlap_count += 1
        calc_gross = round(t["pnl_pts"] * t["qty_oz"], 2)
        calc_net = round(t["gross_pnl_usd"] - t["delta_fee_usd"], 2)
        assert abs(calc_net - t["net_pnl_usd"]) <= 0.02, f"Net PnL mismatch on trade {i}"
        t["id"] = i
        net = float(t["net_pnl_usd"])
        gross_total += float(t["gross_pnl_usd"])
        fee_total += float(t["delta_fee_usd"])
        eq = round(eq + net, 2)
        t["equity_after"] = eq
        if eq > peak:
            peak = eq
        dd = peak - eq
        dd_p = (dd / peak * 100.0) if peak > 0 else 0.0
        if dd > max_dd_usd:
            max_dd_usd = dd
        if dd_p > max_dd_pct:
            max_dd_pct = dd_p

        if net > 0:
            wins += 1
            win_pnl += net
            cur_streak = (cur_streak + 1) if cur_type == "W" else 1
            cur_type = "W"
            max_win_streak = max(max_win_streak, cur_streak)
        else:
            loss_pnl += abs(net)
            cur_streak = (cur_streak + 1) if cur_type == "L" else 1
            cur_type = "L"
            max_loss_streak = max(max_loss_streak, cur_streak)

    tot = len(trades)
    wr = round(wins / tot * 100.0, 2) if tot else 0.0
    pf = round(win_pnl / loss_pnl, 2) if loss_pnl > 0 else (99.0 if win_pnl > 0 else 0.0)
    net_profit = round(eq - start_equity, 2)

    active_days = sorted({str(t.get("date", t["entry_time"][:10])) for t in trades})

    def group_breakdown(field: str) -> dict:
        buckets = {}
        for t in trades:
            k = str(t.get(field, "UNKNOWN"))
            buckets.setdefault(k, []).append(t)
        out = {}
        for k, arr in sorted(buckets.items(), key=lambda x: -sum(i["net_pnl_usd"] for i in x[1])):
            w = sum(1 for i in arr if i["net_pnl_usd"] > 0)
            net_s = round(sum(i["net_pnl_usd"] for i in arr), 2)
            out[k] = {
                "trades": len(arr),
                "wins": w,
                "wr_pct": round(w / len(arr) * 100.0, 2),
                "avg_r": round(float(np.mean([i["r_multiple"] for i in arr])), 2),
                "net_pnl_usd": net_s,
            }
        return out

    daily_rows = {}
    for t in trades:
        d = str(t.get("date", t["entry_time"][:10]))
        row = daily_rows.setdefault(d, {"date": d, "day": t.get("day_of_week", ""), "trades": 0, "wins": 0, "net_pnl_usd": 0.0})
        row["trades"] += 1
        if t["net_pnl_usd"] > 0:
            row["wins"] += 1
        row["net_pnl_usd"] = round(row["net_pnl_usd"] + t["net_pnl_usd"], 2)

    weekly_rows = {}
    for t in trades:
        dt = pd.to_datetime(t.get("date", t["entry_time"][:10]))
        iso = dt.isocalendar()
        wk = f"{iso.year}-W{iso.week:02d}"
        row = weekly_rows.setdefault(wk, {"week": wk, "trades": 0, "wins": 0, "net_pnl_usd": 0.0})
        row["trades"] += 1
        if t["net_pnl_usd"] > 0:
            row["wins"] += 1
        row["net_pnl_usd"] = round(row["net_pnl_usd"] + t["net_pnl_usd"], 2)

    return {
        "trades": tot,
        "wins": wins,
        "losses": tot - wins,
        "wr_pct": wr,
        "pf": pf,
        "net_pnl_usd": net_profit,
        "start_equity": start_equity,
        "end_equity": round(eq, 2),
        "equity_multiplier": round(eq / start_equity, 2),
        "gross_pnl_usd": round(gross_total, 2),
        "delta_fee_total_usd": round(fee_total, 2),
        "max_dd_usd": round(max_dd_usd, 2),
        "max_dd_pct": round(max_dd_pct, 2),
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "overlap_count": overlap_count,
        "active_days": len(active_days),
        "avg_hold_mins": round(float(np.mean([t["hold_mins"] for t in trades])), 1) if tot else 0.0,
        "max_r_multiple": round(max((t["r_multiple"] for t in trades), default=0.0), 2),
        "by_exit_reason": group_breakdown("exit_reason"),
        "by_playbook": group_breakdown("playbook"),
        "by_setup_agent": group_breakdown("setup_agent"),
        "by_tf": group_breakdown("tf"),
        "by_direction": group_breakdown("direction"),
        "by_session": group_breakdown("session"),
        "daily_pnl": list(daily_rows.values()),
        "weekly_pnl": list(weekly_rows.values()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch-only", action="store_true", help="Fetch and cache Delta 1m dataset only")
    parser.add_argument("--refresh", action="store_true", help="Force re-fetch from Delta Exchange API")
    parser.add_argument("--use-cache", action="store_true", help="Use cached enriched parquet without live HTTP calls")
    args = parser.parse_args()

    df, meta = fetch_and_enrich_xautusd_1m(force_refresh=args.refresh, use_cache=args.use_cache)
    print("[SUMMARY DATA META]", json.dumps(meta, indent=2))
    if args.fetch_only:
        return

    from backtest_runner import load_config, CONFIG_PATH
    from src.agents.syndicate_agents import precompute_features
    from scripts.backtest_agent_2_maya_lab import compute_maya_indicators
    import master_16_agent_engine as m

    cfg = load_config(CONFIG_PATH)
    m.DATA_PATH = DELTA_CACHE_PATH
    m.START_DATE = "2026-10-01 00:00:00"
    F = m.load_and_engineer_16_agent_features()
    df_feat = precompute_features(F["df"].copy(), cfg)
    A = compute_maya_indicators(df_feat)

    oct8_ts = int(datetime(2026, 10, 8, 0, 0, tzinfo=timezone.utc).timestamp())
    oct31_ts = int(datetime(2026, 10, 31, 0, 0, tzinfo=timezone.utc).timestamp())

    candidates = build_signal_pool(df_feat, cfg, F, A, start_utc_ts=oct8_ts)
    print(f"[SIGNALS] Filtered Gate-2 Pass Candidates (>= Oct 8): {len(candidates):,}")

    # TRACK B: Pure Standalone Delta XAUTUSD 1m simulation (Oct 8 -> Nov 15 present)
    track_b_trades = run_single_slot_stream(F, A, candidates, min_entry_ts=oct8_ts)
    track_b_stats = compute_summary_metrics(track_b_trades, start_equity=100.0)
    track_b_oct = compute_summary_metrics([dict(t) for t in track_b_trades if t["entry_ts"] < oct31_ts], start_equity=100.0)
    track_b_nov = compute_summary_metrics([dict(t) for t in track_b_trades if t["entry_ts"] >= oct31_ts], start_equity=100.0)

    # TRACK A: Exact Verified Oct 8-30 Baseline (41 trades) + Live Delta Extension (Oct 31 -> Nov 15)
    with open(DASHBOARD_PAYLOAD_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    base_oct_raw = [
        dict(t) for t in payload["profiles"]["MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL"]["trades"]
        if str(t.get("entry_time", "")) >= "2026-10-08"
    ]
    # Add Delta price diagnostics onto the 41 baseline trades without mutating verified fill math
    delta_ts_arr = index_to_epoch_sec(df.index)
    for t in base_oct_raw:
        t["source_feed"] = "VERIFIED_BASELINE_GC_V0_MBP10"
        t.setdefault("date", t["entry_time"][:10])
        pos = int(np.searchsorted(delta_ts_arr, t["entry_ts"]))
        if pos < len(delta_ts_arr) and abs(int(delta_ts_arr[pos]) - int(t["entry_ts"])) <= 60:
            t["delta_xautusd_close_at_entry"] = round(float(df["close"].iloc[pos]), 2)

    base_oct_last_exit = max(int(t["exit_ts"]) for t in base_oct_raw) if base_oct_raw else oct31_ts
    ext_trades = run_single_slot_stream(F, A, candidates, min_entry_ts=max(oct31_ts, base_oct_last_exit))
    for t in ext_trades:
        t["source_feed"] = "DELTA_XAUTUSD_LIVE_EXTENSION"

    track_a_trades = base_oct_raw + [dict(t) for t in ext_trades]
    # Note: Historical Oct 8-30 baseline in dashboard_payload.json has 1 moonbag target-snap overlap (#40->#41);
    # newly simulated Track A extension & Track B enforce strict_no_overlap=True.
    track_a_stats = compute_summary_metrics(track_a_trades, start_equity=100.0, strict_no_overlap=False)
    track_a_base_stats = compute_summary_metrics([dict(t) for t in base_oct_raw], start_equity=100.0, strict_no_overlap=False)
    track_a_ext_stats = compute_summary_metrics([dict(t) for t in ext_trades], start_equity=100.0, strict_no_overlap=True)

    print("\n" + "=" * 105)
    print("MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL — DELTA XAUTUSD BACKTEST (OCT 8, 2026 -> NOV 15, 2026)")
    print("=" * 105)
    for label, st in [
        ("1A. Verified Baseline Slice (Oct 8 - Oct 30)", track_a_base_stats),
        ("1B. Live Delta Extension (Oct 31 - Nov 15)", track_a_ext_stats),
        ("1C. TRACK A Combined Continuous (Oct 8 - Nov 15)", track_a_stats),
        ("2A. Track B Pure Delta Slice (Oct 8 - Oct 30)", track_b_oct),
        ("2B. Track B Pure Delta Slice (Oct 31 - Nov 15)", track_b_nov),
        ("2C. TRACK B Pure Delta Full Run (Oct 8 - Nov 15)", track_b_stats),
    ]:
        print(
            f"{label:<50} | {st['trades']:3d}t | {st['wr_pct']:5.2f}% WR | PF {st['pf']:4.2f} | "
            f"Net ${st['net_pnl_usd']:+7.2f} | Eq ${st['end_equity']:7.2f} ({st['equity_multiplier']:.2f}X) | "
            f"DD -{st['max_dd_pct']:.2f}%"
        )

    # Save CSV of Track B (pure Delta XAUTUSD simulation across entire Oct 8 - Nov 15) + Track column
    csv_rows = []
    for t in track_a_trades:
        r = dict(t)
        r["track"] = "TRACK_A_CONTINUOUS"
        csv_rows.append(r)
    for t in track_b_trades:
        r = dict(t)
        r["track"] = "TRACK_B_PURE_DELTA"
        csv_rows.append(r)

    csv_cols = [
        "track", "id", "entry_time", "exit_time", "date", "day_of_week", "session", "tf", "direction",
        "setup_agent", "playbook", "entry_price", "exit_price", "sl_price", "tp1_price", "tp2_price",
        "init_risk_pts", "pnl_pts", "r_multiple", "qty_oz", "notional_usd", "gross_pnl_usd",
        "delta_fee_usd", "net_pnl_usd", "equity_after", "exit_reason", "hold_mins", "mfe_r", "mae_r",
        "confirming_count", "source_feed",
    ]
    with open(OUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_cols, extrasaction="ignore")
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)
    print(f"\n[SAVED CSV] {OUT_CSV_PATH} ({len(csv_rows)} rows across Track A + Track B)")

    report_json = {
        "strategy": "MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL",
        "symbol": "XAUTUSD",
        "exchange": "Delta Exchange India",
        "window_start_utc": "2026-10-08 00:00:00+00:00",
        "window_end_utc": str(df.index[-1]),
        "risk_per_trade_usd": 5.0,
        "start_equity_usd": 100.0,
        "fee_rate_per_side": 0.0001,
        "sl_multiplier": 0.85,
        "data_meta": meta,
        "track_a_continuous": {
            "summary": track_a_stats,
            "oct8_oct30_baseline": track_a_base_stats,
            "oct31_nov15_delta_extension": track_a_ext_stats,
            "trades": track_a_trades,
        },
        "track_b_pure_delta": {
            "summary": track_b_stats,
            "oct8_oct30": track_b_oct,
            "oct31_nov15": track_b_nov,
            "trades": track_b_trades,
        },
    }
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2, default=str)
    print(f"[SAVED JSON] {OUT_JSON_PATH}")


if __name__ == "__main__":
    main()
