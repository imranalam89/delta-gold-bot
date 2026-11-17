"""
Builds `backtest_dashboard.html` as the Complete All-in-One Master Dashboard:
1. 🏆 Combined Master Floor: Non-Overlapping Master Book (296 trades, 65.88% WR, +$234.75 Net, 2.69 trades/day) + Elite Pods
2. 🧪 11-Field-Specialist Laboratory: Full individual agent audits (1:ALEX to 11:LIAM), 3-gen evolution, 1m/5m/15m/1h cards, Sarah/Lucas/Oracle logs
3. 📊 Continuous TradingView Chart: 1m to 1D candles, trade markers, TP/SL overlays, timeline navigator
4. 📅 Daily P&L Calendar & Equity Growth Simulator: Heatmap calendar, equity & drawdown curves, killzone/weekday analytics
5. 🔬 Trade Journal & Multi-Agent Forensic Auditor: Full trade logs, 16-agent reliability matrix, CSV export
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD_PATH = os.path.join(BASE_DIR, "data", "processed", "dashboard_payload.json")
OUT_HTML = os.path.join(BASE_DIR, "backtest_dashboard.html")


def generate_all_in_one_html():
    print(f"[ALL-IN-ONE BUILDER] Reading payload from {PAYLOAD_PATH}...")
    with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
        payload_str = f.read()

    print(f"[ALL-IN-ONE BUILDER] Payload size: {len(payload_str)/1024/1024:.2f} MB")
    
    # We will embed payload_str into the HTML template replacing __PAYLOAD_JSON__
    from scripts.render_html import HTML_TEMPLATE
    
    html_out = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", payload_str)
    
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)
        
    print(f"[SUCCESS] Generated All-in-One Master Dashboard: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    generate_all_in_one_html()
