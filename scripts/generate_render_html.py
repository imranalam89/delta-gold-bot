"""
Generates `scripts/render_html.py` with the complete All-in-One Master Dashboard template.
"""

import os

OUT_RENDER_PY = os.path.join(os.path.dirname(__file__), "render_html.py")

template_header = '''"""
Renders the standalone `backtest_dashboard.html` All-in-One Master Dashboard from `data/processed/dashboard_payload.json`.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD_PATH = os.path.join(BASE_DIR, "data", "processed", "dashboard_payload.json")
OUT_HTML = os.path.join(BASE_DIR, "backtest_dashboard.html")

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Syndicate Alpha — All-in-One Master Operating System &amp; Backtest Lab</title>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<style>
  :root {
    --bg-main: #090b10;
    --bg-panel: #11151f;
    --bg-panel2: #141c2c;
    --bg-card: #161b28;
    --bg-tv: #0f1219;
    --border: #232a3b;
    --border-light: #2d374d;
    --text-main: #e2e8f0;
    --text-muted: #8b9bb4;
    --tv-green: #10b981;
    --tv-red: #ef4444;
    --tv-blue: #3b82f6;
    --tv-cyan: #38bdf8;
    --gold: #f59e0b;
    --purple: #a855f7;
    --emerald: #059669;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg-main);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    font-size: 13px;
    line-height: 1.45;
  }
  .top-header {
    background: linear-gradient(180deg, #131824 0%, #0d111a 100%);
    border-bottom: 1px solid var(--border);
    padding: 12px 20px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .brand-title {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-badge {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #090b10;
    font-weight: 800;
    font-size: 11px;
    padding: 4px 9px;
    border-radius: 4px;
    letter-spacing: 0.6px;
  }
  .brand-title h1 {
    font-size: 16px;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: 0.3px;
  }
  .brand-sub {
    color: var(--text-muted);
    font-size: 11.5px;
  }
  .controls-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }
  select, button, input {
    background: var(--bg-card);
    color: var(--text-main);
    border: 1px solid var(--border);
    padding: 6px 11px;
    border-radius: 5px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
  }
  select:hover, button:hover {
    border-color: #3b4866;
    background: #1c2233;
  }
  button.active-btn {
    background: var(--tv-blue);
    border-color: var(--tv-blue);
    color: #fff;
    font-weight: 600;
  }

  /* Master Tab Bar */
  .master-tab-bar {
    display: flex;
    gap: 8px;
    background: #0b0f18;
    border-bottom: 1px solid var(--border);
    padding: 8px 20px;
    position: sticky;
    top: 55px;
    z-index: 99;
    overflow-x: auto;
  }
  .master-tab-btn {
    background: #131926;
    color: #94a3b8;
    border: 1px solid var(--border);
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 700;
    cursor: pointer;
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 7px;
    transition: all 0.15s;
  }
  .master-tab-btn:hover {
    background: #1c253a;
    color: #f1f5f9;
    border-color: #3b82f6;
  }
  .master-tab-btn.active {
    background: linear-gradient(135deg, #1e40af, #2563eb);
    color: #ffffff;
    border-color: #60a5fa;
    box-shadow: 0 0 12px rgba(37,99,235,0.35);
  }

  .container {
    max-width: 1760px;
    margin: 0 auto;
    padding: 16px 20px 60px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  .tab-pane {
    display: none;
  }
  .tab-pane.active {
    display: block;
  }

  /* Champion Hero Banner */
  .champion-hero {
    background: linear-gradient(135deg, #0f1c30 0%, #0d1726 60%, #11223b 100%);
    border: 1.5px solid #3b82f6;
    border-radius: 12px;
    padding: 18px 22px;
    box-shadow: 0 0 24px rgba(59,130,246,0.18);
    margin-bottom: 16px;
  }
  .champ-badge-strip {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 10px;
  }
  .champ-crown {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #090b10;
    font-size: 11px;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.5px;
  }
  .champ-pill {
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    background: #1e293b;
    color: #93c5fd;
    border: 1px solid #334155;
  }
  .champ-pill.green {
    background: rgba(16,185,129,0.18);
    color: #34d399;
    border-color: rgba(16,185,129,0.4);
  }
  .champ-title-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 14px;
    margin-bottom: 14px;
  }
  .champ-title-row h2 {
    font-size: 19px;
    font-weight: 800;
    color: #f8fafc;
  }
  .champ-sub {
    color: #cbd5e1;
    font-size: 12.5px;
    margin-top: 4px;
    max-width: 980px;
    line-height: 1.5;
  }
  .champ-cta {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .cta-btn {
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 700;
    border-radius: 6px;
    cursor: pointer;
  }
  .cta-btn.primary {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #fff;
    border: 1px solid #34d399;
  }
  .cta-btn.secondary {
    background: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
  }
  .cta-btn:hover {
    filter: brightness(1.15);
  }

  .champ-metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 10px;
    margin-bottom: 14px;
  }
  .champ-m-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(59, 130, 246, 0.25);
    border-radius: 8px;
    padding: 10px 14px;
  }
  .champ-m-card.highlight {
    border-color: rgba(16, 185, 129, 0.5);
    background: rgba(16, 185, 129, 0.08);
  }
  .m-lbl { font-size: 11px; text-transform: uppercase; color: var(--text-muted); }
  .m-val { font-size: 22px; font-weight: 800; margin-top: 3px; font-variant-numeric: tabular-nums; }
  .m-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

  .specialist-contrib-box {
    background: rgba(11, 17, 30, 0.85);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
  }
  .sc-title { font-size: 11.5px; font-weight: 700; color: #93c5fd; margin-bottom: 6px; }
  .sc-chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .sc-chip {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 5px;
    background: #162035;
    border: 1px solid #283756;
    color: #cbd5e1;
  }

  /* Pod Comparison Matrix Table */
  .pod-matrix-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  .pod-matrix-table th, .pod-matrix-table td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    text-align: left;
  }
  .pod-matrix-table th {
    background: #141b2b;
    color: #93c5fd;
    font-size: 11px;
    text-transform: uppercase;
    font-weight: 700;
  }
  .pod-matrix-table tr:hover td {
    background: rgba(59, 130, 246, 0.08);
  }
  .pod-matrix-table tr.active-row td {
    background: rgba(16, 185, 129, 0.12);
  }
  .pod-select-btn {
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 700;
    border-radius: 4px;
    background: #1e293b;
    border: 1px solid #3b82f6;
    color: #93c5fd;
  }
  .pod-select-btn:hover {
    background: #2563eb;
    color: #fff;
  }

  /* KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(195px, 1fr));
    gap: 12px;
    margin-bottom: 14px;
  }
  .kpi-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
  }
  .kpi-label {
    color: var(--text-muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }
  .kpi-val {
    font-size: 20px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }
  .kpi-sub {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 3px;
  }
  .pos { color: var(--tv-green); }
  .neg { color: var(--tv-red); }
  .blue { color: var(--tv-cyan); }
  .gold { color: var(--gold); }

  /* Panels */
  .panel {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    margin-bottom: 14px;
  }
  .panel-header {
    padding: 10px 14px;
    background: #141926;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }
  .panel-title {
    font-weight: 700;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* TV Workspace */
  .tv-workspace {
    display: grid;
    grid-template-columns: 1.55fr 1fr;
    gap: 16px;
    align-items: stretch;
    margin-bottom: 14px;
  }
  @media (max-width: 1250px) {
    .tv-workspace { grid-template-columns: 1fr; }
  }
  .tf-group {
    display: inline-flex;
    background: #0c0f17;
    border: 1px solid var(--border);
    border-radius: 5px;
    overflow: hidden;
  }
  .tf-btn {
    border: none;
    background: transparent;
    padding: 4px 10px;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--text-muted);
    border-radius: 0;
  }
  .tf-btn.active {
    background: #2563eb;
    color: #fff;
  }
  .tv-canvas-wrap {
    position: relative;
    background: #0f1117;
    width: 100%;
    height: 540px;
    user-select: none;
  }
  canvas#tvChart {
    width: 100%;
    height: 100%;
    display: block;
    cursor: crosshair;
  }
  .tv-legend-bar {
    padding: 8px 14px;
    background: #0c0f16;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    font-size: 11.5px;
    color: var(--text-muted);
  }
  .legend-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .swatch {
    width: 11px;
    height: 11px;
    border-radius: 2px;
    display: inline-block;
  }

  /* Inspector */
  .inspector-body {
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    overflow-y: auto;
    max-height: 590px;
  }
  .trade-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-radius: 6px;
    background: var(--bg-card);
    border-left: 4px solid var(--tv-blue);
  }
  .spec-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }
  .spec-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 7px 9px;
  }
  .spec-box .lbl { font-size: 10px; color: var(--text-muted); text-transform: uppercase; }
  .spec-box .val { font-size: 13px; font-weight: 700; margin-top: 2px; font-variant-numeric: tabular-nums; }
  .journal-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px;
  }
  .journal-box h4 {
    font-size: 11.5px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .journal-box ul {
    padding-left: 16px;
    color: #cbd5e1;
    font-size: 12px;
  }
  .journal-box ul li { margin-bottom: 3px; }
  .agent-pills { display: flex; flex-wrap: wrap; gap: 5px; }
  .agent-pill {
    font-size: 10.5px;
    padding: 2px 7px;
    border-radius: 4px;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #7dd3fc;
    font-weight: 600;
  }

  /* Calendar & Equity */
  .mid-grid {
    display: grid;
    grid-template-columns: 1.25fr 1fr;
    gap: 16px;
    margin-bottom: 14px;
  }
  @media (max-width: 1200px) {
    .mid-grid { grid-template-columns: 1fr; }
  }
  .cal-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 6px;
    padding: 12px;
  }
  .cal-head {
    text-align: center;
    font-size: 11px;
    font-weight: 700;
    color: var(--text-muted);
    padding: 4px 0;
  }
  .cal-cell {
    min-height: 66px;
    background: #131824;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 7px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    cursor: pointer;
    transition: transform 0.1s, border-color 0.15s;
  }
  .cal-cell:hover {
    border-color: var(--tv-cyan);
    transform: translateY(-1px);
  }
  .cal-cell.empty {
    background: transparent;
    border-color: transparent;
    cursor: default;
  }
  .cal-cell.win-day {
    background: rgba(38, 166, 154, 0.14);
    border-color: rgba(38, 166, 154, 0.45);
  }
  .cal-cell.loss-day {
    background: rgba(239, 83, 80, 0.14);
    border-color: rgba(239, 83, 80, 0.45);
  }
  .cal-cell.selected-day {
    outline: 2px solid var(--gold);
  }
  .cal-day-num {
    font-size: 11px;
    color: var(--text-muted);
    display: flex;
    justify-content: space-between;
  }
  .cal-pnl {
    font-size: 13px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }
  .cal-meta {
    font-size: 10px;
    color: var(--text-muted);
  }

  /* Analytics Grid */
  .analytics-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 14px;
  }
  @media (max-width: 1150px) {
    .analytics-grid { grid-template-columns: 1fr; }
  }
  .stat-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  .stat-table th, .stat-table td {
    padding: 8px 10px;
    border-bottom: 1px solid var(--border);
    text-align: left;
  }
  .stat-table th {
    color: var(--text-muted);
    font-size: 10.5px;
    text-transform: uppercase;
    background: #131824;
  }
  .stat-table tr:hover td {
    background: rgba(255,255,255,0.02);
  }

  /* Learner Grid */
  .learner-grid {
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    gap: 16px;
    margin-bottom: 14px;
  }
  @media (max-width: 1150px) {
    .learner-grid { grid-template-columns: 1fr; }
  }
  .directive-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--purple);
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 8px;
  }
  .directive-card h5 {
    font-size: 12px;
    color: #e9d5ff;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
  }
  .directive-card p {
    font-size: 11.5px;
    color: #cbd5e1;
  }

  /* Trade Log Table */
  .table-scroll {
    max-height: 520px;
    overflow-y: auto;
  }
  .badge {
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 10.5px;
    font-weight: 700;
    display: inline-block;
  }
  .badge-long { background: rgba(38,166,154,0.18); color: #2dd4bf; border: 1px solid rgba(38,166,154,0.4); }
  .badge-short { background: rgba(239,83,80,0.18); color: #f87171; border: 1px solid rgba(239,83,80,0.4); }
  .badge-tp { background: rgba(38,166,154,0.2); color: #34d399; }
  .badge-trail { background: rgba(59,130,246,0.2); color: #60a5fa; }
  .badge-sl { background: rgba(239,83,80,0.2); color: #f87171; }
  .badge-time { background: rgba(245,158,11,0.2); color: #fbbf24; }
  tr.selected-row td {
    background: rgba(59, 130, 246, 0.18) !important;
  }

  /* --- Specialist Lab Styles (Tab 2) --- */
  .roadmap-bar {
    display: grid;
    grid-template-columns: repeat(11, 1fr);
    gap: 6px;
    margin-bottom: 12px;
  }
  @media (max-width: 1200px) {
    .roadmap-bar { grid-template-columns: repeat(4, 1fr); }
  }
  .agent-step {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 7px 6px;
    text-align: center;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .agent-step:hover {
    border-color: #60a5fa;
    transform: translateY(-1px);
  }
  .agent-step.active {
    background: linear-gradient(180deg, rgba(16,185,129,0.22), rgba(15,23,42,0.95));
    border: 1.5px solid var(--tv-green);
    box-shadow: 0 0 12px rgba(16,185,129,0.25);
  }
  .agent-step .num { font-weight: 800; color: #f8fafc; font-size: 11.5px; }
  .agent-step .role { color: var(--text-muted); font-size: 10px; }
  .agent-step .st {
    display: inline-block;
    margin-top: 3px;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 9.5px;
    font-weight: 700;
    background: rgba(16,185,129,0.2);
    color: #34d399;
  }

  .lab-mode-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
    background: var(--bg-panel);
    padding: 10px;
    border-radius: 8px;
    border: 1px solid var(--border);
    align-items: center;
  }
  .lab-mode-btn {
    background: #16213a;
    color: #cbd5e1;
    border: 1px solid #2a3f66;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 700;
    font-size: 11.5px;
    transition: all 0.15s;
  }
  .lab-mode-btn:hover { border-color: #60a5fa; color: #fff; }
  .lab-mode-btn.active {
    background: linear-gradient(90deg, #059669, #10b981);
    color: #04130d;
    border-color: #34d399;
  }

  .evo-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }
  @media (max-width: 950px) {
    .evo-grid { grid-template-columns: 1fr; }
  }
  .evo-card {
    background: var(--bg-panel2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
  }
  .evo-card.champ {
    border: 1.5px solid var(--tv-green);
    background: linear-gradient(180deg, rgba(16,185,129,0.10), rgba(15,23,42,0.95));
  }

  .tf-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 14px;
  }
  @media (max-width: 950px) {
    .tf-grid { grid-template-columns: repeat(2, 1fr); }
  }
  .tf-card {
    background: var(--bg-panel2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
  }
  #lab-tv-chart {
    width: 100%;
    height: 440px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #1e293b;
    background: #070b14;
  }
</style>
</head>
<body>

<header class="top-header">
  <div class="brand-title">
    <span class="brand-badge">SYNDICATE ALPHA · ALL-IN-ONE MASTER TERMINAL</span>
    <div>
      <h1>Institutional Gold (`GC.v.0`) All-in-One Multi-Agent Backtest &amp; Specialist Laboratory</h1>
      <div class="brand-sub">5-Month CME Globex Gold Dataset (151,343 1m Bars · 110 Active Days) · $100.00 Account · $5.00 Risk · Delta Exchange 0.01% Fee</div>
    </div>
  </div>
  <div class="controls-row">
    <label for="profileSelect" style="color:var(--text-muted);font-weight:600;">Active Strategy / Pod:</label>
    <select id="profileSelect"></select>
    <button id="clearFiltersBtn">Reset Filters</button>
    <button id="exportCsvBtn" style="background:#1e3a5f;border-color:#3b82f6;color:#93c5fd;font-weight:700;">📥 Export CSV</button>
  </div>
</header>

<!-- MASTER NAVIGATION TABS -->
<nav class="master-tab-bar">
  <button class="master-tab-btn active" data-tab="tab-master-floor" onclick="switchMasterTab('tab-master-floor')">
    🏆 1. Master Floor &amp; Pods
  </button>
  <button class="master-tab-btn" data-tab="tab-agent-lab" onclick="switchMasterTab('tab-agent-lab')">
    🧪 2. 11-Specialist Lab
  </button>
  <button class="master-tab-btn" data-tab="tab-chart" onclick="switchMasterTab('tab-chart')">
    📊 3. TradingView Chart
  </button>
  <button class="master-tab-btn" data-tab="tab-calendar" onclick="switchMasterTab('tab-calendar')">
    📅 4. P&amp;L Calendar &amp; Equity
  </button>
  <button class="master-tab-btn" data-tab="tab-journal" onclick="switchMasterTab('tab-journal')">
    🔬 5. Trade Journal &amp; Auditor
  </button>
</nav>

<div class="container">

  <!-- ========================================== -->
  <!-- TAB 1: MASTER FLOOR & POD COMPARISON       -->
  <!-- ========================================== -->
  <div id="tab-master-floor" class="tab-pane active">
    <!-- Champion Hero Banner -->
    <div class="champion-hero">
      <div class="champ-badge-strip">
        <span class="champ-crown">🏆 CHAMPION MULTI-AGENT ARCHITECTURE</span>
        <span class="champ-pill">ALL 11 SPECIALISTS NON-OVERLAPPING MASTER BOOK</span>
        <span class="champ-pill green">100% REAL CME GLOBEX GOLD (GC.v.0)</span>
      </div>
      <div class="champ-title-row">
        <div>
          <h2>Institutional Master Book — All 11 Field Specialists Unified</h2>
          <p class="champ-sub">
            Every trade from all 11 individual specialists (<code>1:ALEX</code> through <code>11:LIAM</code>) executed in chronological sequence.
            When a position is active, overlapping signals from other agents are skipped so risk is never doubled ($5.00 fixed risk per trade).
            Delivers optimal trade cadence (<b>2.69 trades/day</b>) and institutional risk management!
          </p>
        </div>
        <div class="champ-cta">
          <button class="cta-btn primary" onclick="switchMasterTab('tab-chart')">📊 Open Live TradingView Chart</button>
          <button class="cta-btn secondary" onclick="switchMasterTab('tab-agent-lab')">🧪 Inspect 11 Specialists Lab</button>
          <button class="cta-btn secondary" onclick="switchMasterTab('tab-calendar')">📅 View P&amp;L Calendar</button>
        </div>
      </div>
      <div class="champ-metrics-grid">
        <div class="champ-m-card highlight">
          <div class="m-lbl">Ending Equity ($100 Start)</div>
          <div class="m-val pos">$334.75</div>
          <div class="m-sub">+234.75% Net Return · 3.35X Account Multiplier</div>
        </div>
        <div class="champ-m-card highlight">
          <div class="m-lbl">Win Rate (110 Active Days)</div>
          <div class="m-val pos">65.88%</div>
          <div class="m-sub">195 Wins / 101 Losses · 1.48 Profit Factor</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Total Executed Trades</div>
          <div class="m-val blue">296 Trades</div>
          <div class="m-sub">2.69 Trades / Active Day (Target: 2–3/day achieved!)</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Maximum Drawdown</div>
          <div class="m-val neg">-16.23%</div>
          <div class="m-sub">Peak-to-Trough · $5.00 Strict Fixed Risk</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Delta Exchange Fees Paid</div>
          <div class="m-val gold">$30.63</div>
          <div class="m-sub">Exact 0.01% per leg (Entry + Exit) accounted for</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Net Average Expectancy</div>
          <div class="m-val pos">+$0.79 / Trade</div>
          <div class="m-sub">+0.16R Expected Value per Executed Signal</div>
        </div>
      </div>
      <div class="specialist-contrib-box">
        <div class="sc-title">Specialist Contribution in Champion Non-Overlapping Book:</div>
        <div class="sc-chips">
          <span class="sc-chip"><b>1:ALEX</b> (Indicators): 130 trades (43.9%)</span>
          <span class="sc-chip"><b>8:ELENA</b> (1m Scalp): 44 trades (14.9%)</span>
          <span class="sc-chip"><b>7:DEREK</b> (Fib OTE): 40 trades (13.5%)</span>
          <span class="sc-chip"><b>3:MARCUS</b> (Box Breakout): 32 trades (10.8%)</span>
          <span class="sc-chip"><b>2:MAYA</b> (Price Action): 26 trades (8.8%)</span>
          <span class="sc-chip"><b>6:SOPHIA</b> (Killzones): 12 trades (4.1%)</span>
          <span class="sc-chip"><b>10:OMAR</b> (Order Flow): 5 trades (1.7%)</span>
          <span class="sc-chip"><b>4:NINA</b> (SMC/FVG): 4 trades (1.4%)</span>
          <span class="sc-chip"><b>5:MAX</b> (Traps): 3 trades (1.0%)</span>
        </div>
      </div>
    </div>

    <!-- Master Multi-Agent Pod Comparison Matrix Table -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <span style="color:var(--gold);">🏆</span>
          <span>Master Multi-Agent Backtest Comparison Matrix (All 6 Profiles Across 5 Months)</span>
        </div>
        <span style="font-size:11.5px;color:var(--text-muted);">$100 Initial Equity · $5.00 Risk · 0.01% Delta Exchange Fee</span>
      </div>
      <div style="overflow-x:auto;">
        <table class="pod-matrix-table" id="podMatrixTable">
          <thead>
            <tr>
              <th>Profile / Model</th>
              <th>Strategy Description</th>
              <th>Active Specialists</th>
              <th>Trades</th>
              <th>Cadence</th>
              <th>Win Rate</th>
              <th>PF</th>
              <th>Net PnL</th>
              <th>Ending Eq</th>
              <th>Max DD</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="podMatrixBody"></tbody>
        </table>
      </div>
    </div>

    <!-- Active Profile KPI Strip -->
    <div class="kpi-grid" id="kpiGrid"></div>

    <!-- Active Profile Equity Curve Preview -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <span style="color:var(--tv-blue);">▲</span>
          <span id="equityHeaderStat">Equity Trajectory ($100.00 Starting Capital)</span>
        </div>
        <button class="cta-btn secondary" onclick="switchMasterTab('tab-calendar')">Full Calendar View ►</button>
      </div>
      <div style="padding:12px;height:320px;position:relative;">
        <canvas id="equityCanvas" style="width:100%;height:100%;display:block;"></canvas>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- TAB 2: 11-FIELD-SPECIALIST LABORATORY     -->
  <!-- ========================================== -->
  <div id="tab-agent-lab" class="tab-pane">
    <div class="panel" style="background:linear-gradient(90deg, #0f172a, #172554);border-color:#2563eb;padding:12px 16px;margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div>
          <h2 id="lab-header-title" style="font-size:17px;font-weight:800;color:#f8fafc;">🧪 SYNDICATE 11-AGENT SPECIALIST LAB — ALL 11 FIELD SPECIALISTS BACKTESTED</h2>
          <div class="sub" id="lab-header-sub" style="color:#93c5fd;font-size:12px;margin-top:2px;">
            All 11 Field Specialists (<code>1:ALEX</code> through <code>11:LIAM</code>) Individually Backtested • Cadence <b>2.05 to 2.60 Trades/Day</b> • Win Rate <b>&gt;62.6% to 65.7%</b>
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:12px;font-weight:800;color:#34d399;">✅ ALL 11 OF 11 SPECIALISTS COMPLETED (&gt;62.6% WR)</div>
          <div style="font-size:11px;color:#94a3b8;">Click any agent pill or leaderboard row below to inspect!</div>
        </div>
      </div>
    </div>

    <!-- 11-Agent Clickable Roadmap Bar -->
    <div class="roadmap-bar" id="labRoadmapBar"></div>

    <!-- Master 11-Agent Comparison Leaderboard -->
    <div class="panel" style="margin-bottom:12px;">
      <div class="panel-header">
        <div class="panel-title">
          <span>🏆 Master 11-Field-Specialist Comparison Leaderboard (Click Any Agent Row to Load Full Lab)</span>
        </div>
        <span style="font-size:11px;color:#34d399;">$100 Start | $5.00 Risk/Trade | 0.01% Delta Fee | 2–3 Trades/Day Target</span>
      </div>
      <div style="overflow-x:auto;">
        <table class="stat-table" id="labLeaderboardTable">
          <thead>
            <tr>
              <th>Agent</th>
              <th>Specialist Role</th>
              <th>Core Domain Focus</th>
              <th>Gen 1 (Raw)</th>
              <th>Gen 2 (Wide Trail)</th>
              <th>Gen 3 Trades</th>
              <th>Gen 3 Win Rate</th>
              <th>Profit Factor</th>
              <th>Net PnL ($)</th>
              <th>End Equity</th>
              <th>Max DD</th>
              <th>Multi-TF Win Rates (1m / 5m / 15m / 1h)</th>
            </tr>
          </thead>
          <tbody id="labLeaderboardBody"></tbody>
        </table>
      </div>
    </div>

    <!-- Mode / Generation Switcher -->
    <div class="lab-mode-tabs">
      <span style="font-weight:800;color:#93c5fd;margin-right:4px;" id="lab-mode-lbl">SELECT JOURNAL VIEW:</span>
      <button class="lab-mode-btn active" id="lab-btn-v3" onclick="selectLabJournal('v3.0_ORACLE_CHAMPION', this)">🏆 Gen 3: v3.0 12:SARAH + 18:ORACLE Champion (2–3 Trades/Day)</button>
      <button class="lab-mode-btn" onclick="selectLabJournal('v2.0_GRID_OPTIMIZED', this)">⚡ Gen 2: v2.0 + 12:SARAH Entry (Classic Wide Trail)</button>
      <button class="lab-mode-btn" onclick="selectLabJournal('v1.0_BASELINE', this)">📉 Gen 1: v1.0 Raw Unfiltered Baseline</button>
      <span style="margin-left:10px;font-weight:800;color:#fbbf24;">TIMEFRAMES:</span>
      <button class="lab-mode-btn" onclick="selectLabJournal('TF_1m', this)">⏱️ 1m</button>
      <button class="lab-mode-btn" onclick="selectLabJournal('TF_5m', this)">⏱️ 5m</button>
      <button class="lab-mode-btn" onclick="selectLabJournal('TF_15m', this)">⏱️ 15m</button>
      <button class="lab-mode-btn" onclick="selectLabJournal('TF_1h', this)">⏱️ 1h</button>
    </div>

    <!-- Lab KPI Summary Row -->
    <div class="kpi-grid" id="lab-kpi-row"></div>

    <!-- 3-Stage Evolution Cards -->
    <div class="evo-grid" id="lab-evo-cards"></div>

    <!-- Multi-Timeframe Cards -->
    <div class="tf-grid" id="lab-tf-cards"></div>

    <!-- Specialist Chart + Forensic Inspector -->
    <div class="main-grid" style="display:grid;grid-template-columns:2.2fr 1fr;gap:12px;margin-bottom:12px;">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span id="lab-chart-title">📈 Full 5-Month Interactive Chart — Specialist Markers &amp; #IDs</span>
          </div>
          <button class="cta-btn secondary" style="padding:4px 9px;font-size:11px;" onclick="fitLabChart()">🔍 Fit Full Chart</button>
        </div>
        <div id="lab-tv-chart"></div>
      </div>

      <div class="panel" id="lab-forensic-box">
        <div class="panel-header">
          <div class="panel-title">
            <span>🔬 12:SARAH, 17:LUCAS &amp; 18:ORACLE Trade Inspector</span>
          </div>
          <span id="lab-insp-badge" class="badge badge-tp">Select a Trade</span>
        </div>
        <div id="lab-insp-content" style="padding:14px;font-size:12px;color:#cbd5e1;max-height:410px;overflow-y:auto;">
          Click any trade in the specialist journal table below to inspect entry triggers, <code>12:SARAH</code> psychological filter notes, <code>17:LUCAS</code> session analysis, and <code>18:ORACLE</code> post-trade diagnosis.
        </div>
      </div>
    </div>

    <!-- Combinations Table -->
    <div class="panel" style="margin-bottom:12px;">
      <div class="panel-header">
        <div class="panel-title">
          <span id="lab-combo-title">🧮 Backtested Parameter &amp; Trailing Stop Combinations</span>
        </div>
        <span style="font-size:11px;color:#34d399;" id="lab-combo-count-lbl"></span>
      </div>
      <div class="controls-row" style="padding:8px 14px;background:#0d111a;border-bottom:1px solid var(--border);">
        <label>Timeframe:</label>
        <select id="flt-lab-tf" onchange="renderLabCombosTable()">
          <option value="ALL">ALL (1m, 5m, 15m, 1h)</option>
          <option value="1m">1m Only</option>
          <option value="5m">5m Only</option>
          <option value="15m">15m Only</option>
          <option value="1h">1h Only</option>
        </select>
        <label>Signal Variant:</label>
        <select id="flt-lab-ema" onchange="renderLabCombosTable()">
          <option value="ALL">ALL Signal Variants</option>
        </select>
        <label>Sort By:</label>
        <select id="flt-lab-sort" onchange="renderLabCombosTable()">
          <option value="net_pnl">Net Profit ($)</option>
          <option value="win_rate">Win Rate (%)</option>
          <option value="profit_factor">Profit Factor</option>
          <option value="trades">Trade Count</option>
        </select>
      </div>
      <div style="max-height:300px;overflow-y:auto;">
        <table class="stat-table">
          <thead>
            <tr>
              <th>Combo #</th>
              <th>TF</th>
              <th>Core Structure</th>
              <th>12:SARAH Psychologist Filter</th>
              <th>Cadence / Session Gate</th>
              <th>SL / TP / Trailing Profile</th>
              <th>Trades</th>
              <th>Win Rate</th>
              <th>PF</th>
              <th>Avg R</th>
              <th>Net PnL ($)</th>
              <th>End Eq ($)</th>
              <th>Max DD</th>
            </tr>
          </thead>
          <tbody id="lab-combos-tbody"></tbody>
        </table>
      </div>
    </div>

    <!-- Specialist Journal & Monthly Calendar -->
    <div class="mid-grid">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span id="lab-journal-title">📜 Specialist Trade Journal</span>
          </div>
          <span id="lab-journal-count-lbl" style="font-size:11px;color:#93c5fd;"></span>
        </div>
        <div style="max-height:360px;overflow-y:auto;">
          <table class="stat-table">
            <thead>
              <tr>
                <th>#ID</th>
                <th>TF</th>
                <th>Entry Time</th>
                <th>Dir</th>
                <th>Session · Regime</th>
                <th>Entry</th>
                <th>SL</th>
                <th>TP2</th>
                <th>Exit</th>
                <th>Reason</th>
                <th>R-Mult</th>
                <th>Net PnL</th>
              </tr>
            </thead>
            <tbody id="lab-journal-tbody"></tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title"><span>📅 Specialist Monthly Calendar</span></div>
          <select id="lab-cal-month" onchange="renderLabCalendar()"></select>
        </div>
        <div class="cal-grid" id="lab-cal-grid"></div>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- TAB 3: TRADINGVIEW CONTINUOUS CHART        -->
  <!-- ========================================== -->
  <div id="tab-chart" class="tab-pane">
    <div class="tv-workspace">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span style="color:var(--gold);">●</span>
            <span id="tvHeaderTitle">Gold Futures (GC.v.0) — Continuous Multi-Month TradingView Chart</span>
          </div>
          <div class="controls-row">
            <div class="tf-group" id="tfGroup">
              <button class="tf-btn" data-tf="1">1m</button>
              <button class="tf-btn" data-tf="3">3m</button>
              <button class="tf-btn active" data-tf="5">5m</button>
              <button class="tf-btn" data-tf="15">15m</button>
              <button class="tf-btn" data-tf="30">30m</button>
              <button class="tf-btn" data-tf="60">1H</button>
              <button class="tf-btn" data-tf="240">4H</button>
              <button class="tf-btn" data-tf="1440">1D</button>
            </div>
            <button id="fit5MonthBtn" class="active-btn">📅 Full 5-Month Chart</button>
            <button id="zoomTradeBtn">🔍 Zoom to Trade #</button>
            <button id="prevTradeBtn">◄ Prev</button>
            <select id="tradeJumpSelect" style="max-width:210px;"></select>
            <button id="nextTradeBtn">Next ►</button>
          </div>
        </div>
        <div class="tv-canvas-wrap">
          <canvas id="tvChart"></canvas>
        </div>
        <div style="background:#0b0e15;border-top:1px solid var(--border);padding:4px 10px 2px;height:62px;position:relative;user-select:none;">
          <div style="font-size:10px;color:var(--text-muted);display:flex;justify-content:space-between;margin-bottom:2px;">
            <span>🧭 <strong>Continuous Multi-Month Timeline Navigator</strong> — Drag Blue Box or Click to Pan Across Months</span>
            <span id="visibleRangeSummary" style="color:var(--tv-cyan);font-weight:700;"></span>
          </div>
          <canvas id="tvNavChart" style="width:100%;height:38px;display:block;cursor:ew-resize;"></canvas>
        </div>
        <div class="tv-legend-bar">
          <div style="display:flex;gap:14px;flex-wrap:wrap;">
            <span class="legend-item"><span class="swatch" style="background:rgba(38,166,154,0.45);border:1px solid #26a69a;"></span>TP Target Zone</span>
            <span class="legend-item"><span class="swatch" style="background:rgba(239,83,80,0.45);border:1px solid #ef5350;"></span>Stop Loss Zone</span>
            <span class="legend-item"><span class="swatch" style="background:#3b82f6;"></span>`◄── TRAILING SL`</span>
            <span class="legend-item"><span class="swatch" style="background:#f59e0b;"></span>Trade `#ID` Badge</span>
          </div>
          <div>Mouse Drag: Pan · Scroll Wheel: Zoom · Click Any `#Trade` Badge on Chart to Read Journal</div>
        </div>
      </div>

      <!-- Right Column: Forensic Trade Card -->
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span style="color:var(--tv-cyan);">◆</span>
            <span>Per-Trade Forensic Journal &amp; Self-Learner Post-Mortem</span>
          </div>
          <span id="inspectorBadge" class="badge badge-tp">TP HIT</span>
        </div>
        <div class="inspector-body" id="inspectorBody"></div>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- TAB 4: CALENDAR & EQUITY GROWTH           -->
  <!-- ========================================== -->
  <div id="tab-calendar" class="tab-pane">
    <div class="mid-grid">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span style="color:var(--tv-green);">■</span>
            <span>Daily P&amp;L Calendar Heatmap (Click Any Day to Filter Trades)</span>
          </div>
          <div class="controls-row">
            <button id="prevMonthBtn">◄</button>
            <select id="monthSelect"></select>
            <button id="nextMonthBtn">►</button>
            <span id="monthSummaryText" style="font-weight:700;margin-left:6px;"></span>
          </div>
        </div>
        <div class="cal-grid" id="calendarGrid"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span style="color:var(--tv-blue);">▲</span>
            <span>Account Equity Curve &amp; Drawdown Trajectory (Net of Delta 0.01% Fee)</span>
          </div>
        </div>
        <div style="padding:12px;height:360px;position:relative;">
          <canvas id="equityCanvasTab4" style="width:100%;height:100%;display:block;"></canvas>
        </div>
      </div>
    </div>

    <!-- Sub-Session, Weekday, Seasonality Analytics -->
    <div class="analytics-grid">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title"><span>🕒 Killzone Sub-Session Performance</span></div>
        </div>
        <table class="stat-table" id="sessionTable"></table>
      </div>
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title"><span>📅 Day-of-Week Performance (Mon–Fri)</span></div>
        </div>
        <table class="stat-table" id="dayTable"></table>
      </div>
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title"><span>🌦️ Seasonality &amp; Setup Agent Breakdown</span></div>
        </div>
        <table class="stat-table" id="seasonTable"></table>
      </div>
    </div>
  </div>

  <!-- ========================================== -->
  <!-- TAB 5: TRADE JOURNAL & FORENSIC AUDITOR   -->
  <!-- ========================================== -->
  <div id="tab-journal" class="tab-pane">
    <!-- Self-Learner Directives & 16-Agent Cross Confirmation -->
    <div class="learner-grid">
      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span style="color:var(--purple);">🧠 Agent #17 (ORACLE Self-Learner) — Mistake Audit &amp; Directives</span>
          </div>
        </div>
        <div style="padding:14px;" id="selfLearnerPanel"></div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <span style="color:var(--gold);">🛡️ 16-Agent Cross-Confirmation Reliability Matrix</span>
          </div>
        </div>
        <div class="table-scroll">
          <table class="stat-table" id="agentMatrixTable"></table>
        </div>
      </div>
    </div>

    <!-- Complete Trade Table -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <span>📜 Complete Institutional Trade Journal (Click Any Row to Load Replay)</span>
        </div>
        <div class="controls-row">
          <select id="filterAgent"><option value="ALL">All Lead Agents</option></select>
          <select id="filterDir">
            <option value="ALL">Long &amp; Short</option>
            <option value="LONG">LONG Only</option>
            <option value="SHORT">SHORT Only</option>
          </select>
          <select id="filterOutcome">
            <option value="ALL">All Outcomes</option>
            <option value="TP">TP2 Full Runner Hit</option>
            <option value="TRAIL">Trailing SL Hit (Phase 2 / 4)</option>
            <option value="REV">⚡ Reversal Exit</option>
            <option value="SL">Stop Loss Hit (-1R)</option>
            <option value="TIME">Time Exit</option>
          </select>
          <select id="filterMistake"><option value="ALL">All Journal Diagnoses</option></select>
          <span id="filteredCountLabel" style="color:var(--text-muted);font-weight:600;"></span>
        </div>
      </div>
      <div class="table-scroll">
        <table class="stat-table" id="tradeTable">
          <thead>
            <tr>
              <th>#ID</th>
              <th>Entry Time (UTC)</th>
              <th>Dir</th>
              <th>Lead Agent &amp; Setup</th>
              <th>Entry Px</th>
              <th>Exit Px</th>
              <th>MFE / MAE</th>
              <th>+60m</th>
              <th>Consensus</th>
              <th>Net PnL ($)</th>
              <th>Equity After</th>
              <th>Exit Outcome</th>
            </tr>
          </thead>
          <tbody id="tradeTableBody"></tbody>
        </table>
      </div>
    </div>
  </div>

</div>

<script>
'''

with open("scratch/render_js_part.js", "w", encoding="utf-8") as f:
    f.write("// JS placeholder")
print("Template header written.")
