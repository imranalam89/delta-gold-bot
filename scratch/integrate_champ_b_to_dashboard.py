import json
import os
import sys
import csv
sys.path.insert(0, '.')
from datetime import datetime, timezone

print("[INTEGRATION] Starting Champion B (Max Profit) Dashboard Integration...")

# 1. Run simulation to get full trade records
from scratch.generate_champ_b_profile import executed_trades, tot_net, wr, max_dd_pct, pf, equity

print(f"[INTEGRATION] Generated {len(executed_trades)} trades for Champion B.")

champ_b_meta = {
    "name": "CHAMPION_B_MAX_PROFIT",
    "label": f"👑 Strategy 0: Champion B (Max Profit) | {len(executed_trades)} Trades | {wr:.2f}% WR | +${tot_net:.2f} Net | ${equity:.2f} Eq | PF {pf:.2f}",
    "pod_type": "ALL_11_CONCURRENT_SLOTS",
    "agents": None,
    "max_slots": 2,
    "sl_atr_mult": 1.25,
    "tp1_r": 1.80,
    "tp2_r": 3.35,
    "be_trigger_r": 1.05,
    "be_lock_r": 0.38,
    "trail_trigger_r": 2.50,
    "trail_dist_r": 1.05,
    "stall_trig_r": 0.54,
    "stall_bars": 6,
    "stall_lock_r": 0.28,
    "cooldown_mins": 8,
    "max_hold_mins": 1440,
    "adaptive_regime": True
}

# 2. Save CSV log for export button
csv_path = os.path.join("data", "processed", "trades_CHAMPION_B_MAX_PROFIT.csv")
csv_cols = [
    "id", "entry_time", "exit_time", "direction", "setup_agent", "entry_price", "exit_price",
    "sl_price", "tp1_price", "tp2_price", "init_risk_pts", "pnl_pts", "r_multiple",
    "qty_oz", "notional_usd", "gross_pnl_usd", "delta_fee_usd", "net_pnl_usd",
    "equity_after", "exit_reason", "session", "regime"
]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=csv_cols, extrasaction="ignore")
    writer.writeheader()
    for t in executed_trades:
        writer.writerow(t)

print(f"[INTEGRATION] Saved {csv_path} ({os.path.getsize(csv_path)/1024:.1f} KB)")

# 3. Load dashboard_payload.json
payload_path = os.path.join("data", "processed", "dashboard_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

# Reorder profiles so CHAMPION_B_MAX_PROFIT is the first (default) strategy
new_profiles = {
    "CHAMPION_B_MAX_PROFIT": {
        "meta": champ_b_meta,
        "trades": executed_trades
    }
}

for k, v in payload.get("profiles", {}).items():
    if k != "CHAMPION_B_MAX_PROFIT":
        new_profiles[k] = v

payload["profiles"] = new_profiles

# 4. Save updated dashboard_payload.json
with open(payload_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, separators=(",", ":"))

print(f"[INTEGRATION] Updated {payload_path} ({os.path.getsize(payload_path)/1024/1024:.2f} MB)")

# 5. Rebuild backtest_dashboard.html
out_html = "backtest_dashboard.html"
from scripts.render_html import HTML_TEMPLATE

with open(payload_path, "r", encoding="utf-8") as f:
    payload_str = f.read()

html_out = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", payload_str)

with open(out_html, "w", encoding="utf-8") as f:
    f.write(html_out)

print(f"[SUCCESS] Rebuilt {out_html} ({os.path.getsize(out_html)/1024/1024:.2f} MB) with Champion B as #1 Default Strategy!")
