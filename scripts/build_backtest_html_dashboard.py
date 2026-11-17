"""
Syndicate Alpha — Interactive Backtest Forensics, TradingView Chart, PnL Calendar & Self-Learner HTML Generator
---------------------------------------------------------------------------------------------------------------
Builds `backtest_dashboard.html` using 100% real CME Globex Gold (`GC.v.0`) data from
`data/processed/GC_v0_2Year_L2_OrderFlow_Master.parquet` and all 5 Multi-Setting Backtest CSV logs.
"""

import base64
import json
import os
import sys
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backtest_runner import load_config, CONFIG_PATH, STRATEGY_PROFILES
from src.agents.syndicate_agents import precompute_features

PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
OUT_HTML = os.path.join(BASE_DIR, "backtest_dashboard.html")


def classify_session_and_season(ts: pd.Timestamp):
    est_ts = ts - pd.Timedelta(hours=5)
    hr = est_ts.hour
    mn = est_ts.minute
    if hr == 2:
        session = "London Open (02:00-03:00 EST)"
    elif hr == 3:
        session = "London Silver Bullet (03:00-04:00 EST)"
    elif hr == 4:
        session = "Late London (04:00-05:00 EST)"
    elif hr in (8, 9):
        session = "NY Open (08:00-10:00 EST)"
    elif hr == 10:
        session = "NY Silver Bullet (10:00-11:00 EST)"
    elif hr == 11:
        session = "NY London Close (11:00-12:00 EST)"
    else:
        session = "Off-Killzone Session"

    m = est_ts.month
    if m in (12, 1, 2):
        season = "Winter (Dec-Feb)"
    elif m in (3, 4, 5):
        season = "Spring (Mar-May)"
    elif m in (6, 7, 8):
        season = "Summer (Jun-Aug)"
    else:
        season = "Autumn (Sep-Nov)"

    day_name = est_ts.strftime("%A")
    date_str = est_ts.strftime("%Y-%m-%d")
    month_str = est_ts.strftime("%Y-%m")
    return session, season, day_name, date_str, month_str


