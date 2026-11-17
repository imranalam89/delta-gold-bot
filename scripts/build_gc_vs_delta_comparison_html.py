"""
Builds a dedicated, standalone, offline-ready institutional HTML Backtest & Comparison Report:
  `backtest_DELTA_vs_GC_COMPARISON.html`

Compares exact `MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL` ($5.00 risk/trade, $100 start equity,
0.01% per-side fee) performance across:
1. Delta Exchange XAUTUSD Standalone Backtest (Oct 8 - Oct 30 overlap & Oct 8 - Nov 15 full)
2. CME Gold Futures (GC.v.0 + Databento MBP-10 L2) Reference Baseline (Oct 8 - Oct 30 & 5-Month)
3. Hybrid Master-Slave Bridge: GC Analysis Brain -> Delta XAUTUSD Execution (Oct 8 - Oct 30)

Includes Day-to-Day, Weekly, Monthly Calendar Heatmap, Mechanics Breakdown,
and Trade-by-Trade Auditor + CSV export.
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELTA_JSON_PATH = os.path.join(BASE_DIR, "data", "processed", "xautusd_oct8_to_now_mux_085sl_adaptive_chandelier.json")
BRIDGE_JSON_PATH = os.path.join(BASE_DIR, "data", "processed", "gc_master_delta_slave_oct8_oct30_report.json")
MASTER_JSON_PATH = os.path.join(BASE_DIR, "data", "processed", "dashboard_payload.json")
OUT_HTML_PATH = os.path.join(BASE_DIR, "backtest_DELTA_vs_GC_COMPARISON.html")


def _compute_trade_stats(trades: list, start_equity: float = 100.0) -> dict:
    tot = len(trades)
    wins_list = [t for t in trades if float(t.get("net_pnl_usd", 0.0)) > 0]
    losses_list = [t for t in trades if float(t.get("net_pnl_usd", 0.0)) <= 0]
    gross_wins = sum(float(t.get("net_pnl_usd", 0.0)) for t in wins_list)
    gross_losses = abs(sum(float(t.get("net_pnl_usd", 0.0)) for t in losses_list))
    pf = round(gross_wins / gross_losses, 2) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)
    net_total = round(sum(float(t.get("net_pnl_usd", 0.0)) for t in trades), 2)
    gross_total = round(sum(float(t.get("gross_pnl_usd", 0.0)) for t in trades), 2)
    fee_total = round(sum(float(t.get("delta_fee_usd", 0.0)) for t in trades), 2)
    avg_win = round(gross_wins / len(wins_list), 2) if wins_list else 0.0
    avg_loss = round(-gross_losses / len(losses_list), 2) if losses_list else 0.0
    avg_r = round(sum(float(t.get("r_multiple", 0.0)) for t in trades) / tot, 2) if tot else 0.0
    max_r = round(max((float(t.get("r_multiple", 0.0)) for t in trades), default=0.0), 2)
    avg_hold = round(sum(float(t.get("hold_mins", 0.0)) for t in trades) / tot, 1) if tot else 0.0

    eq = start_equity
    peak = start_equity
    max_dd_usd = 0.0
    max_dd_pct = 0.0
    for t in trades:
        eq = round(eq + float(t.get("net_pnl_usd", 0.0)), 2)
        if eq > peak:
            peak = eq
        dd_usd = round(peak - eq, 2)
        dd_pct = round((dd_usd / peak) * 100.0, 2) if peak > 0 else 0.0
        if dd_usd > max_dd_usd:
            max_dd_usd = dd_usd
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct

    return {
        "trades": tot,
        "wins": len(wins_list),
        "losses": len(losses_list),
        "wr_pct": round((len(wins_list) / tot) * 100.0, 2) if tot else 0.0,
        "pf": pf,
        "gross_pnl_usd": gross_total,
        "delta_fee_total_usd": fee_total,
        "net_pnl_usd": net_total,
        "start_equity": start_equity,
        "end_equity": round(start_equity + net_total, 2),
        "equity_multiplier": round((start_equity + net_total) / start_equity, 2),
        "max_dd_usd": max_dd_usd,
        "max_dd_pct": max_dd_pct,
        "avg_win_usd": avg_win,
        "avg_loss_usd": avg_loss,
        "avg_r": avg_r,
        "max_r_multiple": max_r,
        "avg_hold_mins": avg_hold,
    }


def _group_trades_by(trades: list, field: str) -> dict:
    buckets = defaultdict(list)
    for t in trades:
        key = str(t.get(field) or "UNKNOWN")
        buckets[key].append(t)
    out = {}
    for k, items in sorted(buckets.items(), key=lambda kv: sum(float(x.get("net_pnl_usd", 0.0)) for x in kv[1]), reverse=True):
        tot = len(items)
        wins = sum(1 for x in items if float(x.get("net_pnl_usd", 0.0)) > 0)
        net = round(sum(float(x.get("net_pnl_usd", 0.0)) for x in items), 2)
        avg_r = round(sum(float(x.get("r_multiple", 0.0)) for x in items) / tot, 2) if tot else 0.0
        out[k] = {
            "trades": tot,
            "wins": wins,
            "losses": tot - wins,
            "wr_pct": round((wins / tot) * 100.0, 2) if tot else 0.0,
            "avg_r": avg_r,
            "net_pnl_usd": net,
        }
    return out


def _iso_week(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    iso = dt.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _day_name(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")


def _summarize_day_driver(gc_day_trades: list, delta_day_trades: list, period: str) -> str:
    if period == "OCT1_7_PRE":
        return "Pre-Oct 8 GC reference only (Delta L2 capture began Oct 8)"
    if period == "OCT31_NOV15_EXT":
        if not delta_day_trades:
            return "No qualified triggers"
        sl_cnt = sum(1 for t in delta_day_trades if "STOP_LOSS" in str(t.get("exit_reason", "")))
        win_reasons = [str(t.get("exit_reason", "")) for t in delta_day_trades if float(t.get("net_pnl_usd", 0.0)) > 0]
        if "ADAPTIVE_CHANDELIER_40R_TRAIL" in win_reasons:
            return "Post-Oct 30 Delta L2 proxy: Chandelier runner captured trend"
        if sl_cnt >= 2:
            return f"Post-Oct 30 Delta L2 proxy: {sl_cnt}x 0.85x SL chop without CME L2 filter"
        return "Post-Oct 30 Delta-only L2 proxy window"

    # Overlap Oct 8 - Oct 30 driver explanation
    gc_net = sum(float(t.get("net_pnl_usd", 0.0)) for t in gc_day_trades)
    d_net = sum(float(t.get("net_pnl_usd", 0.0)) for t in delta_day_trades)
    gc_reasons = {str(t.get("exit_reason", "")) for t in gc_day_trades}
    d_sl = sum(1 for t in delta_day_trades if "STOP_LOSS" in str(t.get("exit_reason", "")))
    d_stall = sum(1 for t in delta_day_trades if str(t.get("exit_reason", "")) in ("SMART_STALL_LOCK", "BREAKEVEN"))

    if "ADAPTIVE_CHANDELIER_40R_TRAIL" in gc_reasons and gc_net - d_net > 10:
        return "GC 40R Chandelier runner stayed live; Delta wicks exited early"
    if "TIME_EXTENDED_CHANDELIER_RUNNER" in gc_reasons and gc_net - d_net > 8:
        return "GC Time-Extended Chandelier rode swing; Delta capped smaller"
    if d_sl >= 2 and len(gc_day_trades) < len(delta_day_trades):
        return "CME MBP-10 blocked false sweep entries that stopped out on Delta"
    if d_net < 0 and gc_net > 0:
        return "Delta local chop vs CME institutional continuation"
    if d_stall >= 2 and gc_net > d_net:
        return "Delta Smart Stall/BE clipped momentum prematurely"
    if d_net > gc_net + 5:
        return "Delta standalone triggered extra winning scalp leg"
    return "Aligned directional flow across both feeds"


def build_payload() -> dict:
    with open(DELTA_JSON_PATH, "r", encoding="utf-8") as f:
        p1 = json.load(f)
    with open(BRIDGE_JSON_PATH, "r", encoding="utf-8") as f:
        p2 = json.load(f)
    with open(MASTER_JSON_PATH, "r", encoding="utf-8") as f:
        p3 = json.load(f)

    master_profile = p3["profiles"]["MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL"]
    gc_all_5mo_trades = master_profile["trades"]
    gc_oct_all_trades = [dict(t) for t in gc_all_5mo_trades if str(t.get("entry_time", "")) >= "2026-10-01"]
    gc_oct1_7_trades = [dict(t) for t in gc_oct_all_trades if str(t.get("entry_time", "")) < "2026-10-08"]
    gc_oct8_30_trades = [dict(t) for t in gc_oct_all_trades if str(t.get("entry_time", "")) >= "2026-10-08"]

    # Reconstruct individual mode trade lists from p2["trade_comparison"]
    trade_comp = p2["trade_comparison"]
    bridge_m1_trades = []
    bridge_m2_trades = []
    bridge_m3_trades = []
    for i, tc in enumerate(trade_comp):
        gc_base = gc_oct8_30_trades[i] if i < len(gc_oct8_30_trades) else {}
        date_str = str(tc["entry_time"])[:10]
        sl_pts = float(tc["init_risk_pts"])
        qty = float(gc_base.get("qty_oz", round(5.0 / sl_pts, 4)))

        def _make_mode_trade(exit_px, pnl_pts, r_mult, net_usd, eq_after, exit_reason):
            gross = round(pnl_pts * qty, 2)
            fee = round(gross - net_usd, 2)
            return {
                "id": tc["id"],
                "entry_time": tc["entry_time"],
                "exit_time": tc["exit_time_gc"],
                "date": date_str,
                "day_of_week": _day_name(date_str),
                "tf": tc["tf"],
                "direction": tc["direction"],
                "session": gc_base.get("session", "NEW_YORK"),
                "setup_agent": tc["setup_agent"],
                "playbook": tc["playbook"],
                "entry_price": tc["delta_entry_px"],
                "exit_price": exit_px,
                "init_risk_pts": sl_pts,
                "pnl_pts": pnl_pts,
                "r_multiple": r_mult,
                "qty_oz": qty,
                "gross_pnl_usd": gross,
                "delta_fee_usd": fee,
                "net_pnl_usd": net_usd,
                "equity_after": eq_after,
                "exit_reason": exit_reason,
                "hold_mins": gc_base.get("hold_mins", 60),
                "entry_basis_pts": tc["entry_basis_pts"],
            }

        bridge_m1_trades.append(_make_mode_trade(tc["mode1_delta_exit_px"], tc["mode1_pnl_pts"], tc["mode1_r_multiple"], tc["mode1_net_usd"], tc["mode1_eq_after"], tc["exit_reason_gc"]))
        bridge_m2_trades.append(_make_mode_trade(tc["mode2_delta_close_exit_px"], tc["mode2_pnl_pts"], tc["mode2_r_multiple"], tc["mode2_net_usd"], tc["mode2_eq_after"], tc["exit_reason_gc"]))
        bridge_m3_trades.append(_make_mode_trade(tc["mode3_delta_local_exit_px"], tc["mode3_pnl_pts"], tc["mode3_r_multiple"], tc["mode3_net_usd"], tc["mode3_eq_after"], tc["mode3_exit_reason"]))

    delta_all_trades = [dict(t) for t in p1["track_b_pure_delta"]["trades"]]
    delta_oct8_30_trades = [t for t in delta_all_trades if str(t.get("entry_time", "")) < "2026-10-31"]
    delta_oct31_nov15_trades = [t for t in delta_all_trades if str(t.get("entry_time", "")) >= "2026-10-31"]
    track_a_all_trades = [dict(t) for t in p1["track_a_continuous"]["trades"]]

    # Enrich summary dicts from JSON + computed avg metrics
    s_gc_5mo = _compute_trade_stats(gc_all_5mo_trades)
    s_gc_5mo["max_dd_pct"] = master_profile["meta"]["full_metrics"]["max_dd_pct"]
    s_gc_5mo["max_dd_usd"] = master_profile["meta"]["full_metrics"]["max_dd_usd"]
    s_gc_5mo["active_days"] = master_profile["meta"]["full_metrics"]["active_days"]

    s_gc_oct_all = _compute_trade_stats(gc_oct_all_trades)
    s_gc_overlap = dict(p2["modes"]["0_gc_baseline"])
    s_gc_overlap.update({k: v for k, v in _compute_trade_stats(gc_oct8_30_trades).items() if k in ("avg_win_usd", "avg_loss_usd", "avg_r")})

    s_m1 = dict(p2["modes"]["1_delta_intrabar_bridge"])
    s_m1.update({k: v for k, v in _compute_trade_stats(bridge_m1_trades).items() if k in ("avg_win_usd", "avg_loss_usd", "avg_r")})

    s_m2 = dict(p2["modes"]["2_delta_1m_close_bridge"])
    s_m2.update({k: v for k, v in _compute_trade_stats(bridge_m2_trades).items() if k in ("avg_win_usd", "avg_loss_usd", "avg_r")})

    s_m3 = dict(p2["modes"]["3_delta_local_trail"])
    s_m3.update({k: v for k, v in _compute_trade_stats(bridge_m3_trades).items() if k in ("avg_win_usd", "avg_loss_usd", "avg_r")})

    s_delta_overlap = dict(p1["track_b_pure_delta"]["oct8_oct30"])
    s_delta_overlap.update({k: v for k, v in _compute_trade_stats(delta_oct8_30_trades).items() if k in ("avg_win_usd", "avg_loss_usd", "avg_r")})

    s_delta_ext = dict(p1["track_b_pure_delta"]["oct31_nov15"])
    s_delta_ext.update({k: v for k, v in _compute_trade_stats(delta_oct31_nov15_trades).items() if k in ("avg_win_usd", "avg_loss_usd", "avg_r")})

    s_delta_full = dict(p1["track_b_pure_delta"]["summary"])
    s_delta_full.update({k: v for k, v in _compute_trade_stats(delta_all_trades).items() if k in ("avg_win_usd", "avg_loss_usd", "avg_r")})

    s_track_a_full = dict(p1["track_a_continuous"]["summary"])
    s_track_a_full.update({k: v for k, v in _compute_trade_stats(track_a_all_trades).items() if k in ("avg_win_usd", "avg_loss_usd", "avg_r")})

    # Day-to-day aggregation across Oct 1 -> Nov 15
    by_day_gc = defaultdict(list)
    for t in gc_oct_all_trades:
        by_day_gc[str(t.get("date") or str(t["entry_time"])[:10])].append(t)

    by_day_m1 = defaultdict(list)
    for t in bridge_m1_trades:
        by_day_m1[t["date"]].append(t)

    by_day_m2 = defaultdict(list)
    for t in bridge_m2_trades:
        by_day_m2[t["date"]].append(t)

    by_day_delta = defaultdict(list)
    for t in delta_all_trades:
        by_day_delta[str(t.get("date") or str(t["entry_time"])[:10])].append(t)

    by_day_track_a = defaultdict(list)
    for t in track_a_all_trades:
        by_day_track_a[str(t.get("date") or str(t["entry_time"])[:10])].append(t)

    all_dates = sorted(set(list(by_day_gc.keys()) + list(by_day_delta.keys()) + list(by_day_track_a.keys())))

    daily_rows = []
    cum_gc_overlap = 100.0
    cum_m1_overlap = 100.0
    cum_delta_full = 100.0
    cum_track_a = 100.0

    for d in all_dates:
        if d < "2026-10-08":
            period = "OCT1_7_PRE"
        elif d <= "2026-10-30":
            period = "OCT8_30_OVERLAP"
        else:
            period = "OCT31_NOV15_EXT"

        g_list = by_day_gc.get(d, [])
        m1_list = by_day_m1.get(d, [])
        m2_list = by_day_m2.get(d, [])
        del_list = by_day_delta.get(d, [])
        ta_list = by_day_track_a.get(d, [])

        gc_net = round(sum(float(x.get("net_pnl_usd", 0.0)) for x in g_list), 2)
        gc_gross = round(sum(float(x.get("gross_pnl_usd", 0.0)) for x in g_list), 2)
        gc_fee = round(sum(float(x.get("delta_fee_usd", 0.0)) for x in g_list), 2)
        gc_wins = sum(1 for x in g_list if float(x.get("net_pnl_usd", 0.0)) > 0)

        m1_net = round(sum(float(x.get("net_pnl_usd", 0.0)) for x in m1_list), 2)
        m1_wins = sum(1 for x in m1_list if float(x.get("net_pnl_usd", 0.0)) > 0)
        m2_net = round(sum(float(x.get("net_pnl_usd", 0.0)) for x in m2_list), 2)

        d_net = round(sum(float(x.get("net_pnl_usd", 0.0)) for x in del_list), 2)
        d_gross = round(sum(float(x.get("gross_pnl_usd", 0.0)) for x in del_list), 2)
        d_fee = round(sum(float(x.get("delta_fee_usd", 0.0)) for x in del_list), 2)
        d_wins = sum(1 for x in del_list if float(x.get("net_pnl_usd", 0.0)) > 0)

        ta_net = round(sum(float(x.get("net_pnl_usd", 0.0)) for x in ta_list), 2)
        ta_wins = sum(1 for x in ta_list if float(x.get("net_pnl_usd", 0.0)) > 0)

        if period == "OCT8_30_OVERLAP":
            cum_gc_overlap = round(cum_gc_overlap + gc_net, 2)
            cum_m1_overlap = round(cum_m1_overlap + m1_net, 2)
        if period in ("OCT8_30_OVERLAP", "OCT31_NOV15_EXT"):
            cum_delta_full = round(cum_delta_full + d_net, 2)
            cum_track_a = round(cum_track_a + ta_net, 2)

        daily_rows.append({
            "date": d,
            "day": _day_name(d),
            "week": _iso_week(d),
            "period": period,
            "gc_trades": len(g_list),
            "gc_wins": gc_wins,
            "gc_losses": len(g_list) - gc_wins,
            "gc_gross": gc_gross,
            "gc_fees": gc_fee,
            "gc_net": gc_net,
            "gc_cum_eq": cum_gc_overlap if period == "OCT8_30_OVERLAP" else None,
            "m1_trades": len(m1_list),
            "m1_wins": m1_wins,
            "m1_losses": len(m1_list) - m1_wins,
            "m1_net": m1_net,
            "m1_cum_eq": cum_m1_overlap if period == "OCT8_30_OVERLAP" else None,
            "m2_net": m2_net,
            "delta_trades": len(del_list),
            "delta_wins": d_wins,
            "delta_losses": len(del_list) - d_wins,
            "delta_gross": d_gross,
            "delta_fees": d_fee,
            "delta_net": d_net,
            "delta_cum_eq": cum_delta_full if period != "OCT1_7_PRE" else None,
            "ta_trades": len(ta_list),
            "ta_wins": ta_wins,
            "ta_net": ta_net,
            "ta_cum_eq": cum_track_a if period != "OCT1_7_PRE" else None,
            "diff_gc_minus_delta": round(gc_net - d_net, 2) if period == "OCT8_30_OVERLAP" else None,
            "diff_m1_minus_delta": round(m1_net - d_net, 2) if period == "OCT8_30_OVERLAP" else None,
            "driver": _summarize_day_driver(g_list, del_list, period),
        })

    # Weekly comparison rows (from Oct 8 onward + W40/W41 full Oct reference note)
    week_ranges = {
        "2026-W40": "Oct 01 – Oct 02 (Pre-Delta)",
        "2026-W41": "Oct 08 – Oct 09 (Overlap Start)*",
        "2026-W42": "Oct 12 – Oct 16 (Overlap Wk 2)",
        "2026-W43": "Oct 19 – Oct 23 (Overlap Wk 3)",
        "2026-W44": "Oct 26 – Oct 30 (Overlap Wk 4)",
        "2026-W45": "Nov 02 – Nov 06 (Delta Proxy Ext)",
        "2026-W46": "Nov 09 – Nov 13 (Delta Proxy Ext)",
    }
    weekly_rows = []
    for wk, label in week_ranges.items():
        if wk == "2026-W40":
            rows = [r for r in daily_rows if r["week"] == wk]
            period = "PRE_OVERLAP"
        elif wk in ("2026-W41", "2026-W42", "2026-W43", "2026-W44"):
            rows = [r for r in daily_rows if r["week"] == wk and r["period"] == "OCT8_30_OVERLAP"]
            period = "OVERLAP"
        else:
            rows = [r for r in daily_rows if r["week"] == wk and r["period"] == "OCT31_NOV15_EXT"]
            period = "EXTENSION"

        gc_t = sum(r["gc_trades"] for r in rows)
        gc_w = sum(r["gc_wins"] for r in rows)
        gc_gross = round(sum(r["gc_gross"] for r in rows), 2)
        gc_fee = round(sum(r["gc_fees"] for r in rows), 2)
        gc_net = round(sum(r["gc_net"] for r in rows), 2)

        m1_t = sum(r["m1_trades"] for r in rows)
        m1_w = sum(r["m1_wins"] for r in rows)
        m1_net = round(sum(r["m1_net"] for r in rows), 2)

        d_t = sum(r["delta_trades"] for r in rows)
        d_w = sum(r["delta_wins"] for r in rows)
        d_gross = round(sum(r["delta_gross"] for r in rows), 2)
        d_fee = round(sum(r["delta_fees"] for r in rows), 2)
        d_net = round(sum(r["delta_net"] for r in rows), 2)

        ta_t = sum(r["ta_trades"] for r in rows)
        ta_w = sum(r["ta_wins"] for r in rows)
        ta_net = round(sum(r["ta_net"] for r in rows), 2)

        weekly_rows.append({
            "week": wk,
            "label": label,
            "period": period,
            "gc_trades": gc_t,
            "gc_wins": gc_w,
            "gc_wr": round((gc_w / gc_t) * 100, 1) if gc_t else 0.0,
            "gc_gross": gc_gross,
            "gc_fees": gc_fee,
            "gc_net": gc_net,
            "m1_trades": m1_t,
            "m1_wins": m1_w,
            "m1_wr": round((m1_w / m1_t) * 100, 1) if m1_t else 0.0,
            "m1_net": m1_net,
            "delta_trades": d_t,
            "delta_wins": d_w,
            "delta_wr": round((d_w / d_t) * 100, 1) if d_t else 0.0,
            "delta_gross": d_gross,
            "delta_fees": d_fee,
            "delta_net": d_net,
            "ta_trades": ta_t,
            "ta_wins": ta_w,
            "ta_net": ta_net,
            "diff_gc_vs_delta": round(gc_net - d_net, 2) if period == "OVERLAP" else None,
            "diff_m1_vs_delta": round(m1_net - d_net, 2) if period == "OVERLAP" else None,
        })

    # Equity curve points for Canvas
    def _build_eq_series(trades, start_eq=100.0):
        pts = [{"idx": 0, "ts": "2026-10-08 00:00", "date": "2026-10-08", "eq": start_eq, "dd_pct": 0.0, "net": 0.0, "reason": "START"}]
        eq = start_eq
        peak = start_eq
        for idx, t in enumerate(trades, 1):
            eq = round(eq + float(t.get("net_pnl_usd", 0.0)), 2)
            if eq > peak:
                peak = eq
            dd_pct = round(-((peak - eq) / peak) * 100.0, 2) if peak > 0 else 0.0
            pts.append({
                "idx": idx,
                "ts": str(t.get("entry_time", ""))[:16],
                "date": str(t.get("date") or str(t.get("entry_time", ""))[:10]),
                "eq": eq,
                "dd_pct": dd_pct,
                "net": round(float(t.get("net_pnl_usd", 0.0)), 2),
                "reason": str(t.get("exit_reason", "")),
                "dir": str(t.get("direction", "")),
                "r": round(float(t.get("r_multiple", 0.0)), 2),
            })
        return pts

    # Daily equity curve aligned by date for direct apples-to-apples chart comparison
    overlap_daily = [r for r in daily_rows if r["period"] == "OCT8_30_OVERLAP"]
    full_daily = [r for r in daily_rows if r["period"] != "OCT1_7_PRE"]

    daily_eq_series = {
        "dates": ["2026-10-07 (Start)"] + [r["date"] for r in full_daily],
        "gc_overlap_eq": [100.0] + [r["gc_cum_eq"] for r in overlap_daily],
        "m1_overlap_eq": [100.0] + [r["m1_cum_eq"] for r in overlap_daily],
        "delta_full_eq": [100.0] + [r["delta_cum_eq"] for r in full_daily],
        "track_a_full_eq": [100.0] + [r["ta_cum_eq"] for r in full_daily],
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "strategy": p1.get("strategy", "MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL"),
        "params": {
            "risk_per_trade_usd": 5.0,
            "start_equity_usd": 100.0,
            "fee_rate_per_side_pct": 0.01,
            "sl_atr_multiplier": 0.85,
            "data_meta": p1.get("data_meta", {}),
            "entry_basis_stats_pts": p2.get("entry_basis_stats_pts", {}),
        },
        "summaries": {
            "gc_overlap": s_gc_overlap,
            "bridge_m1": s_m1,
            "bridge_m2": s_m2,
            "bridge_m3": s_m3,
            "delta_overlap": s_delta_overlap,
            "delta_ext": s_delta_ext,
            "delta_full": s_delta_full,
            "track_a_full": s_track_a_full,
            "gc_5mo": s_gc_5mo,
            "gc_oct_all": s_gc_oct_all,
        },
        "breakdowns": {
            "exit_reason": {
                "gc_overlap": _group_trades_by(gc_oct8_30_trades, "exit_reason"),
                "bridge_m1": _group_trades_by(bridge_m1_trades, "exit_reason"),
                "delta_overlap": _group_trades_by(delta_oct8_30_trades, "exit_reason"),
                "delta_full": _group_trades_by(delta_all_trades, "exit_reason"),
            },
            "playbook": {
                "gc_overlap": _group_trades_by(gc_oct8_30_trades, "playbook"),
                "bridge_m1": _group_trades_by(bridge_m1_trades, "playbook"),
                "delta_overlap": _group_trades_by(delta_oct8_30_trades, "playbook"),
                "delta_full": _group_trades_by(delta_all_trades, "playbook"),
            },
            "session": {
                "gc_overlap": _group_trades_by(gc_oct8_30_trades, "session"),
                "bridge_m1": _group_trades_by(bridge_m1_trades, "session"),
                "delta_overlap": _group_trades_by(delta_oct8_30_trades, "session"),
                "delta_full": _group_trades_by(delta_all_trades, "session"),
            },
            "day_of_week": {
                "gc_overlap": _group_trades_by(gc_oct8_30_trades, "day_of_week"),
                "bridge_m1": _group_trades_by(bridge_m1_trades, "day_of_week"),
                "delta_overlap": _group_trades_by(delta_oct8_30_trades, "day_of_week"),
                "delta_full": _group_trades_by(delta_all_trades, "day_of_week"),
            },
        },
        "daily_rows": daily_rows,
        "weekly_rows": weekly_rows,
        "equity_curves": {
            "gc_overlap": _build_eq_series(gc_oct8_30_trades),
            "bridge_m1": _build_eq_series(bridge_m1_trades),
            "delta_overlap": _build_eq_series(delta_oct8_30_trades),
            "delta_full": _build_eq_series(delta_all_trades),
            "track_a_full": _build_eq_series(track_a_all_trades),
            "daily_aligned": daily_eq_series,
        },
        "trades": {
            "matched_overlap_41": trade_comp,
            "delta_full_71": [
                {
                    "id": i + 1,
                    "entry_time": str(t.get("entry_time", ""))[:19],
                    "exit_time": str(t.get("exit_time", ""))[:19],
                    "date": str(t.get("date") or str(t.get("entry_time", ""))[:10]),
                    "day_of_week": t.get("day_of_week", ""),
                    "session": t.get("session", ""),
                    "tf": t.get("tf", ""),
                    "direction": t.get("direction", ""),
                    "setup_agent": t.get("setup_agent", ""),
                    "playbook": t.get("playbook", ""),
                    "entry_price": t.get("entry_price", 0),
                    "exit_price": t.get("exit_price", 0),
                    "sl_price": t.get("sl_price", 0),
                    "init_risk_pts": t.get("init_risk_pts", 0),
                    "pnl_pts": t.get("pnl_pts", 0),
                    "r_multiple": t.get("r_multiple", 0),
                    "qty_oz": t.get("qty_oz", 0),
                    "gross_pnl_usd": t.get("gross_pnl_usd", 0),
                    "delta_fee_usd": t.get("delta_fee_usd", 0),
                    "net_pnl_usd": t.get("net_pnl_usd", 0),
                    "equity_after": t.get("equity_after", 0),
                    "exit_reason": t.get("exit_reason", ""),
                    "hold_mins": t.get("hold_mins", 0),
                    "source_feed": t.get("source_feed", ""),
                }
                for i, t in enumerate(delta_all_trades)
            ],
            "track_a_68": [
                {
                    "id": i + 1,
                    "entry_time": str(t.get("entry_time", ""))[:19],
                    "exit_time": str(t.get("exit_time", ""))[:19],
                    "date": str(t.get("date") or str(t.get("entry_time", ""))[:10]),
                    "day_of_week": t.get("day_of_week", ""),
                    "session": t.get("session", ""),
                    "tf": t.get("tf", ""),
                    "direction": t.get("direction", ""),
                    "setup_agent": t.get("setup_agent", ""),
                    "playbook": t.get("playbook", ""),
                    "entry_price": t.get("entry_price", 0),
                    "exit_price": t.get("exit_price", 0),
                    "init_risk_pts": t.get("init_risk_pts", 0),
                    "pnl_pts": t.get("pnl_pts", 0),
                    "r_multiple": t.get("r_multiple", 0),
                    "qty_oz": t.get("qty_oz", 0),
                    "gross_pnl_usd": t.get("gross_pnl_usd", 0),
                    "delta_fee_usd": t.get("delta_fee_usd", 0),
                    "net_pnl_usd": t.get("net_pnl_usd", 0),
                    "equity_after": t.get("equity_after", 0),
                    "exit_reason": t.get("exit_reason", ""),
                    "hold_mins": t.get("hold_mins", 0),
                    "source_feed": t.get("source_feed", ""),
                }
                for i, t in enumerate(track_a_all_trades)
            ],
            "gc_oct1_7_pre": [
                {
                    "id": t.get("id", i + 1),
                    "entry_time": str(t.get("entry_time", ""))[:19],
                    "date": str(t.get("date") or str(t.get("entry_time", ""))[:10]),
                    "direction": t.get("direction", ""),
                    "playbook": t.get("playbook", ""),
                    "net_pnl_usd": t.get("net_pnl_usd", 0),
                    "r_multiple": t.get("r_multiple", 0),
                    "exit_reason": t.get("exit_reason", ""),
                }
                for i, t in enumerate(gc_oct1_7_trades)
            ],
        },
    }
    return payload


def generate_html(data: dict) -> str:
    data_json = json.dumps(data, separators=(",", ":"))
    s_gc = data["summaries"]["gc_overlap"]
    s_m1 = data["summaries"]["bridge_m1"]
    s_do = data["summaries"]["delta_overlap"]
    s_df = data["summaries"]["delta_full"]
    s_ta = data["summaries"]["track_a_full"]
    s_5m = data["summaries"]["gc_5mo"]

    profit_gap_gc_delta = round(s_gc["net_pnl_usd"] - s_do["net_pnl_usd"], 2)
    profit_gap_m1_delta = round(s_m1["net_pnl_usd"] - s_do["net_pnl_usd"], 2)
    mult_m1_vs_delta = round(s_m1["net_pnl_usd"] / s_do["net_pnl_usd"], 2) if s_do["net_pnl_usd"] else 0.0

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Delta Exchange vs GC Backtest Comparison — MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL</title>
<style>
  :root {{
    --bg-main: #07090e;
    --bg-panel: #0e121b;
    --bg-card: #141926;
    --bg-card-hover: #1c2336;
    --border: #232d42;
    --border-light: #2d3a54;
    --text-main: #f1f5f9;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
    --tv-green: #10b981;
    --tv-green-dim: rgba(16, 185, 129, 0.14);
    --tv-red: #ef4444;
    --tv-red-dim: rgba(239, 68, 68, 0.14);
    --tv-blue: #3b82f6;
    --tv-cyan: #06b6d4;
    --gold: #f59e0b;
    --gold-dim: rgba(245, 158, 11, 0.15);
    --purple: #a855f7;
    --indigo: #6366f1;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg-main);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    font-size: 13px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
  .text-green {{ color: var(--tv-green); }}
  .text-red {{ color: var(--tv-red); }}
  .text-gold {{ color: var(--gold); }}
  .text-cyan {{ color: var(--tv-cyan); }}
  .text-purple {{ color: var(--purple); }}
  .text-muted {{ color: var(--text-muted); }}

  /* Sticky Top Header */
  .header-bar {{
    background: linear-gradient(180deg, #111624 0%, #0a0d15 100%);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 4px 20px rgba(0,0,0,0.55);
  }}
  .brand-area {{
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }}
  .badge-crown {{
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #000;
    font-weight: 800;
    font-size: 11px;
    padding: 5px 10px;
    border-radius: 4px;
    letter-spacing: 0.7px;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.35);
  }}
  .brand-info h1 {{
    font-size: 16.5px;
    font-weight: 700;
    color: #fff;
  }}
  .brand-info p {{
    font-size: 11.5px;
    color: var(--text-muted);
  }}
  .header-actions {{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .btn {{
    background: var(--bg-card);
    color: var(--text-main);
    border: 1px solid var(--border);
    padding: 7px 13px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .btn:hover {{ background: var(--bg-card-hover); border-color: var(--tv-blue); }}
  .btn.active, .btn.btn-primary {{
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    border-color: #3b82f6;
    color: #fff;
  }}
  .btn.btn-success {{
    background: linear-gradient(135deg, #059669, #047857);
    border-color: #10b981;
    color: #fff;
  }}

  /* Main Container */
  .container {{
    max-width: 1760px;
    margin: 0 auto;
    padding: 20px 24px 80px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}

  /* Hero Comparison Strip */
  .hero-banner {{
    background: linear-gradient(135deg, #0e1424 0%, #141c2f 60%, #161425 100%);
    border: 1px solid var(--border-light);
    border-left: 4px solid var(--gold);
    border-radius: 10px;
    padding: 18px 22px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  .hero-top {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
  }}
  .hero-pills {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }}
  .pill {{
    font-size: 10.5px;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 4px;
    letter-spacing: 0.4px;
    border: 1px solid transparent;
  }}
  .pill-gold {{ background: rgba(245,158,11,0.16); color: #fbbf24; border-color: rgba(245,158,11,0.4); }}
  .pill-cyan {{ background: rgba(6,182,212,0.15); color: #22d3ee; border-color: rgba(6,182,212,0.4); }}
  .pill-green {{ background: rgba(16,185,129,0.15); color: #34d399; border-color: rgba(16,185,129,0.4); }}
  .pill-purple {{ background: rgba(168,85,247,0.15); color: #c084fc; border-color: rgba(168,85,247,0.4); }}
  .pill-red {{ background: rgba(239,68,68,0.15); color: #f87171; border-color: rgba(239,68,68,0.4); }}

  /* KPI Grid */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
  }}
  .kpi-card {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
  }}
  .kpi-card.highlight-gold {{ border-color: rgba(245,158,11,0.55); background: linear-gradient(180deg, #161412 0%, #0e121b 100%); }}
  .kpi-card.highlight-cyan {{ border-color: rgba(6,182,212,0.55); background: linear-gradient(180deg, #0c1a22 0%, #0e121b 100%); }}
  .kpi-card.highlight-purple {{ border-color: rgba(168,85,247,0.5); background: linear-gradient(180deg, #161124 0%, #0e121b 100%); }}
  .kpi-label {{
    color: var(--text-muted);
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .kpi-val {{
    font-size: 23px;
    font-weight: 800;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    line-height: 1.2;
  }}
  .kpi-sub {{
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 5px;
  }}

  /* Tab Navigation */
  .tab-nav {{
    display: flex;
    gap: 6px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    overflow-x: auto;
  }}
  .tab-btn {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 9px 16px;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 7px;
    white-space: nowrap;
  }}
  .tab-btn:hover {{ background: var(--bg-card); color: #fff; }}
  .tab-btn.active {{
    background: var(--tv-blue);
    border-color: var(--tv-blue);
    color: #fff;
    box-shadow: 0 2px 10px rgba(59, 130, 246, 0.35);
  }}
  .tab-btn .badge-count {{
    background: rgba(255,255,255,0.2);
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
  }}

  .tab-pane {{ display: none; flex-direction: column; gap: 18px; }}
  .tab-pane.active {{ display: flex; }}

  /* Panels */
  .panel {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  .panel-header {{
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .panel-title {{
    font-size: 13.5px;
    font-weight: 700;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .panel-body {{ padding: 16px 18px; }}

  .grid-2 {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
    gap: 16px;
  }}

  /* Tables */
  .data-table-wrap {{ overflow-x: auto; width: 100%; max-height: 620px; overflow-y: auto; }}
  table.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    text-align: left;
  }}
  table.data-table th {{
    background: #111624;
    color: var(--text-muted);
    font-weight: 700;
    padding: 9px 11px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 2;
  }}
  table.data-table td {{
    padding: 8px 11px;
    border-bottom: 1px solid #1a2130;
    white-space: nowrap;
  }}
  table.data-table tr:hover td {{ background: rgba(59, 130, 246, 0.08); }}
  table.data-table tr.row-sub td {{
    background: #121827;
    font-weight: 700;
    border-top: 1px solid var(--border-light);
    border-bottom: 1px solid var(--border-light);
  }}
  table.data-table tr.row-pre td {{ opacity: 0.72; }}
  table.data-table tr.clickable {{ cursor: pointer; }}
  table.data-table tr.selected td {{ background: rgba(245, 158, 11, 0.16) !important; }}

  /* Canvas */
  .chart-canvas-box {{
    position: relative;
    width: 100%;
    height: 370px;
    background: #090c13;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
  }}
  canvas {{ display: block; width: 100%; height: 100%; }}

  /* Dual Calendar */
  .cal-grid {{
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 6px;
  }}
  .cal-header {{
    text-align: center;
    font-weight: 700;
    font-size: 11px;
    color: var(--text-dim);
    padding: 6px 0;
    text-transform: uppercase;
  }}
  .cal-day {{
    background: #101522;
    border: 1px solid #1d263b;
    border-radius: 6px;
    min-height: 98px;
    padding: 7px 8px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .cal-day:hover {{ border-color: var(--tv-blue); transform: translateY(-1px); }}
  .cal-day.empty {{ background: transparent; border-color: transparent; cursor: default; }}
  .cal-day.empty:hover {{ transform: none; }}
  .cal-day.week-col {{ background: #0c1220; border-color: #26324c; cursor: default; }}
  .cal-day.selected {{ outline: 2px solid var(--gold); }}
  .cal-day-num {{ font-size: 11px; font-weight: 700; color: var(--text-muted); display: flex; justify-content: space-between; }}
  .cal-badges {{ display: flex; flex-direction: column; gap: 3px; }}
  .cal-badge {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10.5px;
    padding: 2px 5px;
    border-radius: 3px;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-weight: 700;
  }}
  .cb-pos {{ background: rgba(16,185,129,0.14); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }}
  .cb-neg {{ background: rgba(239,68,68,0.14); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }}
  .cb-zero {{ background: rgba(100,116,139,0.12); color: #94a3b8; border: 1px solid rgba(100,116,139,0.2); }}

  /* Filter Toolbar */
  .toolbar {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }}
  .input-dark {{
    background: #090d16;
    border: 1px solid var(--border);
    color: var(--text-main);
    padding: 6px 10px;
    border-radius: 5px;
    font-size: 12px;
  }}

  /* Root Cause Box */
  .insight-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
    gap: 12px;
  }}
  .insight-card {{
    background: #101522;
    border: 1px solid var(--border);
    border-top: 3px solid var(--tv-cyan);
    border-radius: 7px;
    padding: 13px 15px;
  }}
  .insight-card h4 {{ font-size: 12.5px; color: #fff; margin-bottom: 5px; }}
  .insight-card p {{ font-size: 11.5px; color: var(--text-muted); line-height: 1.45; }}

  @media (max-width: 900px) {{
    .cal-grid {{ grid-template-columns: repeat(4, 1fr); }}
    .grid-2 {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="header-bar">
  <div class="brand-area">
    <span class="badge-crown">GC vs DELTA COMPARISON</span>
    <div class="brand-info">
      <h1>MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL — Delta Exchange XAUTUSD vs CME GC.v.0 Backtest</h1>
      <p>Exact Strategy Specs ($5.00 Fixed Risk • $100 Start Equity • 0.85x SL • 40R Continuous Chandelier Trail • 0.01% Delta Taker Fee)</p>
    </div>
  </div>
  <div class="header-actions">
    <span class="pill pill-gold">Overlap Window: Oct 08 – Oct 30, 2026</span>
    <span class="pill pill-purple">Full Delta Capture: Oct 08 – Nov 15, 2026</span>
    <button class="btn btn-success" onclick="exportCurrentCSV()">⬇ Export Visible CSV</button>
  </div>
</div>

<div class="container">

  <!-- HERO SUMMARY BANNER -->
  <div class="hero-banner">
    <div class="hero-top">
      <div>
        <div class="hero-pills">
          <span class="pill pill-gold">SAME STRATEGY: MUX_085SL_ADAPTIVE_CHANDELIER_TRAIL</span>
          <span class="pill pill-cyan">MODE A: GC DATA BASELINE</span>
          <span class="pill pill-green">MODE B: GC ANALYSIS → DELTA EXECUTION</span>
          <span class="pill pill-purple">MODE C: DELTA EXCHANGE DATA ONLY</span>
        </div>
        <h2 style="font-size:16px; color:#fff; margin-bottom:6px;">
          Verdict: Using CME GC Analysis Brain + Delta Execution Beats Delta-Only by <span class="text-green">+{profit_gap_m1_delta:.2f} USD ({mult_m1_vs_delta:.2f}X Higher Profit)</span>
        </h2>
        <p class="text-muted" style="max-width:1050px; font-size:12px;">
          Across the exact matching <strong>Oct 08 – Oct 30, 2026</strong> overlap where both datasets exist simultaneously (CME Globex <code>GC.v.0</code> Databento MBP-10 L2 vs Delta Exchange India <code>XAUTUSD</code>), running the strategy purely on Delta data earned <strong class="text-purple">+$29.43</strong> (PF 1.35, -24.07% DD). Running the exact same strategy on GC data earned <strong class="text-gold">+$165.43</strong> (PF 3.70, -10.50% DD), and analyzing on GC while executing live on Delta netted <strong class="text-cyan">+$148.34</strong> (PF 3.70, -8.50% DD). Including the post-Oct 30 Delta proxy extension through Nov 15, Delta-Only dropped to <strong class="text-red">+$12.73</strong> full net (-$16.70 in Nov), whereas Track A preserved <strong class="text-green">+$148.73</strong>.
        </p>
      </div>
      <div style="text-align:right; min-width:210px;">
        <div class="text-muted" style="font-size:11px; text-transform:uppercase; font-weight:700;">Oct 8 – Oct 30 Net Gap (GC − Delta)</div>
        <div class="mono text-gold" style="font-size:28px; font-weight:800;">+${profit_gap_gc_delta:.2f}</div>
        <div class="text-cyan mono" style="font-size:11.5px;">Bridge − Delta: +${profit_gap_m1_delta:.2f}</div>
      </div>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card highlight-gold">
        <div class="kpi-label"><span>1. GC Data Baseline</span><span class="pill pill-gold">Oct 8–30</span></div>
        <div class="kpi-val text-gold">+$165.43</div>
        <div class="kpi-sub">Eq: <strong>$265.43 (2.65X)</strong> • 41T • 65.85% WR • PF 3.70 • DD -10.50%</div>
      </div>
      <div class="kpi-card highlight-cyan">
        <div class="kpi-label"><span>2. GC Brain → Delta Exec</span><span class="pill pill-cyan">Oct 8–30</span></div>
        <div class="kpi-val text-cyan">+$148.34</div>
        <div class="kpi-sub">Eq: <strong>$248.34 (2.48X)</strong> • 41T • 63.41% WR • PF 3.70 • DD -8.50%</div>
      </div>
      <div class="kpi-card highlight-purple">
        <div class="kpi-label"><span>3. Delta Data Standalone</span><span class="pill pill-purple">Oct 8–30</span></div>
        <div class="kpi-val text-purple">+$29.43</div>
        <div class="kpi-sub">Eq: <strong>$129.43 (1.29X)</strong> • 44T • 63.64% WR • PF 1.35 • DD -24.07%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label"><span>4. Delta Standalone Full</span><span class="pill pill-red">Oct 8–Nov 15</span></div>
        <div class="kpi-val" style="color:#f59e0b;">+$12.73</div>
        <div class="kpi-sub">Eq: <strong>$112.73 (1.13X)</strong> • 71T • 59.15% WR • Nov Ext: -$16.70</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label"><span>5. Track A Continuous</span><span class="pill pill-green">Oct 8–Nov 15</span></div>
        <div class="kpi-val text-green">+$148.73</div>
        <div class="kpi-sub">Eq: <strong>$248.73 (2.49X)</strong> • 68T • 60.29% WR • PF 2.23</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label"><span>6. 5-Mo GC Champion Ref</span><span class="pill pill-gold">May 29–Oct 30</span></div>
        <div class="kpi-val text-gold">+$605.41</div>
        <div class="kpi-sub">Eq: <strong>$705.41 (7.05X)</strong> • 265T • 62.64% WR • PF 2.25</div>
      </div>
    </div>
  </div>

  <!-- TAB NAVIGATION -->
  <div class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('tab1', this)">1. Total P&amp;L &amp; Equity Curves</button>
    <button class="tab-btn" onclick="switchTab('tab2', this)">2. Day-to-Day P&amp;L &amp; Calendar <span class="badge-count" id="dayBadgeCount">30d</span></button>
    <button class="tab-btn" onclick="switchTab('tab3', this)">3. Weekly P&amp;L Comparison <span class="badge-count">7 Wks</span></button>
    <button class="tab-btn" onclick="switchTab('tab4', this)">4. Exit Reasons, Playbooks &amp; Sessions</button>
    <button class="tab-btn" onclick="switchTab('tab5', this)">5. Trade-by-Trade Auditor</button>
  </div>

  <!-- TAB 1: EXECUTIVE TOTAL P&L COMPARISON -->
  <div id="tab1" class="tab-pane active">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📈 Comparative Account Equity Curve ($100 Start Equity, $5.00 Fixed Risk/Trade)</div>
        <div class="toolbar">
          <button class="btn active" id="btnChartDaily" onclick="setChartMode('daily', this)">Daily Aligned (Oct 8 – Nov 15)</button>
          <button class="btn" id="btnChartTrade" onclick="setChartMode('trade', this)">Trade-by-Trade Sequence</button>
        </div>
      </div>
      <div class="panel-body">
        <div style="display:flex; gap:16px; flex-wrap:wrap; margin-bottom:10px; font-size:11.5px;">
          <span><strong style="color:#f59e0b;">━━</strong> GC Data Baseline (Oct 8–30: $265.43)</span>
          <span><strong style="color:#06b6d4;">━━</strong> GC Brain → Delta Bridge Mode 1 (Oct 8–30: $248.34)</span>
          <span><strong style="color:#10b981;">━━</strong> Track A Continuous (GC Oct 8–30 + Delta Nov Ext: $248.73)</span>
          <span><strong style="color:#a855f7;">━━</strong> Pure Delta Exchange Standalone (Oct 8–30: $129.43 → Nov 15: $112.73)</span>
        </div>
        <div class="chart-canvas-box">
          <canvas id="compEquityCanvas"></canvas>
        </div>
        <div id="chartHoverBar" style="margin-top:8px; font-size:11.5px; color:var(--text-muted);" class="mono">
          Hover over chart to inspect exact equity trajectory across GC Data, GC→Delta Bridge, and Delta Standalone.
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📊 Full Head-to-Head Metrics Matrix (Same Strategy Across All Data Feeds &amp; Windows)</div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table" id="execMatrixTable">
          <thead>
            <tr>
              <th>Data Feed / Execution Architecture</th>
              <th>Date Window</th>
              <th>Trades</th>
              <th>Wins / Losses</th>
              <th>Win %</th>
              <th>Profit Factor</th>
              <th>Gross P&amp;L</th>
              <th>Delta Fees (0.01%)</th>
              <th>Net P&amp;L ($)</th>
              <th>End Equity ($100 Start)</th>
              <th>Max DD % / $</th>
              <th>Avg Win / Loss</th>
              <th>Avg R / Max R</th>
              <th>Avg Hold</th>
            </tr>
          </thead>
          <tbody id="execMatrixBody"></tbody>
        </table>
      </div>
    </div>

    <div class="insight-grid">
      <div class="insight-card" style="border-top-color:#f59e0b;">
        <h4>1. Institutional MBP-10 Filter vs Retail Crypto Noise</h4>
        <p>On CME Globex (Databento MBP-10), SAM (#11) filters low-conviction swings using genuine 10-level order book absorption and aggressor delta. Delta historical L2 lacks full CME depth prior to Oct 8 and swaps to synthetic CLV proxy after Oct 30, creating chop losses (-$16.70 in Nov).</p>
      </div>
      <div class="insight-card" style="border-top-color:#06b6d4;">
        <h4>2. Chandelier Trailing Survival (Max +7.94R vs +3.30R)</h4>
        <p>Using GC analysis to execute &amp; trail on Delta kept runners open <strong>85.3 mins avg</strong> and unlocked <strong>+7.94R</strong> peak gains (+$39.68 single trade). Delta-only 1m micro-wicks prematurely hit tight trailing/stall exits (48.2m avg hold, max +3.30R).</p>
      </div>
      <div class="insight-card" style="border-top-color:#10b981;">
        <h4>3. Fee Drag &amp; Drawdown Compression</h4>
        <p>Over Oct 8–30, Delta-only lost 48.2% of gross profits to taker fees ($27.37 fees on $56.80 gross) and suffered a <strong>-24.07%</strong> max drawdown. The GC→Delta Bridge cut fee drag to <strong>13.4%</strong> ($22.86 fees on $171.20 gross) and shrank drawdown by nearly 3x to <strong>-8.50%</strong>.</p>
      </div>
    </div>
  </div>

  <!-- TAB 2: DAY-TO-DAY P&L COMPARISON & CALENDAR -->
  <div id="tab2" class="tab-pane">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📅 Side-by-Side Daily Calendar Heatmap (GC Data vs Bridge vs Delta Standalone)</div>
        <div class="toolbar">
          <button class="btn active" id="calOctBtn" onclick="setCalMonth('2026-10', this)">October 2026</button>
          <button class="btn" id="calNovBtn" onclick="setCalMonth('2026-11', this)">November 2026</button>
        </div>
      </div>
      <div class="panel-body">
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:10px; font-size:11.5px;">
          <div id="calMonthSummary" class="mono"></div>
          <div class="text-muted">Legend per cell: <span class="text-gold">GC</span> = GC.v.0 Baseline • <span class="text-cyan">BR</span> = GC→Delta Bridge • <span class="text-purple">DL</span> = Delta Data Only</div>
        </div>
        <div class="cal-grid" id="calGrid"></div>
        <div id="calDayInspector" style="margin-top:14px; padding:12px 14px; background:#090d16; border:1px solid var(--border); border-radius:6px; font-size:12px;">
          Click any calendar day card above to inspect that day's exact trades across GC Data and Delta Data.
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📋 Complete Day-by-Day P&amp;L Comparison Table (Every Trading Day)</div>
        <div class="toolbar">
          <select class="input-dark" id="dailyPeriodFilter" onchange="renderDailyTable()">
            <option value="ALL">Show All Days (Oct 1 – Nov 15)</option>
            <option value="OVERLAP" selected>Exact Overlap Only (Oct 8 – Oct 30)</option>
            <option value="SINCE_OCT8">Full Delta Capture Window (Oct 8 – Nov 15)</option>
          </select>
        </div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table" id="dailyCompTable">
          <thead>
            <tr>
              <th>Date</th>
              <th>Day</th>
              <th>Week</th>
              <th>GC Trades (W/L)</th>
              <th>GC Net ($)</th>
              <th>GC Eq ($)</th>
              <th>Bridge Trades</th>
              <th>Bridge Net ($)</th>
              <th>Bridge Eq ($)</th>
              <th>Delta Trades (W/L)</th>
              <th>Delta Gross</th>
              <th>Delta Fees</th>
              <th>Delta Net ($)</th>
              <th>Delta Eq ($)</th>
              <th>Daily Diff (GC − Delta)</th>
              <th>Daily Diff (Bridge − Delta)</th>
              <th>Driver / Root Cause</th>
            </tr>
          </thead>
          <tbody id="dailyCompBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 3: WEEKLY P&L COMPARISON -->
  <div id="tab3" class="tab-pane">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📊 Weekly Net P&amp;L Grouped Comparison Chart (USD per Week)</div>
      </div>
      <div class="panel-body">
        <div style="display:flex; gap:16px; flex-wrap:wrap; margin-bottom:10px; font-size:11.5px;">
          <span><strong style="color:#f59e0b;">■</strong> GC Data Baseline</span>
          <span><strong style="color:#06b6d4;">■</strong> GC Brain → Delta Bridge</span>
          <span><strong style="color:#a855f7;">■</strong> Pure Delta Data Standalone</span>
        </div>
        <div class="chart-canvas-box" style="height:310px;">
          <canvas id="weeklyBarCanvas"></canvas>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🗓️ Week-by-Week Performance Comparison Table (ISO Weeks W40 – W46)</div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table" id="weeklyCompTable">
          <thead>
            <tr>
              <th>ISO Week</th>
              <th>Date Range</th>
              <th>Period Type</th>
              <th>GC Trades (W)</th>
              <th>GC WR%</th>
              <th>GC Net ($)</th>
              <th>Bridge WR%</th>
              <th>Bridge Net ($)</th>
              <th>Delta Trades (W)</th>
              <th>Delta WR%</th>
              <th>Delta Gross ($)</th>
              <th>Delta Fees ($)</th>
              <th>Delta Net ($)</th>
              <th>Weekly Diff (GC − Delta)</th>
              <th>Weekly Diff (Bridge − Delta)</th>
            </tr>
          </thead>
          <tbody id="weeklyCompBody"></tbody>
        </table>
      </div>
      <div class="panel-body" style="border-top:1px solid var(--border); font-size:11.5px; color:var(--text-muted);">
        <strong>* Note on Week W41:</strong> In the full October screenshot, W41 spans Oct 5–9 (11T, +$27.64 on GC). For exact apples-to-apples comparison from when Delta L2 collection began (<strong>Oct 8</strong>), the W41 Overlap row strictly counts <strong>Oct 8–9</strong> (4T: +$11.81 on GC vs +$11.48 on Bridge vs +$2.24 on Delta-Only).
      </div>
    </div>
  </div>

  <!-- TAB 4: MECHANICS, PLAYBOOKS & SESSIONS -->
  <div id="tab4" class="tab-pane">
    <div class="grid-2">
      <div class="panel">
        <div class="panel-header"><div class="panel-title">🎯 Exit Reason Attribution (Oct 8 – Oct 30 Overlap)</div></div>
        <div class="data-table-wrap"><table class="data-table" id="exitReasonTable"><thead><tr><th>Exit Reason</th><th>GC (T / WR% / Net)</th><th>Bridge M1 (T / WR% / Net)</th><th>Delta Only (T / WR% / Net)</th><th>Delta Full Nov15 Net</th></tr></thead><tbody id="exitReasonBody"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">🧠 Playbook Family Breakdown (Oct 8 – Oct 30 Overlap)</div></div>
        <div class="data-table-wrap"><table class="data-table" id="playbookTable"><thead><tr><th>Playbook</th><th>GC (T / WR% / Net)</th><th>Bridge M1 (T / WR% / Net)</th><th>Delta Only (T / WR% / Net)</th><th>Delta Full Nov15 Net</th></tr></thead><tbody id="playbookBody"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">🌍 Killzone Session Comparison (Oct 8 – Oct 30)</div></div>
        <div class="data-table-wrap"><table class="data-table" id="sessionTable"><thead><tr><th>Killzone</th><th>GC (T / WR% / Net)</th><th>Bridge M1 (T / WR% / Net)</th><th>Delta Only (T / WR% / Net)</th><th>Delta Full Nov15 Net</th></tr></thead><tbody id="sessionBody"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">📆 Day-of-Week Comparison (Mon – Fri, Oct 8 – Oct 30)</div></div>
        <div class="data-table-wrap"><table class="data-table" id="dowTable"><thead><tr><th>Weekday</th><th>GC (T / WR% / Net)</th><th>Bridge M1 (T / WR% / Net)</th><th>Delta Only (T / WR% / Net)</th><th>Delta Full Nov15 Net</th></tr></thead><tbody id="dowBody"></tbody></table></div>
      </div>
    </div>
  </div>

  <!-- TAB 5: TRADE AUDITOR -->
  <div id="tab5" class="tab-pane">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🔍 Trade-by-Trade Ledger &amp; Execution Auditor</div>
        <div class="toolbar">
          <button class="btn active" id="btnLedgerMatched" onclick="setLedgerMode('matched', this)">Matched 41 Setups (GC vs Bridge vs Delta Fill)</button>
          <button class="btn" id="btnLedgerDelta" onclick="setLedgerMode('delta', this)">Delta Standalone Full (71 Trades)</button>
          <button class="btn" id="btnLedgerTrackA" onclick="setLedgerMode('track_a', this)">Track A Continuous (68 Trades)</button>
          <input type="text" id="tradeSearchInput" class="input-dark" placeholder="Filter date, playbook, exit..." oninput="renderLedger()" />
        </div>
      </div>
      <div class="data-table-wrap" style="max-height:660px;">
        <table class="data-table" id="ledgerTable">
          <thead id="ledgerHead"></thead>
          <tbody id="ledgerBody"></tbody>
        </table>
      </div>
    </div>
  </div>

</div>

<script>
const REPORT_DATA = {data_json};

let currentChartMode = 'daily';
let currentCalMonth = '2026-10';
let currentLedgerMode = 'matched';

function fmtUsd(v, signed=true) {{
  if (v === null || v === undefined || isNaN(v)) return '—';
  const n = Number(v);
  if (!signed) return '$' + n.toFixed(2);
  return (n >= 0 ? '+$' : '-$') + Math.abs(n).toFixed(2);
}}
function clsVal(v) {{
  if (v === null || v === undefined || isNaN(v)) return 'text-muted';
  return Number(v) >= 0 ? 'text-green' : 'text-red';
}}

function switchTab(tabId, btn) {{
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  btn.classList.add('active');
  if (tabId === 'tab1') drawEquityChart();
  if (tabId === 'tab3') drawWeeklyChart();
}}

/* ---------------- TAB 1: EXECUTIVE MATRIX & EQUITY CHART ---------------- */
function renderExecMatrix() {{
  const s = REPORT_DATA.summaries;
  const rows = [
    {{ name: 'GC Data Baseline (CME Databento MBP-10)', win: 'Oct 08 – Oct 30, 2026 (Overlap)', d: s.gc_overlap, badge: 'pill-gold' }},
    {{ name: 'Bridge Mode 1: GC Analysis → Delta Intrabar Exec', win: 'Oct 08 – Oct 30, 2026 (Overlap)', d: s.bridge_m1, badge: 'pill-cyan' }},
    {{ name: 'Bridge Mode 2: GC Analysis → Delta 1m Close Exec', win: 'Oct 08 – Oct 30, 2026 (Overlap)', d: s.bridge_m2, badge: 'pill-cyan' }},
    {{ name: 'Bridge Mode 3: GC Entry → Delta Local Trail', win: 'Oct 08 – Oct 30, 2026 (Overlap)', d: s.bridge_m3, badge: 'pill-muted' }},
    {{ name: 'Delta Exchange Standalone (Pure XAUTUSD)', win: 'Oct 08 – Oct 30, 2026 (Overlap)', d: s.delta_overlap, badge: 'pill-purple' }},
    {{ name: 'Delta Exchange Standalone (Post-Oct 30 Proxy)', win: 'Oct 31 – Nov 15, 2026 (Ext Only)', d: s.delta_ext, badge: 'pill-red' }},
    {{ name: 'Delta Exchange Standalone (FULL RUN)', win: 'Oct 08 – Nov 15, 2026 (Full)', d: s.delta_full, badge: 'pill-purple' }},
    {{ name: 'Track A Continuous (GC Oct 8-30 + Delta Nov Ext)', win: 'Oct 08 – Nov 15, 2026 (Full)', d: s.track_a_full, badge: 'pill-green' }},
    {{ name: 'GC October Full Month Reference (Oct 1 – Oct 30)', win: 'Oct 01 – Oct 30, 2026 (Ref)', d: s.gc_oct_all, badge: 'pill-gold' }},
    {{ name: 'GC Full 5-Month Apex Champion Reference', win: 'May 29 – Oct 30, 2026 (5-Mo)', d: s.gc_5mo, badge: 'pill-gold' }},
  ];
  const tb = document.getElementById('execMatrixBody');
  tb.innerHTML = rows.map(r => {{
    const x = r.d;
    return `<tr>
      <td><strong>${{r.name}}</strong></td>
      <td class="text-muted">${{r.win}}</td>
      <td class="mono">${{x.trades}}</td>
      <td class="mono">${{x.wins}}W / ${{x.losses}}L</td>
      <td class="mono">${{Number(x.wr_pct).toFixed(2)}}%</td>
      <td class="mono"><strong>${{Number(x.pf).toFixed(2)}}</strong></td>
      <td class="mono ${{clsVal(x.gross_pnl_usd)}}">${{fmtUsd(x.gross_pnl_usd)}}</td>
      <td class="mono text-red">-$${{Number(x.delta_fee_total_usd).toFixed(2)}}</td>
      <td class="mono ${{clsVal(x.net_pnl_usd)}}"><strong>${{fmtUsd(x.net_pnl_usd)}}</strong></td>
      <td class="mono"><strong>$${{Number(x.end_equity).toFixed(2)}}</strong> <span class="text-muted">(${{Number(x.equity_multiplier).toFixed(2)}}X)</span></td>
      <td class="mono text-red">-${{Number(x.max_dd_pct).toFixed(2)}}% (-$${{Number(x.max_dd_usd).toFixed(2)}})</td>
      <td class="mono"><span class="text-green">${{fmtUsd(x.avg_win_usd)}}</span> / <span class="text-red">${{fmtUsd(x.avg_loss_usd)}}</span></td>
      <td class="mono">${{Number(x.avg_r || 0).toFixed(2)}}R / <span class="text-gold">+${{Number(x.max_r_multiple).toFixed(2)}}R</span></td>
      <td class="mono">${{Number(x.avg_hold_mins).toFixed(1)}}m</td>
    </tr>`;
  }}).join('');
}}

function setChartMode(mode, btn) {{
  currentChartMode = mode;
  document.getElementById('btnChartDaily').classList.toggle('active', mode === 'daily');
  document.getElementById('btnChartTrade').classList.toggle('active', mode === 'trade');
  drawEquityChart();
}}

function drawEquityChart() {{
  const canvas = document.getElementById('compEquityCanvas');
  if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(600, rect.width) * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const W = Math.max(600, rect.width);
  const H = rect.height;

  ctx.fillStyle = '#090c13';
  ctx.fillRect(0, 0, W, H);

  const padL = 62, padR = 24, padT = 22, padB = 34;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const curves = REPORT_DATA.equity_curves;
  let seriesList = [];
  let xLabels = [];
  if (currentChartMode === 'daily') {{
    const da = curves.daily_aligned;
    xLabels = da.dates;
    seriesList = [
      {{ label: 'GC Baseline (Oct 8–30)', color: '#f59e0b', vals: da.gc_overlap_eq, width: 2.5 }},
      {{ label: 'GC→Delta Bridge M1 (Oct 8–30)', color: '#06b6d4', vals: da.m1_overlap_eq, width: 2.5 }},
      {{ label: 'Track A Continuous (Oct 8–Nov 15)', color: '#10b981', vals: da.track_a_full_eq, width: 2.0, dash: [5, 4] }},
      {{ label: 'Pure Delta Standalone (Oct 8–Nov 15)', color: '#a855f7', vals: da.delta_full_eq, width: 2.5 }},
    ];
  }} else {{
    const maxLen = Math.max(curves.gc_overlap.length, curves.delta_full.length, curves.track_a_full.length);
    xLabels = Array.from({{length: maxLen}}, (_, i) => 'Trade #' + i);
    seriesList = [
      {{ label: 'GC Baseline (Oct 8–30, 41T)', color: '#f59e0b', vals: curves.gc_overlap.map(p => p.eq), width: 2.5 }},
      {{ label: 'GC→Delta Bridge M1 (Oct 8–30, 41T)', color: '#06b6d4', vals: curves.bridge_m1.map(p => p.eq), width: 2.5 }},
      {{ label: 'Track A Continuous (68T)', color: '#10b981', vals: curves.track_a_full.map(p => p.eq), width: 2.0, dash: [5, 4] }},
      {{ label: 'Pure Delta Standalone (71T)', color: '#a855f7', vals: curves.delta_full.map(p => p.eq), width: 2.5 }},
    ];
  }}

  const allY = seriesList.flatMap(s => s.vals).filter(v => v !== null && v !== undefined);
  const yMin = Math.floor(Math.min(90, ...allY) / 10) * 10;
  const yMax = Math.ceil(Math.max(280, ...allY) / 10) * 10;
  const nX = Math.max(2, xLabels.length);

  const toX = idx => padL + (idx / (nX - 1)) * plotW;
  const toY = val => padT + (1 - (val - yMin) / (yMax - yMin)) * plotH;

  // Grid lines
  ctx.strokeStyle = '#192235';
  ctx.lineWidth = 1;
  ctx.font = '11px ui-monospace, monospace';
  ctx.fillStyle = '#64748b';
  for (let yv = yMin; yv <= yMax; yv += 40) {{
    const y = toY(yv);
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    ctx.fillText('$' + yv, 8, y + 4);
  }}
  // $100 start line
  const y100 = toY(100);
  ctx.strokeStyle = 'rgba(255,255,255,0.22)';
  ctx.setLineDash([3, 3]);
  ctx.beginPath(); ctx.moveTo(padL, y100); ctx.lineTo(W - padR, y100); ctx.stroke();
  ctx.setLineDash([]);

  // X ticks
  const stepX = Math.max(1, Math.floor(nX / 8));
  for (let i = 0; i < nX; i += stepX) {{
    const x = toX(i);
    ctx.fillStyle = '#64748b';
    ctx.fillText(String(xLabels[i]).slice(0, 10), Math.max(padL, x - 28), H - 10);
  }}

  // Draw curves
  seriesList.forEach(s => {{
    ctx.save();
    ctx.strokeStyle = s.color;
    ctx.lineWidth = s.width;
    if (s.dash) ctx.setLineDash(s.dash);
    ctx.beginPath();
    let started = false;
    s.vals.forEach((v, i) => {{
      if (v === null || v === undefined) return;
      const x = toX(i);
      const y = toY(v);
      if (!started) {{ ctx.moveTo(x, y); started = true; }} else ctx.lineTo(x, y);
    }});
    ctx.stroke();
    ctx.restore();
  }});

  // Interactive hover
  canvas.onmousemove = ev => {{
    const br = canvas.getBoundingClientRect();
    const mx = ev.clientX - br.left;
    const idx = Math.max(0, Math.min(nX - 1, Math.round(((mx - padL) / plotW) * (nX - 1))));
    const parts = seriesList.map(s => {{
      const v = s.vals[idx];
      return v !== undefined && v !== null ? `${{s.label.split(' ')[0]}}: $${{Number(v).toFixed(2)}}` : null;
    }}).filter(Boolean);
    document.getElementById('chartHoverBar').innerHTML = `<strong>${{xLabels[idx]}}</strong> &nbsp;|&nbsp; ` + parts.join(' &nbsp;|&nbsp; ');
  }};
}}

/* ---------------- TAB 2: DAILY TABLE & CALENDAR ---------------- */
function setCalMonth(ym, btn) {{
  currentCalMonth = ym;
  document.getElementById('calOctBtn').classList.toggle('active', ym === '2026-10');
  document.getElementById('calNovBtn').classList.toggle('active', ym === '2026-11');
  renderCalendar();
}}

function renderCalendar() {{
  const [yr, mo] = currentCalMonth.split('-').map(Number);
  const daysInMonth = new Date(yr, mo, 0).getDate();
  const firstDow = new Date(yr, mo - 1, 1).getDay(); // 0=Sun..6=Sat

  const dailyMap = {{}};
  REPORT_DATA.daily_rows.forEach(r => {{ dailyMap[r.date] = r; }});
  const weeklyMap = {{}};
  REPORT_DATA.weekly_rows.forEach(w => {{ weeklyMap[w.week] = w; }});

  let gcSum = 0, m1Sum = 0, dSum = 0;
  let gcT = 0, dT = 0;
  Object.values(dailyMap).forEach(r => {{
    if (r.date.startsWith(currentCalMonth)) {{
      if (r.period === 'OCT8_30_OVERLAP') {{
        gcSum += r.gc_net; gcT += r.gc_trades;
        m1Sum += r.m1_net;
      }}
      if (r.period !== 'OCT1_7_PRE') {{
        dSum += r.delta_net; dT += r.delta_trades;
      }}
    }}
  }});
  document.getElementById('calMonthSummary').innerHTML = currentCalMonth === '2026-10'
    ? `Oct 8–30 Overlap Totals: <span class="text-gold">GC ${'{'}fmtUsd(gcSum){'}'} (${'{'}gcT{'}'}T)</span> &nbsp;|&nbsp; <span class="text-cyan">Bridge ${'{'}fmtUsd(m1Sum){'}'} (${'{'}gcT{'}'}T)</span> &nbsp;|&nbsp; <span class="text-purple">Delta Only ${'{'}fmtUsd(dSum){'}'} (${'{'}dT{'}'}T)</span>`
    : `Nov 1–15 Extension: <span class="text-muted">GC Data Ended Oct 30</span> &nbsp;|&nbsp; <span class="text-purple">Delta Standalone ${'{'}fmtUsd(dSum){'}'} (${'{'}dT{'}'}T)</span>`;

  const grid = document.getElementById('calGrid');
  const headers = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat','Week Total'].map(h => `<div class="cal-header">${{h}}</div>`).join('');
  let cells = '';
  let col = 0;
  let curWeekDates = [];

  for (let i = 0; i < firstDow; i++) {{
    cells += `<div class="cal-day empty"></div>`;
    col++;
  }}

  const flushWeekCell = () => {{
    if (!curWeekDates.length) {{
      cells += `<div class="cal-day week-col"><div class="cal-day-num"><span>Wk</span></div><div class="text-muted" style="font-size:10px;">—</div></div>`;
      return;
    }}
    let wGc = 0, wM1 = 0, wD = 0, hasOverlap = false, hasDelta = false;
    curWeekDates.forEach(dStr => {{
      const r = dailyMap[dStr];
      if (!r) return;
      if (r.period === 'OCT8_30_OVERLAP') {{ wGc += r.gc_net; wM1 += r.m1_net; hasOverlap = true; }}
      if (r.period !== 'OCT1_7_PRE') {{ wD += r.delta_net; hasDelta = true; }}
    }});
    const bCls = v => v > 0 ? 'cb-pos' : (v < 0 ? 'cb-neg' : 'cb-zero');
    cells += `<div class="cal-day week-col">
      <div class="cal-day-num"><span>Week Sum</span><span class="text-muted">${{curWeekDates[0].slice(5)}}</span></div>
      <div class="cal-badges">
        ${{hasOverlap ? `<div class="cal-badge ${{bCls(wGc)}}"><span>GC</span><span>${{fmtUsd(wGc)}}</span></div>` : ''}}
        ${{hasOverlap ? `<div class="cal-badge ${{bCls(wM1)}}"><span>BR</span><span>${{fmtUsd(wM1)}}</span></div>` : ''}}
        ${{hasDelta ? `<div class="cal-badge ${{bCls(wD)}}"><span>DL</span><span>${{fmtUsd(wD)}}</span></div>` : ''}}
      </div>
    </div>`;
    curWeekDates = [];
  }};

  for (let day = 1; day <= daysInMonth; day++) {{
    const dStr = `${{currentCalMonth}}-${{String(day).padStart(2, '0')}}`;
    curWeekDates.push(dStr);
    const r = dailyMap[dStr];
    const bCls = v => v > 0 ? 'cb-pos' : (v < 0 ? 'cb-neg' : 'cb-zero');

    if (!r) {{
      cells += `<div class="cal-day"><div class="cal-day-num"><span>${{day}}</span><span style="font-size:9.5px; color:#475569;">No trades</span></div></div>`;
    }} else if (r.period === 'OCT1_7_PRE') {{
      cells += `<div class="cal-day" style="opacity:0.7;" onclick="inspectCalDay('${{dStr}}')">
        <div class="cal-day-num"><span>${{day}}</span><span style="font-size:9.5px;">Pre-Oct8</span></div>
        <div class="cal-badges"><div class="cal-badge ${{bCls(r.gc_net)}}"><span>GC Ref</span><span>${{fmtUsd(r.gc_net)}}</span></div></div>
      </div>`;
    }} else if (r.period === 'OCT8_30_OVERLAP') {{
      cells += `<div class="cal-day" onclick="inspectCalDay('${{dStr}}')">
        <div class="cal-day-num"><span>${{day}}</span><span style="font-size:9.5px;">${{r.gc_trades}}T / ${{r.delta_trades}}T</span></div>
        <div class="cal-badges">
          <div class="cal-badge ${{bCls(r.gc_net)}}"><span>GC</span><span>${{fmtUsd(r.gc_net)}}</span></div>
          <div class="cal-badge ${{bCls(r.m1_net)}}"><span>BR</span><span>${{fmtUsd(r.m1_net)}}</span></div>
          <div class="cal-badge ${{bCls(r.delta_net)}}"><span>DL</span><span>${{fmtUsd(r.delta_net)}}</span></div>
        </div>
      </div>`;
    }} else {{
      cells += `<div class="cal-day" onclick="inspectCalDay('${{dStr}}')">
        <div class="cal-day-num"><span>${{day}}</span><span style="font-size:9.5px;">Delta Ext</span></div>
        <div class="cal-badges">
          <div class="cal-badge ${{bCls(r.delta_net)}}"><span>DL (${{r.delta_trades}}T)</span><span>${{fmtUsd(r.delta_net)}}</span></div>
        </div>
      </div>`;
    }}
    col++;
    if (col === 7) {{
      flushWeekCell();
      col = 0;
    }}
  }}
  if (col > 0) {{
    while (col < 7) {{ cells += `<div class="cal-day empty"></div>`; col++; }}
    flushWeekCell();
  }}
  grid.innerHTML = headers + cells;
}}

function inspectCalDay(dStr) {{
  const r = REPORT_DATA.daily_rows.find(x => x.date === dStr);
  if (!r) return;
  const matched = REPORT_DATA.trades.matched_overlap_41.filter(t => String(t.entry_time).startsWith(dStr));
  const delTrades = REPORT_DATA.trades.delta_full_71.filter(t => t.date === dStr);
  const preTrades = REPORT_DATA.trades.gc_oct1_7_pre.filter(t => t.date === dStr);

  let html = `<div style="margin-bottom:8px;"><strong>${{dStr}} (${{r.day}})</strong> — <span class="text-muted">${{r.driver}}</span></div>`;
  if (matched.length) {{
    html += `<div style="margin-bottom:6px;"><strong class="text-gold">GC Brain / Bridge Trades (${{matched.length}}):</strong> ` +
      matched.map(t => `<span class="pill ${{t.gc_net_usd>=0?'pill-green':'pill-red'}}" style="margin-right:4px;">#${{t.id}} ${{t.direction}} GC:${{fmtUsd(t.gc_net_usd)}} | BR:${{fmtUsd(t.mode1_net_usd)}} (${{t.exit_reason_gc}})</span>`).join('') + `</div>`;
  }}
  if (delTrades.length) {{
    html += `<div><strong class="text-purple">Delta Standalone Trades (${{delTrades.length}}):</strong> ` +
      delTrades.map(t => `<span class="pill ${{t.net_pnl_usd>=0?'pill-green':'pill-red'}}" style="margin-right:4px;">#${{t.id}} ${{t.direction}} ${{fmtUsd(t.net_pnl_usd)}} (${{t.exit_reason}})</span>`).join('') + `</div>`;
  }}
  if (preTrades.length) {{
    html += `<div><strong class="text-gold">Pre-Oct 8 GC Reference (${{preTrades.length}}):</strong> ` +
      preTrades.map(t => `<span class="pill ${{t.net_pnl_usd>=0?'pill-green':'pill-red'}}" style="margin-right:4px;">#${{t.id}} ${{t.direction}} ${{fmtUsd(t.net_pnl_usd)}} (${{t.exit_reason}})</span>`).join('') + `</div>`;
  }}
  document.getElementById('calDayInspector').innerHTML = html;
}}

function renderDailyTable() {{
  const filt = document.getElementById('dailyPeriodFilter').value;
  let rows = REPORT_DATA.daily_rows;
  if (filt === 'OVERLAP') rows = rows.filter(r => r.period === 'OCT8_30_OVERLAP');
  else if (filt === 'SINCE_OCT8') rows = rows.filter(r => r.period !== 'OCT1_7_PRE');

  document.getElementById('dayBadgeCount').innerText = rows.length + 'd';

  let sumGcT = 0, sumGcW = 0, sumGcNet = 0;
  let sumM1T = 0, sumM1Net = 0;
  let sumDT = 0, sumDW = 0, sumDGross = 0, sumDFee = 0, sumDNet = 0;

  const htmlRows = rows.map(r => {{
    const isPre = r.period === 'OCT1_7_PRE';
    const isExt = r.period === 'OCT31_NOV15_EXT';
    if (!isPre && !isExt) {{
      sumGcT += r.gc_trades; sumGcW += r.gc_wins; sumGcNet += r.gc_net;
      sumM1T += r.m1_trades; sumM1Net += r.m1_net;
    }}
    if (!isPre) {{
      sumDT += r.delta_trades; sumDW += r.delta_wins;
      sumDGross += r.delta_gross; sumDFee += r.delta_fees; sumDNet += r.delta_net;
    }}
    return `<tr class="${{isPre ? 'row-pre' : ''}} clickable" onclick="inspectCalDay('${{r.date}}')">
      <td class="mono"><strong>${{r.date}}</strong></td>
      <td>${{r.day.slice(0,3)}}</td>
      <td class="mono text-muted">${{r.week}}</td>
      <td class="mono">${{isExt ? '—' : `${{r.gc_trades}} (${{r.gc_wins}}W/${{r.gc_losses}}L)`}}</td>
      <td class="mono ${{isExt ? 'text-muted' : clsVal(r.gc_net)}}">${{isExt ? '—' : fmtUsd(r.gc_net)}}</td>
      <td class="mono">${{r.gc_cum_eq !== null ? '$' + r.gc_cum_eq.toFixed(2) : '—'}}</td>
      <td class="mono">${{isExt || isPre ? '—' : r.m1_trades}}</td>
      <td class="mono ${{isExt || isPre ? 'text-muted' : clsVal(r.m1_net)}}">${{isExt || isPre ? '—' : fmtUsd(r.m1_net)}}</td>
      <td class="mono">${{r.m1_cum_eq !== null ? '$' + r.m1_cum_eq.toFixed(2) : '—'}}</td>
      <td class="mono">${{isPre ? '—' : `${{r.delta_trades}} (${{r.delta_wins}}W/${{r.delta_losses}}L)`}}</td>
      <td class="mono ${{isPre ? 'text-muted' : clsVal(r.delta_gross)}}">${{isPre ? '—' : fmtUsd(r.delta_gross)}}</td>
      <td class="mono text-red">${{isPre ? '—' : '-$' + r.delta_fees.toFixed(2)}}</td>
      <td class="mono ${{isPre ? 'text-muted' : clsVal(r.delta_net)}}"><strong>${{isPre ? '—' : fmtUsd(r.delta_net)}}</strong></td>
      <td class="mono">${{r.delta_cum_eq !== null ? '$' + r.delta_cum_eq.toFixed(2) : '—'}}</td>
      <td class="mono ${{clsVal(r.diff_gc_minus_delta)}}">${{fmtUsd(r.diff_gc_minus_delta)}}</td>
      <td class="mono ${{clsVal(r.diff_m1_minus_delta)}}">${{fmtUsd(r.diff_m1_minus_delta)}}</td>
      <td class="text-muted" style="font-size:11px;">${{r.driver}}</td>
    </tr>`;
  }}).join('');

  const footer = `<tr class="row-sub">
    <td colspan="3">VISIBLE PERIOD TOTALS</td>
    <td class="mono">${{sumGcT}} (${{sumGcW}}W)</td>
    <td class="mono ${{clsVal(sumGcNet)}}">${{fmtUsd(sumGcNet)}}</td>
    <td class="mono text-gold">$${{(100 + sumGcNet).toFixed(2)}}</td>
    <td class="mono">${{sumM1T}}</td>
    <td class="mono ${{clsVal(sumM1Net)}}">${{fmtUsd(sumM1Net)}}</td>
    <td class="mono text-cyan">$${{(100 + sumM1Net).toFixed(2)}}</td>
    <td class="mono">${{sumDT}} (${{sumDW}}W)</td>
    <td class="mono ${{clsVal(sumDGross)}}">${{fmtUsd(sumDGross)}}</td>
    <td class="mono text-red">-$${{sumDFee.toFixed(2)}}</td>
    <td class="mono ${{clsVal(sumDNet)}}">${{fmtUsd(sumDNet)}}</td>
    <td class="mono text-purple">$${{(100 + sumDNet).toFixed(2)}}</td>
    <td class="mono text-gold">${{fmtUsd(sumGcNet - (filt === 'SINCE_OCT8' ? REPORT_DATA.summaries.delta_overlap.net_pnl_usd : sumDNet))}}</td>
    <td class="mono text-cyan">${{fmtUsd(sumM1Net - (filt === 'SINCE_OCT8' ? REPORT_DATA.summaries.delta_overlap.net_pnl_usd : sumDNet))}}</td>
    <td>Oct 8–30 Overlap vs Extended Window</td>
  </tr>`;

  document.getElementById('dailyCompBody').innerHTML = htmlRows + footer;
}}

/* ---------------- TAB 3: WEEKLY TABLE & BAR CHART ---------------- */
function renderWeeklyTable() {{
  const wks = REPORT_DATA.weekly_rows;
  let gcT=0, gcW=0, gcNet=0, m1Net=0, dT=0, dW=0, dGross=0, dFee=0, dNet=0;
  const rowsHtml = wks.map(w => {{
    if (w.period === 'OVERLAP') {{ gcT += w.gc_trades; gcW += w.gc_wins; gcNet += w.gc_net; m1Net += w.m1_net; }}
    if (w.period !== 'PRE_OVERLAP') {{ dT += w.delta_trades; dW += w.delta_wins; dGross += w.delta_gross; dFee += w.delta_fees; dNet += w.delta_net; }}
    const isOv = w.period === 'OVERLAP';
    const isPre = w.period === 'PRE_OVERLAP';
    const badge = isOv ? 'pill-cyan' : (isPre ? 'pill-gold' : 'pill-purple');
    return `<tr class="${{isPre ? 'row-pre' : ''}}">
      <td class="mono"><strong>${{w.week}}</strong></td>
      <td>${{w.label}}</td>
      <td><span class="pill ${{badge}}">${{w.period}}</span></td>
      <td class="mono">${{w.period === 'EXTENSION' ? '—' : `${{w.gc_trades}} (${{w.gc_wins}}W)`}}</td>
      <td class="mono">${{w.period === 'EXTENSION' ? '—' : w.gc_wr.toFixed(1) + '%'}}</td>
      <td class="mono ${{w.period === 'EXTENSION' ? 'text-muted' : clsVal(w.gc_net)}}"><strong>${{w.period === 'EXTENSION' ? '—' : fmtUsd(w.gc_net)}}</strong></td>
      <td class="mono">${{isOv ? w.m1_wr.toFixed(1) + '%' : '—'}}</td>
      <td class="mono ${{isOv ? clsVal(w.m1_net) : 'text-muted'}}"><strong>${{isOv ? fmtUsd(w.m1_net) : '—'}}</strong></td>
      <td class="mono">${{isPre ? '—' : `${{w.delta_trades}} (${{w.delta_wins}}W)`}}</td>
      <td class="mono">${{isPre ? '—' : w.delta_wr.toFixed(1) + '%'}}</td>
      <td class="mono ${{isPre ? 'text-muted' : clsVal(w.delta_gross)}}">${{isPre ? '—' : fmtUsd(w.delta_gross)}}</td>
      <td class="mono text-red">${{isPre ? '—' : '-$' + w.delta_fees.toFixed(2)}}</td>
      <td class="mono ${{isPre ? 'text-muted' : clsVal(w.delta_net)}}"><strong>${{isPre ? '—' : fmtUsd(w.delta_net)}}</strong></td>
      <td class="mono ${{clsVal(w.diff_gc_vs_delta)}}">${{fmtUsd(w.diff_gc_vs_delta)}}</td>
      <td class="mono ${{clsVal(w.diff_m1_vs_delta)}}">${{fmtUsd(w.diff_m1_vs_delta)}}</td>
    </tr>`;
  }}).join('');

  const sOvDelta = REPORT_DATA.summaries.delta_overlap;
  const subOverlap = `<tr class="row-sub">
    <td colspan="3">OVERLAP SUBTOTAL (W41 Oct 8 – W44 Oct 30)</td>
    <td class="mono">${{gcT}} (${{gcW}}W)</td>
    <td class="mono">65.9%</td>
    <td class="mono text-gold">${{fmtUsd(gcNet)}}</td>
    <td class="mono">63.4%</td>
    <td class="mono text-cyan">${{fmtUsd(m1Net)}}</td>
    <td class="mono">${{sOvDelta.trades}} (${{sOvDelta.wins}}W)</td>
    <td class="mono">${{sOvDelta.wr_pct}}%</td>
    <td class="mono">${{fmtUsd(sOvDelta.gross_pnl_usd)}}</td>
    <td class="mono text-red">-$${{sOvDelta.delta_fee_total_usd}}</td>
    <td class="mono text-purple">${{fmtUsd(sOvDelta.net_pnl_usd)}}</td>
    <td class="mono text-gold">${{fmtUsd(gcNet - sOvDelta.net_pnl_usd)}}</td>
    <td class="mono text-cyan">${{fmtUsd(m1Net - sOvDelta.net_pnl_usd)}}</td>
  </tr>`;

  const subFullDelta = `<tr class="row-sub">
    <td colspan="3">FULL DELTA CAPTURE TOTAL (W41 Oct 8 – W46 Nov 15)</td>
    <td colspan="5" class="text-muted">Track A Combined (GC Oct 8-30 + Delta Nov Ext): <strong class="text-green">+$148.73 (68T, 60.29% WR)</strong></td>
    <td class="mono">${{dT}} (${{dW}}W)</td>
    <td class="mono">${{((dW/dT)*100).toFixed(2)}}%</td>
    <td class="mono">${{fmtUsd(dGross)}}</td>
    <td class="mono text-red">-$${{dFee.toFixed(2)}}</td>
    <td class="mono ${{clsVal(dNet)}}"><strong>${{fmtUsd(dNet)}}</strong></td>
    <td colspan="2" class="mono text-muted">Nov Extension alone: -$16.70</td>
  </tr>`;

  document.getElementById('weeklyCompBody').innerHTML = rowsHtml + subOverlap + subFullDelta;
}}

function drawWeeklyChart() {{
  const canvas = document.getElementById('weeklyBarCanvas');
  if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(600, rect.width) * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  const W = Math.max(600, rect.width);
  const H = rect.height;

  ctx.fillStyle = '#090c13';
  ctx.fillRect(0, 0, W, H);

  const wks = REPORT_DATA.weekly_rows.filter(w => w.period !== 'PRE_OVERLAP');
  const padL = 56, padR = 24, padT = 24, padB = 38;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const vals = wks.flatMap(w => [w.gc_net || 0, w.m1_net || 0, w.delta_net || 0]);
  const yMin = Math.min(-30, Math.floor(Math.min(...vals) / 10) * 10);
  const yMax = Math.max(70, Math.ceil(Math.max(...vals) / 10) * 10);
  const toY = v => padT + (1 - (v - yMin) / (yMax - yMin)) * plotH;
  const y0 = toY(0);

  ctx.strokeStyle = '#192235';
  ctx.font = '11px ui-monospace, monospace';
  for (let yv = yMin; yv <= yMax; yv += 20) {{
    const y = toY(yv);
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    ctx.fillStyle = '#64748b';
    ctx.fillText('$' + yv, 8, y + 4);
  }}
  ctx.strokeStyle = 'rgba(255,255,255,0.3)';
  ctx.beginPath(); ctx.moveTo(padL, y0); ctx.lineTo(W - padR, y0); ctx.stroke();

  const groupW = plotW / wks.length;
  const barW = Math.min(26, groupW * 0.22);

  wks.forEach((w, idx) => {{
    const cx = padL + idx * groupW + groupW / 2;
    const bars = [
      {{ val: w.period === 'OVERLAP' ? w.gc_net : null, col: '#f59e0b', dx: -barW * 1.15 }},
      {{ val: w.period === 'OVERLAP' ? w.m1_net : null, col: '#06b6d4', dx: 0 }},
      {{ val: w.delta_net, col: '#a855f7', dx: barW * 1.15 }},
    ];
    bars.forEach(b => {{
      if (b.val === null) return;
      const yv = toY(b.val);
      const top = Math.min(y0, yv);
      const h = Math.max(2, Math.abs(y0 - yv));
      ctx.fillStyle = b.col;
      ctx.fillRect(cx + b.dx - barW / 2, top, barW, h);
      ctx.fillStyle = '#e2e8f0';
      ctx.font = '10px ui-monospace, monospace';
      ctx.fillText((b.val >= 0 ? '+$' : '-$') + Math.abs(b.val).toFixed(0), cx + b.dx - barW / 2, b.val >= 0 ? top - 4 : top + h + 11);
    }});
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px sans-serif';
    ctx.fillText(w.week, cx - 24, H - 12);
  }});
}}

/* ---------------- TAB 4: BREAKDOWNS ---------------- */
function renderBreakdowns() {{
  const b = REPORT_DATA.breakdowns;
  const fillCat = (catKey, bodyId) => {{
    const cat = b[catKey];
    const keys = Array.from(new Set([
      ...Object.keys(cat.gc_overlap),
      ...Object.keys(cat.bridge_m1),
      ...Object.keys(cat.delta_overlap),
      ...Object.keys(cat.delta_full),
    ]));
    keys.sort((a, k) => ((cat.gc_overlap[k]?.net_pnl_usd || 0) - (cat.gc_overlap[a]?.net_pnl_usd || 0)));
    const fmtCell = obj => obj ? `${{obj.trades}}T • ${{obj.wr_pct.toFixed(0)}}% • <span class="${{clsVal(obj.net_pnl_usd)}}">${{fmtUsd(obj.net_pnl_usd)}}</span>` : '<span class="text-muted">—</span>';
    document.getElementById(bodyId).innerHTML = keys.map(k => `<tr>
      <td><strong>${{k}}</strong></td>
      <td class="mono">${{fmtCell(cat.gc_overlap[k])}}</td>
      <td class="mono">${{fmtCell(cat.bridge_m1[k])}}</td>
      <td class="mono">${{fmtCell(cat.delta_overlap[k])}}</td>
      <td class="mono">${{fmtCell(cat.delta_full[k])}}</td>
    </tr>`).join('');
  }};
  fillCat('exit_reason', 'exitReasonBody');
  fillCat('playbook', 'playbookBody');
  fillCat('session', 'sessionBody');
  fillCat('day_of_week', 'dowBody');
}}

/* ---------------- TAB 5: TRADE LEDGER ---------------- */
function setLedgerMode(mode, btn) {{
  currentLedgerMode = mode;
  ['btnLedgerMatched', 'btnLedgerDelta', 'btnLedgerTrackA'].forEach(id => document.getElementById(id).classList.remove('active'));
  btn.classList.add('active');
  renderLedger();
}}

function renderLedger() {{
  const q = (document.getElementById('tradeSearchInput').value || '').toLowerCase();
  const thead = document.getElementById('ledgerHead');
  const tbody = document.getElementById('ledgerBody');

  if (currentLedgerMode === 'matched') {{
    thead.innerHTML = `<tr>
      <th>#</th><th>Entry UTC</th><th>TF</th><th>Dir</th><th>Playbook</th><th>GC Exit Reason</th>
      <th>GC Entry / Exit</th><th>GC Net ($)</th><th>Delta Entry (Basis)</th><th>Bridge M1 Exit / Net</th><th>Bridge M2 Net</th><th>Bridge Eq ($)</th>
    </tr>`;
    const rows = REPORT_DATA.trades.matched_overlap_41.filter(t => !q || JSON.stringify(t).toLowerCase().includes(q));
    tbody.innerHTML = rows.map(t => `<tr>
      <td class="mono">${{t.id}}</td>
      <td class="mono">${{t.entry_time}}</td>
      <td>${{t.tf}}</td>
      <td><span class="pill ${{t.direction==='LONG'?'pill-green':'pill-red'}}">${{t.direction}}</span></td>
      <td>${{t.playbook}}</td>
      <td class="text-muted">${{t.exit_reason_gc}}</td>
      <td class="mono">${{t.gc_entry_px}} → ${{t.gc_exit_px}}</td>
      <td class="mono ${{clsVal(t.gc_net_usd)}}"><strong>${{fmtUsd(t.gc_net_usd)}}</strong> (${{t.gc_r_multiple}}R)</td>
      <td class="mono">${{t.delta_entry_px}} <span class="text-muted">(${{t.entry_basis_pts}})</span></td>
      <td class="mono ${{clsVal(t.mode1_net_usd)}}"><strong>${{fmtUsd(t.mode1_net_usd)}}</strong> (${{t.mode1_r_multiple}}R)</td>
      <td class="mono ${{clsVal(t.mode2_net_usd)}}">${{fmtUsd(t.mode2_net_usd)}}</td>
      <td class="mono text-cyan">$${{Number(t.mode1_eq_after).toFixed(2)}}</td>
    </tr>`).join('');
  }} else {{
    const list = currentLedgerMode === 'delta' ? REPORT_DATA.trades.delta_full_71 : REPORT_DATA.trades.track_a_68;
    thead.innerHTML = `<tr>
      <th>#</th><th>Entry UTC</th><th>Day</th><th>Session</th><th>TF</th><th>Dir</th><th>Playbook</th>
      <th>Entry → Exit</th><th>SL</th><th>R-Mult</th><th>Gross ($)</th><th>Fees ($)</th><th>Net ($)</th><th>Eq After ($)</th><th>Exit Reason</th><th>Hold</th>
    </tr>`;
    const rows = list.filter(t => !q || JSON.stringify(t).toLowerCase().includes(q));
    tbody.innerHTML = rows.map(t => `<tr>
      <td class="mono">${{t.id}}</td>
      <td class="mono">${{t.entry_time}}</td>
      <td>${{String(t.day_of_week).slice(0,3)}}</td>
      <td>${{t.session}}</td>
      <td>${{t.tf}}</td>
      <td><span class="pill ${{t.direction==='LONG'?'pill-green':'pill-red'}}">${{t.direction}}</span></td>
      <td>${{t.playbook}}</td>
      <td class="mono">${{t.entry_price}} → ${{t.exit_price}}</td>
      <td class="mono text-muted">${{t.sl_price || '—'}}</td>
      <td class="mono ${{clsVal(t.r_multiple)}}">${{Number(t.r_multiple).toFixed(2)}}R</td>
      <td class="mono ${{clsVal(t.gross_pnl_usd)}}">${{fmtUsd(t.gross_pnl_usd)}}</td>
      <td class="mono text-red">-$${{Number(t.delta_fee_usd).toFixed(2)}}</td>
      <td class="mono ${{clsVal(t.net_pnl_usd)}}"><strong>${{fmtUsd(t.net_pnl_usd)}}</strong></td>
      <td class="mono">$${{Number(t.equity_after).toFixed(2)}}</td>
      <td class="text-muted">${{t.exit_reason}}</td>
      <td class="mono">${{t.hold_mins}}m</td>
    </tr>`).join('');
  }}
}}

function exportCurrentCSV() {{
  const rows = REPORT_DATA.daily_rows.filter(r => r.period !== 'OCT1_7_PRE');
  const headers = ['date','day','week','period','gc_trades','gc_wins','gc_net','m1_net','delta_trades','delta_wins','delta_gross','delta_fees','delta_net','delta_cum_eq','diff_gc_minus_delta','driver'];
  const csv = [headers.join(','), ...rows.map(r => headers.map(h => '"' + String(r[h] ?? '').replace(/"/g, '""') + '"').join(','))].join('\\n');
  const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'delta_vs_gc_daily_comparison.csv';
  a.click();
}}

window.addEventListener('resize', () => {{
  drawEquityChart();
  drawWeeklyChart();
}});

renderExecMatrix();
drawEquityChart();
renderCalendar();
renderDailyTable();
renderWeeklyTable();
drawWeeklyChart();
renderBreakdowns();
renderLedger();
</script>
</body>
</html>
"""


def main():
    print("[1/3] Loading verified JSON datasets...")
    data = build_payload()
    print(f"      Daily rows: {len(data['daily_rows'])} | Weekly rows: {len(data['weekly_rows'])}")
    print(f"      GC Overlap: +${data['summaries']['gc_overlap']['net_pnl_usd']:.2f} | Bridge M1: +${data['summaries']['bridge_m1']['net_pnl_usd']:.2f} | Delta Overlap: +${data['summaries']['delta_overlap']['net_pnl_usd']:.2f} | Delta Full: +${data['summaries']['delta_full']['net_pnl_usd']:.2f}")

    print("[2/3] Generating standalone comparison HTML dashboard...")
    html = generate_html(data)
    with open(OUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_HTML_PATH) / 1024.0
    print(f"[3/3] Saved {OUT_HTML_PATH} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
