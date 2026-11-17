"""
Syndicate Alpha — Cross-Exchange Master/Slave Bridge Backtest (Oct 8 – Oct 30, 2026)
Exact Strategy: MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL ($5.00 Fixed Risk/Trade, $100 Start Equity)

Architecture:
- Master Analysis Brain: CME Gold Futures (`GC.v.0` 1m + Databento MBP-10 L2 Order Book)
  across the verified 41 trades in `2026-10-08 .. 2026-10-30`.
- Execution Venue: Delta Exchange India `XAUTUSD` 1m perpetual (`0.01%` fee per side).

Compares 4 execution modes side-by-side over the exact 41 overlapping Oct 8 – Oct 30 setups:
0. Reference Baseline: GC Master Signal & Exit -> Executed on GC.v.0
1. Bridge Mode 1 (Recommended Live Bridge): GC Master Entry & Exit Triggers -> Executed on Delta XAUTUSD
   (Intrabar basis-mapped stop/trail/TP fill clamped to Delta's real [low, high] + local Delta hard SL guard)
2. Bridge Mode 2 (Pure Market Webhook): GC Master Entry & Exit Timestamps -> Executed at Delta 1m Close
3. Bridge Mode 3 (GC Entry / Delta Trail): GC Master Entry Signal Only -> Trailed locally on Delta 1m bars
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backtest_runner import CONFIG_PATH, load_config
import master_16_agent_engine as m
from scripts.backtest_agent_2_maya_lab import compute_maya_indicators
from scripts.backtest_xautusd_oct8_to_now_mux_champion import (
    DASHBOARD_PAYLOAD_PATH,
    DELTA_CACHE_PATH,
    GC_PARQUET_PATH,
    compute_summary_metrics,
    index_to_epoch_sec,
    simulate_mux_085sl_trade,
)
from src.agents.syndicate_agents import precompute_features

OUT_JSON_PATH = os.path.join(BASE_DIR, "data", "processed", "gc_master_delta_slave_oct8_oct30_report.json")
OUT_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "trades_GC_MASTER_DELTA_SLAVE_OCT8_OCT30.csv")


def _ensure_utc_ns(df: pd.DataFrame) -> pd.DataFrame:
    if not df.index.tz:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df.index = df.index.as_unit("ns")
    return df


def _build_trade_record(
    base: dict,
    ent_px: float,
    ext_px: float,
    ent_ts: int,
    ext_ts: int,
    exit_reason: str,
    entry_idx: int,
    exit_idx: int,
    mfe_r: float,
    mae_r: float,
    fee_rate: float = 0.0001,
) -> dict:
    is_long = base["direction"] == "LONG"
    sl_dist = float(base["init_risk_pts"])
    qty = round(5.0 / sl_dist, 4)
    pnl_pts = round((ext_px - ent_px) if is_long else (ent_px - ext_px), 2)
    r_mult = round(pnl_pts / sl_dist, 2)
    gross = round(pnl_pts * qty, 2)
    fee = round(fee_rate * qty * (ent_px + ext_px), 2)
    net = round(gross - fee, 2)
    dt_ent = pd.Timestamp(ent_ts, unit="s", tz="UTC")
    dt_ext = pd.Timestamp(ext_ts, unit="s", tz="UTC")
    sl_px = round(ent_px - sl_dist if is_long else ent_px + sl_dist, 2)

    rec = dict(base)
    rec.update({
        "entry_idx": int(entry_idx),
        "exit_idx": int(exit_idx),
        "entry_ts": int(ent_ts),
        "exit_ts": int(ext_ts),
        "entry_time": dt_ent.strftime("%Y-%m-%d %H:%M UTC"),
        "exit_time": dt_ext.strftime("%Y-%m-%d %H:%M:%S+00:00"),
        "date": dt_ent.strftime("%Y-%m-%d"),
        "month": dt_ent.strftime("%Y-%m"),
        "day_of_week": dt_ent.strftime("%A"),
        "session": base.get("session", "NEW_YORK"),
        "regime": base.get("regime", "TRENDING"),
        "entry_price": round(float(ent_px), 2),
        "exit_price": round(float(ext_px), 2),
        "sl_price": sl_px,
        "init_risk_pts": sl_dist,
        "pnl_pts": pnl_pts,
        "r_multiple": r_mult,
        "qty_oz": qty,
        "notional_usd": round(qty * ent_px, 2),
        "gross_pnl_usd": gross,
        "delta_fee_usd": fee,
        "net_pnl_usd": net,
        "exit_reason": exit_reason,
        "hold_mins": int(max(1, round((ext_ts - ent_ts) / 60.0))),
        "mfe_r": round(float(mfe_r), 2),
        "mae_r": round(float(mae_r), 2),
    })
    return rec


def main():
    with open(DASHBOARD_PAYLOAD_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    gc_raw = [
        dict(t)
        for t in payload["profiles"]["MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL"]["trades"]
        if "2026-10-08" <= str(t.get("entry_time", ""))[:10] <= "2026-10-30"
    ]
    if not gc_raw:
        raise RuntimeError("No Oct 8 - Oct 30 baseline trades found in dashboard_payload.json")

    df_gc = _ensure_utc_ns(pd.read_parquet(GC_PARQUET_PATH))
    df_delta = _ensure_utc_ns(pd.read_parquet(DELTA_CACHE_PATH))

    cfg = load_config(CONFIG_PATH)
    m.DATA_PATH = DELTA_CACHE_PATH
    m.START_DATE = "2026-10-01 00:00:00"
    F = m.load_and_engineer_16_agent_features()
    df_feat = precompute_features(F["df"].copy(), cfg)
    A = compute_maya_indicators(df_feat)

    ts_sec = index_to_epoch_sec(df_feat.index)
    ts_to_idx = {int(ts): int(i) for i, ts in enumerate(ts_sec)}

    ent_matched = sum(1 for t in gc_raw if int(t["entry_ts"]) in ts_to_idx)
    ext_matched = sum(1 for t in gc_raw if int(t["exit_ts"]) in ts_to_idx)
    if ent_matched != len(gc_raw) or ext_matched != len(gc_raw):
        raise RuntimeError(f"Timestamp mismatch: entry {ent_matched}/{len(gc_raw)}, exit {ext_matched}/{len(gc_raw)}")

    baseline_trades = []
    mode1_trades = []
    mode2_trades = []
    mode3_trades = []
    comparison_rows = []
    basis_entries = []

    for i, gt in enumerate(gc_raw, 1):
        ent_ts = int(gt["entry_ts"])
        ext_ts = int(gt["exit_ts"])
        ts_e = pd.Timestamp(ent_ts, unit="s", tz="UTC")
        ts_x = pd.Timestamp(ext_ts, unit="s", tz="UTC")
        idx_e = ts_to_idx[ent_ts]
        idx_x = ts_to_idx[ext_ts]
        direction = gt["direction"]
        is_long = direction == "LONG"
        sl_dist = float(gt["init_risk_pts"])
        qty = round(5.0 / sl_dist, 4)

        # Normalize Baseline record for uniform compute_summary_metrics
        dt_ent = pd.Timestamp(ent_ts, unit="s", tz="UTC")
        base_rec = dict(gt)
        base_rec.setdefault("date", dt_ent.strftime("%Y-%m-%d"))
        base_rec.setdefault("month", dt_ent.strftime("%Y-%m"))
        base_rec.setdefault("day_of_week", dt_ent.strftime("%A"))
        base_rec.setdefault("session", gt.get("session", "NEW_YORK"))
        base_rec.setdefault("regime", gt.get("regime", "TRENDING"))
        base_rec.setdefault("mfe_r", gt.get("peak_r", max(0.0, float(gt["r_multiple"]))))
        base_rec.setdefault("mae_r", 1.0 if gt["exit_reason"] == "STOP_LOSS" else 0.0)
        baseline_trades.append(base_rec)

        d_row_e = df_delta.loc[ts_e]
        d_row_x = df_delta.loc[ts_x]
        g_row_x = df_gc.loc[ts_x] if ts_x in df_gc.index else None

        d_ent = round(float(d_row_e["close"]), 2)
        gc_ent = float(gt["entry_price"])
        gc_ext = float(gt["exit_price"])
        basis_e = round(d_ent - gc_ent, 2)
        basis_entries.append(basis_e)

        # Excursion on Delta across (ts_e, ts_x]
        sub_d_full = df_delta.loc[ts_e:ts_x]
        path_after = df_delta.loc[ts_e + pd.Timedelta(minutes=1) : ts_x]
        if len(path_after) > 0:
            if is_long:
                d_mfe = max(0.0, (float(path_after["high"].max()) - d_ent) / sl_dist)
                d_mae = min(1.0, max(0.0, (d_ent - float(path_after["low"].min())) / sl_dist))
            else:
                d_mfe = max(0.0, (d_ent - float(path_after["low"].min())) / sl_dist)
                d_mae = min(1.0, max(0.0, (float(path_after["high"].max()) - d_ent) / sl_dist))
        else:
            d_mfe, d_mae = 0.0, 0.0

        # Mode 1: Intrabar Basis-Mapped Bridge + Local Hard SL Guard
        d_sl = round(d_ent - sl_dist if is_long else d_ent + sl_dist, 2)
        hit_local_sl = False
        first_sl_ts = ext_ts
        first_sl_idx = idx_x
        if len(path_after) > 0:
            breach = (path_after["low"] <= d_sl) if is_long else (path_after["high"] >= d_sl)
            if breach.any() and gt["exit_reason"] != "STOP_LOSS":
                hit_local_sl = True
                sl_ts = breach.idxmax()
                first_sl_ts = int(sl_ts.timestamp())
                first_sl_idx = ts_to_idx[first_sl_ts]

        if hit_local_sl:
            m1_ext_px = d_sl
            m1_ext_ts = first_sl_ts
            m1_ext_idx = first_sl_idx
            m1_reason = "STOP_LOSS (DELTA_LOCAL_SL)"
        else:
            basis_x = float(d_row_x["close"] - g_row_x["close"]) if g_row_x is not None else basis_e
            est_d_fill = gc_ext + basis_x
            if ("ADAPTIVE_CHANDELIER" in gt["exit_reason"]) or ("TIME_EXTENDED" in gt["exit_reason"]):
                m1_ext_px = round(float(np.clip(est_d_fill, sub_d_full["low"].min(), sub_d_full["high"].max())), 2)
            else:
                m1_ext_px = round(float(np.clip(est_d_fill, d_row_x["low"], d_row_x["high"])), 2)
            m1_ext_ts = ext_ts
            m1_ext_idx = idx_x
            m1_reason = gt["exit_reason"]

        m1_rec = _build_trade_record(
            base_rec, d_ent, m1_ext_px, ent_ts, m1_ext_ts, m1_reason, idx_e, m1_ext_idx, d_mfe, d_mae
        )
        m1_rec["entry_basis_pts"] = basis_e
        m1_rec["source_feed"] = "GC_MASTER_DELTA_INTRABAR_BRIDGE"
        mode1_trades.append(m1_rec)

        # Mode 2: 1m Close-to-Close Market Signal Bridge
        m2_ext_px = round(float(d_row_x["close"]), 2)
        m2_rec = _build_trade_record(
            base_rec, d_ent, m2_ext_px, ent_ts, ext_ts, f"{gt['exit_reason']} (MKT_CLOSE)", idx_e, idx_x, d_mfe, d_mae
        )
        m2_rec["entry_basis_pts"] = basis_e
        m2_rec["source_feed"] = "GC_MASTER_DELTA_1M_CLOSE_BRIDGE"
        mode2_trades.append(m2_rec)

        # Mode 3: GC Entry Signal Only -> Managed Locally by Delta 1m Bars
        cand = {
            "idx": idx_e,
            "ts": ent_ts,
            "direction": direction,
            "tf": gt.get("tf", "5m"),
            "setup_agent": gt.get("setup_agent", "MUX"),
            "initiator": gt.get("initiator_16", "5:LEO"),
            "playbook": gt.get("playbook", "LEO_KILLZONE_SWEEP"),
            "orig_sl_dist": sl_dist / 0.85,
            "confirming_agents": gt.get("confirming_agents", []),
            "sess_key": gt.get("session", "NEW_YORK"),
            "regime_key": gt.get("regime", "TRENDING"),
        }
        m3_rec = simulate_mux_085sl_trade(F, A, cand, risk_usd=5.0, fee_rate=0.0001)
        m3_rec["entry_basis_pts"] = basis_e
        m3_rec["source_feed"] = "GC_ENTRY_DELTA_LOCAL_TRAIL"
        mode3_trades.append(m3_rec)

    st_base = compute_summary_metrics(baseline_trades, start_equity=100.0, strict_no_overlap=False)
    st_m1 = compute_summary_metrics(mode1_trades, start_equity=100.0, strict_no_overlap=False)
    st_m2 = compute_summary_metrics(mode2_trades, start_equity=100.0, strict_no_overlap=False)
    st_m3 = compute_summary_metrics(mode3_trades, start_equity=100.0, strict_no_overlap=False)

    # Build side-by-side comparison CSV rows after equity curves are populated
    for i in range(len(baseline_trades)):
        b, m1, m2, m3 = baseline_trades[i], mode1_trades[i], mode2_trades[i], mode3_trades[i]
        comparison_rows.append({
            "id": i + 1,
            "entry_time": b["entry_time"],
            "exit_time_gc": b["exit_time"],
            "tf": b["tf"],
            "direction": b["direction"],
            "setup_agent": b["setup_agent"],
            "playbook": b["playbook"],
            "exit_reason_gc": b["exit_reason"],
            "init_risk_pts": b["init_risk_pts"],
            "gc_entry_px": b["entry_price"],
            "gc_exit_px": b["exit_price"],
            "gc_pnl_pts": b["pnl_pts"],
            "gc_r_multiple": b["r_multiple"],
            "gc_net_usd": b["net_pnl_usd"],
            "gc_eq_after": b["equity_after"],
            "delta_entry_px": m1["entry_price"],
            "entry_basis_pts": m1["entry_basis_pts"],
            "mode1_delta_exit_px": m1["exit_price"],
            "mode1_pnl_pts": m1["pnl_pts"],
            "mode1_r_multiple": m1["r_multiple"],
            "mode1_net_usd": m1["net_pnl_usd"],
            "mode1_eq_after": m1["equity_after"],
            "mode2_delta_close_exit_px": m2["exit_price"],
            "mode2_pnl_pts": m2["pnl_pts"],
            "mode2_r_multiple": m2["r_multiple"],
            "mode2_net_usd": m2["net_pnl_usd"],
            "mode2_eq_after": m2["equity_after"],
            "mode3_delta_local_exit_px": m3["exit_price"],
            "mode3_exit_reason": m3["exit_reason"],
            "mode3_pnl_pts": m3["pnl_pts"],
            "mode3_r_multiple": m3["r_multiple"],
            "mode3_net_usd": m3["net_pnl_usd"],
            "mode3_eq_after": m3["equity_after"],
        })

    fieldnames = list(comparison_rows[0].keys())
    with open(OUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(comparison_rows)

    # Build day-by-day calendar comparison
    d_base = {r["date"]: r for r in st_base["daily_pnl"]}
    d_m1 = {r["date"]: r for r in st_m1["daily_pnl"]}
    d_m2 = {r["date"]: r for r in st_m2["daily_pnl"]}
    d_m3 = {r["date"]: r for r in st_m3["daily_pnl"]}
    daily_cmp = []
    for dt_str in sorted(d_base.keys()):
        rb = d_base[dt_str]
        r1 = d_m1.get(dt_str, {})
        r2 = d_m2.get(dt_str, {})
        r3 = d_m3.get(dt_str, {})
        daily_cmp.append({
            "date": dt_str,
            "day": rb["day"],
            "trades": rb["trades"],
            "gc_wins": rb["wins"],
            "gc_net_usd": rb["net_pnl_usd"],
            "m1_wins": r1.get("wins", 0),
            "m1_net_usd": r1.get("net_pnl_usd", 0.0),
            "m2_wins": r2.get("wins", 0),
            "m2_net_usd": r2.get("net_pnl_usd", 0.0),
            "m3_wins": r3.get("wins", 0),
            "m3_net_usd": r3.get("net_pnl_usd", 0.0),
        })

    print("\n" + "=" * 112)
    print("GC MASTER BRAIN (DATABENTO MBP-10) -> DELTA EXCHANGE XAUTUSD SLAVE EXECUTION (OCT 8 - OCT 30, 2026)")
    print("=" * 112)
    for label, st in [
        ("0. Baseline: GC Brain -> Executed on GC.v.0", st_base),
        ("1. Bridge Mode 1: GC Entry+Exit -> Delta Intrabar", st_m1),
        ("2. Bridge Mode 2: GC Entry+Exit -> Delta 1m Close", st_m2),
        ("3. Bridge Mode 3: GC Entry Only -> Delta Local Trail", st_m3),
    ]:
        print(
            f"{label:<52} | {st['trades']:2d}t | {st['wr_pct']:5.2f}% WR | PF {st['pf']:4.2f} | "
            f"Net ${st['net_pnl_usd']:+7.2f} | Eq ${st['end_equity']:7.2f} ({st['equity_multiplier']:.2f}X) | "
            f"Fees ${st['delta_fee_total_usd']:5.2f} | DD -{st['max_dd_pct']:.2f}%"
        )

    print("\n--- DAY-BY-DAY COMPARISON (OCT 8 - OCT 30, 2026) ---")
    print(f"{'Date':<10} | {'Day':<9} | {'T':>2} | {'GC Base':>16} | {'M1 Intrabar':>16} | {'M2 1m Close':>16} | {'M3 Local Trail':>16}")
    print("-" * 98)
    for r in daily_cmp:
        print(
            f"{r['date']} | {r['day']:<9} | {r['trades']:2d} | "
            f"{r['gc_wins']:2d}W ${r['gc_net_usd']:+7.2f}    | "
            f"{r['m1_wins']:2d}W ${r['m1_net_usd']:+7.2f}    | "
            f"{r['m2_wins']:2d}W ${r['m2_net_usd']:+7.2f}    | "
            f"{r['m3_wins']:2d}W ${r['m3_net_usd']:+7.2f}"
        )

    report = {
        "strategy": "MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL",
        "architecture": "GC.v.0 Master Signal Brain (Databento MBP-10 L2) -> Delta Exchange India XAUTUSD Execution",
        "window": "2026-10-08 00:00:00+00:00 -> 2026-10-30 20:59:00+00:00",
        "risk_per_trade_usd": 5.0,
        "start_equity_usd": 100.0,
        "fee_rate_per_side": 0.0001,
        "entry_basis_stats_pts": {
            "mean": round(float(np.mean(basis_entries)), 2),
            "median": round(float(np.median(basis_entries)), 2),
            "min": round(float(np.min(basis_entries)), 2),
            "max": round(float(np.max(basis_entries)), 2),
        },
        "modes": {
            "0_gc_baseline": {k: v for k, v in st_base.items() if k not in ("daily_pnl", "weekly_pnl")},
            "1_delta_intrabar_bridge": {k: v for k, v in st_m1.items() if k not in ("daily_pnl", "weekly_pnl")},
            "2_delta_1m_close_bridge": {k: v for k, v in st_m2.items() if k not in ("daily_pnl", "weekly_pnl")},
            "3_delta_local_trail": {k: v for k, v in st_m3.items() if k not in ("daily_pnl", "weekly_pnl")},
        },
        "daily_comparison": daily_cmp,
        "weekly_comparison": {
            "0_gc_baseline": st_base["weekly_pnl"],
            "1_delta_intrabar_bridge": st_m1["weekly_pnl"],
            "2_delta_1m_close_bridge": st_m2["weekly_pnl"],
            "3_delta_local_trail": st_m3["weekly_pnl"],
        },
        "trade_comparison": comparison_rows,
    }
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n[SAVED CSV]  {OUT_CSV_PATH}")
    print(f"[SAVED JSON] {OUT_JSON_PATH}")


if __name__ == "__main__":
    main()