def build_dashboard():
    cfg = load_config(CONFIG_PATH)
    parquet_path = os.path.join(PROCESSED_DIR, "GC_v0_2Year_L2_OrderFlow_Master.parquet")
    print(f"[HTML BUILDER] Loading Master Parquet: {parquet_path}")
    raw_df = pd.read_parquet(parquet_path)
    # Restrict to the last 5 months (155 days) of fully available data
    raw_df = raw_df[raw_df.index >= raw_df.index[-1] - pd.Timedelta(days=155)].copy()
    df = precompute_features(raw_df, cfg)

    opens = df["open"].to_numpy()
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    closes = df["close"].to_numpy()
    vols = df["volume"].to_numpy(dtype=float)
    chop = df["chop_index"].to_numpy()
    adx = df["adx"].to_numpy()
    atr15m = df["atr_5m"].to_numpy()
    vol_z = df["vol_z_score"].to_numpy()
    delta5 = df["delta_sum_5"].to_numpy()
    delta15 = df["delta_sum_15"].to_numpy()
    l2_mean = df["l2_bid_ask_ratio_mean"].to_numpy()
    l2_max = df["l2_bid_ask_ratio_max"].to_numpy()
    spread = df["avg_spread_pts"].to_numpy()
    fib240_long = df["fib_240_long"].to_numpy()
    fib240_short = df["fib_240_short"].to_numpy()
    l_wick = df["lower_wick_ratio"].to_numpy()
    u_wick = df["upper_wick_ratio"].to_numpy()
    room_h = df["room_to_high_240"].to_numpy()
    room_l = df["room_to_low_240"].to_numpy()
    unix_secs = df.index.asi8 // 10**9

    # Map timestamp to integer index for instant O(1) lookup
    ts_to_idx = {ts: idx for idx, ts in enumerate(df.index)}

    profiles_data = {}
    candle_windows = {}

    for prof in STRATEGY_PROFILES:
        pname = prof["name"]
        csv_path = os.path.join(PROCESSED_DIR, f"trades_{pname}.csv")
        if not os.path.exists(csv_path):
            continue
        t_df = pd.read_csv(csv_path)
        trades_list = []

        for tid, row in t_df.iterrows():
            ent_ts = pd.to_datetime(row["entry_time"], utc=True)
            ext_ts = pd.to_datetime(row["exit_time"], utc=True)
            i_ent = ts_to_idx.get(ent_ts, None)
            i_ext = ts_to_idx.get(ext_ts, None)
            if i_ent is None or i_ext is None:
                i_ent = int(df.index.get_indexer([ent_ts], method="nearest")[0])
                i_ext = int(df.index.get_indexer([ext_ts], method="nearest")[0])

            direction = row["direction"]
            entry_px = float(row["entry_price"])
            exit_px = float(row["exit_price"])
            risk_pts = float(row["init_risk_pts"])
            r_mult = float(row["r_multiple"])
            net_pnl = float(row["net_pnl_usd"])
            gross_pnl = float(row["gross_pnl_usd"])
            delta_fee = float(row["delta_fee_usd"])
            notional_usd = float(row["notional_usd"])
            qty_oz = float(row["qty_oz"])

            is_chop_bar = chop[i_ent] > 56.0
            tp1_m = prof["tp1_r"]
            tp2_m = prof["tp2_r"]
            if prof["adaptive_regime"]:
                if is_chop_bar:
                    tp1_m = max(1.35, prof["tp1_r"] - 0.15)
                    tp2_m = max(2.35, prof["tp2_r"] - 0.30)
                elif adx[i_ent] >= 25.0:
                    tp2_m = prof["tp2_r"] + 0.15

            if direction == "LONG":
                sl_px = round(entry_px - risk_pts, 2)
                tp1_px = round(entry_px + tp1_m * risk_pts, 2)
                tp2_px = round(entry_px + tp2_m * risk_pts, 2)
            else:
                sl_px = round(entry_px + risk_pts, 2)
                tp1_px = round(entry_px - tp1_m * risk_pts, 2)
                tp2_px = round(entry_px - tp2_m * risk_pts, 2)

            # Compute intra-trade MFE / MAE & post-exit 60m excursion
            slice_end = max(i_ext + 1, i_ent + 2)
            tr_highs = highs[i_ent:slice_end]
            tr_lows = lows[i_ent:slice_end]
            if direction == "LONG":
                mfe_pts = float(np.max(tr_highs) - entry_px)
                mae_pts = float(entry_px - np.min(tr_lows))
                peak_rel_idx = int(np.argmax(tr_highs))
            else:
                mfe_pts = float(entry_px - np.min(tr_lows))
                mae_pts = float(np.max(tr_highs) - entry_px)
                peak_rel_idx = int(np.argmin(tr_lows))

            mfe_r = round(mfe_pts / max(risk_pts, 0.5), 2)
            mae_r = round(mae_pts / max(risk_pts, 0.5), 2)
            hold_mins = max(1, int(i_ext - i_ent))

            post_end = min(len(df), i_ext + 61)
            if post_end > i_ext + 1:
                if direction == "LONG":
                    post_60m_pts = float(np.max(highs[i_ext:post_end]) - exit_px)
                else:
                    post_60m_pts = float(exit_px - np.min(lows[i_ext:post_end]))
            else:
                post_60m_pts = 0.0
            post_60m_r = round(post_60m_pts / max(risk_pts, 0.5), 2)

            session, season, day_name, date_str, month_str = classify_session_and_season(ent_ts)
            exit_reason = str(row["exit_reason"])

            # Build Pros & Mistake Forensic Diagnosis for Self-Learner Agent
            pros = []
            fib_val = fib240_long[i_ent] if direction == "LONG" else fib240_short[i_ent]
            wick_val = l_wick[i_ent] if direction == "LONG" else u_wick[i_ent]
            room_val = room_h[i_ent] if direction == "LONG" else room_l[i_ent]

            if 0.60 <= fib_val <= 0.85:
                pros.append(f"KAI confirmed deep 4H Fibonacci Golden Pocket ({fib_val*100:.1f}% retracement).")
            if wick_val >= 1.5:
                pros.append(f"ELENA detected strong {wick_val:.1f}x rejection wick rejecting liquidity pool.")
            if vol_z[i_ent] >= 1.3:
                pros.append(f"JACK confirmed institutional volume expansion (Vol Z-Score +{vol_z[i_ent]:.2f}σ).")
            if (direction == "LONG" and delta5[i_ent] > 0) or (direction == "SHORT" and delta5[i_ent] < 0):
                pros.append(f"OMAR confirmed aligned 5m CVD order flow delta ({delta5[i_ent]:+.0f} contracts).")
            else:
                pros.append("OMAR detected passive limit absorption at extreme liquidity boundary.")
            if room_val >= 1.5 * risk_pts:
                pros.append(f"DAVID verified {room_val:.1f} pts clearance to opposing 4H structure wall ({room_val/risk_pts:.1f}R room).")

            if exit_reason == "STOP_LOSS":
                if mfe_r >= 0.80:
                    mistake_code = "UNBANKED_PROFIT_GIVEBACK"
                    mistake_title = f"Reached +{mfe_r:.2f}R (+${mfe_pts:.1f} pts) Before Reversing to -1.0R Stop"
                    mistake_desc = (
                        f"Setup direction was right (+{mfe_r:.2f}R MFE in {peak_rel_idx}m), but price reversed before hitting "
                        f"RYAN's +{prof['be_trigger_r']:.2f}R Break-Even trigger (CHOP={chop[i_ent]:.1f}, ADX={adx[i_ent]:.1f})."
                    )
                    learner_fix = (
                        f"RYAN Directive: When 15M CHOP > 50 or ADX < 22, lower Phase-2 Break-Even trigger from "
                        f"+{prof['be_trigger_r']:.2f}R to +0.80R to protect green trades from range snapbacks."
                    )
                elif hold_mins <= 18 and post_60m_r >= 1.15:
                    mistake_code = "STOP_HUNT_WHIPSAW"
                    mistake_title = f"Stopped Out in {hold_mins}m Then Reversed +{post_60m_r:.2f}R in Target Direction"
                    mistake_desc = (
                        f"Classic liquidity sweep double-tap: price wicked SL at {sl_px:.2f} within {hold_mins}m and then "
                        f"moved +{post_60m_pts:.1f} pts (+{post_60m_r:.2f}R) in our favor over the next 60m."
                    )
                    learner_fix = (
                        "NINA & ETHAN Directive: Wait for 2nd 1M candle close back inside range or add +0.15x ATR buffer "
                        "behind the sweep wick extreme during high-volatility NY/London opens."
                    )
                elif (direction == "LONG" and delta15[i_ent] < -30) or (direction == "SHORT" and delta15[i_ent] > 30):
                    mistake_code = "COUNTER_CVD_MOMENTUM"
                    mistake_title = f"Faded Heavy 15m Cumulative Volume Delta ({delta15[i_ent]:+.0f})"
                    mistake_desc = (
                        f"Entered {direction} while 15-minute aggressive order flow delta ({delta15[i_ent]:+.0f}) was still "
                        f"pushing against the level, resulting in a -1.0R trend continuation stop-out."
                    )
                    learner_fix = (
                        "OMAR & VICTOR Directive: Require 5m delta deceleration before fading a 4H level when 15m CVD "
                        "exceeds ±30 contracts."
                    )
                else:
                    mistake_code = "STRUCTURAL_TREND_FAILURE"
                    mistake_title = f"HTF Level Broken cleanly (Max MFE only +{mfe_r:.2f}R)"
                    mistake_desc = (
                        f"Price never gained traction (MFE +{mfe_r:.2f}R) as institutional momentum broke through the "
                        f"setup zone over {hold_mins}m."
                    )
                    learner_fix = (
                        "ARTHUR & KAI Directive: Require 15M ADX slope confirmation or stronger L2 Bid/Ask wall (>=1.20) "
                        "to filter low-bounce structural breaks."
                    )
            elif "PHASE_2_BREAKEVEN" in exit_reason:
                mistake_code = "BREAKEVEN_WHIPSAW_PROTECTED"
                mistake_title = f"Reached +{mfe_r:.2f}R & Protected by RYAN Phase-2 Break-Even Lock"
                mistake_desc = (
                    f"Trade pushed +{mfe_r:.2f}R (+{mfe_pts:.1f} pts) but stalled just shy of TP1 (+{tp1_m:.2f}R), "
                    f"exiting safely at +{r_mult:.2f}R (+${net_pnl:.2f} net after Delta 0.01% fee)."
                )
                learner_fix = (
                    f"RYAN Feedback: Phase-2 Break-Even lock saved $5.00 risk and banked +${net_pnl:.2f} net. "
                    f"Post-exit moved +{post_60m_r:.2f}R."
                )
            elif "PHASE_4_STRUCTURE_RUNNER" in exit_reason:
                mistake_code = "PARTIAL_TP1_PLUS_TRAIL_WIN"
                mistake_title = f"TP1 Banked (+{tp1_m:.2f}R) + Runner Trailed to +{r_mult:.2f}R Total"
                mistake_desc = (
                    f"Reached +{mfe_r:.2f}R peak (+{mfe_pts:.1f} pts) with only -{mae_r:.2f}R drawdown. "
                    f"50% banked at TP1 ({tp1_px:.2f}) and runner locked via Chandelier trail at {exit_px:.2f}."
                )
                learner_fix = (
                    f"Execution Excellence: {row['confirming_agents_count']}/16 agents confirmed. "
                    f"Net profit +${net_pnl:.2f} after ${delta_fee:.2f} Delta Exchange fee."
                )
            elif "TP2_FULL_RUNNER_TARGET" in exit_reason:
                mistake_code = "TEXTBOOK_FULL_TP2_RUNNER"
                mistake_title = f"Full TP1 + TP2 Runner Target Hit (+{r_mult:.2f}R | +${net_pnl:.2f} Net)"
                mistake_desc = (
                    f"Institutional sniper execution: suffered only -{mae_r:.2f}R MAE before surging +{mfe_pts:.1f} pts "
                    f"to smash both TP1 ({tp1_px:.2f}) and full TP2 runner target ({tp2_px:.2f}) in {hold_mins}m."
                )
                learner_fix = (
                    f"Self-Learner Benchmark: High-confluence {row['setup_type']} in {session} ({day_name}) — "
                    f"model template for 16-agent reinforcement."
                )
            elif "REVERSAL_EXIT" in exit_reason:
                if r_mult >= 0:
                    mistake_code = "AGENT_REVERSAL_PROFIT_LOCK"
                    mistake_title = f"Instant Reversal Cut ({exit_reason}) Locked +{r_mult:.2f}R Before Trail SL Hit"
                    mistake_desc = (
                        f"Trade peaked at +{mfe_r:.2f}R (+{mfe_pts:.1f} pts), then >70% of active agents detected an "
                        f"opposite structural & CVD reversal. Cut instantly at {exit_px:.2f} (+${net_pnl:.2f} net) before price could drop to SL/Trail."
                    )
                    learner_fix = (
                        "ORACLE + RYAN Reversal Rule: Instant multi-agent flip exit preserved open runner profit ahead of a sharp counter-impulse."
                    )
                else:
                    mistake_code = "AGENT_REVERSAL_SL_SAVED"
                    mistake_title = f"Defensive Reversal Cut ({exit_reason}) at {r_mult:+.2f}R — Saved Full -1.00R SL!"
                    mistake_desc = (
                        f"After {hold_mins}m with low traction (MFE +{mfe_r:.2f}R), >70% of active agents flagged an opposite "
                        f"breakout + CVD surge heading straight for SL ({sl_px:.2f}). Cut early at {exit_px:.2f} ({r_mult:+.2f}R), saving {(1.0 + r_mult)*100:.0f}% of the stop loss!"
                    )
                    learner_fix = (
                        f"ORACLE + VICTOR Emergency Cut: Reduced -$5.00 full stop risk down to ${net_pnl:+.2f} net after 70%+ agents flipped opposite."
                    )
            else:  # TIME_EXIT
                mistake_code = "TIME_DECAY_EXIT"
                mistake_title = f"Max Hold Window Reached ({hold_mins}m) at {r_mult:+.2f}R"
                mistake_desc = (
                    f"Trade peaked at +{mfe_r:.2f}R and closed at {r_mult:+.2f}R (${net_pnl:+.2f} net) when the "
                    f"{prof['max_hold_mins']}m session timer expired."
                )
                learner_fix = (
                    "LEO & RYAN Directive: Time-stop prevented overnight/post-killzone drift while preserving open profit."
                )

            w_key = str(int(unix_secs[i_ent]))

            trades_list.append({
                "id": int(tid + 1),
                "w_key": w_key,
                "entry_ts": int(unix_secs[i_ent]),
                "exit_ts": int(unix_secs[i_ext]),
                "entry_time": ent_ts.strftime("%Y-%m-%d %H:%M UTC"),
                "exit_time": ext_ts.strftime("%Y-%m-%d %H:%M UTC"),
                "date": date_str,
                "month": month_str,
                "day_of_week": day_name,
                "session": session,
                "season": season,
                "setup_agent": str(row["setup_agent"]),
                "setup_type": str(row["setup_type"]),
                "regime": str(row["regime"]),
                "direction": direction,
                "entry_price": entry_px,
                "exit_price": exit_px,
                "sl_price": sl_px,
                "tp1_price": tp1_px,
                "tp2_price": tp2_px,
                "init_risk_pts": risk_pts,
                "pnl_pts": float(row["pnl_pts"]),
                "r_multiple": r_mult,
                "qty_oz": qty_oz,
                "notional_usd": notional_usd,
                "gross_pnl_usd": gross_pnl,
                "delta_fee_usd": delta_fee,
                "net_pnl_usd": net_pnl,
                "equity_after": float(row["equity_after"]),
                "consensus_pct": float(row["consensus_pct"]),
                "confirming_count": int(row["confirming_agents_count"]),
                "confirming_agents": str(row["confirming_agents"]).split("|"),
                "skipped_agents": [x for x in str(row.get("skipped_agents", "NONE")).split("|") if x and x != "NONE"],
                "analyser_brief": str(row.get("analyser_brief", "")),
                "scalper_bypass": bool(row.get("scalper_bypass", False)),
                "council_verdict": str(row.get("council_verdict", "")),
                "has_l2": bool(row["has_l2"]),
                "exit_reason": exit_reason,
                "hold_mins": hold_mins,
                "mfe_pts": round(mfe_pts, 2),
                "mfe_r": mfe_r,
                "mae_pts": round(mae_pts, 2),
                "mae_r": mae_r,
                "post_60m_pts": round(post_60m_pts, 2),
                "post_60m_r": post_60m_r,
                "chop_15m": round(float(chop[i_ent]), 1),
                "adx_15m": round(float(adx[i_ent]), 1),
                "atr_15m": round(float(atr15m[i_ent]), 2),
                "vol_z": round(float(vol_z[i_ent]), 2),
                "l2_ratio": round(float(l2_mean[i_ent]), 2),
                "delta_5m": round(float(delta5[i_ent]), 0),
                "delta_15m": round(float(delta15[i_ent]), 0),
                "fib_240_pct": round(float(fib_val * 100.0), 1),
                "wick_ratio": round(float(wick_val), 2),
                "spread_pts": round(float(spread[i_ent]), 2),
                "mistake_code": mistake_code,
                "mistake_title": mistake_title,
                "mistake_desc": mistake_desc,
                "learner_fix": learner_fix,
                "pros": pros,
            })

        profiles_data[pname] = {
            "meta": prof,
            "trades": trades_list,
        }
        print(f"  -> Processed profile {pname}: {len(trades_list)} trades")

    # Encode ALL 699,702 1-minute GC.v.0 bars losslessly for continuous multi-month / 5-month interactive panning & zooming
    ts_min = (unix_secs // 60).astype(np.int64)
    dt_u16 = np.diff(ts_min, prepend=ts_min[0]).clip(0, 65535).astype("<u2")
    o_d = np.round(opens * 10.0).astype(np.int64)
    h_d = np.round(highs * 10.0).astype(np.int64)
    l_d = np.round(lows * 10.0).astype(np.int64)
    c_d = np.round(closes * 10.0).astype(np.int64)

    do_i16 = np.diff(o_d, prepend=o_d[0]).clip(-32768, 32767).astype("<i2")
    dh_u16 = (h_d - o_d).clip(0, 65535).astype("<u2")
    dl_u16 = (o_d - l_d).clip(0, 65535).astype("<u2")
    dc_i16 = (c_d - o_d).clip(-32768, 32767).astype("<i2")
    v_u16 = np.clip(vols, 0, 65535).astype("<u2")

    continuous_1m = {
        "n": int(len(df)),
        "start_ts_min": int(ts_min[0]),
        "start_open_d": int(o_d[0]),
        "dt": base64.b64encode(dt_u16.tobytes()).decode("ascii"),
        "do": base64.b64encode(do_i16.tobytes()).decode("ascii"),
        "dh": base64.b64encode(dh_u16.tobytes()).decode("ascii"),
        "dl": base64.b64encode(dl_u16.tobytes()).decode("ascii"),
        "dc": base64.b64encode(dc_i16.tobytes()).decode("ascii"),
        "v": base64.b64encode(v_u16.tobytes()).decode("ascii"),
    }
    print(f"[HTML BUILDER] Encoded {len(df):,} continuous 1m GC.v.0 bars across all months.")
    return profiles_data, continuous_1m


if __name__ == "__main__":
    profiles_data, continuous_1m = build_dashboard()
    trust_path = os.path.join(PROCESSED_DIR, "agent_trust_weights.json")
    trust_bench = {}
    if os.path.exists(trust_path):
        with open(trust_path, "r", encoding="utf-8") as tf:
            trust_bench = json.load(tf)

    bundle_path = os.path.join(PROCESSED_DIR, "all_11_agents_lab_bundle.json")
    candles_path = os.path.join(PROCESSED_DIR, "lab_candles_15m.json")

    agents_bundle = {}
    if os.path.exists(bundle_path):
        with open(bundle_path, "r", encoding="utf-8") as f:
            agents_bundle = json.load(f)
        for aid, data in agents_bundle.items():
            data.pop("top_combos", None)
            if "1m" in data.get("timeframes", {}):
                tf1m = dict(data["timeframes"]["1m"])
                tf1m.pop("trades", None)
                data["timeframes"]["1m"] = tf1m

    lab_candles = []
    if os.path.exists(candles_path):
        with open(candles_path, "r", encoding="utf-8") as f:
            lab_candles = json.load(f)

    payload_path = os.path.join(PROCESSED_DIR, "dashboard_payload.json")
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "profiles": profiles_data,
                "continuous_1m": continuous_1m,
                "trust_benchmark": trust_bench,
                "agent_lab": agents_bundle,
                "lab_candles": lab_candles,
            },
            f,
            separators=(",", ":"),
        )
    print(f"[HTML BUILDER] Saved JSON payload ({os.path.getsize(payload_path)/1024/1024:.2f} MB) to {payload_path}")
