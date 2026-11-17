"""
Builds a dedicated, standalone, institutional-grade deep dive HTML dashboard
for backtest MUX_085SL_40R_CONTINUOUS_TRAIL (New 40R Continuous Trail).
Equipped with high-performance 60 FPS HTML5 Canvas TradingView candlestick engine.
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD_PATH = os.path.join(BASE_DIR, "data", "processed", "dashboard_payload.json")
OUT_HTML = os.path.join(BASE_DIR, "backtest_MUX_085SL_40R_CONTINUOUS_TRAIL.html")

def build_dashboard():
    print(f"Loading data from {PAYLOAD_PATH}...")
    with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
        full_data = json.load(f)

    target_profile_key = "MUX_085SL_40R_CONTINUOUS_TRAIL"
    if target_profile_key not in full_data.get("profiles", {}):
        raise ValueError(f"Profile {target_profile_key} not found in payload!")

    profile = full_data["profiles"][target_profile_key]
    continuous_1m = full_data.get("continuous_1m", {})

    print(f"Target profile loaded: {len(profile.get('trades', []))} trades")
    print(f"Continuous 1m bars: {continuous_1m.get('n', 0)} bars")

    # Extract dedicated payload
    sub_payload = {
        "profile": profile,
        "continuous_1m": continuous_1m
    }

    sub_payload_json = json.dumps(sub_payload)
    print(f"Sub-payload size: {len(sub_payload_json) / 1024 / 1024:.2f} MB")

    html_content = generate_html(sub_payload_json)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_size_mb = os.path.getsize(OUT_HTML) / 1024 / 1024
    print(f"Successfully generated {OUT_HTML} ({file_size_mb:.2f} MB)")

def generate_html(payload_json: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Backtest Dossier — MUX_085SL_40R_CONTINUOUS_TRAIL (New 40R Continuous Trail)</title>
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
    --tv-green-dim: rgba(16, 185, 129, 0.15);
    --tv-red: #ef4444;
    --tv-red-dim: rgba(239, 68, 68, 0.15);
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
  a {{ color: var(--tv-cyan); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* Top Sticky Bar */
  .header-bar {{
    background: linear-gradient(180deg, #111624 0%, #0a0d15 100%);
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }}
  .brand-area {{
    display: flex;
    align-items: center;
    gap: 14px;
  }}
  .badge-crown {{
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #000;
    font-weight: 800;
    font-size: 11px;
    padding: 5px 10px;
    border-radius: 4px;
    letter-spacing: 0.8px;
    display: flex;
    align-items: center;
    gap: 5px;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
  }}
  .brand-info h1 {{
    font-size: 17px;
    font-weight: 700;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .brand-info p {{
    font-size: 12px;
    color: var(--text-muted);
  }}
  .header-actions {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .btn {{
    background: var(--bg-card);
    color: var(--text-main);
    border: 1px solid var(--border);
    padding: 7px 14px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .btn:hover {{
    background: var(--bg-card-hover);
    border-color: var(--tv-blue);
    transform: translateY(-1px);
  }}
  .btn.btn-primary {{
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    border-color: #3b82f6;
    color: #fff;
    box-shadow: 0 2px 10px rgba(37, 99, 235, 0.3);
  }}
  .btn.btn-gold {{
    background: linear-gradient(135deg, #d97706, #b45309);
    border-color: #f59e0b;
    color: #fff;
  }}
  .btn.btn-success {{
    background: linear-gradient(135deg, #059669, #047857);
    border-color: #10b981;
    color: #fff;
  }}

  /* Main Container */
  .container {{
    max-width: 1780px;
    margin: 0 auto;
    padding: 20px 24px 80px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}

  /* KPI Grid */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
  }}
  .kpi-card {{
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 16px;
    transition: border-color 0.2s;
  }}
  .kpi-card:hover {{
    border-color: var(--border-light);
  }}
  .kpi-label {{
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .kpi-val {{
    font-size: 22px;
    font-weight: 700;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    letter-spacing: -0.5px;
    line-height: 1.2;
  }}
  .kpi-sub {{
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 4px;
  }}
  .text-green {{ color: var(--tv-green); }}
  .text-red {{ color: var(--tv-red); }}
  .text-gold {{ color: var(--gold); }}
  .text-cyan {{ color: var(--tv-cyan); }}
  .text-blue {{ color: var(--tv-blue); }}
  .text-purple {{ color: var(--purple); }}

  /* Strategy Architecture Ribbon */
  .arch-strip {{
    background: linear-gradient(135deg, #101626 0%, #161a29 100%);
    border: 1px solid var(--border);
    border-left: 4px solid var(--gold);
    border-radius: 8px;
    padding: 16px 20px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
  }}
  .arch-item {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .arch-title {{
    font-size: 12px;
    font-weight: 700;
    color: var(--gold);
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .arch-desc {{
    font-size: 11.5px;
    color: var(--text-muted);
    line-height: 1.4;
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
    padding: 9px 18px;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
  }}
  .tab-btn:hover {{
    background: var(--bg-card);
    color: var(--text-main);
  }}
  .tab-btn.active {{
    background: var(--tv-blue);
    border-color: var(--tv-blue);
    color: #fff;
    box-shadow: 0 2px 10px rgba(59, 130, 246, 0.35);
  }}
  .tab-btn .badge-count {{
    background: rgba(255, 255, 255, 0.2);
    font-size: 10.5px;
    padding: 2px 6px;
    border-radius: 10px;
  }}

  /* Tab Contents */
  .tab-pane {{
    display: none;
    flex-direction: column;
    gap: 20px;
  }}
  .tab-pane.active {{
    display: flex;
  }}

  /* Panel Cards */
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
  }}
  .panel-title {{
    font-size: 13.5px;
    font-weight: 700;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .panel-body {{
    padding: 16px 18px;
  }}

  /* Grid Layouts */
  .grid-2 {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
    gap: 16px;
  }}
  .grid-3 {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 14px;
  }}

  /* Tables */
  .data-table-wrap {{
    overflow-x: auto;
    width: 100%;
  }}
  table.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    text-align: left;
  }}
  table.data-table th {{
    background: #111624;
    color: var(--text-muted);
    font-weight: 600;
    padding: 9px 12px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 2;
    cursor: pointer;
  }}
  table.data-table th:hover {{
    color: #fff;
  }}
  table.data-table td {{
    padding: 8px 12px;
    border-bottom: 1px solid #1a2130;
    white-space: nowrap;
  }}
  table.data-table tr:hover td {{
    background: rgba(59, 130, 246, 0.08);
  }}
  table.data-table tr.clickable {{
    cursor: pointer;
  }}
  table.data-table tr.selected td {{
    background: rgba(245, 158, 11, 0.16) !important;
    border-bottom: 1px solid var(--gold);
  }}

  /* Canvas Chart Containers */
  .chart-canvas-box {{
    position: relative;
    width: 100%;
    height: 380px;
    background: #090c13;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
  }}
  canvas#equityChartCanvas {{
    width: 100%;
    height: 100%;
    display: block;
  }}

  /* TRADINGVIEW WORKSPACE */
  .tv-chart-box {{
    position: relative;
    width: 100%;
    height: 600px;
    background: #090c13;
    border: 1px solid var(--border);
    border-radius: 6px 6px 0 0;
    overflow: hidden;
  }}
  canvas#tvChart {{
    width: 100%;
    height: 100%;
    display: block;
    cursor: crosshair;
  }}
  .tv-nav-box {{
    width: 100%;
    height: 48px;
    background: #06080d;
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 6px 6px;
    display: block;
    cursor: pointer;
  }}
  .chart-toolbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 14px;
    background: #0c1018;
    border-bottom: 1px solid var(--border);
    gap: 10px;
    flex-wrap: wrap;
  }}
  .tf-group {{
    display: flex;
    gap: 4px;
  }}
  .tf-btn {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 4px 9px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
  }}
  .tf-btn:hover {{ background: #1c2336; color: #fff; }}
  .tf-btn.active {{ background: var(--tv-blue); color: #fff; border-color: var(--tv-blue); }}

  /* Calendar Heatmap */
  .calendar-nav {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
  }}
  .cal-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
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
    background: #111624;
    border: 1px solid #1c2438;
    border-radius: 6px;
    min-height: 86px;
    padding: 7px 8px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.15s;
    cursor: pointer;
  }}
  .cal-day:hover {{
    transform: translateY(-2px);
    border-color: var(--tv-blue);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  }}
  .cal-day.empty {{
    background: transparent;
    border-color: transparent;
    cursor: default;
  }}
  .cal-day.win-day {{
    background: linear-gradient(180deg, #0d221c 0%, #101c1f 100%);
    border-color: rgba(16, 185, 129, 0.4);
  }}
  .cal-day.loss-day {{
    background: linear-gradient(180deg, #261115 0%, #1c1015 100%);
    border-color: rgba(239, 68, 68, 0.4);
  }}
  .cal-day.selected {{
    outline: 2px solid var(--gold);
    box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
  }}
  .cal-day-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
  }}
  .cal-day-num {{
    font-weight: 700;
    color: #e2e8f0;
  }}
  .cal-day-count {{
    font-size: 10px;
    color: var(--text-muted);
    background: rgba(255,255,255,0.08);
    padding: 1px 4px;
    border-radius: 3px;
  }}
  .cal-day-pnl {{
    font-size: 13px;
    font-weight: 700;
    font-family: ui-monospace, SFMono-Regular, monospace;
    margin-top: 4px;
  }}
  .cal-day-bot {{
    font-size: 10px;
    color: var(--text-dim);
    display: flex;
    justify-content: space-between;
  }}

  /* Filter Toolbar */
  .filter-bar {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    background: var(--bg-card);
    padding: 10px 14px;
    border-radius: 6px;
    border: 1px solid var(--border);
    margin-bottom: 12px;
  }}
  select, input[type="text"] {{
    background: #0d111a;
    color: var(--text-main);
    border: 1px solid var(--border);
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 12px;
  }}
  select:focus, input[type="text"]:focus {{
    outline: none;
    border-color: var(--tv-blue);
  }}

  /* Badges */
  .badge {{
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }}
  .badge.badge-long {{ background: rgba(16, 185, 129, 0.2); color: var(--tv-green); border: 1px solid rgba(16, 185, 129, 0.4); }}
  .badge.badge-short {{ background: rgba(239, 68, 68, 0.2); color: var(--tv-red); border: 1px solid rgba(239, 68, 68, 0.4); }}
  .badge.badge-oos {{ background: rgba(168, 85, 247, 0.2); color: var(--purple); border: 1px solid rgba(168, 85, 247, 0.4); }}
  .badge.badge-is {{ background: rgba(59, 130, 246, 0.2); color: var(--tv-blue); border: 1px solid rgba(59, 130, 246, 0.4); }}
  .badge.badge-trail {{ background: rgba(245, 158, 11, 0.2); color: var(--gold); border: 1px solid rgba(245, 158, 11, 0.4); }}
  .badge.badge-sl {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }}
  .badge.badge-stall {{ background: rgba(6, 182, 212, 0.2); color: var(--tv-cyan); border: 1px solid rgba(6, 182, 212, 0.4); }}

  /* Modal Dialog */
  .modal-overlay {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.78);
    backdrop-filter: blur(5px);
    z-index: 1000;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }}
  .modal-overlay.open {{ display: flex; }}
  .modal-card {{
    background: #0f1420;
    border: 1px solid var(--border-light);
    border-radius: 10px;
    width: 100%;
    max-width: 900px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 40px rgba(0,0,0,0.8);
    animation: modalPop 0.2s ease;
  }}
  @keyframes modalPop {{
    from {{ transform: scale(0.96); opacity: 0; }}
    to {{ transform: scale(1); opacity: 1; }}
  }}
  .modal-head {{
    background: #141b2c;
    border-bottom: 1px solid var(--border);
    padding: 14px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .modal-body {{
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .modal-foot {{
    background: #141b2c;
    border-top: 1px solid var(--border);
    padding: 12px 20px;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }}
  .audit-sec {{
    background: #141a29;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 14px;
  }}
  .audit-sec-title {{
    font-size: 11px;
    font-weight: 700;
    color: var(--gold);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .radar-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 8px;
    margin-top: 6px;
  }}
  .radar-box {{
    background: #0d121c;
    border: 1px solid #1a2233;
    border-radius: 4px;
    padding: 6px 8px;
    text-align: center;
  }}
  .radar-lbl {{ font-size: 10px; color: var(--text-dim); text-transform: uppercase; }}
  .radar-val {{ font-size: 13px; font-weight: 700; color: #fff; font-family: ui-monospace, monospace; }}

  /* Scrollbars */
  ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
  ::-webkit-scrollbar-track {{ background: #080a10; }}
  ::-webkit-scrollbar-thumb {{ background: #1f2738; border-radius: 4px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: #2f3b54; }}
</style>
</head>
<body>

<!-- Header -->
<header class="header-bar">
  <div class="brand-area">
    <div class="badge-crown">👑 #1 APEX CHAMPION</div>
    <div class="brand-info">
      <h1>MUX_085SL_40R_CONTINUOUS_TRAIL <span style="font-weight: normal; font-size: 13px; color: var(--gold);">(New 40R Continuous Trail)</span></h1>
      <p>Institutional 5-Month Gold Backtest Dossier • 100% Mon-Fri Single-Slot Execution • Instant Pre-SL Cut Active</p>
    </div>
  </div>
  <div class="header-actions">
    <button class="btn btn-primary" onclick="switchTab('tab-chart')">📈 Open TradingView Chart</button>
    <button class="btn btn-gold" onclick="exportTradesCSV()">📥 Export 265 Trades (CSV)</button>
    <button class="btn" onclick="exportMetadataJSON()">💾 Export JSON</button>
    <button class="btn" onclick="window.print()">🖨️ Print / PDF</button>
  </div>
</header>

<main class="container">

  <!-- Core KPI Grid -->
  <section class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Final Equity ($100 Init) <span class="text-green">+430.70%</span></div>
      <div class="kpi-val text-green">$530.70</div>
      <div class="kpi-sub">Net Profit: +$430.70 (+$568.85 Gross)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Win Rate / Payoff <span class="text-gold">162W / 103L</span></div>
      <div class="kpi-val text-gold">61.13%</div>
      <div class="kpi-sub">Win/Loss: 1.20x | Avg Win: $5.66 / Loss: -$4.73</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Profit Factor <span class="text-cyan">Institutional</span></div>
      <div class="kpi-val text-cyan">1.88</div>
      <div class="kpi-sub">Total Fees Paid: $138.15 (0.01% Delta)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Total Trades <span class="text-blue">Single Slot</span></div>
      <div class="kpi-val text-blue">265</div>
      <div class="kpi-sub">Zero Overlaps | 2.62 Trades / Day</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Max Drawdown <span class="text-red">Low Risk</span></div>
      <div class="kpi-val text-red">-18.43%</div>
      <div class="kpi-sub">Peak-to-Trough: -$36.38 (Fast V-Recovery)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Day Coverage <span class="text-green">Consistency</span></div>
      <div class="kpi-val text-green">90.2%</div>
      <div class="kpi-sub">101 Active Trading Days / 112 Weekdays</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Max Single Runner <span class="text-purple">Continuous 40R</span></div>
      <div class="kpi-val text-purple">+7.67R</div>
      <div class="kpi-sub">Gross Single Leg: +8.92R ($44.12 Net)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Out-of-Sample (OOS) <span class="text-cyan">81 Trades</span></div>
      <div class="kpi-val text-cyan">58.02%</div>
      <div class="kpi-sub">OOS Net: +$140.03 | OOS PF: 1.89</div>
    </div>
  </section>

  <!-- Architectural Blueprint Ribbon -->
  <section class="arch-strip">
    <div class="arch-item">
      <div class="arch-title">🛡️ 0.85x SL Initial Risk Sizing</div>
      <div class="arch-desc">Tightened initial ATR baseline risk to 0.85x ($4.73 avg loss), preventing adverse capital leakage and maintaining maximum dry powder for high-expectancy setups.</div>
    </div>
    <div class="arch-item">
      <div class="arch-title">🚀 40R Continuous SL/TP Trail</div>
      <div class="arch-desc">Uncapped bar-by-bar ratcheting trailing engine triggered at +2.10R with 0.45R trailing offset. Captured 49 super-runner trades banking <b>+$177.58 alone</b> (87.8% WR).</div>
    </div>
    <div class="arch-item">
      <div class="arch-title">⚡ Instant Pre-SL Cut (Defensive)</div>
      <div class="arch-desc">Early order flow liquidation triggers the second CVD delta flips opposite or order book depth drops below threshold, saving 14 trades at small -$4.19 scratches rather than full stops.</div>
    </div>
    <div class="arch-item">
      <div class="arch-title">🔒 Smart Stall Lock (Greed Guard)</div>
      <div class="arch-desc">Locks +0.28R after 6 stagnant bars past +0.54R excursion. Banked 33 winning trades (+ $37.61, 100% WR), permanently curing chop givebacks.</div>
    </div>
  </section>

  <!-- Navigation Tabs -->
  <nav class="tab-nav">
    <button class="tab-btn" data-tab="tab-analytics" onclick="switchTab('tab-analytics')">
      📊 Dossier &amp; Analytics
    </button>
    <button class="tab-btn active" data-tab="tab-chart" onclick="switchTab('tab-chart')">
      📈 TradingView Candlestick Chart <span class="badge-count">151,343 Bars</span>
    </button>
    <button class="tab-btn" data-tab="tab-calendar" onclick="switchTab('tab-calendar')">
      📅 5-Month P&amp;L Calendar <span class="badge-count">101 Days</span>
    </button>
    <button class="tab-btn" data-tab="tab-journal" onclick="switchTab('tab-journal')">
      📋 265-Trade Complete Journal <span class="badge-count">265 Trades</span>
    </button>
    <button class="tab-btn" data-tab="tab-agents" onclick="switchTab('tab-agents')">
      🤖 16-Agent Syndicate &amp; Playbooks
    </button>
  </nav>

  <!-- TAB 1: Dossier & Analytics -->
  <div id="tab-analytics" class="tab-pane">

    <!-- Equity Curve & Drawdown Chart -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📈 Trade-by-Trade Equity Progression &amp; Underwater Drawdown ($100 Starting Balance)</div>
        <div style="font-size: 11.5px; color: var(--text-muted);">
          In-Sample: Trades #1–#184 (+$290.67) | Out-of-Sample: Trades #185–#265 (+$140.03)
        </div>
      </div>
      <div class="panel-body">
        <div class="chart-canvas-box" style="height: 340px;">
          <canvas id="equityChartCanvas"></canvas>
        </div>
      </div>
    </div>

    <!-- Monthly & Session Tables -->
    <div class="grid-2">
      <!-- Monthly Breakdown -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">📅 Monthly Performance Breakdown (June – October 2026)</div>
          <span class="badge badge-long">100% Green Months</span>
        </div>
        <div class="panel-body" style="padding: 0;">
          <div class="data-table-wrap">
            <table class="data-table" id="monthlyStatsTable">
              <thead>
                <tr>
                  <th>Month</th>
                  <th>Trades</th>
                  <th>Win Rate</th>
                  <th>Wins / Loss</th>
                  <th>Net P&amp;L ($)</th>
                  <th>Fees ($)</th>
                  <th>Profit Factor</th>
                </tr>
              </thead>
              <tbody><!-- Populated via JS --></tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Session Breakdown -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">🌍 Session Performance (Killzones)</div>
          <span class="badge badge-long">All Sessions Profitable</span>
        </div>
        <div class="panel-body" style="padding: 0;">
          <div class="data-table-wrap">
            <table class="data-table" id="sessionStatsTable">
              <thead>
                <tr>
                  <th>Killzone Session</th>
                  <th>Trades</th>
                  <th>Win Rate</th>
                  <th>Net P&amp;L ($)</th>
                  <th>Avg / Trade</th>
                  <th>Volume %</th>
                </tr>
              </thead>
              <tbody><!-- Populated via JS --></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Direction & Day of Week -->
    <div class="grid-2">
      <!-- Day of Week Breakdown -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">📆 Day-of-Week Distribution (Monday to Friday)</div>
          <span class="badge badge-long">5/5 Profitable Days</span>
        </div>
        <div class="panel-body" style="padding: 0;">
          <div class="data-table-wrap">
            <table class="data-table" id="dowStatsTable">
              <thead>
                <tr>
                  <th>Day of Week</th>
                  <th>Trades</th>
                  <th>Win Rate</th>
                  <th>Net P&amp;L ($)</th>
                  <th>Avg Win</th>
                  <th>Avg Loss</th>
                </tr>
              </thead>
              <tbody><!-- Populated via JS --></tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Direction & Duration Breakdown -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">⚖️ Directional &amp; Holding Duration Analysis</div>
        </div>
        <div class="panel-body" style="padding: 0;">
          <div class="data-table-wrap">
            <table class="data-table" id="directionStatsTable">
              <thead>
                <tr>
                  <th>Direction / Duration</th>
                  <th>Trades</th>
                  <th>Win Rate</th>
                  <th>Net P&amp;L ($)</th>
                  <th>Max Win</th>
                  <th>Share %</th>
                </tr>
              </thead>
              <tbody><!-- Populated via JS --></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Exit Reasons Table -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🎯 Complete Exit Reason Distribution (Mechanic Attribution)</div>
        <div style="font-size: 11px; color: var(--gold);">40R Continuous Trail is the #1 Contributor (+$177.58 Net)</div>
      </div>
      <div class="panel-body" style="padding: 0;">
        <div class="data-table-wrap">
          <table class="data-table" id="exitReasonTable">
            <thead>
              <tr>
                <th>Exit Mechanism</th>
                <th>Count</th>
                <th>Win Rate</th>
                <th>Total Net P&amp;L ($)</th>
                <th>Avg Net P&amp;L ($)</th>
                <th>Strategic Role</th>
              </tr>
            </thead>
            <tbody><!-- Populated via JS --></tbody>
          </table>
        </div>
      </div>
    </div>

  </div> <!-- /tab-analytics -->

  <!-- TAB 2: Interactive TradingView Candlestick Chart -->
  <div id="tab-chart" class="tab-pane active">
    <div class="panel">
      <div class="chart-toolbar">
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
          <span style="font-weight: 700; color: #fff;">Gold Futures (GC.v.0 Continuous)</span>
          <div class="tf-group">
            <button class="tf-btn" data-tf="1">1m</button>
            <button class="tf-btn active" data-tf="5">5m</button>
            <button class="tf-btn" data-tf="15">15m</button>
            <button class="tf-btn" data-tf="60">1h</button>
            <button class="tf-btn" data-tf="240">4h</button>
          </div>
          <span style="color: var(--text-dim);">|</span>
          <select id="tradeJumpSelect" style="width: 280px;">
            <!-- Populated via JS -->
          </select>
          <button class="btn" id="prevTradeBtn" style="padding: 4px 8px;">◀ Prev</button>
          <button class="btn" id="nextTradeBtn" style="padding: 4px 8px;">Next ▶</button>
          <button class="btn btn-primary" id="zoomTradeBtn" style="padding: 4px 10px;">🔍 Focus Trade</button>
          <button class="btn" id="fit5MonthBtn" style="padding: 4px 10px;">🌐 Fit 5-Month Window</button>
        </div>
        <div style="font-size: 11px; color: var(--text-muted);" id="visibleRangeSummary">
          Scroll wheel to zoom · Drag to pan · Hover for crosshair · Click any trade badge to inspect
        </div>
      </div>

      <div class="tv-chart-box">
        <canvas id="tvChart"></canvas>
      </div>
      <canvas id="tvNavChart" class="tv-nav-box"></canvas>

      <!-- Active Trade Banner Below Chart -->
      <div id="chartTradeBanner" style="background: #0d121c; border-top: 1px solid var(--border); padding: 10px 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
        <div id="bannerTradeText" style="font-size: 12.5px; font-weight: 600;">
          Select or click a trade on the chart above to inspect full order flow &amp; microstructure telemetry.
        </div>
        <button class="btn btn-gold" id="bannerInspectBtn" style="display: none; padding: 4px 10px;" onclick="openSelectedTradeModal()">
          🔍 Open Institutional Trade Audit
        </button>
      </div>
    </div>
  </div> <!-- /tab-chart -->

  <!-- TAB 3: 5-Month P&L Calendar -->
  <div id="tab-calendar" class="tab-pane">
    <div class="panel">
      <div class="panel-header">
        <div class="calendar-nav">
          <button class="btn" id="calPrevMonthBtn">◀</button>
          <select id="calMonthSelect" style="font-weight: 700; font-size: 13px;">
            <option value="2026-06">June 2026</option>
            <option value="2026-07">July 2026</option>
            <option value="2026-08">August 2026</option>
            <option value="2026-09">September 2026</option>
            <option value="2026-10" selected>October 2026</option>
          </select>
          <button class="btn" id="calNextMonthBtn">▶</button>
        </div>
        <div id="calMonthSummaryBadge" style="font-size: 12px; font-weight: 700; color: var(--tv-green);">
          October 2026: 54 Trades · 61.1% WR · +$143.18 Net
        </div>
      </div>
      <div class="panel-body">
        <div class="cal-grid">
          <div class="cal-header">Sun</div>
          <div class="cal-header">Mon</div>
          <div class="cal-header">Tue</div>
          <div class="cal-header">Wed</div>
          <div class="cal-header">Thu</div>
          <div class="cal-header">Fri</div>
          <div class="cal-header">Sat</div>
        </div>
        <div class="cal-grid" id="calDaysGrid">
          <!-- Populated via JS -->
        </div>
        <div style="margin-top: 14px; font-size: 11.5px; color: var(--text-dim); display: flex; align-items: center; justify-content: space-between;">
          <span>💡 Tip: Click on any active trading day to instantly filter the Trade Journal table to that date.</span>
          <button class="btn" style="padding: 3px 8px; font-size: 11px;" onclick="clearDateFilter()">Show All 265 Trades</button>
        </div>
      </div>
    </div>
  </div> <!-- /tab-calendar -->

  <!-- TAB 4: 265-Trade Complete Journal -->
  <div id="tab-journal" class="tab-pane">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📋 Complete 265-Trade Execution Journal &amp; Forensic Log</div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-gold" onclick="exportTradesCSV()">📥 Download CSV</button>
        </div>
      </div>
      <div class="panel-body">
        <!-- Filter Toolbar -->
        <div class="filter-bar">
          <label style="font-size: 11px; color: var(--text-muted); font-weight: 600;">FILTERS:</label>
          <select id="filterDirection">
            <option value="ALL">Direction: All (265)</option>
            <option value="LONG">Longs Only (106)</option>
            <option value="SHORT">Shorts Only (159)</option>
          </select>
          <select id="filterOutcome">
            <option value="ALL">Outcome: All</option>
            <option value="WIN">Winners (162)</option>
            <option value="LOSS">Losses (103)</option>
          </select>
          <select id="filterSample">
            <option value="ALL">Sample: In + Out</option>
            <option value="IS">In-Sample #1–#184</option>
            <option value="OOS">Out-of-Sample #185–#265</option>
          </select>
          <select id="filterExitReason">
            <option value="ALL">Exit Reason: All</option>
            <option value="CONTINUOUS_40R_SL_TRAIL">40R Continuous Trail (49)</option>
            <option value="STOP_LOSS">Full Stop Loss (72)</option>
            <option value="SMART_STALL_LOCK">Smart Stall Lock (33)</option>
            <option value="INSTANT_PRE_SL_CUT">Instant Pre-SL Cut (14)</option>
            <option value="TRAIL_STOP">Trail Stop (22)</option>
            <option value="TIME_">Time Window Exits (30)</option>
          </select>
          <input type="text" id="filterSearch" placeholder="Search playbook, agent, date..." style="width: 220px;" />
          <button class="btn" onclick="resetJournalFilters()">Reset Filters</button>
          <span style="font-size: 11px; color: var(--text-muted); margin-left: auto;" id="filteredCountLabel">
            Showing 265 of 265 Trades
          </span>
        </div>

        <div class="data-table-wrap" style="max-height: 650px; overflow-y: auto;">
          <table class="data-table" id="journalTable">
            <thead>
              <tr>
                <th>#</th>
                <th>Date / Time (UTC)</th>
                <th>Dir</th>
                <th>Playbook Setup</th>
                <th>Initiator</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>SL</th>
                <th>PnL Pts</th>
                <th>R-Mult</th>
                <th>Net P&amp;L ($)</th>
                <th>Equity ($)</th>
                <th>Hold</th>
                <th>Exit Reason</th>
                <th>Consensus</th>
                <th>Sample</th>
              </tr>
            </thead>
            <tbody><!-- Populated via JS --></tbody>
          </table>
        </div>
      </div>
    </div>
  </div> <!-- /tab-journal -->

  <!-- TAB 5: 16-Agent Syndicate & Playbooks -->
  <div id="tab-agents" class="tab-pane">
    <div class="grid-2">
      <!-- Playbook Performance -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">🎯 Initiator Playbook Performance Attribution</div>
        </div>
        <div class="panel-body" style="padding: 0;">
          <div class="data-table-wrap">
            <table class="data-table" id="playbookTable">
              <thead>
                <tr>
                  <th>Playbook Strategy</th>
                  <th>Trades</th>
                  <th>Win Rate</th>
                  <th>Net P&amp;L ($)</th>
                  <th>Avg R</th>
                  <th>Win Share</th>
                </tr>
              </thead>
              <tbody><!-- Populated via JS --></tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Agent Confirmation Consensus -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">🤖 16-Agent Syndicate Confirmation Consensus</div>
        </div>
        <div class="panel-body" style="padding: 0;">
          <div class="data-table-wrap">
            <table class="data-table" id="agentVotingTable">
              <thead>
                <tr>
                  <th>Agent Specialist</th>
                  <th>Confirmations</th>
                  <th>Confirmed WR</th>
                  <th>Veto Rate</th>
                  <th>Specialty Edge</th>
                </tr>
              </thead>
              <tbody><!-- Populated via JS --></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Council & Risk Audit Architecture -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🏛️ Multi-Tier Council Governance Framework</div>
      </div>
      <div class="panel-body">
        <div class="grid-3">
          <div class="audit-sec">
            <div class="audit-sec-title">🔍 Part 1: Lucas Analyser (#17 LUCAS)</div>
            <p style="font-size: 11.5px; color: var(--text-muted); line-height: 1.5;">
              Scans 15m order flow, Ker trend persistence, Level-2 depth imbalance, and volatility Z-scores. Verifies that at least 8 of 16 agents align before passing signal to Council.
            </p>
          </div>
          <div class="audit-sec">
            <div class="audit-sec-title">⚖️ Part 2: Clara &amp; Victor (#13 CLARA + #15 VICTOR)</div>
            <p style="font-size: 11.5px; color: var(--text-muted); line-height: 1.5;">
              Victor Boss and Clara Psychologist conduct emotional risk vetting. Enforces zero hard vetoes across all agents, verifies session killzone liquidity, and authorizes execution.
            </p>
          </div>
          <div class="audit-sec">
            <div class="audit-sec-title">🧮 Part 3: Ethan Math &amp; Ryan Exec (#16 RYAN)</div>
            <p style="font-size: 11.5px; color: var(--text-muted); line-height: 1.5;">
              Ethan Math Engine computes fixed $5.00 fractional risk with 0.85x ATR SL. Ryan Execution Engine dynamically ratchets the 40R continuous trail and handles instant pre-SL cuts.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div> <!-- /tab-agents -->

</main>

<!-- Institutional Trade Audit Modal -->
<div class="modal-overlay" id="tradeModal" onclick="closeModalOnBg(event)">
  <div class="modal-card">
    <div class="modal-head">
      <div style="display: flex; align-items: center; gap: 10px;">
        <span class="badge-crown" id="modalTradeIdBadge">TRADE #1</span>
        <h3 id="modalTradeTitle" style="font-size: 15px; color: #fff;">Trade Audit</h3>
      </div>
      <button class="btn" style="padding: 4px 10px;" onclick="closeTradeModal()">✕</button>
    </div>
    <div class="modal-body" id="modalTradeBody">
      <!-- Populated dynamically via JS -->
    </div>
    <div class="modal-foot">
      <button class="btn btn-primary" id="modalViewChartBtn" onclick="jumpToModalTradeOnChart()">📍 View on Candlestick Chart</button>
      <button class="btn" onclick="closeTradeModal()">Close</button>
    </div>
  </div>
</div>

<!-- Embedded Data Payload -->
<script>
window.PAYLOAD = {payload_json};
</script>

<!-- Engine Logic Script -->
<script>
// ============================================================================
// DATA & STATE MANAGEMENT
// ============================================================================
const PROFILE = PAYLOAD.profile;
const TRADES = PROFILE.trades;
const CONTINUOUS = PAYLOAD.continuous_1m;

let filteredTrades = [...TRADES];
let selectedTrade = TRADES[0];
let currentTF = 5;
let currentMonth = "2026-10";
let selectedCalDate = null;

// Multi-month continuous candle cache
const TF_CACHE = {{}};
let viewStartIdx = 0;
let viewEndIdx = 400;
let isDragging = false;
let dragStartX = 0;
let hoverMouse = null;
let chartTradeHitboxes = [];

// Base64 to ArrayBuffer
function b64ToBytes(b64) {{
  const bin = atob(b64);
  const len = bin.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}}

function unpackContinuous1m() {{
  if (TF_CACHE[1]) return TF_CACHE[1];
  const c = CONTINUOUS;
  const n = c.n;
  const dt = new Uint16Array(b64ToBytes(c.dt));
  const doArr = new Int16Array(b64ToBytes(c.do));
  const dh = new Uint16Array(b64ToBytes(c.dh));
  const dl = new Uint16Array(b64ToBytes(c.dl));
  const dc = new Int16Array(b64ToBytes(c.dc));
  const v = new Uint16Array(b64ToBytes(c.v));

  const time = new Int32Array(n);
  const open = new Float32Array(n);
  const high = new Float32Array(n);
  const low = new Float32Array(n);
  const close = new Float32Array(n);
  const vol = new Int32Array(n);

  let curMin = c.start_ts_min;
  let curOpenD = c.start_open_d;
  for (let i = 0; i < n; i++) {{
    if (i > 0) {{
      curMin += dt[i];
      curOpenD += doArr[i];
    }}
    time[i] = curMin * 60;
    open[i] = curOpenD * 0.1;
    high[i] = (curOpenD + dh[i]) * 0.1;
    low[i] = (curOpenD - dl[i]) * 0.1;
    close[i] = (curOpenD + dc[i]) * 0.1;
    vol[i] = v[i];
  }}
  TF_CACHE[1] = {{ length: n, time, open, high, low, close, vol }};
  return TF_CACHE[1];
}}

function getContinuousBars(tfMins) {{
  if (TF_CACHE[tfMins]) return TF_CACHE[tfMins];
  const raw = unpackContinuous1m();
  if (tfMins === 1) return raw;

  const bucketSec = tfMins * 60;
  const n = raw.length;
  let count = 0;
  let prevB = -1;
  for (let i = 0; i < n; i++) {{
    const b = Math.floor(raw.time[i] / bucketSec) * bucketSec;
    if (b !== prevB) {{
      count++;
      prevB = b;
    }}
  }}

  const time = new Int32Array(count);
  const open = new Float32Array(count);
  const high = new Float32Array(count);
  const low = new Float32Array(count);
  const close = new Float32Array(count);
  const vol = new Int32Array(count);

  let k = -1;
  prevB = -1;
  for (let i = 0; i < n; i++) {{
    const b = Math.floor(raw.time[i] / bucketSec) * bucketSec;
    if (b !== prevB) {{
      k++;
      prevB = b;
      time[k] = b;
      open[k] = raw.open[i];
      high[k] = raw.high[i];
      low[k] = raw.low[i];
      close[k] = raw.close[i];
      vol[k] = raw.vol[i];
    }} else {{
      if (raw.high[i] > high[k]) high[k] = raw.high[i];
      if (raw.low[i] < low[k]) low[k] = raw.low[i];
      close[k] = raw.close[i];
      vol[k] += raw.vol[i];
    }}
  }}

  TF_CACHE[tfMins] = {{ length: count, time, open, high, low, close, vol }};
  return TF_CACHE[tfMins];
}}

function findBarIdx(timeArr, targetSec) {{
  let lo = 0, hi = timeArr.length - 1;
  while (lo < hi) {{
    const mid = (lo + hi) >> 1;
    if (timeArr[mid] < targetSec) lo = mid + 1;
    else hi = mid;
  }}
  return lo;
}}

// ============================================================================
// INITIALIZATION
// ============================================================================
window.addEventListener("DOMContentLoaded", () => {{
  unpackContinuous1m();
  renderAnalyticsTables();
  drawEquityCurve();
  renderCalendar();
  populateTradeJumpSelect();
  renderJournalTable();
  setupCanvasInteractions();

  // ResizeObserver on .tv-chart-box guarantees instant auto-render when visible
  const chartWrap = document.querySelector(".tv-chart-box");
  if (window.ResizeObserver && chartWrap) {{
    const ro = new ResizeObserver(entries => {{
      for (let entry of entries) {{
        if (entry.contentRect.width > 50 && entry.contentRect.height > 50) {{
          drawTradingViewChart();
        }}
      }}
    }});
    ro.observe(chartWrap);
  }}

  // Focus initial trade and prepare viewStartIdx / viewEndIdx
  if (TRADES.length > 0) {{
    selectedTrade = TRADES[0];
    const bars = getContinuousBars(currentTF);
    const iEnt = findBarIdx(bars.time, selectedTrade.entry_ts);
    const iExt = Math.max(iEnt + 2, findBarIdx(bars.time, selectedTrade.exit_ts));
    const span = Math.max(30, (iExt - iEnt) * 4);
    viewStartIdx = Math.max(0, Math.round(iEnt - span * 0.4));
    viewEndIdx = Math.min(bars.length - 1, Math.round(viewStartIdx + span));
    selectTrade(selectedTrade, false, false);
  }}

  window.addEventListener("resize", () => {{
    drawEquityCurve();
    drawTradingViewChart();
  }});

  // Initial draw
  setTimeout(() => {{
    drawTradingViewChart();
    drawEquityCurve();
  }}, 100);
}});

// ============================================================================
// TAB NAVIGATION
// ============================================================================
function switchTab(tabId) {{
  document.querySelectorAll(".tab-btn").forEach(btn => {{
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  }});
  document.querySelectorAll(".tab-pane").forEach(pane => {{
    pane.classList.toggle("active", pane.id === tabId);
  }});

  if (tabId === "tab-chart") {{
    requestAnimationFrame(() => {{
      drawTradingViewChart();
      const bars = getContinuousBars(currentTF);
      drawNavigatorBar(bars, Math.floor(viewStartIdx), Math.ceil(viewEndIdx));
    }});
  }} else if (tabId === "tab-analytics") {{
    requestAnimationFrame(() => {{
      drawEquityCurve();
    }});
  }}
}}

// ============================================================================
// ANALYTICS & TABLES
// ============================================================================
function renderAnalyticsTables() {{
  // 1. Monthly Table
  const months = ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10"];
  const mTableBody = document.querySelector("#monthlyStatsTable tbody");
  mTableBody.innerHTML = "";

  months.forEach(m => {{
    const ts = TRADES.filter(t => t.month === m);
    if (!ts.length) return;
    const wins = ts.filter(t => t.net_pnl_usd > 0);
    const losses = ts.filter(t => t.net_pnl_usd < 0);
    const wr = (wins.length / ts.length) * 100;
    const net = ts.reduce((s, t) => s + t.net_pnl_usd, 0);
    const fees = ts.reduce((s, t) => s + t.delta_fee_usd, 0);
    const grossW = wins.reduce((s, t) => s + t.gross_pnl_usd, 0);
    const grossL = Math.abs(losses.reduce((s, t) => s + t.gross_pnl_usd, 0));
    const pf = grossL > 0 ? (grossW / grossL).toFixed(2) : "∞";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${{m}}</strong></td>
      <td>${{ts.length}}</td>
      <td><span class="text-green font-bold">${{wr.toFixed(1)}}%</span></td>
      <td>${{wins.length}}W / ${{losses.length}}L</td>
      <td class="text-green font-mono font-bold">+$${{net.toFixed(2)}}</td>
      <td class="text-dim font-mono">$${{fees.toFixed(2)}}</td>
      <td class="text-cyan font-mono font-bold">${{pf}}</td>
    `;
    mTableBody.appendChild(tr);
  }});

  // 2. Session Table
  const sessions = ["LONDON", "NEW_YORK", "ASIA"];
  const sTableBody = document.querySelector("#sessionStatsTable tbody");
  sTableBody.innerHTML = "";
  sessions.forEach(s => {{
    const ts = TRADES.filter(t => t.session === s);
    if (!ts.length) return;
    const wins = ts.filter(t => t.net_pnl_usd > 0);
    const wr = (wins.length / ts.length) * 100;
    const net = ts.reduce((s, t) => s + t.net_pnl_usd, 0);
    const avg = net / ts.length;
    const share = (ts.length / TRADES.length) * 100;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${{s}} Killzone</strong></td>
      <td>${{ts.length}}</td>
      <td><span class="text-green">${{wr.toFixed(1)}}%</span></td>
      <td class="text-green font-mono font-bold">+$${{net.toFixed(2)}}</td>
      <td class="text-dim font-mono">+$${{avg.toFixed(2)}}</td>
      <td>${{share.toFixed(1)}}%</td>
    `;
    sTableBody.appendChild(tr);
  }});

  // 3. Day of Week Table
  const dows = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const dowTableBody = document.querySelector("#dowStatsTable tbody");
  dowTableBody.innerHTML = "";
  dows.forEach(d => {{
    const ts = TRADES.filter(t => t.day_of_week === d);
    if (!ts.length) return;
    const wins = ts.filter(t => t.net_pnl_usd > 0);
    const losses = ts.filter(t => t.net_pnl_usd < 0);
    const wr = (wins.length / ts.length) * 100;
    const net = ts.reduce((s, t) => s + t.net_pnl_usd, 0);
    const avgW = wins.length ? wins.reduce((s, t) => s + t.net_pnl_usd, 0) / wins.length : 0;
    const avgL = losses.length ? losses.reduce((s, t) => s + t.net_pnl_usd, 0) / losses.length : 0;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${{d}}</strong></td>
      <td>${{ts.length}}</td>
      <td><span class="text-green">${{wr.toFixed(1)}}%</span></td>
      <td class="text-green font-mono font-bold">+$${{net.toFixed(2)}}</td>
      <td class="text-green font-mono">+$${{avgW.toFixed(2)}}</td>
      <td class="text-red font-mono">-$${{Math.abs(avgL).toFixed(2)}}</td>
    `;
    dowTableBody.appendChild(tr);
  }});

  // 4. Direction & Duration Table
  const dirTableBody = document.querySelector("#directionStatsTable tbody");
  dirTableBody.innerHTML = "";
  ["SHORT", "LONG"].forEach(dir => {{
    const ts = TRADES.filter(t => t.direction === dir);
    const wins = ts.filter(t => t.net_pnl_usd > 0);
    const wr = (wins.length / ts.length) * 100;
    const net = ts.reduce((s, t) => s + t.net_pnl_usd, 0);
    const maxW = Math.max(...ts.map(t => t.net_pnl_usd));

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><span class="badge ${{dir === 'LONG' ? 'badge-long' : 'badge-short'}}">${{dir}} Orders</span></td>
      <td>${{ts.length}}</td>
      <td><span class="text-green">${{wr.toFixed(1)}}%</span></td>
      <td class="text-green font-mono font-bold">+$${{net.toFixed(2)}}</td>
      <td class="text-gold font-mono">+$${{maxW.toFixed(2)}}</td>
      <td>${{((ts.length/TRADES.length)*100).toFixed(1)}}%</td>
    `;
    dirTableBody.appendChild(tr);
  }});

  // 5. Exit Reasons Table
  const exitGroups = {{}};
  TRADES.forEach(t => {{
    const r = t.exit_reason;
    if (!exitGroups[r]) exitGroups[r] = [];
    exitGroups[r].push(t);
  }});
  const erTableBody = document.querySelector("#exitReasonTable tbody");
  erTableBody.innerHTML = "";

  Object.keys(exitGroups)
    .sort((a, b) => exitGroups[b].length - exitGroups[a].length)
    .forEach(r => {{
      const list = exitGroups[r];
      const wins = list.filter(t => t.net_pnl_usd > 0);
      const wr = (wins.length / list.length) * 100;
      const net = list.reduce((s, t) => s + t.net_pnl_usd, 0);
      const avg = net / list.length;

      let role = "Standard Exit";
      if (r === "CONTINUOUS_40R_SL_TRAIL") role = "🔥 Signature 40R Trail Ratchet (Top Net Earner)";
      else if (r === "STOP_LOSS") role = "Disciplined Risk Barrier (-1.00R Hard Cut)";
      else if (r === "SMART_STALL_LOCK") role = "🛡️ Greed-Guard Momentum Stall Lock (+0.28R)";
      else if (r === "INSTANT_PRE_SL_CUT") role = "⚡ Delta-Flipped Early Scratch (Saves Capital)";
      else if (r.includes("TRAIL")) role = "Structural Trailing Win Lock";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${{r}}</strong></td>
        <td>${{list.length}}</td>
        <td><span class="${{wr >= 50 ? 'text-green' : 'text-red'}}">${{wr.toFixed(1)}}%</span></td>
        <td class="${{net >= 0 ? 'text-green' : 'text-red'}} font-mono font-bold">${{net >= 0 ? '+' : ''}}$${{net.toFixed(2)}}</td>
        <td class="text-dim font-mono">${{avg >= 0 ? '+' : ''}}$${{avg.toFixed(2)}}</td>
        <td style="font-size: 11px; color: var(--text-muted);">${{role}}</td>
      `;
      erTableBody.appendChild(tr);
    }});

  // 6. Playbooks Table
  const pbGroups = {{}};
  TRADES.forEach(t => {{
    const p = t.playbook;
    if (!pbGroups[p]) pbGroups[p] = [];
    pbGroups[p].push(t);
  }});
  const pbTableBody = document.querySelector("#playbookTable tbody");
  pbTableBody.innerHTML = "";

  Object.keys(pbGroups)
    .sort((a, b) => pbGroups[b].reduce((s, t) => s + t.net_pnl_usd, 0) - pbGroups[a].reduce((s, t) => s + t.net_pnl_usd, 0))
    .forEach(p => {{
      const list = pbGroups[p];
      const wins = list.filter(t => t.net_pnl_usd > 0);
      const wr = (wins.length / list.length) * 100;
      const net = list.reduce((s, t) => s + t.net_pnl_usd, 0);
      const avgR = list.reduce((s, t) => s + t.r_multiple, 0) / list.length;

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${{p}}</strong></td>
        <td>${{list.length}}</td>
        <td><span class="text-green">${{wr.toFixed(1)}}%</span></td>
        <td class="${{net >= 0 ? 'text-green' : 'text-red'}} font-mono font-bold">${{net >= 0 ? '+' : ''}}$${{net.toFixed(2)}}</td>
        <td class="text-gold font-mono">${{avgR >= 0 ? '+' : ''}}${{avgR.toFixed(2)}}R</td>
        <td>${{((list.length/TRADES.length)*100).toFixed(1)}}%</td>
      `;
      pbTableBody.appendChild(tr);
    }});

  // 7. Agent Voting Table
  const allAgents = [
    "1:MARCUS", "2:ARTHUR", "3:BEN", "4:OWEN", "5:LEO", "6:KAI", "7:NINA",
    "8:MAX", "9:ELENA", "10:ZOE", "11:SAM", "12:JACK", "13:CLARA", "14:DAVID", "15:VICTOR", "16:RYAN"
  ];
  const agTableBody = document.querySelector("#agentVotingTable tbody");
  agTableBody.innerHTML = "";

  allAgents.forEach(a => {{
    const confirmed = TRADES.filter(t => (t.confirming_agents || []).includes(a));
    const cWins = confirmed.filter(t => t.net_pnl_usd > 0);
    const wr = confirmed.length ? (cWins.length / confirmed.length) * 100 : 0;
    const vetoCount = TRADES.length - confirmed.length;
    const vetoRate = (vetoCount / TRADES.length) * 100;

    let edge = "Confluence Co-Signer";
    if (a.includes("LEO")) edge = "Killzone Sweeps & Liquidity Traps";
    else if (a.includes("KAI")) edge = "SMC Optimal Trade Entry";
    else if (a.includes("ELENA")) edge = "VWAP Volume Profile & Wicks";
    else if (a.includes("MAX")) edge = "Multi-Timeframe Trend & Boxes";
    else if (a.includes("SAM")) edge = "Level-2 Order Book Imbalance";
    else if (a.includes("JACK")) edge = "Volume Spread Analysis (VSA)";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${{a}}</strong></td>
      <td>${{confirmed.length}} / ${{TRADES.length}}</td>
      <td><span class="text-green">${{wr.toFixed(1)}}%</span></td>
      <td class="text-dim">${{vetoRate.toFixed(1)}}%</td>
      <td style="font-size: 11px; color: var(--text-muted);">${{edge}}</td>
    `;
    agTableBody.appendChild(tr);
  }});
}}

// ============================================================================
// EQUITY & DRAWDOWN CANVAS CHART
// ============================================================================
function drawEquityCurve() {{
  const canvas = document.getElementById("equityChartCanvas");
  if (!canvas) return;
  const wrap = canvas.parentElement;
  const rect = wrap.getBoundingClientRect();
  const W = Math.floor(rect.width);
  const H = Math.floor(rect.height);
  if (W <= 50 || H <= 50) return;

  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(W * dpr);
  canvas.height = Math.floor(H * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  ctx.fillStyle = "#090c13";
  ctx.fillRect(0, 0, W, H);

  // Calculate equity & peak series
  let curEq = 100.0;
  let peak = 100.0;
  const points = [{{ eq: 100.0, dd: 0.0, is_oos: false }}];

  TRADES.forEach(t => {{
    curEq += t.net_pnl_usd;
    if (curEq > peak) peak = curEq;
    const dd = curEq - peak;
    points.push({{ eq: curEq, dd: dd, is_oos: t.is_oos }});
  }});

  const minEq = 85.0;
  const maxEq = Math.max(...points.map(p => p.eq)) * 1.05;

  const padL = 60, padR = 20, padT = 30, padB = 40;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  const xOf = idx => padL + (idx / (points.length - 1)) * plotW;
  const yOfEq = v => padT + plotH * (1 - (v - minEq) / (maxEq - minEq));

  // Grid
  ctx.strokeStyle = "#161d2b";
  ctx.lineWidth = 1;
  for (let eqVal = 100; eqVal <= maxEq; eqVal += 100) {{
    const y = yOfEq(eqVal);
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(W - padR, y);
    ctx.stroke();

    ctx.fillStyle = "#64748b";
    ctx.font = "10px ui-monospace, monospace";
    ctx.textAlign = "right";
    ctx.fillText(`$${{eqVal}}`, padL - 8, y + 3);
  }}

  // In-Sample / Out-of-Sample separator
  const oosIdx = TRADES.findIndex(t => t.is_oos);
  if (oosIdx > 0) {{
    const xOOS = xOf(oosIdx);
    ctx.strokeStyle = "rgba(168, 85, 247, 0.6)";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(xOOS, padT);
    ctx.lineTo(xOOS, padT + plotH);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = "#a855f7";
    ctx.font = "bold 10px -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("◀ IN-SAMPLE (184)", xOOS - 55, padT + 14);
    ctx.fillText("OUT-OF-SAMPLE (81) ▶", xOOS + 65, padT + 14);
  }}

  // Area under equity curve
  const grad = ctx.createLinearGradient(0, padT, 0, padT + plotH);
  grad.addColorStop(0, "rgba(16, 185, 129, 0.28)");
  grad.addColorStop(1, "rgba(16, 185, 129, 0.0)");

  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.moveTo(xOf(0), padT + plotH);
  points.forEach((p, i) => ctx.lineTo(xOf(i), yOfEq(p.eq)));
  ctx.lineTo(xOf(points.length - 1), padT + plotH);
  ctx.closePath();
  ctx.fill();

  // Equity Line
  ctx.strokeStyle = "#10b981";
  ctx.lineWidth = 2.2;
  ctx.beginPath();
  points.forEach((p, i) => {{
    const x = xOf(i);
    const y = yOfEq(p.eq);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }});
  ctx.stroke();

  // Draw X axis label
  ctx.fillStyle = "#94a3b8";
  ctx.font = "11px -apple-system, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("Trade Progression (#1 to #265) · 100% Weekday Single Slot", padL + plotW / 2, H - 12);
}}

// ============================================================================
// INTERACTIVE TRADINGVIEW CANDLESTICK ENGINE (60 FPS ADAPTIVE CANVAS)
// ============================================================================
function setupCanvasInteractions() {{
  const canvas = document.getElementById("tvChart");
  const nav = document.getElementById("tvNavChart");

  // Timeframe switch buttons
  document.querySelectorAll(".tf-btn").forEach(btn => {{
    btn.addEventListener("click", () => {{
      const oldBars = getContinuousBars(currentTF);
      const sSec = oldBars.time[Math.max(0, Math.floor(viewStartIdx))];
      const eSec = oldBars.time[Math.min(oldBars.length - 1, Math.ceil(viewEndIdx))];

      document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentTF = parseInt(btn.getAttribute("data-tf"), 10);

      const newBars = getContinuousBars(currentTF);
      viewStartIdx = findBarIdx(newBars.time, sSec);
      viewEndIdx = Math.max(viewStartIdx + 30, findBarIdx(newBars.time, eSec));
      drawTradingViewChart();
    }});
  }});

  // Mouse wheel zoom (anchored at cursor)
  canvas.addEventListener("wheel", e => {{
    e.preventDefault();
    const bars = getContinuousBars(currentTF);
    if (!bars || !bars.length) return;

    const rect = canvas.getBoundingClientRect();
    const plotW = Math.max(100, rect.width - 80);
    const mouseRatio = Math.max(0, Math.min(1, (e.clientX - rect.left) / plotW));

    const span = viewEndIdx - viewStartIdx;
    const factor = e.deltaY > 0 ? 1.25 : 0.8;
    const newSpan = Math.max(15, Math.min(bars.length - 1, span * factor));
    const anchor = viewStartIdx + span * mouseRatio;

    viewStartIdx = Math.max(0, Math.round(anchor - newSpan * mouseRatio));
    viewEndIdx = Math.min(bars.length - 1, Math.round(viewStartIdx + newSpan));
    drawTradingViewChart();
  }});

  // Pan dragging
  canvas.addEventListener("mousedown", e => {{
    isDragging = true;
    dragStartX = e.clientX;
  }});

  window.addEventListener("mouseup", () => {{
    isDragging = false;
  }});

  canvas.addEventListener("mousemove", e => {{
    const rect = canvas.getBoundingClientRect();
    hoverMouse = {{ x: e.clientX - rect.left, y: e.clientY - rect.top }};

    if (isDragging) {{
      const dx = e.clientX - dragStartX;
      dragStartX = e.clientX;
      const bars = getContinuousBars(currentTF);
      const span = viewEndIdx - viewStartIdx;
      const plotW = Math.max(100, rect.width - 80);
      const barsMoved = Math.round((dx / plotW) * span);

      viewStartIdx = Math.max(0, Math.min(bars.length - 20, viewStartIdx - barsMoved));
      viewEndIdx = Math.min(bars.length - 1, viewStartIdx + span);
    }}
    drawTradingViewChart();
  }});

  canvas.addEventListener("mouseleave", () => {{
    hoverMouse = null;
    drawTradingViewChart();
  }});

  // Click on trade badges or boxes
  canvas.addEventListener("click", e => {{
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    for (let box of chartTradeHitboxes) {{
      if (mx >= box.x && mx <= box.x + box.w && my >= box.y && my <= box.y + box.h) {{
        selectTrade(box.trade, false, false);
        openTradeAuditModal(box.trade);
        return;
      }}
    }}
  }});

  // Minimap Navigator Click / Drag
  nav.addEventListener("click", e => {{
    const rect = nav.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const bars = getContinuousBars(currentTF);
    const span = viewEndIdx - viewStartIdx;
    const center = Math.round(ratio * (bars.length - 1));
    viewStartIdx = Math.max(0, Math.round(center - span / 2));
    viewEndIdx = Math.min(bars.length - 1, viewStartIdx + span);
    drawTradingViewChart();
  }});

  // Buttons
  document.getElementById("prevTradeBtn").addEventListener("click", () => stepTrade(-1));
  document.getElementById("nextTradeBtn").addEventListener("click", () => stepTrade(1));
  document.getElementById("zoomTradeBtn").addEventListener("click", () => zoomToSelectedTrade());
  document.getElementById("fit5MonthBtn").addEventListener("click", () => fitFull5MonthWindow());
  document.getElementById("tradeJumpSelect").addEventListener("change", e => {{
    const t = TRADES.find(x => x.id === parseInt(e.target.value, 10));
    if (t) selectTrade(t, true);
  }});
}}

function drawTradingViewChart() {{
  const canvas = document.getElementById("tvChart");
  if (!canvas) return;
  const wrap = canvas.parentElement;
  const rect = wrap.getBoundingClientRect();
  const W = Math.floor(rect.width);
  const H = Math.floor(rect.height);
  if (W <= 50 || H <= 50) return;

  const dpr = window.devicePixelRatio || 1;
  if (canvas.width !== Math.floor(W * dpr) || canvas.height !== Math.floor(H * dpr)) {{
    canvas.width = Math.floor(W * dpr);
    canvas.height = Math.floor(H * dpr);
  }}
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  chartTradeHitboxes = [];

  ctx.fillStyle = "#090c13";
  ctx.fillRect(0, 0, W, H);

  const bars = getContinuousBars(currentTF);
  if (!bars || !bars.length) return;

  const sIdx = Math.max(0, Math.floor(viewStartIdx));
  const eIdx = Math.min(bars.length - 1, Math.ceil(viewEndIdx));
  const numBars = eIdx - sIdx + 1;
  if (numBars <= 1) return;

  const priceAxisW = 75;
  const plotW = W - priceAxisW;
  const timeAxisH = 26;
  const headerH = 34;
  const plotH = H - timeAxisH - headerH;

  // Find min/max price and max vol in view
  let minP = Infinity, maxP = -Infinity, maxVol = 1;
  const strideScan = Math.max(1, Math.floor(numBars / 800));
  for (let i = sIdx; i <= eIdx; i += strideScan) {{
    if (bars.low[i] < minP) minP = bars.low[i];
    if (bars.high[i] > maxP) maxP = bars.high[i];
    if (bars.vol[i] > maxVol) maxVol = bars.vol[i];
  }}

  // Find visible trades
  const sSec = bars.time[sIdx];
  const eSec = bars.time[eIdx];
  const visibleTrades = TRADES.filter(t => t.exit_ts >= sSec && t.entry_ts <= eSec);

  // Pad price scale by trade levels if close
  visibleTrades.forEach(t => {{
    const lo = Math.min(t.sl_price, t.tp2_price, t.entry_price, t.exit_price);
    const hi = Math.max(t.sl_price, t.tp2_price, t.entry_price, t.exit_price);
    if (lo < minP) minP = lo;
    if (hi > maxP) maxP = hi;
  }});

  if (!isFinite(minP) || !isFinite(maxP)) {{ minP = 4400; maxP = 4700; }}
  const padP = Math.max(2.0, (maxP - minP) * 0.08);
  minP -= padP;
  maxP += padP;

  const xOf = idx => ((idx - sIdx) / Math.max(1, numBars - 1)) * plotW;
  const yOfP = p => headerH + plotH * (1 - (p - minP) / Math.max(1, maxP - minP));
  const stepX = plotW / Math.max(1, numBars);

  // Background Grid Lines
  ctx.strokeStyle = "#131824";
  ctx.lineWidth = 1;
  const stepP = (maxP - minP) / 7;
  for (let i = 0; i <= 7; i++) {{
    const p = minP + i * stepP;
    const y = yOfP(p);
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(plotW, y);
    ctx.stroke();

    ctx.fillStyle = "#64748b";
    ctx.font = "10px ui-monospace, monospace";
    ctx.textAlign = "left";
    ctx.fillText(p.toFixed(2), plotW + 6, y + 3);
  }}

  // Volume Histogram at bottom of chart
  const volH = plotH * 0.16;
  for (let i = sIdx; i <= eIdx; i += strideScan) {{
    const x = xOf(i);
    const vH = (bars.vol[i] / maxVol) * volH;
    const isUp = bars.close[i] >= bars.open[i];
    ctx.fillStyle = isUp ? "rgba(16, 185, 129, 0.18)" : "rgba(239, 68, 68, 0.18)";
    const bW = Math.max(1.5, stepX * 0.7);
    ctx.fillRect(x - bW / 2, headerH + plotH - vH, bW, vH);
  }}

  // =========================================================================
  // 1. POSITION SHADED BOXES FOR VISIBLE TRADES
  // =========================================================================
  visibleTrades.forEach(t => {{
    const isSel = selectedTrade && selectedTrade.id === t.id;
    const iEnt = findBarIdx(bars.time, t.entry_ts);
    const iExt = findBarIdx(bars.time, t.exit_ts);

    const xEnt = Math.max(0, Math.min(plotW - 5, xOf(iEnt)));
    const xExt = Math.min(plotW - 2, Math.max(xEnt + 8, xOf(iExt)));
    const boxW = Math.max(6, xExt - xEnt);

    const yEnt = yOfP(t.entry_price);
    const yExt = yOfP(t.exit_price);
    const ySL = yOfP(t.sl_price);
    const yTP1 = yOfP(t.tp1_price);
    const yTP2 = yOfP(t.tp2_price);

    const isWin = t.net_pnl_usd > 0;
    const color = isWin ? "#10b981" : "#ef4444";

    // Position Zone (Green / Red)
    const boxTop = Math.min(yEnt, yExt);
    const boxH = Math.max(3, Math.abs(yExt - yEnt));
    ctx.fillStyle = isWin ? (isSel ? "rgba(16, 185, 129, 0.35)" : "rgba(16, 185, 129, 0.18)") : (isSel ? "rgba(239, 68, 68, 0.35)" : "rgba(239, 68, 68, 0.18)");
    ctx.fillRect(xEnt, boxTop, boxW, boxH);
    ctx.strokeStyle = isSel ? (isWin ? "#34d399" : "#f87171") : (isWin ? "rgba(16,185,129,0.5)" : "rgba(239,68,68,0.5)");
    ctx.lineWidth = isSel ? 2 : 1;
    ctx.strokeRect(xEnt, boxTop, boxW, boxH);

    // Stop Loss Line
    ctx.strokeStyle = "rgba(239, 68, 68, 0.65)";
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(xEnt, ySL);
    ctx.lineTo(xExt, ySL);
    ctx.stroke();

    // TP1 Line
    ctx.strokeStyle = "rgba(245, 158, 11, 0.55)";
    ctx.beginPath();
    ctx.moveTo(xEnt, yTP1);
    ctx.lineTo(xExt, yTP1);
    ctx.stroke();

    // Entry Line
    ctx.strokeStyle = "rgba(255, 255, 255, 0.75)";
    ctx.beginPath();
    ctx.moveTo(xEnt, yEnt);
    ctx.lineTo(xExt, yEnt);
    ctx.stroke();
    ctx.setLineDash([]);

    // Entry Marker Badge
    const badgeW = 68;
    const badgeH = 20;
    const badgeX = xEnt - badgeW / 2;
    const badgeY = t.direction === "LONG" ? yEnt + 10 : yEnt - 28;

    ctx.fillStyle = isSel ? "#f59e0b" : (t.direction === "LONG" ? "#065f46" : "#7f1d1d");
    ctx.strokeStyle = isSel ? "#fff" : color;
    ctx.lineWidth = 1.2;
    ctx.fillRect(badgeX, badgeY, badgeW, badgeH);
    ctx.strokeRect(badgeX, badgeY, badgeW, badgeH);

    ctx.fillStyle = "#fff";
    ctx.font = "bold 9.5px -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${{t.direction === 'LONG' ? '▲ BUY' : '▼ SELL'}} #${{t.id}}`, xEnt, badgeY + 13);

    // Exit Marker Badge
    const eBadgeW = 74;
    const eBadgeH = 18;
    const eBadgeX = xExt - eBadgeW / 2;
    const eBadgeY = yExt - 9;

    ctx.fillStyle = isWin ? "#064e3b" : "#7f1d1d";
    ctx.fillRect(eBadgeX, eBadgeY, eBadgeW, eBadgeH);
    ctx.strokeRect(eBadgeX, eBadgeY, eBadgeW, eBadgeH);

    ctx.fillStyle = "#fff";
    ctx.font = "bold 9px ui-monospace, monospace";
    ctx.fillText(`${{isWin ? '+' : ''}}${{t.r_multiple.toFixed(2)}}R ($${{t.net_pnl_usd.toFixed(2)}})`, xExt, eBadgeY + 12);

    // Clickable hitboxes
    chartTradeHitboxes.push({{
      x: badgeX,
      y: badgeY,
      w: badgeW,
      h: badgeH,
      trade: t
    }});
    chartTradeHitboxes.push({{
      x: xEnt,
      y: boxTop,
      w: boxW,
      h: boxH,
      trade: t
    }});
  }});

  // =========================================================================
  // 2. CANDLESTICKS (60 FPS ADAPTIVE LEVEL-OF-DETAIL)
  // =========================================================================
  if (numBars <= plotW * 0.75) {{
    // Draw individual candlesticks
    const barW = Math.max(1.8, Math.min(16, stepX * 0.7));
    for (let i = sIdx; i <= eIdx; i++) {{
      const x = xOf(i);
      const oY = yOfP(bars.open[i]);
      const hY = yOfP(bars.high[i]);
      const lY = yOfP(bars.low[i]);
      const cY = yOfP(bars.close[i]);
      const isUp = bars.close[i] >= bars.open[i];
      const color = isUp ? "#10b981" : "#ef4444";

      // Wick
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.1;
      ctx.beginPath();
      ctx.moveTo(x, hY);
      ctx.lineTo(x, lY);
      ctx.stroke();

      // Body
      ctx.fillStyle = color;
      const topY = Math.min(oY, cY);
      const bodyH = Math.max(1.2, Math.abs(cY - oY));
      ctx.fillRect(x - barW / 2, topY, barW, bodyH);
    }}
  }} else {{
    // Pixel-column aggregated candlesticks for ultra-smooth multi-month view
    const numCols = Math.max(180, Math.floor(plotW / 3.0));
    const barsPerCol = numBars / numCols;
    const colW = plotW / numCols;
    const bodyW = Math.max(1.5, colW * 0.7);

    for (let col = 0; col < numCols; col++) {{
      const b0 = Math.min(bars.length - 1, Math.floor(sIdx + col * barsPerCol));
      const b1 = Math.min(bars.length - 1, Math.max(b0, Math.floor(sIdx + (col + 1) * barsPerCol) - 1));
      const o = bars.open[b0];
      const c = bars.close[b1];
      let h = bars.high[b0];
      let l = bars.low[b0];
      for (let k = b0 + 1; k <= b1; k++) {{
        if (bars.high[k] > h) h = bars.high[k];
        if (bars.low[k] < l) l = bars.low[k];
      }}

      const cx = (col + 0.5) * colW;
      const oY = yOfP(o), hY = yOfP(h), lY = yOfP(l), cY = yOfP(c);
      const isUp = c >= o;
      const color = isUp ? "#10b981" : "#ef4444";

      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx, hY);
      ctx.lineTo(cx, lY);
      ctx.stroke();

      ctx.fillStyle = color;
      ctx.fillRect(cx - bodyW / 2, Math.min(oY, cY), bodyW, Math.max(1.2, Math.abs(cY - oY)));
    }}
  }}

  // =========================================================================
  // 3. CROSSHAIRS & OHLCV BANNER ON CANVAS
  // =========================================================================
  let hoverBarIdx = sIdx + Math.floor(numBars / 2);
  if (hoverMouse && hoverMouse.x >= 0 && hoverMouse.x <= plotW && hoverMouse.y >= headerH && hoverMouse.y <= headerH + plotH) {{
    const ratio = hoverMouse.x / plotW;
    hoverBarIdx = Math.max(0, Math.min(bars.length - 1, Math.round(sIdx + ratio * (numBars - 1))));

    // Draw Crosshair Lines
    ctx.strokeStyle = "rgba(148, 163, 184, 0.4)";
    ctx.setLineDash([3, 3]);
    ctx.lineWidth = 1;

    // Vertical line
    ctx.beginPath();
    ctx.moveTo(hoverMouse.x, headerH);
    ctx.lineTo(hoverMouse.x, headerH + plotH);
    ctx.stroke();

    // Horizontal line
    ctx.beginPath();
    ctx.moveTo(0, hoverMouse.y);
    ctx.lineTo(plotW, hoverMouse.y);
    ctx.stroke();
    ctx.setLineDash([]);

    // Y Axis Price Tag
    const hoverP = minP + (1 - (hoverMouse.y - headerH) / plotH) * (maxP - minP);
    ctx.fillStyle = "#3b82f6";
    ctx.fillRect(plotW, hoverMouse.y - 9, priceAxisW, 18);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 10px ui-monospace, monospace";
    ctx.textAlign = "left";
    ctx.fillText(hoverP.toFixed(2), plotW + 6, hoverMouse.y + 4);
  }}

  // Top Info Banner on Canvas
  const hO = bars.open[hoverBarIdx], hH = bars.high[hoverBarIdx], hL = bars.low[hoverBarIdx], hC = bars.close[hoverBarIdx], hV = bars.vol[hoverBarIdx];
  const dStart = new Date(sSec * 1000).toISOString().slice(0, 10);
  const dEnd = new Date(eSec * 1000).toISOString().slice(0, 10);
  const chg = hC - hO;
  const chgPct = (chg / hO) * 100;

  ctx.fillStyle = "#fff";
  ctx.font = "bold 12px -apple-system, sans-serif";
  ctx.textAlign = "left";
  ctx.fillText(
    `Gold Futures (GC.v.0 · ${{currentTF}}m · ${{dStart}} → ${{dEnd}} · ${{visibleTrades.length}} Trades in View)   O ${{hO.toFixed(2)}}   H ${{hH.toFixed(2)}}   L ${{hL.toFixed(2)}}   C ${{hC.toFixed(2)}}   ${{chg >= 0 ? '+' : ''}}${{chg.toFixed(2)}} (${{chg >= 0 ? '+' : ''}}${{chgPct.toFixed(2)}}%)   Vol ${{hV}}`,
    12, 21
  );

  // Time Axis at Bottom
  ctx.fillStyle = "#0c1018";
  ctx.fillRect(0, headerH + plotH, W, timeAxisH);
  ctx.strokeStyle = "#1a2130";
  ctx.beginPath();
  ctx.moveTo(0, headerH + plotH);
  ctx.lineTo(W, headerH + plotH);
  ctx.stroke();

  ctx.fillStyle = "#64748b";
  ctx.font = "10px -apple-system, sans-serif";
  ctx.textAlign = "center";
  const timeStep = Math.max(1, Math.floor(numBars / 6));
  for (let i = sIdx; i <= eIdx; i += timeStep) {{
    const x = xOf(i);
    const dStr = new Date(bars.time[i] * 1000).toISOString().replace("T", " ").slice(5, 16);
    ctx.fillText(dStr, x, headerH + plotH + 16);
  }}

  drawNavigatorBar(bars, sIdx, eIdx);
}}

function drawNavigatorBar(bars, sIdx, eIdx) {{
  const nav = document.getElementById("tvNavChart");
  if (!nav || !bars || !bars.length) return;
  const rect = nav.getBoundingClientRect();
  const W = Math.floor(rect.width) || nav.parentElement.clientWidth || 1200;
  const H = 48;

  const dpr = window.devicePixelRatio || 1;
  if (nav.width !== Math.floor(W * dpr) || nav.height !== Math.floor(H * dpr)) {{
    nav.width = Math.floor(W * dpr);
    nav.height = Math.floor(H * dpr);
  }}
  const ctx = nav.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  ctx.fillStyle = "#080b11";
  ctx.fillRect(0, 0, W, H);

  const n = bars.length;
  const step = Math.max(1, Math.floor(n / 500));
  let minP = Infinity, maxP = -Infinity;
  for (let i = 0; i < n; i += step) {{
    if (bars.close[i] < minP) minP = bars.close[i];
    if (bars.close[i] > maxP) maxP = bars.close[i];
  }}

  const yOf = p => 3 + (H - 6) * (1 - (p - minP) / Math.max(1, maxP - minP));

  // Sparkline
  ctx.strokeStyle = "rgba(148, 163, 184, 0.4)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i < n; i += step) {{
    const x = (i / (n - 1)) * W;
    const y = yOf(bars.close[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }}
  ctx.stroke();

  // All 265 trade pins
  TRADES.forEach(t => {{
    const idx = findBarIdx(bars.time, t.entry_ts);
    const x = (idx / (n - 1)) * W;
    const isSel = selectedTrade && selectedTrade.id === t.id;
    ctx.fillStyle = isSel ? "#f59e0b" : (t.net_pnl_usd > 0 ? "#10b981" : "#ef4444");
    ctx.fillRect(x - (isSel ? 2 : 1), 2, isSel ? 4 : 2, H - 4);
  }});

  // Active Viewport Box
  const x1 = (sIdx / (n - 1)) * W;
  const x2 = Math.max(x1 + 6, (eIdx / (n - 1)) * W);
  ctx.fillStyle = "rgba(59, 130, 246, 0.22)";
  ctx.fillRect(x1, 0, x2 - x1, H);
  ctx.strokeStyle = "#3b82f6";
  ctx.lineWidth = 1.5;
  ctx.strokeRect(x1, 0.5, x2 - x1, H - 1);
}}

function selectTrade(trade, zoomToIt = false, switchTabIfNeed = false) {{
  selectedTrade = trade;
  document.getElementById("tradeJumpSelect").value = String(trade.id);

  // Update banner below chart
  const bannerText = document.getElementById("bannerTradeText");
  const bannerBtn = document.getElementById("bannerInspectBtn");
  const isWin = trade.net_pnl_usd > 0;

  bannerText.innerHTML = `
    <span class="badge ${{trade.direction === 'LONG' ? 'badge-long' : 'badge-short'}}">${{trade.direction}}</span>
    <strong>Trade #${{trade.id}} (${{trade.date}} ${{trade.session}})</strong> · 
    Playbook: <strong>${{trade.playbook}}</strong> · 
    Entry: ${{trade.entry_price.toFixed(2)}} → Exit: ${{trade.exit_price.toFixed(2)}} · 
    <span class="${{isWin ? 'text-green' : 'text-red'}} font-mono font-bold">${{isWin ? '+' : ''}}${{trade.r_multiple.toFixed(2)}}R ($${{trade.net_pnl_usd.toFixed(2)}} Net)</span> · 
    Exit Reason: <strong>${{trade.exit_reason}}</strong>
  `;
  bannerBtn.style.display = "inline-flex";

  // Highlight table row
  document.querySelectorAll("#journalTable tr.clickable").forEach(tr => {{
    tr.classList.toggle("selected", tr.getAttribute("data-id") === String(trade.id));
  }});

  if (zoomToIt) zoomToSelectedTrade();
  else drawTradingViewChart();

  if (switchTabIfNeed) {{
    switchTab("tab-chart");
  }}
}}

function stepTrade(dir) {{
  const curIdx = TRADES.findIndex(t => t.id === selectedTrade.id);
  const nextIdx = Math.max(0, Math.min(TRADES.length - 1, curIdx + dir));
  selectTrade(TRADES[nextIdx], true);
}}

function zoomToSelectedTrade() {{
  if (!selectedTrade) return;
  const bars = getContinuousBars(currentTF);
  const bucketSec = currentTF * 60;
  const iEnt = findBarIdx(bars.time, selectedTrade.entry_ts);
  const iExt = Math.max(iEnt + 2, findBarIdx(bars.time, selectedTrade.exit_ts));
  const span = Math.max(30, (iExt - iEnt) * 4);

  viewStartIdx = Math.max(0, Math.round(iEnt - span * 0.4));
  viewEndIdx = Math.min(bars.length - 1, Math.round(viewStartIdx + span));
  drawTradingViewChart();
}}

function fitFull5MonthWindow() {{
  const bars = getContinuousBars(currentTF);
  viewStartIdx = 0;
  viewEndIdx = bars.length - 1;
  drawTradingViewChart();
}}

function populateTradeJumpSelect() {{
  const sel = document.getElementById("tradeJumpSelect");
  sel.innerHTML = "";
  TRADES.forEach(t => {{
    const opt = document.createElement("option");
    opt.value = String(t.id);
    const sign = t.net_pnl_usd > 0 ? "+" : "";
    opt.textContent = `#${{t.id}} (${{t.date}}) ${{t.direction}} ${{t.playbook}} (${{sign}}${{t.r_multiple.toFixed(2)}}R | ${{sign}}$${{t.net_pnl_usd.toFixed(2)}})`;
    sel.appendChild(opt);
  }});
}}

// ============================================================================
// 5-MONTH P&L CALENDAR HEATMAP
// ============================================================================
function renderCalendar() {{
  const grid = document.getElementById("calDaysGrid");
  grid.innerHTML = "";

  const [yr, mo] = currentMonth.split("-").map(Number);
  const firstDay = new Date(yr, mo - 1, 1).getDay();
  const daysInMonth = new Date(yr, mo, 0).getDate();

  // Aggregate by date
  const dayMap = {{}};
  TRADES.filter(t => t.month === currentMonth).forEach(t => {{
    if (!dayMap[t.date]) dayMap[t.date] = [];
    dayMap[t.date].push(t);
  }});

  // Empty leading days
  for (let i = 0; i < firstDay; i++) {{
    const emptyDiv = document.createElement("div");
    emptyDiv.className = "cal-day empty";
    grid.appendChild(emptyDiv);
  }}

  // Month summary badge
  const mTrades = TRADES.filter(t => t.month === currentMonth);
  const mWins = mTrades.filter(t => t.net_pnl_usd > 0);
  const mNet = mTrades.reduce((s, t) => s + t.net_pnl_usd, 0);
  const mWR = mTrades.length ? (mWins.length / mTrades.length) * 100 : 0;
  document.getElementById("calMonthSummaryBadge").textContent = 
    `${{currentMonth}}: ${{mTrades.length}} Trades · ${{mWR.toFixed(1)}}% WR · +$${{mNet.toFixed(2)}} Net`;

  // Populate days
  for (let d = 1; d <= daysInMonth; d++) {{
    const dateStr = `${{yr}}-${{String(mo).padStart(2, '0')}}-${{String(d).padStart(2, '0')}}`;
    const list = dayMap[dateStr] || [];

    const cell = document.createElement("div");
    cell.className = "cal-day";
    if (selectedCalDate === dateStr) cell.classList.add("selected");

    if (list.length) {{
      const net = list.reduce((s, t) => s + t.net_pnl_usd, 0);
      const wins = list.filter(t => t.net_pnl_usd > 0);
      const isWin = net >= 0;

      cell.classList.add(isWin ? "win-day" : "loss-day");
      cell.innerHTML = `
        <div class="cal-day-top">
          <span class="cal-day-num">${{d}}</span>
          <span class="cal-day-count">${{list.length}}T (${{wins.length}}W)</span>
        </div>
        <div class="cal-day-pnl ${{isWin ? 'text-green' : 'text-red'}}">
          ${{isWin ? '+' : ''}}$${{net.toFixed(2)}}
        </div>
        <div class="cal-day-bot">
          <span>${{list[0].session.slice(0, 3)}}</span>
          <span>${{list[0].initiator_16.split(':')[1] || ''}}</span>
        </div>
      `;

      cell.addEventListener("click", () => {{
        selectedCalDate = dateStr;
        document.querySelectorAll(".cal-day").forEach(c => c.classList.remove("selected"));
        cell.classList.add("selected");
        filterJournalByDate(dateStr);
      }});
    }} else {{
      cell.innerHTML = `
        <div class="cal-day-top"><span class="cal-day-num" style="color: #475569;">${{d}}</span></div>
      `;
    }}

    grid.appendChild(cell);
  }}

  document.getElementById("calMonthSelect").value = currentMonth;
}}

document.getElementById("calPrevMonthBtn").addEventListener("click", () => {{
  const months = ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10"];
  const idx = months.indexOf(currentMonth);
  if (idx > 0) {{
    currentMonth = months[idx - 1];
    renderCalendar();
  }}
}});

document.getElementById("calNextMonthBtn").addEventListener("click", () => {{
  const months = ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10"];
  const idx = months.indexOf(currentMonth);
  if (idx < months.length - 1) {{
    currentMonth = months[idx + 1];
    renderCalendar();
  }}
}});

document.getElementById("calMonthSelect").addEventListener("change", e => {{
  currentMonth = e.target.value;
  renderCalendar();
}});

function filterJournalByDate(dateStr) {{
  document.getElementById("filterSearch").value = dateStr;
  applyJournalFilters();
  switchTab("tab-journal");
}}

function clearDateFilter() {{
  selectedCalDate = null;
  document.querySelectorAll(".cal-day").forEach(c => c.classList.remove("selected"));
  resetJournalFilters();
}}

// ============================================================================
// 265-TRADE COMPLETE JOURNAL
// ============================================================================
function renderJournalTable() {{
  const tbody = document.querySelector("#journalTable tbody");
  tbody.innerHTML = "";

  filteredTrades.forEach(t => {{
    const tr = document.createElement("tr");
    tr.className = "clickable";
    tr.setAttribute("data-id", String(t.id));
    if (selectedTrade && selectedTrade.id === t.id) tr.classList.add("selected");

    const isWin = t.net_pnl_usd > 0;
    const isLong = t.direction === "LONG";

    tr.innerHTML = `
      <td><strong>${{t.id}}</strong></td>
      <td>${{t.entry_time.slice(0, 16)}}</td>
      <td><span class="badge ${{isLong ? 'badge-long' : 'badge-short'}}">${{t.direction}}</span></td>
      <td><strong>${{t.playbook}}</strong></td>
      <td>${{t.initiator_16}}</td>
      <td class="font-mono">${{t.entry_price.toFixed(2)}}</td>
      <td class="font-mono">${{t.exit_price.toFixed(2)}}</td>
      <td class="font-mono text-dim">${{t.sl_price.toFixed(2)}}</td>
      <td class="font-mono ${{t.pnl_pts >= 0 ? 'text-green' : 'text-red'}}">${{t.pnl_pts >= 0 ? '+' : ''}}${{t.pnl_pts.toFixed(2)}}</td>
      <td class="font-mono font-bold ${{t.r_multiple >= 0 ? 'text-green' : 'text-red'}}">${{t.r_multiple >= 0 ? '+' : ''}}${{t.r_multiple.toFixed(2)}}R</td>
      <td class="font-mono font-bold ${{isWin ? 'text-green' : 'text-red'}}">${{isWin ? '+' : ''}}$${{t.net_pnl_usd.toFixed(2)}}</td>
      <td class="font-mono text-cyan">$${{t.equity_after.toFixed(2)}}</td>
      <td class="text-dim">${{t.hold_mins}}m</td>
      <td><span class="badge ${{t.exit_reason.includes('40R') ? 'badge-trail' : (t.exit_reason.includes('STALL') ? 'badge-stall' : 'badge-sl')}}">${{t.exit_reason}}</span></td>
      <td>${{t.confirming_count}}/16 (${{t.consensus_pct}}%)</td>
      <td><span class="badge ${{t.is_oos ? 'badge-oos' : 'badge-is'}}">${{t.is_oos ? 'OOS' : 'IS'}}</span></td>
    `;

    tr.addEventListener("click", () => {{
      selectTrade(t, false, false);
      openTradeAuditModal(t);
    }});

    tbody.appendChild(tr);
  }});

  document.getElementById("filteredCountLabel").textContent = 
    `Showing ${{filteredTrades.length}} of ${{TRADES.length}} Trades`;
}}

function applyJournalFilters() {{
  const dir = document.getElementById("filterDirection").value;
  const outcome = document.getElementById("filterOutcome").value;
  const sample = document.getElementById("filterSample").value;
  const reason = document.getElementById("filterExitReason").value;
  const search = document.getElementById("filterSearch").value.toLowerCase().trim();

  filteredTrades = TRADES.filter(t => {{
    if (dir !== "ALL" && t.direction !== dir) return false;
    if (outcome === "WIN" && t.net_pnl_usd <= 0) return false;
    if (outcome === "LOSS" && t.net_pnl_usd >= 0) return false;
    if (sample === "IS" && t.is_oos) return false;
    if (sample === "OOS" && !t.is_oos) return false;
    if (reason !== "ALL" && !t.exit_reason.includes(reason)) return false;

    if (search) {{
      const match = 
        t.playbook.toLowerCase().includes(search) ||
        t.initiator_16.toLowerCase().includes(search) ||
        t.date.includes(search) ||
        t.exit_reason.toLowerCase().includes(search) ||
        String(t.id) === search;
      if (!match) return false;
    }}
    return true;
  }});

  renderJournalTable();
}}

["filterDirection", "filterOutcome", "filterSample", "filterExitReason"].forEach(id => {{
  document.getElementById(id).addEventListener("change", applyJournalFilters);
}});
document.getElementById("filterSearch").addEventListener("input", applyJournalFilters);

function resetJournalFilters() {{
  document.getElementById("filterDirection").value = "ALL";
  document.getElementById("filterOutcome").value = "ALL";
  document.getElementById("filterSample").value = "ALL";
  document.getElementById("filterExitReason").value = "ALL";
  document.getElementById("filterSearch").value = "";
  filteredTrades = [...TRADES];
  renderJournalTable();
}}

// ============================================================================
// INSTITUTIONAL TRADE AUDIT MODAL
// ============================================================================
function openTradeAuditModal(trade) {{
  selectedTrade = trade;
  const modal = document.getElementById("tradeModal");
  const isWin = trade.net_pnl_usd > 0;

  document.getElementById("modalTradeIdBadge").textContent = `TRADE #${{trade.id}}`;
  document.getElementById("modalTradeTitle").innerHTML = `
    ${{trade.playbook}} · <span class="${{isWin ? 'text-green' : 'text-red'}}">${{isWin ? '+' : ''}}${{trade.r_multiple.toFixed(2)}}R ($${{trade.net_pnl_usd.toFixed(2)}} Net)</span>
  `;

  const body = document.getElementById("modalTradeBody");
  body.innerHTML = `
    <!-- Top Highlights Grid -->
    <div class="radar-grid">
      <div class="radar-box">
        <div class="radar-lbl">Execution Price</div>
        <div class="radar-val">${{trade.entry_price.toFixed(2)}} → ${{trade.exit_price.toFixed(2)}}</div>
      </div>
      <div class="radar-box">
        <div class="radar-lbl">Stop Loss Baseline</div>
        <div class="radar-val text-red">${{trade.sl_price.toFixed(2)}} (-${{trade.init_risk_pts.toFixed(2)}} pts)</div>
      </div>
      <div class="radar-box">
        <div class="radar-lbl">Holding Window</div>
        <div class="radar-val">${{trade.hold_mins}} mins (${{trade.session}})</div>
      </div>
      <div class="radar-box">
        <div class="radar-lbl">Equity After Trade</div>
        <div class="radar-val text-cyan">$${{trade.equity_after.toFixed(2)}}</div>
      </div>
      <div class="radar-box">
        <div class="radar-lbl">Max Excursion (MFE)</div>
        <div class="radar-val text-green">+${{trade.mfe_r.toFixed(2)}}R (+${{trade.mfe_pts.toFixed(2)}} pts)</div>
      </div>
      <div class="radar-box">
        <div class="radar-lbl">Max Adverse (MAE)</div>
        <div class="radar-val text-red">-${{trade.mae_r.toFixed(2)}}R (-${{trade.mae_pts.toFixed(2)}} pts)</div>
      </div>
    </div>

    <!-- Governance Section 1 -->
    <div class="audit-sec">
      <div class="audit-sec-title">🔍 Part 1: Lucas Order Flow Analyser (#17 LUCAS)</div>
      <p style="font-size: 12px; color: #e2e8f0;">${{trade.analyser_brief}}</p>
      <div style="font-size: 11px; color: var(--text-dim); margin-top: 4px;">
        Level 2 Book Ratio: <strong>${{trade.l2_ratio}}x</strong> · Vol Z-Score: <strong>${{trade.vol_z >= 0 ? '+' : ''}}${{trade.vol_z}}σ</strong> · 5m Delta: <strong>${{trade.delta_5m}}</strong> · 15m Delta Z: <strong>${{trade.delta_15m}}</strong>
      </div>
    </div>

    <!-- Governance Section 2 -->
    <div class="audit-sec">
      <div class="audit-sec-title">🏛️ Part 2: Clara &amp; Victor Risk Council (#13 CLARA + #15 VICTOR)</div>
      <p style="font-size: 12px; color: #e2e8f0;">${{trade.council_verdict}}</p>
      <div style="margin-top: 6px; font-size: 11.5px; color: var(--gold);">
        Consensus: <strong>${{trade.confirming_count}}/16 Specialists Signed</strong> (${{trade.consensus_pct}}%) · Historical David Twins: <strong>${{trade.david_twins_wr}}% WR (PF ${{trade.david_twins_pf}})</strong>
      </div>
    </div>

    <!-- Governance Section 3 -->
    <div class="audit-sec">
      <div class="audit-sec-title">🧮 Part 3: Ethan Math Engine Sizing Breakdown</div>
      <p style="font-size: 12px; color: #e2e8f0;">
        Position Sized: <strong>${{trade.qty_oz}} oz</strong> ($${{trade.notional_usd.toFixed(2)}} Notional) with strict <strong>$5.00 fixed capital risk</strong>. Round-turn Delta fee paid: <strong>$${{trade.delta_fee_usd.toFixed(2)}}</strong> (0.01% fee). Gross PnL: <strong>$${{trade.gross_pnl_usd.toFixed(2)}}</strong>.
      </p>
    </div>

    <!-- Strategic Pros -->
    <div class="audit-sec">
      <div class="audit-sec-title">✅ Institutional Confluence Factors (Pros)</div>
      <ul style="font-size: 11.5px; color: #94a3b8; padding-left: 18px; margin-top: 4px;">
        ${{(trade.pros || []).map(p => `<li>${{p}}</li>`).join('')}}
      </ul>
    </div>

    <!-- Post-Trade Fix -->
    <div class="audit-sec" style="border-left: 3px solid ${{isWin ? 'var(--tv-green)' : 'var(--tv-red)'}};">
      <div class="audit-sec-title">📋 Trade Diagnosis: ${{trade.mistake_title}}</div>
      <p style="font-size: 12px; color: #cbd5e1;">${{trade.mistake_desc}}</p>
      <div style="font-size: 11px; color: var(--tv-cyan); margin-top: 6px;">
        <strong>Fix / Dynamic Defense:</strong> ${{trade.learner_fix}}
      </div>
    </div>
  `;

  modal.classList.add("open");
}}

function openSelectedTradeModal() {{
  if (selectedTrade) openTradeAuditModal(selectedTrade);
}}

function closeTradeModal() {{
  document.getElementById("tradeModal").classList.remove("open");
}}

function closeModalOnBg(e) {{
  if (e.target.id === "tradeModal") closeTradeModal();
}}

function jumpToModalTradeOnChart() {{
  closeTradeModal();
  selectTrade(selectedTrade, true, true);
}}

// ============================================================================
// EXPORT UTILITIES
// ============================================================================
function exportTradesCSV() {{
  const keys = [
    "id", "entry_time", "exit_time", "direction", "setup_agent", "initiator_16",
    "playbook", "tf", "entry_price", "exit_price", "sl_price", "init_risk_pts",
    "pnl_pts", "r_multiple", "qty_oz", "notional_usd", "gross_pnl_usd",
    "delta_fee_usd", "net_pnl_usd", "equity_after", "exit_reason", "hold_mins",
    "peak_r", "mfe_r", "mae_r", "confirming_count", "consensus_pct", "is_oos"
  ];

  let csv = keys.join(",") + "\\n";
  TRADES.forEach(t => {{
    const row = keys.map(k => {{
      let v = t[k] !== undefined ? t[k] : "";
      if (typeof v === "string" && v.includes(",")) v = `"${{v}}"`;
      return v;
    }});
    csv += row.join(",") + "\\n";
  }});

  const blob = new Blob([csv], {{ type: "text/csv;charset=utf-8;" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "MUX_085SL_40R_CONTINUOUS_TRAIL_265_Trades.csv";
  a.click();
  URL.revokeObjectURL(url);
}}

function exportMetadataJSON() {{
  const data = {{
    meta: PROFILE.meta,
    summary: {{
      total_trades: TRADES.length,
      net_pnl: TRADES.reduce((s, t) => s + t.net_pnl_usd, 0),
      win_rate: (TRADES.filter(t => t.net_pnl_usd > 0).length / TRADES.length) * 100
    }},
    trades: TRADES
  }};
  const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: "application/json" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "MUX_085SL_40R_CONTINUOUS_TRAIL_Dossier.json";
  a.click();
  URL.revokeObjectURL(url);
}}
</script>

</body>
</html>
"""

if __name__ == "__main__":
    build_dashboard()
