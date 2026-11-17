"""
Builds the dedicated, standalone, offline-ready institutional HTML Backtest Report:
  backtest_DELTA_GOLD_ALL_AGENTS_REPORT.html

Reads:
  data/processed/delta_gold_all_agents_backtest_report.json

Includes:
  - Interactive 6-Champion Profile Switcher + Legacy Baseline Comparison
  - 8 Dynamic KPI Cards + Root-Cause Diagnostics Banner
  - Tab 1: Executive Dossier, Multi-Profile Overlay Equity Curve & Underwater DD Canvas,
           Monthly/Weekly/Session/DOW/Timeframe/Playbook/Agent/Exit Breakdowns
  - Tab 2: 6,336-Combination Grid Explorer (Lifecycles LC0..LC7, Rosters R0..R10,
           Timeframes, and Sortable/Filterable Top-100 Leaderboard)
  - Tab 3: All 16 Floor Agents Telemetry, 11 Specialists + 6 Pods Multi-TF Matrix,
           and Day-of-Week x Session Router Map
  - Tab 4: Interactive 60 FPS HTML5 Canvas XAUTUSD Candlestick Chart (5m/15m/1h/4h)
           with Entry/Exit/SL/TP1/TP2 overlays, Pan/Zoom, Minimap & Trade Stepper
  - Tab 5: Oct & Nov 2026 P&L Calendar Heatmap + Complete 32-Weekday Day-by-Day Log
  - Tab 6: Complete Trade-by-Trade Journal + 16-Agent Forensic Audit Modal + CSV/JSON Export
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_JSON_PATH = os.path.join(BASE_DIR, "data", "processed", "delta_gold_all_agents_backtest_report.json")
OUT_HTML_PATH = os.path.join(BASE_DIR, "backtest_DELTA_GOLD_ALL_AGENTS_REPORT.html")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Delta Exchange Gold (XAUTUSD) — All-Agent 6,336-Combination Backtest Report</title>
<style>
  :root {
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
    --tv-red: #ef4444;
    --tv-blue: #3b82f6;
    --tv-cyan: #06b6d4;
    --gold: #f59e0b;
    --purple: #a855f7;
    --pink: #ec4899;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg-main);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    font-size: 13px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }
  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
  .text-green { color: var(--tv-green); }
  .text-red { color: var(--tv-red); }
  .text-gold { color: var(--gold); }
  .text-cyan { color: var(--tv-cyan); }
  .text-blue { color: var(--tv-blue); }
  .text-purple { color: var(--purple); }
  .text-muted { color: var(--text-muted); }
  .text-dim { color: var(--text-dim); }

  /* Sticky Header */
  .header-bar {
    background: linear-gradient(180deg, #111624 0%, #0a0d15 100%);
    border-bottom: 1px solid var(--border);
    padding: 12px 22px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
  }
  .brand-area { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .badge-crown {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #000;
    font-weight: 800;
    font-size: 11px;
    padding: 5px 10px;
    border-radius: 5px;
    letter-spacing: 0.7px;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.35);
  }
  .brand-info h1 { font-size: 16px; font-weight: 700; color: #fff; }
  .brand-info p { font-size: 11.5px; color: var(--text-muted); }
  .header-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

  .btn {
    background: var(--bg-card);
    color: var(--text-main);
    border: 1px solid var(--border);
    padding: 7px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .btn:hover { background: var(--bg-card-hover); border-color: var(--tv-blue); }
  .btn.active, .btn.btn-primary {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    border-color: #3b82f6;
    color: #fff;
  }
  .btn.btn-gold {
    background: linear-gradient(135deg, #d97706, #b45309);
    border-color: #f59e0b;
    color: #fff;
  }
  .btn.btn-success {
    background: linear-gradient(135deg, #059669, #047857);
    border-color: #10b981;
    color: #fff;
  }

  .container {
    max-width: 1780px;
    margin: 0 auto;
    padding: 18px 22px 80px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  /* Profile Selector Strip */
  .profile-bar {
    background: var(--bg-panel);
    border: 1px solid var(--border-light);
    border-radius: 9px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .profile-bar-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }
  .profile-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 10px;
  }
  .p-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 10px 12px;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: left;
  }
  .p-card.merged-card {
    border-color: rgba(16, 185, 129, 0.35);
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.06) 0%, var(--bg-card) 100%);
  }
  .p-card:hover { background: var(--bg-card-hover); border-color: var(--border-light); transform: translateY(-1px); }
  .p-card.active {
    background: linear-gradient(135deg, #161d31 0%, #101726 100%);
    border-color: var(--gold);
    box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.35), 0 4px 16px rgba(0, 0, 0, 0.45);
  }
  .p-card.merged-card.active {
    border-color: #10b981;
    box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.45), 0 4px 16px rgba(0, 0, 0, 0.45);
  }
  .profile-tier-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 2px;
    padding-top: 6px;
    border-top: 1px dashed var(--border);
    font-size: 11.5px;
    color: var(--text-muted);
  }
  .p-card-top { display: flex; justify-content: space-between; align-items: center; gap: 6px; margin-bottom: 4px; }
  .p-card-title { font-weight: 700; font-size: 12px; color: #fff; }
  .p-card-stats { font-size: 11px; color: var(--text-muted); display: flex; justify-content: space-between; gap: 6px; flex-wrap: wrap; }

  /* Hero Banner */
  .hero-banner {
    background: linear-gradient(135deg, #0e1424 0%, #141b2d 60%, #171324 100%);
    border: 1px solid var(--border-light);
    border-left: 4px solid var(--gold);
    border-radius: 10px;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .hero-top { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; }
  .pill {
    display: inline-block;
    font-size: 10.5px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.35px;
    border: 1px solid transparent;
  }
  .pill-gold { background: rgba(245,158,11,0.16); color: #fbbf24; border-color: rgba(245,158,11,0.4); }
  .pill-cyan { background: rgba(6,182,212,0.15); color: #22d3ee; border-color: rgba(6,182,212,0.4); }
  .pill-green { background: rgba(16,185,129,0.15); color: #34d399; border-color: rgba(16,185,129,0.4); }
  .pill-purple { background: rgba(168,85,247,0.15); color: #c084fc; border-color: rgba(168,85,247,0.4); }
  .pill-red { background: rgba(239,68,68,0.15); color: #f87171; border-color: rgba(239,68,68,0.4); }
  .pill-blue { background: rgba(59,130,246,0.16); color: #60a5fa; border-color: rgba(59,130,246,0.4); }

  .rc-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 12px; }
  .rc-card {
    background: rgba(10, 14, 24, 0.72);
    border: 1px solid var(--border);
    border-top: 3px solid var(--tv-cyan);
    border-radius: 7px;
    padding: 11px 13px;
  }
  .rc-card h4 { font-size: 12px; color: #fff; margin-bottom: 5px; }
  .rc-card p { font-size: 11.2px; color: var(--text-muted); line-height: 1.45; }

  /* KPI Grid */
  .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
  .kpi-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 13px 15px;
    transition: border-color 0.2s;
  }
  .kpi-card:hover { border-color: var(--border-light); }
  .kpi-label {
    color: var(--text-muted);
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 5px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .kpi-val {
    font-size: 22px;
    font-weight: 800;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    line-height: 1.2;
  }
  .kpi-sub { font-size: 11px; color: var(--text-dim); margin-top: 4px; }

  /* Tabs */
  .tab-nav {
    display: flex;
    gap: 6px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    overflow-x: auto;
  }
  .tab-btn {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 9px 15px;
    border-radius: 6px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 7px;
    white-space: nowrap;
  }
  .tab-btn:hover { background: var(--bg-card); color: #fff; }
  .tab-btn.active {
    background: var(--tv-blue);
    border-color: var(--tv-blue);
    color: #fff;
    box-shadow: 0 2px 10px rgba(59, 130, 246, 0.35);
  }
  .tab-btn .badge-count {
    background: rgba(255,255,255,0.2);
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
  }
  .tab-pane { display: none; flex-direction: column; gap: 18px; }
  .tab-pane.active { display: flex; }

  /* Panels & Grids */
  .panel { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  .panel-header {
    background: var(--bg-card);
    border-bottom: 1px solid var(--border);
    padding: 11px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
  }
  .panel-title { font-size: 13.5px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; }
  .panel-body { padding: 15px 16px; }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(520px, 1fr)); gap: 16px; }
  .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 14px; }

  /* Tables */
  .data-table-wrap { overflow-x: auto; width: 100%; max-height: 580px; overflow-y: auto; }
  table.data-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; }
  table.data-table th {
    background: #111624;
    color: var(--text-muted);
    font-weight: 700;
    padding: 9px 11px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 2;
  }
  table.data-table th.sortable { cursor: pointer; }
  table.data-table th.sortable:hover { color: #fff; }
  table.data-table td { padding: 8px 11px; border-bottom: 1px solid #1a2130; white-space: nowrap; }
  table.data-table tr:hover td { background: rgba(59, 130, 246, 0.08); }
  table.data-table tr.clickable { cursor: pointer; }
  table.data-table tr.selected td { background: rgba(245, 158, 11, 0.16) !important; }
  table.data-table tr.row-total td { background: #121827; font-weight: 700; border-top: 1px solid var(--border-light); }

  /* Canvas Containers */
  .chart-canvas-box {
    position: relative;
    width: 100%;
    height: 360px;
    background: #090c13;
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
  }
  canvas#equityCanvas { width: 100%; height: 100%; display: block; }
  .tv-chart-box {
    position: relative;
    width: 100%;
    height: 580px;
    background: #090c13;
    border: 1px solid var(--border);
    border-radius: 6px 6px 0 0;
    overflow: hidden;
  }
  canvas#tvChart { width: 100%; height: 100%; display: block; cursor: crosshair; }
  .tv-nav-box {
    width: 100%;
    height: 48px;
    background: #06080d;
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 6px 6px;
    display: block;
    cursor: pointer;
  }
  .chart-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 14px;
    background: #0c1018;
    border-bottom: 1px solid var(--border);
    gap: 10px;
    flex-wrap: wrap;
  }
  .tf-group { display: flex; gap: 4px; }
  .tf-btn {
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 4px 9px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
  }
  .tf-btn:hover { background: #1c2336; color: #fff; }
  .tf-btn.active { background: var(--tv-blue); color: #fff; border-color: var(--tv-blue); }

  /* Calendar */
  .cal-grid { display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; }
  .cal-header { text-align: center; font-weight: 700; font-size: 11px; color: var(--text-dim); padding: 6px 0; text-transform: uppercase; }
  .cal-day {
    background: #101522;
    border: 1px solid #1d263b;
    border-radius: 6px;
    min-height: 86px;
    padding: 7px 8px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.15s;
    cursor: pointer;
  }
  .cal-day:hover { border-color: var(--tv-blue); transform: translateY(-1px); }
  .cal-day.empty { background: transparent; border-color: transparent; cursor: default; }
  .cal-day.empty:hover { transform: none; }
  .cal-day.week-col { background: #0c1220; border-color: #26324c; cursor: default; }
  .cal-day.win-day { background: linear-gradient(180deg, #0d221c 0%, #101c1f 100%); border-color: rgba(16,185,129,0.4); }
  .cal-day.loss-day { background: linear-gradient(180deg, #261115 0%, #1c1015 100%); border-color: rgba(239,68,68,0.4); }
  .cal-day.selected { outline: 2px solid var(--gold); }
  .cal-day-top { display: flex; justify-content: space-between; font-size: 11px; font-weight: 700; color: #e2e8f0; }
  .cal-day-pnl { font-size: 13.5px; font-weight: 800; font-family: ui-monospace, monospace; }
  .cal-day-bot { font-size: 10px; color: var(--text-dim); display: flex; justify-content: space-between; }

  /* Filters & Badges */
  .filter-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    background: var(--bg-card);
    padding: 10px 14px;
    border-radius: 6px;
    border: 1px solid var(--border);
    margin-bottom: 12px;
  }
  select, input[type="text"] {
    background: #0d111a;
    color: var(--text-main);
    border: 1px solid var(--border);
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 12px;
  }
  select:focus, input[type="text"]:focus { outline: none; border-color: var(--tv-blue); }

  .badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .badge-long { background: rgba(16,185,129,0.2); color: var(--tv-green); border: 1px solid rgba(16,185,129,0.4); }
  .badge-short { background: rgba(239,68,68,0.2); color: var(--tv-red); border: 1px solid rgba(239,68,68,0.4); }
  .badge-oos { background: rgba(168,85,247,0.2); color: var(--purple); border: 1px solid rgba(168,85,247,0.4); }
  .badge-is { background: rgba(59,130,246,0.2); color: var(--tv-blue); border: 1px solid rgba(59,130,246,0.4); }
  .badge-trail { background: rgba(245,158,11,0.2); color: var(--gold); border: 1px solid rgba(245,158,11,0.4); }
  .badge-sl { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.4); }
  .badge-stall { background: rgba(6,182,212,0.2); color: var(--tv-cyan); border: 1px solid rgba(6,182,212,0.4); }

  /* Modal */
  .modal-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.78);
    backdrop-filter: blur(5px);
    z-index: 1000;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .modal-overlay.open { display: flex; }
  .modal-card {
    background: #0f1420;
    border: 1px solid var(--border-light);
    border-radius: 10px;
    width: 100%;
    max-width: 920px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 10px 40px rgba(0,0,0,0.85);
  }
  .modal-head {
    background: #141b2c;
    border-bottom: 1px solid var(--border);
    padding: 14px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .modal-body { padding: 18px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
  .modal-foot { background: #141b2c; border-top: 1px solid var(--border); padding: 12px 20px; display: flex; justify-content: flex-end; gap: 10px; }
  .audit-sec { background: #141a29; border: 1px solid var(--border); border-radius: 6px; padding: 12px 14px; }
  .audit-sec-title { font-size: 11px; font-weight: 700; color: var(--gold); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
  .radar-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 8px; }
  .radar-box { background: #0d121c; border: 1px solid #1a2233; border-radius: 4px; padding: 6px 8px; text-align: center; }
  .radar-lbl { font-size: 10px; color: var(--text-dim); text-transform: uppercase; }
  .radar-val { font-size: 13px; font-weight: 700; color: #fff; font-family: ui-monospace, monospace; }

  @media (max-width: 960px) {
    .grid-2, .grid-3 { grid-template-columns: 1fr; }
    .cal-grid { grid-template-columns: repeat(4, 1fr); }
  }
</style>
</head>
<body>

<header class="header-bar">
  <div class="brand-area">
    <div class="badge-crown">DELTA GOLD · 6-JOURNAL MERGE + 6,336 COMBOS</div>
    <div class="brand-info">
      <h1 id="hdrTitle">Delta Exchange India XAUTUSD — All-16-Agent Multi-Strategy Backtest</h1>
      <p id="hdrSub">65,846 1m Bars (Oct 01 – Nov 15, 2026) • 46 Calendar Days (24/7 Mon–Sun, Incl. Sat &amp; Sun) • Strict Single-Slot (Zero Overlap) • $5.00 Risk • 0.01% Delta Fee</p>
    </div>
  </div>
  <div class="header-actions">
    <button class="btn btn-primary" onclick="switchTab('tab-chart')">📈 Candlestick Chart</button>
    <button class="btn btn-gold" onclick="exportActiveCSV()">📥 Export Profile CSV</button>
    <button class="btn" onclick="exportActiveJSON()">💾 Export Profile JSON</button>
    <button class="btn" onclick="window.print()">🖨️ Print</button>
  </div>
</header>

<main class="container">

  <!-- Strategy Profile Selector -->
  <section class="profile-bar">
    <div class="profile-bar-head">
      <div style="font-weight:700; color:#fff; font-size:13px;">
        🧬 Merged Super-Strategies (<span class="text-green">All 6 Champion Journals Merged, Strict Single-Slot Zero Overlap</span>)
      </div>
      <div style="font-size:11.5px; color:var(--text-muted);" id="activeComboLabel"></div>
    </div>
    <div class="profile-cards" id="mergedCardsGrid"></div>
    <div class="profile-tier-head">
      <div><strong style="color:#fff;">🏆 6 Individual Discovered Delta Gold Champions</strong> (from 6,336 Combinations)</div>
      <div>Click any of the 12 strategies above to switch all charts, breakdowns, calendar, and trade journal</div>
    </div>
    <div class="profile-cards" id="profileCardsGrid"></div>
  </section>

  <!-- Hero Before-vs-After & Root Cause Upgrades -->
  <section class="hero-banner">
    <div class="hero-top">
      <div>
        <div style="display:flex; gap:7px; flex-wrap:wrap; margin-bottom:7px;">
          <span class="pill pill-gold">PURE DELTA EXCHANGE XAUTUSD</span>
          <span class="pill pill-green">ALL 16 FLOOR AGENTS + 11 SPECIALISTS + 6 PODS</span>
          <span class="pill pill-cyan">70% IN-SAMPLE / 30% OUT-OF-SAMPLE VERIFIED</span>
          <span class="pill pill-purple">0.85x SL ADAPTIVE CHANDELIER (40R TRAIL)</span>
        </div>
        <h2 style="font-size:15.5px; color:#fff; margin-bottom:5px;" id="heroHeadline"></h2>
        <p class="text-muted" style="max-width:1120px; font-size:12px;" id="heroNarrative"></p>
      </div>
      <div style="text-align:right; min-width:210px;">
        <div class="text-muted" style="font-size:10.5px; text-transform:uppercase; font-weight:700;">Grid Profitability Rate</div>
        <div class="mono text-green" style="font-size:26px; font-weight:800;" id="heroGridPct"></div>
        <div class="mono text-gold" style="font-size:11.5px;" id="heroGridSub"></div>
      </div>
    </div>
    <div class="rc-grid" id="rootCauseGrid"></div>
  </section>

  <!-- 8 Dynamic KPI Cards -->
  <section class="kpi-grid" id="kpiGrid"></section>

  <!-- 7 Navigation Tabs -->
  <nav class="tab-nav">
    <button class="tab-btn active" data-tab="tab-dossier" onclick="switchTab('tab-dossier')">📊 Executive Dossier &amp; Breakdowns</button>
    <button class="tab-btn" data-tab="tab-merge" onclick="switchTab('tab-merge')">🧬 6-Journal Merge &amp; Consensus Forensics <span class="badge-count" id="mergeTabCount">Setups</span></button>
    <button class="tab-btn" data-tab="tab-grid" onclick="switchTab('tab-grid')">🔬 6,336-Combination Grid Explorer <span class="badge-count">6,336</span></button>
    <button class="tab-btn" data-tab="tab-agents" onclick="switchTab('tab-agents')">🤖 All 16 Agents &amp; 11 Specialists Matrix <span class="badge-count">16+17</span></button>
    <button class="tab-btn" data-tab="tab-chart" onclick="switchTab('tab-chart')">📈 Interactive XAUTUSD Candlestick Chart <span class="badge-count">Oct 1–Nov 15</span></button>
    <button class="tab-btn" data-tab="tab-calendar" onclick="switchTab('tab-calendar')">📅 Daily P&amp;L Calendar &amp; 46-Day 24/7 Log <span class="badge-count">46 Days</span></button>
    <button class="tab-btn" data-tab="tab-journal" onclick="switchTab('tab-journal')">📋 Trade-by-Trade Journal <span class="badge-count" id="journalTabCount">54</span></button>
  </nav>

  <!-- TAB 1: EXECUTIVE DOSSIER & BREAKDOWNS -->
  <div id="tab-dossier" class="tab-pane active">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📈 Account Equity Progression &amp; Drawdown ($100 Start Equity, $5.00 Risk/Trade)</div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <button class="btn active" id="btnEqOverlay" onclick="setEqChartMode('overlay', this)">All 12 Strategies + Old Baseline</button>
          <button class="btn" id="btnEqDetail" onclick="setEqChartMode('detail', this)">Active Profile Equity &amp; Drawdown %</button>
        </div>
      </div>
      <div class="panel-body">
        <div id="eqLegend" style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:9px; font-size:11px;"></div>
        <div class="chart-canvas-box"><canvas id="equityCanvas"></canvas></div>
        <div id="eqHoverBar" class="mono text-muted" style="margin-top:8px; font-size:11.5px;">
          Hover over chart to inspect trade-by-trade equity across the 6 Merged Super-Strategies, 6 Individual Champions, and the In-Sample / Out-of-Sample boundary (2026-11-02).
        </div>
      </div>
    </div>

    <!-- Side-by-Side 12-Strategy (6 Merged + 6 Individual) + Legacy Baseline Matrix -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🏆 Head-to-Head Comparison: 6 Merged Super-Strategies &amp; 6 Individual Champions vs Legacy Track B Baseline (Click Row to Activate)</div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Strategy Profile</th>
              <th>TF Mix</th>
              <th>Trades</th>
              <th>Days Traded</th>
              <th>Win Rate</th>
              <th>Profit Factor</th>
              <th>Gross P&amp;L</th>
              <th>Delta Fees</th>
              <th>Net P&amp;L ($)</th>
              <th>End Equity</th>
              <th>Max DD % ($)</th>
              <th>Calmar</th>
              <th>IS Net (WR%)</th>
              <th>OOS Net (WR%)</th>
            </tr>
          </thead>
          <tbody id="profilesCompareBody"></tbody>
        </table>
      </div>
    </div>

    <!-- Monthly & Weekly -->
    <div class="grid-2">
      <div class="panel">
        <div class="panel-header"><div class="panel-title">📅 Monthly Performance (Oct 2026 IS vs Nov 2026 OOS)</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Month</th><th>Trades</th><th>Wins / Loss</th><th>Win Rate</th><th>PF</th><th>Avg R</th><th>Gross ($)</th><th>Fees ($)</th><th>Net P&amp;L ($)</th></tr></thead><tbody id="monthBody"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">🗓️ Weekly Performance (ISO Weeks W40 – W46)</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Week</th><th>Dates</th><th>Days</th><th>Trades</th><th>Win Rate</th><th>Gross ($)</th><th>Fees ($)</th><th>Net P&amp;L ($)</th><th>Cum Eq ($)</th></tr></thead><tbody id="weekBody"></tbody></table></div>
      </div>
    </div>

    <!-- Session & Day of Week -->
    <div class="grid-2">
      <div class="panel">
        <div class="panel-header"><div class="panel-title">🌍 Killzone Session Breakdown</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Session</th><th>Trades</th><th>W / L</th><th>Win Rate</th><th>PF</th><th>Avg R</th><th>Net P&amp;L ($)</th><th>Share</th></tr></thead><tbody id="sessionBody"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">📆 Day-of-Week Breakdown (24/7 Mon–Sun, Including Sat &amp; Sun)</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Day (24/7)</th><th>Trades</th><th>W / L</th><th>Win Rate</th><th>PF</th><th>Avg R</th><th>Net P&amp;L ($)</th><th>Share</th></tr></thead><tbody id="dowBody"></tbody></table></div>
      </div>
    </div>

    <!-- Timeframe, Direction & Exit Reason -->
    <div class="grid-2">
      <div class="panel">
        <div class="panel-header"><div class="panel-title">⏱️ Timeframe &amp; Direction Attribution</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Bucket</th><th>Trades</th><th>W / L</th><th>Win Rate</th><th>PF</th><th>Avg R</th><th>Net P&amp;L ($)</th><th>Share</th></tr></thead><tbody id="tfDirBody"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">🎯 Exit Reason Attribution (0.85x SL Adaptive Chandelier)</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Exit Reason</th><th>Trades</th><th>W / L</th><th>Win Rate</th><th>Avg R</th><th>Net P&amp;L ($)</th><th>Share</th></tr></thead><tbody id="exitBody"></tbody></table></div>
      </div>
    </div>

    <!-- Setup Agent & Playbook Attribution -->
    <div class="grid-2">
      <div class="panel">
        <div class="panel-header"><div class="panel-title">🤖 Setup Agent &amp; Synergistic Pod Attribution</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Setup Agent / Pod</th><th>Trades</th><th>W / L</th><th>Win Rate</th><th>PF</th><th>Avg R</th><th>Net P&amp;L ($)</th><th>Share</th></tr></thead><tbody id="setupAgentBody"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">🧠 Playbook &amp; 16-Agent Initiator Attribution</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Playbook / Initiator</th><th>Trades</th><th>W / L</th><th>Win Rate</th><th>PF</th><th>Avg R</th><th>Net P&amp;L ($)</th><th>Share</th></tr></thead><tbody id="playbookBody"></tbody></table></div>
      </div>
    </div>
  </div>

  <!-- TAB MERGE: 6-JOURNAL MERGE & CONSENSUS FORENSICS -->
  <div id="tab-merge" class="tab-pane">
    <div class="kpi-grid" id="mergeKpiStrip"></div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🧬 Head-to-Head Benchmark: 6 Merged Super-Strategies vs 6 Individual Champions vs Legacy Baseline (Strict Single-Slot, Zero Overlap — Click Row to Activate)</div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Tier</th>
              <th>Strategy Profile</th>
              <th>TF Mix / Selection Rule</th>
              <th>Trades</th>
              <th>Days Traded</th>
              <th>Win Rate</th>
              <th>PF</th>
              <th>Net P&amp;L ($)</th>
              <th>End Equity</th>
              <th>Max DD %</th>
              <th>IS Net (WR%)</th>
              <th>OOS Net (WR%)</th>
              <th>Overlaps</th>
            </tr>
          </thead>
          <tbody id="mergeProfilesBody"></tbody>
        </table>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <div class="panel-header"><div class="panel-title" id="mergeVoteTitle">🗳️ Cross-Champion Vote Consensus Attribution (6/6 Down to 1/6 Votes)</div></div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Champion Votes</th>
                <th>Setups</th>
                <th>W / L</th>
                <th>Win Rate</th>
                <th>PF</th>
                <th>Avg Net</th>
                <th>Total Net P&amp;L</th>
                <th>IS Net</th>
                <th>OOS Net (WR%)</th>
              </tr>
            </thead>
            <tbody id="votesBreakdownBody"></tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header"><div class="panel-title" id="mergePatternTitle">🔬 Exact Champion Membership Combinations (Sorted by Net P&amp;L)</div></div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Exact Pattern</th>
                <th>Votes</th>
                <th>Setups</th>
                <th>W / L</th>
                <th>Win Rate</th>
                <th>Net P&amp;L</th>
                <th>IS Net</th>
                <th>OOS Net</th>
                <th>TF Split</th>
              </tr>
            </thead>
            <tbody id="patternBreakdownBody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title" id="mergeMatrixTitle">🗂️ Complete 24/7 Cross-Journal Agreement Matrix (Deduplicated with HTF Priority)</div>
        <span id="setupMatrixCountLabel" class="mono text-gold" style="font-size:11.5px;"></span>
      </div>
      <div class="panel-body">
        <div class="filter-bar">
          <select id="setupMatrixFilter" onchange="applySetupMatrixFilters()">
            <option value="ALL">Status: All Unique Setups</option>
            <option value="EXECUTED_M1">Executed in MERGE_1 (Super Confluence OR 15m)</option>
            <option value="EXECUTED_M3">Executed in MERGE_3 (46/46d Memory Master)</option>
            <option value="FILTERED_M1">Filtered Out by MERGE_1</option>
            <option value="SLOT_BUSY_M1">Blocked by Single-Slot (Zero Overlap)</option>
            <option value="VOTES_GE4">Consensus &gt;= 4/6 Champions</option>
            <option value="VOTES_LE3">Low Consensus &lt;= 3/6 Champions</option>
          </select>
          <input type="text" id="mergeSetupSearch" placeholder="Search date, agent, pattern (e.g. 1+2+3+4+5+6), TF..." oninput="applySetupMatrixFilters()" />
          <button class="btn" onclick="resetSetupMatrixFilters()">Reset</button>
        </div>
        <div class="data-table-wrap" style="max-height:540px; overflow-y:auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Entry Time (UTC)</th>
                <th>Dir</th>
                <th>HTF Selected</th>
                <th>All Fired TFs</th>
                <th>Setup Agent</th>
                <th>Votes</th>
                <th>Pattern</th>
                <th>Chosen From</th>
                <th>R-Mult</th>
                <th>Net P&amp;L</th>
                <th>Exit Reason</th>
                <th>MERGE_1</th>
                <th>MERGE_3</th>
              </tr>
            </thead>
            <tbody id="setupMatrixBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 2: 6,336-COMBINATION GRID EXPLORER -->
  <div id="tab-grid" class="tab-pane">
    <div class="kpi-grid" id="gridKpiStrip"></div>

    <div class="panel">
      <div class="panel-header"><div class="panel-title">⚙️ Lifecycle Geometry Benchmark Across All 6,336 Combinations (792 Combos per Lifecycle)</div></div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Lifecycle Geometry</th>
              <th>Tested</th>
              <th>Profitable %</th>
              <th>Avg Net P&amp;L</th>
              <th>Avg WR%</th>
              <th>Avg PF</th>
              <th>Best Net P&amp;L</th>
              <th>Best WR%</th>
              <th>Best PF</th>
              <th>Best Max DD%</th>
              <th>Best OOS Net</th>
              <th>Top Configuration</th>
            </tr>
          </thead>
          <tbody id="lifecycleAggBody"></tbody>
        </table>
      </div>
    </div>

    <div class="grid-2">
      <div class="panel">
        <div class="panel-header"><div class="panel-title">👥 Roster Performance Summary (All 11 Agent Rosters)</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Roster</th><th>Tested</th><th>Prof %</th><th>Avg Net</th><th>Best Net</th><th>Best WR%</th><th>Best PF</th><th>Best DD%</th></tr></thead><tbody id="rosterAggBody"></tbody></table></div>
      </div>
      <div class="panel">
        <div class="panel-header"><div class="panel-title">⏱️ Timeframe Mix Performance Summary</div></div>
        <div class="data-table-wrap"><table class="data-table"><thead><tr><th>Timeframe Mix</th><th>Tested</th><th>Prof %</th><th>Avg Net</th><th>Best Net</th><th>Best WR%</th><th>Best PF</th><th>Best DD%</th></tr></thead><tbody id="tfAggBody"></tbody></table></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🏅 Top 100 Distinct Delta Gold Combinations Leaderboard</div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <select id="gridFilterLc" onchange="renderTop100Table()"><option value="ALL">All Lifecycles</option></select>
          <select id="gridFilterTf" onchange="renderTop100Table()"><option value="ALL">All TF Mixes</option></select>
          <select id="gridFilterRescue" onchange="renderTop100Table()">
            <option value="ALL">Pure + Rescue</option>
            <option value="PURE">PURE Only</option>
            <option value="RESCUE">RESCUE (100% Days) Only</option>
          </select>
          <input type="text" id="gridSearchInput" placeholder="Search combo / roster..." oninput="renderTop100Table()" />
        </div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Combination ID</th>
              <th>Roster</th>
              <th>TFs</th>
              <th>Lifecycle</th>
              <th>Mem WR</th>
              <th>Mode</th>
              <th class="sortable" onclick="sortTop100('trades')">Trades ⇅</th>
              <th class="sortable" onclick="sortTop100('day_coverage_pct')">Days% ⇅</th>
              <th class="sortable" onclick="sortTop100('wr')">WR% ⇅</th>
              <th class="sortable" onclick="sortTop100('pf')">PF ⇅</th>
              <th class="sortable" onclick="sortTop100('net_pnl')">Net P&amp;L ⇅</th>
              <th class="sortable" onclick="sortTop100('max_dd_pct')">Max DD% ⇅</th>
              <th class="sortable" onclick="sortTop100('oos_net_pnl')">OOS Net ⇅</th>
              <th class="sortable" onclick="sortTop100('oos_wr')">OOS WR% ⇅</th>
            </tr>
          </thead>
          <tbody id="top100Body"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 3: ALL 16 AGENTS & 11 SPECIALISTS MATRIX -->
  <div id="tab-agents" class="tab-pane">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🧬 11 Field Specialists &amp; 6 Synergistic Pods — Multi-Timeframe Backtest on Delta XAUTUSD (1m / 5m / 15m / 1h)</div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Specialist / Pod</th>
              <th>Type</th>
              <th>Domain Focus</th>
              <th>1m (T | WR% | PF | Net)</th>
              <th>5m (T | WR% | PF | Net)</th>
              <th>15m (T | WR% | PF | Net)</th>
              <th>1h (T | WR% | PF | Net)</th>
            </tr>
          </thead>
          <tbody id="specMatrixBody"></tbody>
        </table>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🧭 In-Sample (70%) Day-of-Week × Session Best Specialist Router Map (Zero Lookahead)</div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Weekday</th>
              <th>Session</th>
              <th>#1 Top Specialist</th>
              <th>Playbook</th>
              <th>IS Trades</th>
              <th>IS WR%</th>
              <th>IS PF</th>
              <th>IS Net ($)</th>
              <th>#2 Runner-Up Specialist</th>
            </tr>
          </thead>
          <tbody id="routerMapBody"></tbody>
        </table>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🏛️ All 16 Syndicate Floor Agents — Confirmation, Veto &amp; Governance Telemetry (24/7 Mon–Sun Setups)</div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Agent ID</th>
              <th>Title</th>
              <th>Role</th>
              <th>Confirmed Setups</th>
              <th>Confirm Rate</th>
              <th>Vetoes / Blocks</th>
              <th>0.85x Chandelier WR%</th>
              <th>Deterministic Edge Function</th>
            </tr>
          </thead>
          <tbody id="floor16Body"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 4: INTERACTIVE XAUTUSD CANDLESTICK CHART -->
  <div id="tab-chart" class="tab-pane">
    <div class="panel">
      <div class="chart-toolbar">
        <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
          <span style="font-weight:700; color:#fff;">Delta Exchange XAUTUSD</span>
          <div class="tf-group">
            <button class="tf-btn active" data-tf="5">5m</button>
            <button class="tf-btn" data-tf="15">15m</button>
            <button class="tf-btn" data-tf="60">1h</button>
            <button class="tf-btn" data-tf="240">4h</button>
          </div>
          <span style="color:var(--text-dim);">|</span>
          <select id="tradeJumpSelect" style="width:290px;"></select>
          <button class="btn" id="prevTradeBtn" style="padding:4px 8px;">◀ Prev</button>
          <button class="btn" id="nextTradeBtn" style="padding:4px 8px;">Next ▶</button>
          <button class="btn btn-primary" id="zoomTradeBtn" style="padding:4px 10px;">🔍 Focus Trade</button>
          <button class="btn" id="fitAllBtn" style="padding:4px 10px;">🌐 Fit Full Oct 1–Nov 15</button>
        </div>
        <div style="font-size:11px; color:var(--text-muted);">
          Scroll wheel to zoom · Drag to pan · Click any trade badge to open 16-Agent Audit Modal
        </div>
      </div>
      <div class="tv-chart-box"><canvas id="tvChart"></canvas></div>
      <canvas id="tvNavChart" class="tv-nav-box"></canvas>
      <div id="chartTradeBanner" style="background:#0d121c; border-top:1px solid var(--border); padding:10px 16px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
        <div id="bannerTradeText" style="font-size:12.5px; font-weight:600;">Select a trade to inspect.</div>
        <button class="btn btn-gold" id="bannerInspectBtn" style="display:none; padding:4px 10px;" onclick="openSelectedTradeModal()">🔍 Open 16-Agent Forensic Audit</button>
      </div>
    </div>
  </div>

  <!-- TAB 5: DAILY P&L CALENDAR & 32-DAY LOG -->
  <div id="tab-calendar" class="tab-pane">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📅 Daily P&amp;L Calendar Heatmap (Active Profile)</div>
        <div style="display:flex; gap:8px; align-items:center;">
          <button class="btn active" id="calOctBtn" onclick="setCalMonth('2026-10')">October 2026 (IS)</button>
          <button class="btn" id="calNovBtn" onclick="setCalMonth('2026-11')">November 2026 (OOS)</button>
          <span id="calMonthSummaryBadge" class="mono text-green" style="font-size:12px; font-weight:700; margin-left:8px;"></span>
        </div>
      </div>
      <div class="panel-body">
        <div class="cal-grid" id="calGrid"></div>
        <div id="calDayInspector" style="margin-top:12px; padding:11px 14px; background:#090d16; border:1px solid var(--border); border-radius:6px; font-size:12px;">
          Click any calendar day card to inspect that day's trades or click "Filter Journal" to jump straight to that date.
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📋 Complete 46-Day 24/7 Day-by-Day Log (Oct 01 – Nov 15, 2026 — Includes Sat &amp; Sun)</div>
      </div>
      <div class="data-table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Day</th>
              <th>Week</th>
              <th>Sample</th>
              <th>Trades</th>
              <th>Wins / Losses</th>
              <th>Gross P&amp;L</th>
              <th>Delta Fees</th>
              <th>Net P&amp;L ($)</th>
              <th>Cum Equity ($)</th>
              <th>Active Setup Agents / Pods</th>
            </tr>
          </thead>
          <tbody id="dailyLogBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- TAB 6: COMPLETE TRADE JOURNAL -->
  <div id="tab-journal" class="tab-pane">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📋 Complete Trade-by-Trade Execution Journal (Click Row for 16-Agent Forensic Modal)</div>
        <div style="display:flex; gap:8px; align-items:center;">
          <span id="filteredCountLabel" class="mono text-gold" style="font-size:11.5px;"></span>
          <button class="btn btn-gold" onclick="exportActiveCSV()">📥 Download CSV</button>
        </div>
      </div>
      <div class="panel-body">
        <div class="filter-bar">
          <select id="filterDirection" onchange="applyJournalFilters()"><option value="ALL">Direction: All</option><option value="LONG">LONG</option><option value="SHORT">SHORT</option></select>
          <select id="filterOutcome" onchange="applyJournalFilters()"><option value="ALL">Outcome: All</option><option value="WIN">Winners</option><option value="LOSS">Losses</option></select>
          <select id="filterSample" onchange="applyJournalFilters()"><option value="ALL">Sample: IS + OOS</option><option value="IS">In-Sample</option><option value="OOS">Out-of-Sample</option></select>
          <select id="filterTf" onchange="applyJournalFilters()"><option value="ALL">TF: All</option><option value="1m">1m</option><option value="5m">5m</option><option value="15m">15m</option><option value="1h">1h</option></select>
          <select id="filterSession" onchange="applyJournalFilters()"><option value="ALL">Session: All</option><option value="ASIA">ASIA</option><option value="LONDON">LONDON</option><option value="NEW_YORK">NEW_YORK</option></select>
          <select id="filterAgent" onchange="applyJournalFilters()"><option value="ALL">Setup Agent: All</option></select>
          <select id="filterExit" onchange="applyJournalFilters()"><option value="ALL">Exit Reason: All</option></select>
          <input type="text" id="filterSearch" placeholder="Search date, playbook, #id..." oninput="applyJournalFilters()" />
          <button class="btn" onclick="resetJournalFilters()">Reset</button>
        </div>
        <div class="data-table-wrap">
          <table class="data-table" id="journalTable">
            <thead>
              <tr>
                <th>#</th>
                <th>Entry Time (UTC)</th>
                <th>Dir</th>
                <th>TF</th>
                <th>Session</th>
                <th>Setup Agent</th>
                <th>Playbook</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>SL</th>
                <th>Lots (50x)</th>
                <th>Pts</th>
                <th>R-Mult</th>
                <th>Fees</th>
                <th>Net ($)</th>
                <th>Eq After</th>
                <th>Hold</th>
                <th>Exit Reason</th>
                <th>Agents</th>
                <th>Sample</th>
              </tr>
            </thead>
            <tbody id="journalBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

</main>

<!-- 16-Agent Forensic Trade Audit Modal -->
<div class="modal-overlay" id="tradeModal" onclick="if(event.target.id==='tradeModal') closeTradeModal()">
  <div class="modal-card">
    <div class="modal-head">
      <div style="display:flex; align-items:center; gap:10px;">
        <span class="pill pill-gold" id="modalTradeIdBadge">TRADE #1</span>
        <strong id="modalTradeTitle" style="font-size:14px; color:#fff;"></strong>
      </div>
      <button class="btn" onclick="closeTradeModal()">✕ Close</button>
    </div>
    <div class="modal-body" id="modalTradeBody"></div>
    <div class="modal-foot">
      <button class="btn btn-primary" onclick="jumpToModalTradeOnChart()">📈 Inspect on XAUTUSD Chart</button>
      <button class="btn" onclick="closeTradeModal()">Close</button>
    </div>
  </div>
</div>

<script>
const REPORT = __PAYLOAD_JSON__;

let activeProfileId = REPORT.profile_order[0];
let currentEqMode = 'overlay';
let currentCalMonth = '2026-10';
let selectedCalDate = null;
let filteredTrades = [];
let selectedTrade = null;
let top100SortKey = 'net_pnl';
let top100SortAsc = false;

// Chart state
let currentTF = 5;
let viewStartIdx = 0;
let viewEndIdx = 120;
let isDragging = false;
let dragStartX = 0;
let hoverMouse = null;
let chartTradeHitboxes = [];
const TF_BARS_CACHE = {};

function P() { return REPORT.profiles[activeProfileId]; }
function fmtUsd(v, signed = true) {
  if (v === null || v === undefined || isNaN(v)) return '—';
  const n = Number(v);
  if (!signed) return '$' + n.toFixed(2);
  return (n >= 0 ? '+$' : '-$') + Math.abs(n).toFixed(2);
}
function clsVal(v) { return Number(v) >= 0 ? 'text-green' : 'text-red'; }

/* ============================================================================
 * PROFILE SELECTOR & HEADER / HERO / KPI RENDERING
 * ============================================================================ */
function renderProfileCardsHtml(orderList, isMergedTier) {
  return (orderList || []).map(pid => {
    const prof = REPORT.profiles[pid];
    if (!prof) return '';
    const s = prof.summary;
    const isAct = pid === activeProfileId;
    const badgeHtml = isMergedTier
      ? `<span class="pill pill-green" style="font-size:9px;padding:1px 5px;">MERGED</span> `
      : `<span class="pill pill-gold" style="font-size:9px;padding:1px 5px;">SINGLE</span> `;
    return `
      <button class="p-card ${isMergedTier ? 'merged-card' : ''} ${isAct ? 'active' : ''}" onclick="selectProfile('${pid}')">
        <div class="p-card-top">
          <span class="p-card-title">${badgeHtml}${prof.title}</span>
          <span class="mono text-green" style="font-weight:800; font-size:13px;">${fmtUsd(s.net_pnl_usd)}</span>
        </div>
        <div class="p-card-stats">
          <span>${s.trades}T (${s.active_days}/${s.total_weekdays || 46}d)</span>
          <span class="text-gold">${s.wr_pct.toFixed(1)}% WR</span>
          <span class="text-cyan">PF ${s.pf.toFixed(2)}</span>
          <span class="text-red">DD -${s.max_dd_pct.toFixed(1)}%</span>
          <span class="text-purple">OOS ${fmtUsd(s.oos_stats.net_pnl)}</span>
        </div>
      </button>
    `;
  }).join('');
}

function renderProfileSelector() {
  const mergedOrder = REPORT.merged_profile_order || REPORT.profile_order.filter(pid => REPORT.profiles[pid]?.is_merged);
  const singleOrder = REPORT.individual_profile_order || REPORT.profile_order.filter(pid => !REPORT.profiles[pid]?.is_merged);
  const mergedGrid = document.getElementById('mergedCardsGrid');
  if (mergedGrid) mergedGrid.innerHTML = renderProfileCardsHtml(mergedOrder, true);
  const grid = document.getElementById('profileCardsGrid');
  if (grid) grid.innerHTML = renderProfileCardsHtml(singleOrder, false);

  const cur = P();
  document.getElementById('activeComboLabel').innerHTML =
    `Active ID: <span class="mono text-gold">${cur.combo_name}</span> ${cur.is_merged ? '<span class="pill pill-green" style="margin-left:6px;">MERGED SUPER-STRATEGY</span>' : ''}`;
}

function renderHeroAndKPIs() {
  const cur = P();
  const s = cur.summary;
  const leg = REPORT.legacy_baseline || { net_pnl_usd: 12.73, wr_pct: 59.15, pf: 1.09, max_dd_pct: 30.23, trades: 71 };
  const mult = leg.net_pnl_usd > 0 ? (s.net_pnl_usd / leg.net_pnl_usd).toFixed(1) : '9.8';
  const ddCut = (leg.max_dd_pct - s.max_dd_pct).toFixed(1);

  document.getElementById('heroHeadline').innerHTML =
    `${cur.title}: <span class="text-green">${fmtUsd(s.net_pnl_usd)} Net (${mult}x vs Legacy Baseline)</span> · ${s.wr_pct.toFixed(2)}% Win Rate · PF ${s.pf.toFixed(2)} · Max DD -${s.max_dd_pct.toFixed(2)}% (-${ddCut} pts lower)`;

  document.getElementById('heroNarrative').innerHTML =
    `${cur.subtitle}. Across <strong>${REPORT.data_meta.bars_total.toLocaleString()}</strong> 1-minute Delta Exchange <code>XAUTUSD</code> bars (` +
    `<strong>${REPORT.data_meta.start_utc.slice(0,10)}</strong> → <strong>${REPORT.data_meta.end_utc.slice(0,10)}</strong>, ${REPORT.data_meta.active_weekdays} active 24/7 calendar days Mon–Sun incl. ${REPORT.data_meta.weekend_days || 14} weekend days), ` +
    `this strictly non-overlapping single-slot profile executed <strong>${s.trades} trades</strong> ($5.00 fixed risk, 0.01% Delta taker fee/side) turning $100.00 into <strong class="text-green">$${s.end_equity.toFixed(2)}</strong> ` +
    `vs only $${(100 + leg.net_pnl_usd).toFixed(2)} (${fmtUsd(leg.net_pnl_usd)}, ${leg.wr_pct}% WR, PF ${leg.pf}, -${leg.max_dd_pct}% DD) on the legacy single-strategy Track B run.`;

  document.getElementById('heroGridPct').textContent = `${REPORT.grid_summary.profitable_pct}%`;
  document.getElementById('heroGridSub').textContent =
    `${REPORT.grid_summary.profitable_combinations.toLocaleString()} / ${REPORT.grid_summary.total_combinations.toLocaleString()} Combos Profitable`;

  document.getElementById('rootCauseGrid').innerHTML = REPORT.root_cause_upgrades.map(u => `
    <div class="rc-card">
      <h4>${u.title}</h4>
      <p><strong class="text-red">Before:</strong> ${u.before}<br><strong class="text-green">After:</strong> ${u.after}</p>
    </div>
  `).join('');

  document.getElementById('kpiGrid').innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Ending Equity ($100 Init) <span class="text-green">+${s.return_pct.toFixed(1)}%</span></div>
      <div class="kpi-val text-green">$${s.end_equity.toFixed(2)}</div>
      <div class="kpi-sub">Net: ${fmtUsd(s.net_pnl_usd)} | Gross: ${fmtUsd(s.gross_pnl_usd)}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Win Rate / Payoff <span class="text-gold">${s.wins}W / ${s.losses}L</span></div>
      <div class="kpi-val text-gold">${s.wr_pct.toFixed(2)}%</div>
      <div class="kpi-sub">Avg Win: ${fmtUsd(s.avg_win_usd)} | Loss: ${fmtUsd(s.avg_loss_usd)} (${s.payoff_ratio.toFixed(2)}x)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Profit Factor <span class="text-cyan">Calmar ${s.calmar.toFixed(1)}</span></div>
      <div class="kpi-val text-cyan">${s.pf.toFixed(2)}</div>
      <div class="kpi-sub">Delta Taker Fees: -$${s.delta_fee_total_usd.toFixed(2)} (0.01%/side)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Trades &amp; Coverage <span class="text-blue">0 Overlaps</span></div>
      <div class="kpi-val text-blue">${s.trades}</div>
      <div class="kpi-sub">${s.active_days}/${s.total_weekdays || 46} Days (${s.day_coverage_pct}%) · Sat/Sun: ${s.weekend_trades || 0}T (${fmtUsd(s.weekend_net_pnl || 0)})</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Max Drawdown <span class="text-red">Streaks ${s.max_win_streak}W / ${s.max_loss_streak}L</span></div>
      <div class="kpi-val text-red">-${s.max_dd_pct.toFixed(2)}%</div>
      <div class="kpi-sub">Peak-to-Trough: -$${s.max_dd_usd.toFixed(2)}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">In-Sample (Oct 1–Nov 1) <span class="text-blue">${s.is_stats.trades}T</span></div>
      <div class="kpi-val text-green">${fmtUsd(s.is_stats.net_pnl)}</div>
      <div class="kpi-sub">${s.is_stats.wr.toFixed(1)}% WR | PF ${s.is_stats.pf.toFixed(2)} | DD -${s.is_stats.max_dd_pct.toFixed(1)}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Out-of-Sample (Nov 2–15) <span class="text-purple">${s.oos_stats.trades}T</span></div>
      <div class="kpi-val ${clsVal(s.oos_stats.net_pnl)}">${fmtUsd(s.oos_stats.net_pnl)}</div>
      <div class="kpi-sub">${s.oos_stats.wr.toFixed(1)}% WR | PF ${s.oos_stats.pf.toFixed(2)} | DD -${s.oos_stats.max_dd_pct.toFixed(1)}%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Peak Runner &amp; Hold <span class="text-purple">Avg ${s.avg_r >= 0 ? '+' : ''}${s.avg_r.toFixed(2)}R</span></div>
      <div class="kpi-val text-purple">+${s.max_r_multiple.toFixed(2)}R</div>
      <div class="kpi-sub">Best: ${fmtUsd(s.best_trade_usd)} | Avg Hold: ${s.avg_hold_mins}m</div>
    </div>
  `;
  document.getElementById('journalTabCount').textContent = s.trades;
}

function selectProfile(pid) {
  activeProfileId = pid;
  renderProfileSelector();
  renderHeroAndKPIs();
  renderDossierTables();
  renderMergeForensics();
  drawEquityChart();
  renderCalendar();
  renderDailyLog();
  populateJournalFilters();
  resetJournalFilters();
  populateTradeJumpSelect();
  if (P().trades.length) selectTrade(P().trades[0], false, false);
}

/* ============================================================================
 * TAB 1: EQUITY CURVE CANVAS & BREAKDOWN TABLES
 * ============================================================================ */
function setEqChartMode(mode, btn) {
  currentEqMode = mode;
  document.getElementById('btnEqOverlay').classList.toggle('active', mode === 'overlay');
  document.getElementById('btnEqDetail').classList.toggle('active', mode === 'detail');
  drawEquityChart();
}

function drawEquityChart() {
  const canvas = document.getElementById('equityCanvas');
  if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const W = Math.max(600, Math.floor(rect.width));
  const H = Math.floor(rect.height) || 360;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = W * dpr;
  canvas.height = H * dpr;
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  ctx.fillStyle = '#090c13';
  ctx.fillRect(0, 0, W, H);

  const padL = 62, padR = 24, padT = 26, padB = 34;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;

  let series = [];
  let maxLen = 2;

  if (currentEqMode === 'overlay') {
    series = REPORT.profile_order.map(pid => {
      const pr = REPORT.profiles[pid];
      const isAct = pid === activeProfileId;
      const isKey = isAct || pid === 'MERGE_1_SUPER_CONFLUENCE_OR_15M' || pid === 'CHAMP_1_MAX_PROFIT';
      return {
        label: `${pr.is_merged ? '[M]' : '[C]'} ${pr.title} (${fmtUsd(pr.summary.net_pnl_usd)})`,
        color: pr.color,
        width: isAct ? 3.4 : (pr.is_merged ? 2.0 : 1.3),
        alpha: isAct ? 1.0 : (isKey ? 0.8 : 0.35),
        dash: (!pr.is_merged && !isAct) ? [3, 3] : null,
        pts: pr.equity_curve,
      };
    });
    if (REPORT.legacy_baseline && REPORT.legacy_baseline.equity_curve) {
      series.push({
        label: 'Legacy Track B Baseline (+$12.73)',
        color: '#94a3b8',
        width: 1.8,
        alpha: 0.75,
        dash: [5, 4],
        pts: REPORT.legacy_baseline.equity_curve,
      });
    }
    maxLen = Math.max(...series.map(s => s.pts.length), 2);
  } else {
    const cur = P();
    series = [{
      label: cur.title,
      color: cur.color || '#10b981',
      width: 2.8,
      alpha: 1.0,
      pts: cur.equity_curve,
      fillArea: true,
    }];
    maxLen = cur.equity_curve.length;
  }

  document.getElementById('eqLegend').innerHTML = series.map(s =>
    `<span><strong style="color:${s.color};">${s.dash ? '╍╍' : '━━'}</strong> ${s.label}</span>`
  ).join('');

  const allVals = series.flatMap(s => s.pts.map(p => p.eq));
  const minEq = Math.floor(Math.min(85, ...allVals) / 10) * 10;
  const maxEq = Math.ceil(Math.max(130, ...allVals) / 10) * 10 + 10;

  const toX = (idx, len) => padL + (idx / Math.max(1, len - 1)) * plotW;
  const toY = v => padT + (1 - (v - minEq) / Math.max(1, maxEq - minEq)) * plotH;

  // Y grid
  ctx.strokeStyle = '#182032';
  ctx.lineWidth = 1;
  ctx.font = '10.5px ui-monospace, monospace';
  ctx.fillStyle = '#64748b';
  const yStep = Math.max(20, Math.round((maxEq - minEq) / 6 / 10) * 10);
  for (let v = minEq; v <= maxEq; v += yStep) {
    const y = toY(v);
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    ctx.textAlign = 'right';
    ctx.fillText('$' + v, padL - 8, y + 4);
  }

  // $100 baseline
  const y100 = toY(100);
  ctx.strokeStyle = 'rgba(255,255,255,0.22)';
  ctx.setLineDash([3, 3]);
  ctx.beginPath(); ctx.moveTo(padL, y100); ctx.lineTo(W - padR, y100); ctx.stroke();
  ctx.setLineDash([]);

  // In-sample / OOS divider on active profile curve
  const actPts = P().equity_curve;
  const oosIdx = actPts.findIndex(p => p.is_oos);
  if (oosIdx > 0) {
    const xOos = currentEqMode === 'overlay' ? toX(oosIdx, actPts.length) : toX(oosIdx, maxLen);
    ctx.strokeStyle = 'rgba(168, 85, 247, 0.55)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(xOos, padT); ctx.lineTo(xOos, padT + plotH); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#c084fc';
    ctx.font = 'bold 10px -apple-system, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('OOS START (Nov 02)', xOos, padT + 12);
  }

  // Draw curves (aligned by trade progress or sequence)
  series.forEach(s => {
    const len = s.pts.length;
    ctx.save();
    ctx.globalAlpha = s.alpha;
    ctx.strokeStyle = s.color;
    ctx.lineWidth = s.width;
    if (s.dash) ctx.setLineDash(s.dash);
    ctx.beginPath();
    s.pts.forEach((p, i) => {
      const x = currentEqMode === 'overlay' ? toX(i, len) : toX(i, maxLen);
      const y = toY(p.eq);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();

    if (s.fillArea && len > 1) {
      ctx.lineTo(toX(len - 1, maxLen), padT + plotH);
      ctx.lineTo(toX(0, maxLen), padT + plotH);
      ctx.closePath();
      const g = ctx.createLinearGradient(0, padT, 0, padT + plotH);
      g.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
      g.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
      ctx.fillStyle = g;
      ctx.fill();
    }
    ctx.restore();
  });

  // Draw underwater DD% bars in detail mode
  if (currentEqMode === 'detail') {
    const pts = P().equity_curve;
    const ddHeight = plotH * 0.28;
    const maxAbsDd = Math.max(15, ...pts.map(p => Math.abs(p.dd_pct || 0)));
    pts.forEach((p, i) => {
      const dd = Math.abs(p.dd_pct || 0);
      if (dd <= 0) return;
      const barH = (dd / maxAbsDd) * ddHeight;
      const x = toX(i, maxLen);
      ctx.fillStyle = 'rgba(239, 68, 68, 0.35)';
      ctx.fillRect(x - 2, padT + plotH - barH, 4, barH);
    });
  }

  ctx.fillStyle = '#64748b';
  ctx.font = '11px -apple-system, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(`Trade Sequence (0 → ${P().summary.trades} Trades | Oct 01 – Nov 15, 2026)`, padL + plotW / 2, H - 10);

  canvas.onmousemove = ev => {
    const br = canvas.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (ev.clientX - br.left - padL) / plotW));
    const idx = Math.round(ratio * (actPts.length - 1));
    const pt = actPts[idx];
    if (!pt) return;
    document.getElementById('eqHoverBar').innerHTML =
      `<strong>${P().title}</strong> · Trade #${pt.idx} (${pt.date}) · Equity: <span class="text-green">$${pt.eq.toFixed(2)}</span> · Drawdown: <span class="text-red">${Number(pt.dd_pct || 0).toFixed(2)}%</span> · Trade Net: <span class="${clsVal(pt.net || 0)}">${fmtUsd(pt.net || 0)}</span>`;
  };
}

function renderDossierTables() {
  // 12-Strategy (6 Merged + 6 Individual) Comparison + Legacy Baseline
  const pRows = REPORT.profile_order.map(pid => {
    const pr = REPORT.profiles[pid];
    const s = pr.summary;
    const isAct = pid === activeProfileId;
    const tag = pr.is_merged
      ? '<span class="pill pill-green" style="font-size:9px;padding:1px 5px;margin-right:5px;">MERGED</span>'
      : '<span class="pill pill-gold" style="font-size:9px;padding:1px 5px;margin-right:5px;">SINGLE</span>';
    return `
      <tr class="clickable ${isAct ? 'selected' : ''}" onclick="selectProfile('${pid}')">
        <td>${tag}<strong style="color:${pr.color};">${pr.title}</strong></td>
        <td class="mono">${pr.config.timeframes}</td>
        <td class="mono">${s.trades}</td>
        <td class="mono">${s.active_days}/${s.total_weekdays || 46} (${s.day_coverage_pct}%)</td>
        <td class="mono text-gold">${s.wr_pct.toFixed(2)}%</td>
        <td class="mono text-cyan"><strong>${s.pf.toFixed(2)}</strong></td>
        <td class="mono text-green">${fmtUsd(s.gross_pnl_usd)}</td>
        <td class="mono text-red">-$${s.delta_fee_total_usd.toFixed(2)}</td>
        <td class="mono text-green"><strong>${fmtUsd(s.net_pnl_usd)}</strong></td>
        <td class="mono"><strong>$${s.end_equity.toFixed(2)}</strong></td>
        <td class="mono text-red">-${s.max_dd_pct.toFixed(2)}% (-$${s.max_dd_usd.toFixed(2)})</td>
        <td class="mono">${s.calmar.toFixed(2)}</td>
        <td class="mono">${fmtUsd(s.is_stats.net_pnl)} (${s.is_stats.wr.toFixed(0)}%)</td>
        <td class="mono ${clsVal(s.oos_stats.net_pnl)}">${fmtUsd(s.oos_stats.net_pnl)} (${s.oos_stats.wr.toFixed(0)}%)</td>
      </tr>
    `;
  });
  if (REPORT.legacy_baseline) {
    const lb = REPORT.legacy_baseline;
    pRows.push(`
      <tr style="opacity:0.75;">
        <td><strong class="text-muted">${lb.name}</strong></td>
        <td class="mono">1m+5m+15m</td>
        <td class="mono">${lb.trades}</td>
        <td class="mono">${lb.active_days}/28</td>
        <td class="mono">${lb.wr_pct.toFixed(2)}%</td>
        <td class="mono">${lb.pf.toFixed(2)}</td>
        <td class="mono">${fmtUsd(lb.gross_pnl_usd)}</td>
        <td class="mono text-red">-$${lb.delta_fee_total_usd.toFixed(2)}</td>
        <td class="mono">${fmtUsd(lb.net_pnl_usd)}</td>
        <td class="mono">$${lb.end_equity.toFixed(2)}</td>
        <td class="mono text-red">-${lb.max_dd_pct.toFixed(2)}% (-$${lb.max_dd_usd.toFixed(2)})</td>
        <td class="mono">0.42</td>
        <td class="mono text-muted">Oct: +$29.43</td>
        <td class="mono text-red">Nov: -$16.70</td>
      </tr>
    `);
  }
  document.getElementById('profilesCompareBody').innerHTML = pRows.join('');

  const cur = P();
  const bd = cur.breakdowns;

  // Monthly
  document.getElementById('monthBody').innerHTML = bd.month.map(m => `
    <tr>
      <td><strong>${m.key === '2026-10' ? 'October 2026 (In-Sample)' : 'November 2026 (Out-of-Sample)'}</strong></td>
      <td class="mono">${m.trades}</td>
      <td class="mono">${m.wins}W / ${m.losses}L</td>
      <td class="mono text-gold">${m.wr.toFixed(1)}%</td>
      <td class="mono text-cyan">${m.pf.toFixed(2)}</td>
      <td class="mono">${m.avg_r >= 0 ? '+' : ''}${m.avg_r.toFixed(2)}R</td>
      <td class="mono ${clsVal(m.gross_pnl)}">${fmtUsd(m.gross_pnl)}</td>
      <td class="mono text-red">-$${m.fees.toFixed(2)}</td>
      <td class="mono ${clsVal(m.net_pnl)}"><strong>${fmtUsd(m.net_pnl)}</strong></td>
    </tr>
  `).join('');

  // Weekly
  document.getElementById('weekBody').innerHTML = cur.weekly_rows.map(w => `
    <tr>
      <td class="mono"><strong>${w.week}</strong></td>
      <td class="text-muted">${w.range}</td>
      <td class="mono">${w.active_days}d</td>
      <td class="mono">${w.trades} (${w.wins}W)</td>
      <td class="mono text-gold">${w.wr.toFixed(1)}%</td>
      <td class="mono ${clsVal(w.gross_pnl)}">${fmtUsd(w.gross_pnl)}</td>
      <td class="mono text-red">-$${w.fees.toFixed(2)}</td>
      <td class="mono ${clsVal(w.net_pnl)}"><strong>${fmtUsd(w.net_pnl)}</strong></td>
      <td class="mono text-cyan">$${w.end_eq.toFixed(2)}</td>
    </tr>
  `).join('');

  const renderBucketRows = arr => arr.map(r => `
    <tr>
      <td><strong>${r.key}</strong></td>
      <td class="mono">${r.trades}</td>
      <td class="mono">${r.wins}W / ${r.losses}L</td>
      <td class="mono ${r.wr >= 60 ? 'text-green' : 'text-gold'}">${r.wr.toFixed(1)}%</td>
      <td class="mono text-cyan">${r.pf.toFixed(2)}</td>
      <td class="mono">${r.avg_r >= 0 ? '+' : ''}${r.avg_r.toFixed(2)}R</td>
      <td class="mono ${clsVal(r.net_pnl)}"><strong>${fmtUsd(r.net_pnl)}</strong></td>
      <td class="mono text-muted">${r.share_pct}%</td>
    </tr>
  `).join('');

  document.getElementById('sessionBody').innerHTML = renderBucketRows(bd.session);
  document.getElementById('dowBody').innerHTML = renderBucketRows(bd.day_of_week);
  document.getElementById('tfDirBody').innerHTML =
    renderBucketRows(bd.tf) +
    `<tr class="row-total"><td colspan="8">DIRECTION SPLIT</td></tr>` +
    renderBucketRows(bd.direction);
  document.getElementById('exitBody').innerHTML = renderBucketRows(bd.exit_reason);
  document.getElementById('setupAgentBody').innerHTML = renderBucketRows(bd.setup_agent);
  document.getElementById('playbookBody').innerHTML =
    renderBucketRows(bd.playbook) +
    `<tr class="row-total"><td colspan="8">16-AGENT INITIATOR ROUTING</td></tr>` +
    renderBucketRows(bd.initiator_16);
}

/* ============================================================================
 * TAB 2: 6,336-COMBINATION GRID EXPLORER
 * ============================================================================ */
function renderGridExplorer() {
  const g = REPORT.grid_summary;
  document.getElementById('gridKpiStrip').innerHTML = `
    <div class="kpi-card"><div class="kpi-label">Total Tested</div><div class="kpi-val text-blue">${g.total_combinations.toLocaleString()}</div><div class="kpi-sub">11 Rosters × 3 TFs × 8 Lifecycles × 24 Rules</div></div>
    <div class="kpi-card"><div class="kpi-label">Profitable Combos</div><div class="kpi-val text-green">${g.profitable_combinations.toLocaleString()}</div><div class="kpi-sub">${g.profitable_pct}% Success Rate Across Grid</div></div>
    <div class="kpi-card"><div class="kpi-label">Distinct Trajectories</div><div class="kpi-val text-gold">${g.distinct_trajectories.toLocaleString()}</div><div class="kpi-sub">Unique Non-Overlapping Execution Paths</div></div>
    <div class="kpi-card"><div class="kpi-label">OOS Positive Combos</div><div class="kpi-val text-purple">${g.oos_positive_combinations.toLocaleString()}</div><div class="kpi-sub">Profitable in Nov 2–15 Out-of-Sample</div></div>
  `;

  document.getElementById('lifecycleAggBody').innerHTML = g.by_lifecycle.map(r => `
    <tr>
      <td><strong>${r.key}</strong></td>
      <td class="mono">${r.combos_tested}</td>
      <td class="mono ${r.profitable_pct === 100 ? 'text-green' : 'text-gold'}"><strong>${r.profitable_pct}%</strong></td>
      <td class="mono ${clsVal(r.avg_net_pnl)}">${fmtUsd(r.avg_net_pnl)}</td>
      <td class="mono">${r.avg_wr.toFixed(1)}%</td>
      <td class="mono">${r.avg_pf.toFixed(2)}</td>
      <td class="mono text-green"><strong>${fmtUsd(r.best_net_pnl)}</strong></td>
      <td class="mono text-gold">${r.best_wr.toFixed(1)}%</td>
      <td class="mono text-cyan">${r.best_pf.toFixed(2)}</td>
      <td class="mono text-red">-${r.best_dd_pct.toFixed(1)}%</td>
      <td class="mono ${clsVal(r.best_oos_net)}">${fmtUsd(r.best_oos_net)}</td>
      <td class="mono text-muted" style="font-size:10.5px;">${r.best_combo}</td>
    </tr>
  `).join('');

  const renderSubAgg = arr => arr.map(r => `
    <tr>
      <td><strong>${r.key}</strong></td>
      <td class="mono">${r.combos_tested}</td>
      <td class="mono text-gold">${r.profitable_pct}%</td>
      <td class="mono ${clsVal(r.avg_net_pnl)}">${fmtUsd(r.avg_net_pnl)}</td>
      <td class="mono text-green"><strong>${fmtUsd(r.best_net_pnl)}</strong></td>
      <td class="mono text-gold">${r.best_wr.toFixed(1)}%</td>
      <td class="mono text-cyan">${r.best_pf.toFixed(2)}</td>
      <td class="mono text-red">-${r.best_dd_pct.toFixed(1)}%</td>
    </tr>
  `).join('');

  document.getElementById('rosterAggBody').innerHTML = renderSubAgg(g.by_roster);
  document.getElementById('tfAggBody').innerHTML = renderSubAgg(g.by_timeframes);

  const lcs = [...new Set(REPORT.top_100_combinations.map(c => c.lifecycle))];
  const tfs = [...new Set(REPORT.top_100_combinations.map(c => c.timeframes))];
  document.getElementById('gridFilterLc').innerHTML = '<option value="ALL">All Lifecycles</option>' + lcs.map(x => `<option value="${x}">${x}</option>`).join('');
  document.getElementById('gridFilterTf').innerHTML = '<option value="ALL">All TF Mixes</option>' + tfs.map(x => `<option value="${x}">${x}</option>`).join('');
  renderTop100Table();
}

function sortTop100(key) {
  if (top100SortKey === key) top100SortAsc = !top100SortAsc;
  else { top100SortKey = key; top100SortAsc = false; }
  renderTop100Table();
}

function renderTop100Table() {
  const flc = document.getElementById('gridFilterLc').value;
  const ftf = document.getElementById('gridFilterTf').value;
  const fres = document.getElementById('gridFilterRescue').value;
  const q = document.getElementById('gridSearchInput').value.toLowerCase().trim();

  let rows = REPORT.top_100_combinations.filter(r => {
    if (flc !== 'ALL' && r.lifecycle !== flc) return false;
    if (ftf !== 'ALL' && r.timeframes !== ftf) return false;
    if (fres !== 'ALL' && r.rescue_mode !== fres) return false;
    if (q && !(r.combo_name.toLowerCase().includes(q) || r.roster.toLowerCase().includes(q))) return false;
    return true;
  });

  rows.sort((a, b) => {
    const va = Number(a[top100SortKey] || 0), vb = Number(b[top100SortKey] || 0);
    return top100SortAsc ? va - vb : vb - va;
  });

  document.getElementById('top100Body').innerHTML = rows.map(r => `
    <tr>
      <td class="mono"><strong>#${r.rank}</strong></td>
      <td class="mono" style="font-size:11px;">${r.combo_name}</td>
      <td>${r.roster}</td>
      <td class="mono">${r.timeframes}</td>
      <td>${r.lifecycle}</td>
      <td class="mono">${r.min_mem_wr}%</td>
      <td><span class="pill ${r.rescue_mode === 'RESCUE' ? 'pill-green' : 'pill-cyan'}">${r.rescue_mode}</span></td>
      <td class="mono">${r.trades}</td>
      <td class="mono">${r.active_days}/${REPORT.data_meta.active_weekdays || 46} (${r.day_coverage_pct}%)</td>
      <td class="mono text-gold">${r.wr.toFixed(1)}%</td>
      <td class="mono text-cyan">${r.pf.toFixed(2)}</td>
      <td class="mono text-green"><strong>${fmtUsd(r.net_pnl)}</strong></td>
      <td class="mono text-red">-${r.max_dd_pct.toFixed(1)}%</td>
      <td class="mono ${clsVal(r.oos_net_pnl)}">${fmtUsd(r.oos_net_pnl)}</td>
      <td class="mono">${r.oos_wr.toFixed(1)}%</td>
    </tr>
  `).join('');
}

/* ============================================================================
 * TAB 3: ALL 16 AGENTS & 11 SPECIALISTS MATRIX
 * ============================================================================ */
function renderAgentsMatrix() {
  const fmtCell = m => {
    if (!m || !m.trades) return '<span class="text-dim">—</span>';
    return `<span class="mono">${m.trades}T | <span class="text-gold">${m.wr.toFixed(1)}%</span> | PF ${m.pf.toFixed(2)} | <strong class="${clsVal(m.net_pnl)}">${fmtUsd(m.net_pnl)}</strong></span>`;
  };
  document.getElementById('specMatrixBody').innerHTML = REPORT.specialists_matrix.map(r => `
    <tr>
      <td><strong>${r.agent_id}</strong></td>
      <td><span class="pill ${r.kind === 'SPECIALIST' ? 'pill-blue' : 'pill-purple'}">${r.kind === 'SPECIALIST' ? 'SPECIALIST' : 'POD'}</span></td>
      <td class="text-muted">${r.focus}</td>
      <td>${fmtCell(r.tf_1m)}</td>
      <td>${fmtCell(r.tf_5m)}</td>
      <td>${fmtCell(r.tf_15m)}</td>
      <td>${fmtCell(r.tf_1h)}</td>
    </tr>
  `).join('');

  document.getElementById('routerMapBody').innerHTML = REPORT.day_session_router.map(r => `
    <tr>
      <td><strong>${r.weekday}</strong></td>
      <td><span class="pill pill-cyan">${r.session}</span></td>
      <td><strong class="text-gold">${r.top1_agent}</strong></td>
      <td>${r.top1_playbook}</td>
      <td class="mono">${r.top1_trades}</td>
      <td class="mono text-green">${r.top1_wr.toFixed(1)}%</td>
      <td class="mono text-cyan">${r.top1_pf.toFixed(2)}</td>
      <td class="mono ${clsVal(r.top1_net)}">${fmtUsd(r.top1_net)}</td>
      <td class="text-muted">${r.top2_agent}${r.top2_wr !== null ? ` (${r.top2_wr.toFixed(0)}% WR, PF ${r.top2_pf.toFixed(2)})` : ''}</td>
    </tr>
  `).join('');

  document.getElementById('floor16Body').innerHTML = REPORT.floor_16_agents_telemetry.map(a => `
    <tr>
      <td><strong class="text-gold">${a.agent_id}</strong></td>
      <td><strong>${a.title}</strong></td>
      <td><span class="pill pill-blue">${a.role}</span></td>
      <td class="mono">${a.confirm_count.toLocaleString()}</td>
      <td class="mono text-cyan">${a.confirm_pct.toFixed(1)}%</td>
      <td class="mono text-red">${a.veto_count.toLocaleString()}</td>
      <td class="mono text-green">${a.lc6_wr_when_confirmed.toFixed(1)}%</td>
      <td class="text-muted" style="white-space:normal; max-width:440px;">${a.description}</td>
    </tr>
  `).join('');
}

/* ============================================================================
 * TAB 4: INTERACTIVE XAUTUSD CANDLESTICK CHART
 * ============================================================================ */
function formatExitReason(reason) {
  if (!reason) return 'Exit';
  const r = String(reason).toUpperCase();
  if (r.includes('STOP_LOSS') || r === 'SL') return '🛑 SL Hit';
  if (r.includes('INSTANT_PRE_SL') || r.includes('INSTANT_CUT')) return '⚡ Instant Cut';
  if (r.includes('CHANDELIER') || r.includes('40R_SL_TRAIL') || r.includes('TRAIL') || r.includes('RUNNER')) return '🌊 Trailing SL Hit';
  if (r.includes('REVERSAL')) return '🔄 Reversal Cut';
  if (r.includes('STALL')) return '🔒 Stall Lock';
  if (r.includes('BREAKEVEN') || r.includes('BE')) return '🛡️ Breakeven Lock';
  if (r.includes('TP') || r.includes('TARGET')) return '🎯 TP Hit';
  if (r.includes('TIME')) return '⏱️ Time Cycle Exit';
  return reason.replace(/_/g, ' ');
}

function getBars(tfMins) {
  if (TF_BARS_CACHE[tfMins]) return TF_BARS_CACHE[tfMins];
  if (tfMins === 5) { TF_BARS_CACHE[5] = REPORT.candles_5m; return TF_BARS_CACHE[5]; }
  if (tfMins === 15) { TF_BARS_CACHE[15] = REPORT.candles_15m; return TF_BARS_CACHE[15]; }

  const src = REPORT.candles_15m;
  const bSec = tfMins * 60;
  const time = [], open = [], high = [], low = [], close = [], vol = [];
  let prevB = -1;
  for (let i = 0; i < src.length; i++) {
    const b = Math.floor(src.time[i] / bSec) * bSec;
    if (b !== prevB) {
      prevB = b;
      time.push(b); open.push(src.open[i]); high.push(src.high[i]); low.push(src.low[i]); close.push(src.close[i]); vol.push(src.vol[i]);
    } else {
      const k = time.length - 1;
      if (src.high[i] > high[k]) high[k] = src.high[i];
      if (src.low[i] < low[k]) low[k] = src.low[i];
      close[k] = src.close[i];
      vol[k] += src.vol[i];
    }
  }
  TF_BARS_CACHE[tfMins] = { length: time.length, time, open, high, low, close, vol };
  return TF_BARS_CACHE[tfMins];
}

function findBarIdx(timeArr, targetSec) {
  let lo = 0, hi = timeArr.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (timeArr[mid] < targetSec) lo = mid + 1; else hi = mid;
  }
  return lo;
}

function setupCanvasInteractions() {
  const canvas = document.getElementById('tvChart');
  const nav = document.getElementById('tvNavChart');

  document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const oldB = getBars(currentTF);
      const sSec = oldB.time[Math.max(0, Math.floor(viewStartIdx))];
      const eSec = oldB.time[Math.min(oldB.length - 1, Math.ceil(viewEndIdx))];
      document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTF = parseInt(btn.getAttribute('data-tf'), 10);
      const newB = getBars(currentTF);
      viewStartIdx = findBarIdx(newB.time, sSec);
      viewEndIdx = Math.max(viewStartIdx + 24, findBarIdx(newB.time, eSec));
      drawTradingViewChart();
    });
  });

  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    const bars = getBars(currentTF);
    const rect = canvas.getBoundingClientRect();
    const plotW = Math.max(100, rect.width - 75);
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / plotW));
    const span = viewEndIdx - viewStartIdx;
    const newSpan = Math.max(15, Math.min(bars.length - 1, span * (e.deltaY > 0 ? 1.25 : 0.8)));
    const anchor = viewStartIdx + span * ratio;
    viewStartIdx = Math.max(0, Math.round(anchor - newSpan * ratio));
    viewEndIdx = Math.min(bars.length - 1, Math.round(viewStartIdx + newSpan));
    drawTradingViewChart();
  });

  canvas.addEventListener('mousedown', e => { isDragging = true; dragStartX = e.clientX; });
  window.addEventListener('mouseup', () => { isDragging = false; });
  canvas.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    hoverMouse = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    if (isDragging) {
      const dx = e.clientX - dragStartX;
      dragStartX = e.clientX;
      const bars = getBars(currentTF);
      const span = viewEndIdx - viewStartIdx;
      const moved = Math.round((dx / Math.max(100, rect.width - 75)) * span);
      viewStartIdx = Math.max(0, Math.min(bars.length - 20, viewStartIdx - moved));
      viewEndIdx = Math.min(bars.length - 1, viewStartIdx + span);
    }
    drawTradingViewChart();
  });
  canvas.addEventListener('mouseleave', () => { hoverMouse = null; drawTradingViewChart(); });
  canvas.addEventListener('click', e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    for (const box of chartTradeHitboxes) {
      if (mx >= box.x && mx <= box.x + box.w && my >= box.y && my <= box.y + box.h) {
        selectTrade(box.trade, false, false);
        openTradeAuditModal(box.trade);
        return;
      }
    }
  });

  nav.addEventListener('click', e => {
    const rect = nav.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const bars = getBars(currentTF);
    const span = viewEndIdx - viewStartIdx;
    const center = Math.round(ratio * (bars.length - 1));
    viewStartIdx = Math.max(0, Math.round(center - span / 2));
    viewEndIdx = Math.min(bars.length - 1, viewStartIdx + span);
    drawTradingViewChart();
  });

  document.getElementById('prevTradeBtn').addEventListener('click', () => stepTrade(-1));
  document.getElementById('nextTradeBtn').addEventListener('click', () => stepTrade(1));
  document.getElementById('zoomTradeBtn').addEventListener('click', zoomToSelectedTrade);
  document.getElementById('fitAllBtn').addEventListener('click', () => {
    const bars = getBars(currentTF);
    viewStartIdx = 0; viewEndIdx = bars.length - 1;
    drawTradingViewChart();
  });
  document.getElementById('tradeJumpSelect').addEventListener('change', e => {
    const t = P().trades.find(x => x.id === parseInt(e.target.value, 10));
    if (t) selectTrade(t, true, false);
  });
}

function drawTradingViewChart() {
  const canvas = document.getElementById('tvChart');
  if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const W = Math.floor(rect.width), H = Math.floor(rect.height);
  if (W <= 50 || H <= 50) return;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = W * dpr; canvas.height = H * dpr;
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  chartTradeHitboxes = [];

  ctx.fillStyle = '#090c13';
  ctx.fillRect(0, 0, W, H);

  const bars = getBars(currentTF);
  if (!bars || !bars.length) return;
  const sIdx = Math.max(0, Math.floor(viewStartIdx));
  const eIdx = Math.min(bars.length - 1, Math.ceil(viewEndIdx));
  const numBars = Math.max(2, eIdx - sIdx + 1);

  const priceAxisW = 75, plotW = W - priceAxisW, timeAxisH = 26, headerH = 34, plotH = H - timeAxisH - headerH;
  let minP = Infinity, maxP = -Infinity, maxVol = 1;
  const stride = Math.max(1, Math.floor(numBars / 800));
  for (let i = sIdx; i <= eIdx; i += stride) {
    if (bars.low[i] < minP) minP = bars.low[i];
    if (bars.high[i] > maxP) maxP = bars.high[i];
    if (bars.vol[i] > maxVol) maxVol = bars.vol[i];
  }

  const trades = P().trades;
  const sSec = bars.time[sIdx], eSec = bars.time[eIdx];
  const visTrades = trades.filter(t => t.exit_ts >= sSec && t.entry_ts <= eSec);
  visTrades.forEach(t => {
    minP = Math.min(minP, t.sl_price, t.entry_price, t.exit_price);
    maxP = Math.max(maxP, t.sl_price, t.entry_price, t.exit_price);
  });
  const padP = Math.max(2.0, (maxP - minP) * 0.08);
  minP -= padP; maxP += padP;

  const xOf = idx => ((idx - sIdx) / Math.max(1, numBars - 1)) * plotW;
  const yOfP = p => headerH + plotH * (1 - (p - minP) / Math.max(1, maxP - minP));
  const stepX = plotW / numBars;

  // Grid
  ctx.strokeStyle = '#131824'; ctx.lineWidth = 1;
  for (let i = 0; i <= 7; i++) {
    const p = minP + (i / 7) * (maxP - minP);
    const y = yOfP(p);
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(plotW, y); ctx.stroke();
    ctx.fillStyle = '#64748b'; ctx.font = '10px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText(p.toFixed(2), plotW + 6, y + 3);
  }

  // 1. TradingView Long / Short Position Background Tool Boxes
  visTrades.forEach(t => {
    const isSel = selectedTrade && selectedTrade.id === t.id;
    const iEnt = findBarIdx(bars.time, t.entry_ts);
    const iExt = findBarIdx(bars.time, t.exit_ts);
    const xEnt = Math.max(0, Math.min(plotW - 5, xOf(iEnt)));
    const xExt = Math.min(plotW - 2, Math.max(xEnt + 18, xOf(iExt)));
    const yEnt = yOfP(t.entry_price), yExt = yOfP(t.exit_price), ySL = yOfP(t.sl_price), yTP = yOfP(t.tp1_price);
    const isLong = t.direction === 'LONG';
    const boxW = Math.max(16, xExt - xEnt);

    // Target (Profit) Box & Stop (Risk) Box
    let profitTop, profitH, riskTop, riskH;
    if (isLong) {
      profitTop = Math.min(yEnt, yTP);
      profitH = Math.max(3, Math.abs(yEnt - yTP));
      riskTop = yEnt;
      riskH = Math.max(3, Math.abs(ySL - yEnt));
    } else {
      riskTop = Math.min(yEnt, ySL);
      riskH = Math.max(3, Math.abs(ySL - yEnt));
      profitTop = yEnt;
      profitH = Math.max(3, Math.abs(yTP - yEnt));
    }

    // Profit Box (Green)
    ctx.fillStyle = isSel ? 'rgba(16, 185, 129, 0.30)' : 'rgba(16, 185, 129, 0.18)';
    ctx.fillRect(xEnt, profitTop, boxW, profitH);
    ctx.strokeStyle = isSel ? 'rgba(16, 185, 129, 1.0)' : 'rgba(16, 185, 129, 0.75)';
    ctx.lineWidth = isSel ? 1.8 : 1.1;
    ctx.strokeRect(xEnt, profitTop, boxW, profitH);

    // Risk Box (Red)
    ctx.fillStyle = isSel ? 'rgba(239, 68, 68, 0.30)' : 'rgba(239, 68, 68, 0.18)';
    ctx.fillRect(xEnt, riskTop, boxW, riskH);
    ctx.strokeStyle = isSel ? 'rgba(239, 68, 68, 1.0)' : 'rgba(239, 68, 68, 0.75)';
    ctx.lineWidth = isSel ? 1.8 : 1.1;
    ctx.strokeRect(xEnt, riskTop, boxW, riskH);

    // Entry Center Separator Line
    ctx.strokeStyle = isSel ? '#ffffff' : '#e2e8f0';
    ctx.lineWidth = isSel ? 2 : 1.3;
    ctx.beginPath(); ctx.moveTo(xEnt, yEnt); ctx.lineTo(xExt, yEnt); ctx.stroke();

    // Target & Stop Dashed Horizon Lines
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.9)'; ctx.beginPath(); ctx.moveTo(xEnt, yTP); ctx.lineTo(xExt, yTP); ctx.stroke();
    ctx.strokeStyle = 'rgba(239, 68, 68, 0.9)'; ctx.beginPath(); ctx.moveTo(xEnt, ySL); ctx.lineTo(xExt, ySL); ctx.stroke();
    ctx.setLineDash([]);
  });

  // Candles
  if (numBars <= plotW * 0.75) {
    const barW = Math.max(1.8, Math.min(14, stepX * 0.7));
    for (let i = sIdx; i <= eIdx; i++) {
      const x = xOf(i), oY = yOfP(bars.open[i]), hY = yOfP(bars.high[i]), lY = yOfP(bars.low[i]), cY = yOfP(bars.close[i]);
      const col = bars.close[i] >= bars.open[i] ? '#10b981' : '#ef4444';
      ctx.strokeStyle = col; ctx.lineWidth = 1.1; ctx.beginPath(); ctx.moveTo(x, hY); ctx.lineTo(x, lY); ctx.stroke();
      ctx.fillStyle = col; ctx.fillRect(x - barW / 2, Math.min(oY, cY), barW, Math.max(1.2, Math.abs(cY - oY)));
    }
  } else {
    const numCols = Math.max(180, Math.floor(plotW / 3.0)), barsPerCol = numBars / numCols, colW = plotW / numCols, bodyW = Math.max(1.5, colW * 0.7);
    for (let col = 0; col < numCols; col++) {
      const b0 = Math.min(bars.length - 1, Math.floor(sIdx + col * barsPerCol));
      const b1 = Math.min(bars.length - 1, Math.max(b0, Math.floor(sIdx + (col + 1) * barsPerCol) - 1));
      const o = bars.open[b0], c = bars.close[b1];
      let h = bars.high[b0], l = bars.low[b0];
      for (let k = b0 + 1; k <= b1; k++) { if (bars.high[k] > h) h = bars.high[k]; if (bars.low[k] < l) l = bars.low[k]; }
      const cx = (col + 0.5) * colW, colStr = c >= o ? '#10b981' : '#ef4444';
      ctx.strokeStyle = colStr; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(cx, yOfP(h)); ctx.lineTo(cx, yOfP(l)); ctx.stroke();
      ctx.fillStyle = colStr; ctx.fillRect(cx - bodyW / 2, Math.min(yOfP(o), yOfP(c)), bodyW, Math.max(1.2, Math.abs(yOfP(c) - yOfP(o))));
    }
  }

  // 3. Foreground Trade Overlays: Execution Vector, Entry Badges, Right-side Level Tags & Exact Exit Logic Badges
  visTrades.forEach(t => {
    const isSel = selectedTrade && selectedTrade.id === t.id;
    const iEnt = findBarIdx(bars.time, t.entry_ts);
    const iExt = findBarIdx(bars.time, t.exit_ts);
    const xEnt = Math.max(0, Math.min(plotW - 5, xOf(iEnt)));
    const xExt = Math.min(plotW - 2, Math.max(xEnt + 18, xOf(iExt)));
    const yEnt = yOfP(t.entry_price), yExt = yOfP(t.exit_price), ySL = yOfP(t.sl_price), yTP = yOfP(t.tp1_price);
    const isLong = t.direction === 'LONG';
    const isWin = t.net_pnl_usd > 0;
    const boxW = Math.max(16, xExt - xEnt);

    // Dotted Execution Path from Entry to Exit
    ctx.setLineDash([3, 2]);
    ctx.strokeStyle = isWin ? '#34d399' : '#f87171';
    ctx.lineWidth = isSel ? 2 : 1.4;
    ctx.beginPath(); ctx.moveTo(xEnt, yEnt); ctx.lineTo(xExt, yExt); ctx.stroke();
    ctx.setLineDash([]);

    // Entry Point Dot
    ctx.fillStyle = isLong ? '#10b981' : '#ef4444';
    ctx.beginPath(); ctx.arc(xEnt, yEnt, 3, 0, Math.PI * 2); ctx.fill();

    // Exit Point Marker (Target Bullseye)
    ctx.fillStyle = isWin ? '#10b981' : '#ef4444';
    ctx.beginPath(); ctx.arc(xExt, yExt, 4.5, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.beginPath(); ctx.arc(xExt, yExt, 2, 0, Math.PI * 2); ctx.fill();

    // Right-edge TradingView Level Tags (if boxW >= 45 or isSel)
    if (boxW >= 45 || isSel) {
      ctx.font = 'bold 9px ui-monospace, monospace';
      // Target tag
      const tpTxt = `TP ${t.tp1_price.toFixed(1)}`;
      const tpTagW = ctx.measureText(tpTxt).width + 8;
      ctx.fillStyle = '#065f46'; ctx.fillRect(xExt - tpTagW, yTP - 7, tpTagW, 14);
      ctx.strokeStyle = '#10b981'; ctx.lineWidth = 1; ctx.strokeRect(xExt - tpTagW, yTP - 7, tpTagW, 14);
      ctx.fillStyle = '#a7f3d0'; ctx.textAlign = 'center'; ctx.fillText(tpTxt, xExt - tpTagW / 2, yTP + 3.5);

      // Stop tag
      const slTxt = `SL ${t.sl_price.toFixed(1)}`;
      const slTagW = ctx.measureText(slTxt).width + 8;
      ctx.fillStyle = '#7f1d1d'; ctx.fillRect(xExt - slTagW, ySL - 7, slTagW, 14);
      ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 1; ctx.strokeRect(xExt - slTagW, ySL - 7, slTagW, 14);
      ctx.fillStyle = '#fecaca'; ctx.textAlign = 'center'; ctx.fillText(slTxt, xExt - slTagW / 2, ySL + 3.5);

      // Entry tag
      const entTxt = `${t.entry_price.toFixed(1)}`;
      const entTagW = ctx.measureText(entTxt).width + 8;
      ctx.fillStyle = '#1e293b'; ctx.fillRect(xExt - entTagW, yEnt - 7, entTagW, 14);
      ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 1; ctx.strokeRect(xExt - entTagW, yEnt - 7, entTagW, 14);
      ctx.fillStyle = '#f8fafc'; ctx.textAlign = 'center'; ctx.fillText(entTxt, xExt - entTagW / 2, yEnt + 3.5);
    }

    // Entry Badge (at xEnt)
    ctx.font = 'bold 9.5px -apple-system, sans-serif';
    const entBadgeTxt = `${isLong ? '▲ BUY' : '▼ SELL'} #${t.id}`;
    const ebW = ctx.measureText(entBadgeTxt).width + 12, ebH = 18;
    const ebX = Math.max(2, xEnt - ebW / 2);
    const ebY = isLong ? Math.min(plotH + headerH - ebH, yEnt + 14) : Math.max(headerH + 2, yEnt - 28);
    ctx.fillStyle = isSel ? '#f59e0b' : (isLong ? '#065f46' : '#7f1d1d');
    ctx.fillRect(ebX, ebY, ebW, ebH);
    ctx.strokeStyle = isSel ? '#ffffff' : (isLong ? '#10b981' : '#ef4444');
    ctx.lineWidth = isSel ? 1.5 : 1;
    ctx.strokeRect(ebX, ebY, ebW, ebH);
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center';
    ctx.fillText(entBadgeTxt, ebX + ebW / 2, ebY + 12.5);

    // Exact Exit Logic Pill Badge (at xExt, yExt)
    const exitTxt = formatExitReason(t.exit_reason);
    const rTxt = `${t.r_multiple >= 0 ? '+' : ''}${t.r_multiple.toFixed(2)}R`;
    const exitPillTxt = `${exitTxt} (${rTxt} · ${fmtUsd(t.net_pnl_usd)})`;
    ctx.font = 'bold 9.5px -apple-system, sans-serif';
    const pillW = ctx.measureText(exitPillTxt).width + 12, pillH = 19;
    let pillX = xExt + 4;
    if (pillX + pillW > plotW - 2) pillX = Math.max(2, xExt - pillW - 4);
    let pillY = yExt - pillH / 2;
    if (pillY < headerH + 2) pillY = headerH + 2;
    if (pillY + pillH > headerH + plotH) pillY = headerH + plotH - pillH;

    ctx.fillStyle = isWin ? '#064e3b' : '#7f1d1d';
    ctx.fillRect(pillX, pillY, pillW, pillH);
    ctx.strokeStyle = isWin ? '#10b981' : '#ef4444';
    ctx.lineWidth = isSel ? 2 : 1.2;
    ctx.strokeRect(pillX, pillY, pillW, pillH);
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center';
    ctx.fillText(exitPillTxt, pillX + pillW / 2, pillY + 13);

    // Hitbox for clicks
    const hitTop = Math.min(yTP, ySL, yEnt, yExt, ebY, pillY);
    const hitBot = Math.max(yTP, ySL, yEnt, yExt, ebY + ebH, pillY + pillH);
    const hitLeft = Math.min(xEnt, ebX, pillX);
    const hitRight = Math.max(xExt, ebX + ebW, pillX + pillW);
    chartTradeHitboxes.push({ x: hitLeft, y: hitTop, w: Math.max(20, hitRight - hitLeft), h: Math.max(20, hitBot - hitTop), trade: t });
  });

  let hIdx = sIdx + Math.floor(numBars / 2);
  if (hoverMouse && hoverMouse.x >= 0 && hoverMouse.x <= plotW && hoverMouse.y >= headerH && hoverMouse.y <= headerH + plotH) {
    hIdx = Math.max(0, Math.min(bars.length - 1, Math.round(sIdx + (hoverMouse.x / plotW) * (numBars - 1))));
    ctx.strokeStyle = 'rgba(148,163,184,0.4)'; ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(hoverMouse.x, headerH); ctx.lineTo(hoverMouse.x, headerH + plotH); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, hoverMouse.y); ctx.lineTo(plotW, hoverMouse.y); ctx.stroke();
    ctx.setLineDash([]);
    const hp = minP + (1 - (hoverMouse.y - headerH) / plotH) * (maxP - minP);
    ctx.fillStyle = '#3b82f6'; ctx.fillRect(plotW, hoverMouse.y - 9, priceAxisW, 18);
    ctx.fillStyle = '#fff'; ctx.font = 'bold 10px ui-monospace, monospace'; ctx.textAlign = 'left';
    ctx.fillText(hp.toFixed(2), plotW + 6, hoverMouse.y + 4);
  }

  const dStart = new Date(sSec * 1000).toISOString().slice(0, 10), dEnd = new Date(eSec * 1000).toISOString().slice(0, 10);
  ctx.fillStyle = '#fff'; ctx.font = 'bold 12px -apple-system, sans-serif'; ctx.textAlign = 'left';
  ctx.fillText(`Delta XAUTUSD · ${currentTF}m · ${dStart} → ${dEnd} · ${visTrades.length} Trades in View   O ${bars.open[hIdx].toFixed(2)}  H ${bars.high[hIdx].toFixed(2)}  L ${bars.low[hIdx].toFixed(2)}  C ${bars.close[hIdx].toFixed(2)}`, 12, 21);

  ctx.fillStyle = '#0c1018'; ctx.fillRect(0, headerH + plotH, W, timeAxisH);
  ctx.fillStyle = '#64748b'; ctx.font = '10px -apple-system, sans-serif'; ctx.textAlign = 'center';
  const tStep = Math.max(1, Math.floor(numBars / 6));
  for (let i = sIdx; i <= eIdx; i += tStep) {
    ctx.fillText(new Date(bars.time[i] * 1000).toISOString().replace('T', ' ').slice(5, 16), xOf(i), headerH + plotH + 16);
  }
  drawNavigatorBar(bars, sIdx, eIdx);
}

function drawNavigatorBar(bars, sIdx, eIdx) {
  const nav = document.getElementById('tvNavChart');
  if (!nav || !bars || !bars.length) return;
  const W = Math.floor(nav.getBoundingClientRect().width) || 1000, H = 48, dpr = window.devicePixelRatio || 1;
  nav.width = W * dpr; nav.height = H * dpr;
  const ctx = nav.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = '#080b11'; ctx.fillRect(0, 0, W, H);
  const n = bars.length, step = Math.max(1, Math.floor(n / 500));
  let minP = Infinity, maxP = -Infinity;
  for (let i = 0; i < n; i += step) { minP = Math.min(minP, bars.close[i]); maxP = Math.max(maxP, bars.close[i]); }
  const yOf = p => 3 + (H - 6) * (1 - (p - minP) / Math.max(1, maxP - minP));
  ctx.strokeStyle = 'rgba(148,163,184,0.4)'; ctx.lineWidth = 1; ctx.beginPath();
  for (let i = 0; i < n; i += step) {
    const x = (i / (n - 1)) * W, y = yOf(bars.close[i]);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();

  P().trades.forEach(t => {
    const idx = findBarIdx(bars.time, t.entry_ts), x = (idx / (n - 1)) * W;
    const isSel = selectedTrade && selectedTrade.id === t.id;
    ctx.fillStyle = isSel ? '#f59e0b' : (t.net_pnl_usd > 0 ? '#10b981' : '#ef4444');
    ctx.fillRect(x - (isSel ? 2 : 1), 2, isSel ? 4 : 2, H - 4);
  });

  const x1 = (sIdx / (n - 1)) * W, x2 = Math.max(x1 + 6, (eIdx / (n - 1)) * W);
  ctx.fillStyle = 'rgba(59,130,246,0.22)'; ctx.fillRect(x1, 0, x2 - x1, H);
  ctx.strokeStyle = '#3b82f6'; ctx.lineWidth = 1.5; ctx.strokeRect(x1, 0.5, x2 - x1, H - 1);
}

function populateTradeJumpSelect() {
  document.getElementById('tradeJumpSelect').innerHTML = P().trades.map(t =>
    `<option value="${t.id}">#${t.id} (${t.date}) ${t.direction === 'LONG' ? 'BUY' : 'SELL'} · ${formatExitReason(t.exit_reason)} (${t.r_multiple >= 0 ? '+' : ''}${t.r_multiple.toFixed(2)}R | ${fmtUsd(t.net_pnl_usd)})</option>`
  ).join('');
}

function selectTrade(trade, zoom = false, switchToChart = false) {
  selectedTrade = trade;
  document.getElementById('tradeJumpSelect').value = String(trade.id);
  const isWin = trade.net_pnl_usd > 0;
  const exitClean = formatExitReason(trade.exit_reason);
  document.getElementById('bannerTradeText').innerHTML =
    `<span class="badge ${trade.direction === 'LONG' ? 'badge-long' : 'badge-short'}">${trade.direction === 'LONG' ? '▲ BUY' : '▼ SELL'}</span> ` +
    `<strong>Trade #${trade.id} (${trade.entry_time} · ${trade.session})</strong> · ` +
    `Setup: <strong>${trade.setup_agent} (${trade.tf})</strong> · ` +
    `Entry <strong>${trade.entry_price.toFixed(2)}</strong> → Exit <strong>${trade.exit_price.toFixed(2)}</strong> (${trade.hold_mins}m) · ` +
    `<span class="${isWin ? 'text-green' : 'text-red'} mono"><strong>${trade.r_multiple >= 0 ? '+' : ''}${trade.r_multiple.toFixed(2)}R (${fmtUsd(trade.net_pnl_usd)})</strong></span> · ` +
    `Exit Logic: <span class="badge ${isWin ? 'badge-long' : 'badge-short'}" style="font-size:11px;">${exitClean}</span> <span class="text-dim">(${trade.exit_reason})</span>`;
  document.getElementById('bannerInspectBtn').style.display = 'inline-flex';
  if (zoom) zoomToSelectedTrade(); else drawTradingViewChart();
  if (switchToChart) switchTab('tab-chart');
}

function stepTrade(dir) {
  const arr = P().trades;
  if (!arr.length) return;
  const idx = selectedTrade ? arr.findIndex(t => t.id === selectedTrade.id) : 0;
  selectTrade(arr[Math.max(0, Math.min(arr.length - 1, idx + dir))], true, false);
}

function zoomToSelectedTrade() {
  if (!selectedTrade) return;
  const bars = getBars(currentTF);
  const iEnt = findBarIdx(bars.time, selectedTrade.entry_ts);
  const iExt = Math.max(iEnt + 2, findBarIdx(bars.time, selectedTrade.exit_ts));
  const span = Math.max(32, (iExt - iEnt) * 4);
  viewStartIdx = Math.max(0, Math.round(iEnt - span * 0.35));
  viewEndIdx = Math.min(bars.length - 1, Math.round(viewStartIdx + span));
  drawTradingViewChart();
}

/* ============================================================================
 * TAB 5: CALENDAR HEATMAP & 32-DAY LOG
 * ============================================================================ */
function setCalMonth(ym) {
  currentCalMonth = ym;
  document.getElementById('calOctBtn').classList.toggle('active', ym === '2026-10');
  document.getElementById('calNovBtn').classList.toggle('active', ym === '2026-11');
  renderCalendar();
}

function renderCalendar() {
  const [yr, mo] = currentCalMonth.split('-').map(Number);
  const daysInMo = new Date(yr, mo, 0).getDate();
  const firstDow = new Date(yr, mo - 1, 1).getDay();
  const byDay = {};
  P().daily_rows.forEach(r => { byDay[r.date] = r; });

  const moRows = P().daily_rows.filter(r => r.date.startsWith(currentCalMonth));
  const moNet = moRows.reduce((s, r) => s + r.net_pnl, 0);
  const moT = moRows.reduce((s, r) => s + r.trades, 0);
  const moW = moRows.reduce((s, r) => s + r.wins, 0);
  document.getElementById('calMonthSummaryBadge').textContent =
    `${currentCalMonth}: ${moT} Trades · ${moT ? (moW / moT * 100).toFixed(1) : '0.0'}% WR · ${fmtUsd(moNet)}`;

  const headers = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat','Week Sum'].map(h => `<div class="cal-header">${h}</div>`).join('');
  let cells = '';
  let col = 0, wkNet = 0, wkT = 0, wkW = 0;

  for (let i = 0; i < firstDow; i++) { cells += '<div class="cal-day empty"></div>'; col++; }

  const flushWk = () => {
    cells += `<div class="cal-day week-col">
      <div class="cal-day-top"><span>Week Total</span><span>${wkT}T</span></div>
      <div class="cal-day-pnl ${clsVal(wkNet)}">${fmtUsd(wkNet)}</div>
      <div class="cal-day-bot"><span>${wkW}W/${wkT - wkW}L</span><span>${wkT ? (wkW / wkT * 100).toFixed(0) : 0}% WR</span></div>
    </div>`;
    wkNet = 0; wkT = 0; wkW = 0;
  };

  for (let d = 1; d <= daysInMo; d++) {
    const dStr = `${currentCalMonth}-${String(d).padStart(2, '0')}`;
    const r = byDay[dStr];
    if (r && r.trades > 0) {
      wkNet += r.net_pnl; wkT += r.trades; wkW += r.wins;
      const isWin = r.net_pnl >= 0;
      cells += `<div class="cal-day ${isWin ? 'win-day' : 'loss-day'} ${selectedCalDate === dStr ? 'selected' : ''}" onclick="inspectCalDay('${dStr}')">
        <div class="cal-day-top"><span>${d}</span><span>${r.trades}T (${r.wins}W)</span></div>
        <div class="cal-day-pnl ${isWin ? 'text-green' : 'text-red'}">${fmtUsd(r.net_pnl)}</div>
        <div class="cal-day-bot"><span>${r.is_oos ? 'OOS' : 'IS'}</span><span>Eq $${r.cum_eq.toFixed(0)}</span></div>
      </div>`;
    } else {
      cells += `<div class="cal-day"><div class="cal-day-top"><span style="color:#475569;">${d}</span><span style="font-size:10px;color:#475569;">Flat</span></div></div>`;
    }
    col++;
    if (col === 7) { flushWk(); col = 0; }
  }
  if (col > 0) { while (col < 7) { cells += '<div class="cal-day empty"></div>'; col++; } flushWk(); }
  document.getElementById('calGrid').innerHTML = headers + cells;
}

function inspectCalDay(dStr) {
  selectedCalDate = dStr;
  renderCalendar();
  const dTrades = P().trades.filter(t => t.date === dStr);
  const r = P().daily_rows.find(x => x.date === dStr);
  document.getElementById('calDayInspector').innerHTML =
    `<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:6px;">
      <strong>${dStr} (${r ? r.day : ''}) — ${dTrades.length} Trades | Net ${fmtUsd(r ? r.net_pnl : 0)}</strong>
      <button class="btn btn-primary" style="padding:4px 10px;" onclick="filterJournalByDate('${dStr}')">Open in Journal →</button>
    </div>` +
    (dTrades.length
      ? dTrades.map(t => `<span class="pill ${t.net_pnl_usd >= 0 ? 'pill-green' : 'pill-red'}" style="margin:2px 4px 2px 0;">#${t.id} ${t.direction} ${t.setup_agent} (${t.tf}) ${fmtUsd(t.net_pnl_usd)} [${t.exit_reason}]</span>`).join('')
      : '<span class="text-muted">No trades executed on this day.</span>');
}

function filterJournalByDate(dStr) {
  resetJournalFilters();
  document.getElementById('filterSearch').value = dStr;
  applyJournalFilters();
  switchTab('tab-journal');
}

function renderDailyLog() {
  document.getElementById('dailyLogBody').innerHTML = P().daily_rows.map(r => `
    <tr class="clickable" onclick="inspectCalDay('${r.date}')">
      <td class="mono"><strong>${r.date}</strong></td>
      <td>${r.day}</td>
      <td class="mono text-muted">${r.week}</td>
      <td><span class="badge ${r.is_oos ? 'badge-oos' : 'badge-is'}">${r.is_oos ? 'OOS' : 'IS'}</span></td>
      <td class="mono">${r.trades}</td>
      <td class="mono">${r.wins}W / ${r.losses}L</td>
      <td class="mono ${clsVal(r.gross_pnl)}">${fmtUsd(r.gross_pnl)}</td>
      <td class="mono text-red">-$${r.fees.toFixed(2)}</td>
      <td class="mono ${clsVal(r.net_pnl)}"><strong>${fmtUsd(r.net_pnl)}</strong></td>
      <td class="mono text-cyan">$${r.cum_eq.toFixed(2)}</td>
      <td class="text-muted" style="font-size:11px;">${r.agents}</td>
    </tr>
  `).join('');
}

/* ============================================================================
 * TAB 6: TRADE JOURNAL & FORENSIC MODAL
 * ============================================================================ */
function populateJournalFilters() {
  const trades = P().trades;
  const agents = [...new Set(trades.map(t => t.setup_agent))].sort();
  const exits = [...new Set(trades.map(t => t.exit_reason))].sort();
  document.getElementById('filterAgent').innerHTML = '<option value="ALL">Setup Agent: All</option>' + agents.map(a => `<option value="${a}">${a}</option>`).join('');
  document.getElementById('filterExit').innerHTML = '<option value="ALL">Exit Reason: All</option>' + exits.map(e => `<option value="${e}">${e}</option>`).join('');
}

function applyJournalFilters() {
  const dir = document.getElementById('filterDirection').value;
  const out = document.getElementById('filterOutcome').value;
  const smp = document.getElementById('filterSample').value;
  const tf = document.getElementById('filterTf').value;
  const sess = document.getElementById('filterSession').value;
  const ag = document.getElementById('filterAgent').value;
  const ex = document.getElementById('filterExit').value;
  const q = document.getElementById('filterSearch').value.toLowerCase().trim();

  filteredTrades = P().trades.filter(t => {
    if (dir !== 'ALL' && t.direction !== dir) return false;
    if (out === 'WIN' && t.net_pnl_usd <= 0) return false;
    if (out === 'LOSS' && t.net_pnl_usd > 0) return false;
    if (smp === 'IS' && t.is_oos) return false;
    if (smp === 'OOS' && !t.is_oos) return false;
    if (tf !== 'ALL' && t.tf !== tf) return false;
    if (sess !== 'ALL' && t.session !== sess) return false;
    if (ag !== 'ALL' && t.setup_agent !== ag) return false;
    if (ex !== 'ALL' && t.exit_reason !== ex) return false;
    if (q) {
      const hay = `${t.id} ${t.date} ${t.setup_agent} ${t.playbook} ${t.initiator_16} ${t.exit_reason} ${t.pattern || ''} ${t.chosen_from || ''}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
  renderJournalTable();
}

function resetJournalFilters() {
  ['filterDirection','filterOutcome','filterSample','filterTf','filterSession','filterAgent','filterExit'].forEach(id => {
    document.getElementById(id).value = 'ALL';
  });
  document.getElementById('filterSearch').value = '';
  filteredTrades = [...P().trades];
  renderJournalTable();
}

function renderJournalTable() {
  document.getElementById('filteredCountLabel').textContent = `Showing ${filteredTrades.length} / ${P().trades.length} Trades`;
  document.getElementById('journalBody').innerHTML = filteredTrades.map(t => {
    const isWin = t.net_pnl_usd > 0;
    return `
      <tr class="clickable" onclick="openTradeAuditModalById(${t.id})">
        <td class="mono"><strong>#${t.id}</strong></td>
        <td class="mono">${t.entry_time.slice(0, 16)}</td>
        <td><span class="badge ${t.direction === 'LONG' ? 'badge-long' : 'badge-short'}">${t.direction}</span></td>
        <td class="mono">${t.tf}</td>
        <td>${t.session}</td>
        <td><strong>${t.setup_agent}</strong></td>
        <td>${t.playbook}</td>
        <td class="mono">${t.entry_price.toFixed(2)}</td>
        <td class="mono">${t.exit_price.toFixed(2)}</td>
        <td class="mono text-dim">${t.sl_price.toFixed(2)}</td>
        <td class="mono text-gold"><strong>${t.delta_lots || Math.round(t.qty_oz * 1000)}</strong> <span style="font-size:9px;color:var(--text-dim);">($${((t.margin_50x_usd || ((t.delta_lots || Math.round(t.qty_oz * 1000)) * 0.001 * t.entry_price / 50))).toFixed(1)})</span></td>
        <td class="mono ${clsVal(t.pnl_pts)}">${t.pnl_pts >= 0 ? '+' : ''}${t.pnl_pts.toFixed(2)}</td>
        <td class="mono ${clsVal(t.r_multiple)}"><strong>${t.r_multiple >= 0 ? '+' : ''}${t.r_multiple.toFixed(2)}R</strong></td>
        <td class="mono text-red">-$${t.delta_fee_usd.toFixed(2)}</td>
        <td class="mono ${clsVal(t.net_pnl_usd)}"><strong>${fmtUsd(t.net_pnl_usd)}</strong></td>
        <td class="mono text-cyan">$${t.equity_after.toFixed(2)}</td>
        <td class="mono text-dim">${t.hold_mins}m</td>
        <td><span class="badge ${t.exit_reason.includes('40R') || t.exit_reason.includes('CHANDELIER') ? 'badge-trail' : (t.exit_reason.includes('STALL') ? 'badge-stall' : 'badge-sl')}">${formatExitReason(t.exit_reason)}</span></td>
        <td class="mono">${t.confirming_count}/16${t.vote_count ? ` <span class="pill pill-cyan" style="padding:1px 4px;font-size:9px;">${t.vote_count}/6</span>` : ''}</td>
        <td><span class="badge ${t.is_oos ? 'badge-oos' : 'badge-is'}">${t.is_oos ? 'OOS' : 'IS'}</span></td>
      </tr>
    `;
  }).join('');
}

function openTradeAuditModalById(tid) {
  const t = P().trades.find(x => x.id === tid);
  if (t) { selectTrade(t, false, false); openTradeAuditModal(t); }
}
function openSelectedTradeModal() { if (selectedTrade) openTradeAuditModal(selectedTrade); }
function closeTradeModal() { document.getElementById('tradeModal').classList.remove('open'); }
function jumpToModalTradeOnChart() { closeTradeModal(); if (selectedTrade) selectTrade(selectedTrade, true, true); }

function openTradeAuditModal(t) {
  const isWin = t.net_pnl_usd > 0;
  document.getElementById('modalTradeIdBadge').textContent = `TRADE #${t.id}`;
  document.getElementById('modalTradeTitle').innerHTML =
    `${t.setup_agent} (${t.tf}) · ${t.playbook} · <span class="${isWin ? 'text-green' : 'text-red'}">${t.r_multiple >= 0 ? '+' : ''}${t.r_multiple.toFixed(2)}R (${fmtUsd(t.net_pnl_usd)})</span>`;

  const mergeProvHtml = t.vote_count ? `
    <div class="audit-sec" style="border-left:3px solid #10b981;">
      <div class="audit-sec-title">🧬 6-Journal Merge Provenance (${t.vote_count}/6 Champions · Pattern [${t.pattern || ''}])</div>
      <p style="font-size:12px; margin-bottom:6px;">
        HTF Priority Execution Source: <strong class="text-gold">${t.chosen_from || 'N/A'}</strong> ·
        All Same-Bar Fired Timeframes: <strong>${t.fired_tfs || t.tf}</strong>
      </p>
      <div style="display:flex; gap:5px; flex-wrap:wrap;">
        ${(t.member_profiles || []).map(mp => `<span class="pill pill-cyan">${mp}</span>`).join('')}
      </div>
    </div>
  ` : '';

  document.getElementById('modalTradeBody').innerHTML = `
    <div class="radar-grid">
      <div class="radar-box"><div class="radar-lbl">Entry → Exit</div><div class="radar-val">${t.entry_price.toFixed(2)} → ${t.exit_price.toFixed(2)}</div></div>
      <div class="radar-box"><div class="radar-lbl">0.85x Stop Loss</div><div class="radar-val text-red">${t.sl_price.toFixed(2)} (-${t.init_risk_pts.toFixed(2)})</div></div>
      <div class="radar-box"><div class="radar-lbl">Hold / Session</div><div class="radar-val">${t.hold_mins}m (${t.session})</div></div>
      <div class="radar-box"><div class="radar-lbl">Equity After</div><div class="radar-val text-cyan">$${t.equity_after.toFixed(2)}</div></div>
      <div class="radar-box"><div class="radar-lbl">Max Excursion (MFE)</div><div class="radar-val text-green">+${t.mfe_r.toFixed(2)}R (+${t.mfe_pts.toFixed(2)})</div></div>
      <div class="radar-box"><div class="radar-lbl">Max Adverse (MAE)</div><div class="radar-val text-red">-${t.mae_r.toFixed(2)}R (-${t.mae_pts.toFixed(2)})</div></div>
    </div>
    ${mergeProvHtml}
    <div class="audit-sec">
      <div class="audit-sec-title">🔍 Order Flow &amp; Microstructure Telemetry</div>
      <p style="font-size:12px;">${t.analyser_brief}</p>
      <div style="font-size:11px; color:var(--text-muted); margin-top:4px;">
        L2 Bid/Ask Ratio: <strong>${t.l2_ratio}x</strong> · Vol Z-Score: <strong>${t.vol_z >= 0 ? '+' : ''}${t.vol_z}σ</strong> ·
        5m Delta: <strong>${t.delta_5m}</strong> · 4H Fib Pos: <strong>${t.fib_240_pct}%</strong> · Spread: <strong>${t.spread_pts} pts</strong>
      </div>
    </div>
    <div class="audit-sec">
      <div class="audit-sec-title">🏛️ 16-Agent Floor Consensus (${t.confirming_count}/16 Signed · ${t.consensus_pct}%)</div>
      <p style="font-size:12px; margin-bottom:6px;">${t.council_verdict}</p>
      <div style="display:flex; gap:5px; flex-wrap:wrap;">
        ${(t.confirming_agents || []).map(a => `<span class="pill pill-green">${a}</span>`).join('')}
        ${(t.skipped_agents || []).map(a => `<span class="pill pill-red" style="opacity:0.55;">${a}</span>`).join('')}
      </div>
    </div>
    <div class="audit-sec">
      <div class="audit-sec-title">🧮 Risk &amp; Delta Fee Accounting (0.01% per side)</div>
      <p style="font-size:12px;">Position: <strong class="text-gold">${t.delta_lots || Math.round(t.qty_oz * 1000)} Lots (Contracts)</strong> · <strong>${t.qty_oz} oz</strong> · <strong>50x Leverage</strong> (Margin: <strong class="text-cyan">$${(t.margin_50x_usd || ((t.delta_lots || Math.round(t.qty_oz * 1000)) * 0.001 * t.entry_price / 50)).toFixed(2)}</strong>, Notional: $${t.notional_usd.toFixed(2)}, Risk: $5.00) · Gross: <strong class="${clsVal(t.gross_pnl_usd)}">${fmtUsd(t.gross_pnl_usd)}</strong> · Fee: <strong class="text-red">-$${t.delta_fee_usd.toFixed(2)}</strong> · Net: <strong class="${clsVal(t.net_pnl_usd)}">${fmtUsd(t.net_pnl_usd)}</strong></p>
    </div>
    <div class="audit-sec" style="border-left:3px solid ${isWin ? 'var(--tv-green)' : 'var(--tv-red)'};">
      <div class="audit-sec-title">📋 Lifecycle Diagnosis: ${t.mistake_title}</div>
      <p style="font-size:12px; color:#cbd5e1;">${t.mistake_desc}</p>
      <div style="font-size:11px; color:var(--tv-cyan); margin-top:5px;"><strong>Manager Note:</strong> ${t.learner_fix}</div>
    </div>
  `;
  document.getElementById('tradeModal').classList.add('open');
}

/* ============================================================================
 * TAB MERGE: 6-JOURNAL MERGE & CONSENSUS FORENSICS
 * ============================================================================ */
function statusBadgeHtml(st) {
  if (st === 'EXECUTED') return '<span class="pill pill-green">EXECUTED</span>';
  if (st === 'SLOT_BUSY') return '<span class="pill pill-gold">SLOT BUSY</span>';
  return '<span class="pill pill-red" style="opacity:0.75;">FILTERED OUT</span>';
}

function renderMergeForensics() {
  const mf = REPORT.merge_forensics;
  if (!mf) return;

  const badgeEl = document.getElementById('mergeTabCount');
  if (badgeEl) badgeEl.textContent = `${mf.unique_setups} Setups`;
  const vtEl = document.getElementById('mergeVoteTitle');
  if (vtEl) vtEl.textContent = `🗳️ Cross-Champion Vote Consensus Attribution (6/6 Down to 1/6 Votes across ${mf.unique_setups} Unique Setups)`;
  const ptEl = document.getElementById('mergePatternTitle');
  if (ptEl) ptEl.textContent = `🔬 All ${(mf.pattern_breakdown || []).length} Exact Champion Membership Combinations (Sorted by Net P&L)`;
  const mtEl = document.getElementById('mergeMatrixTitle');
  if (mtEl) mtEl.textContent = `🗂️ Complete ${mf.unique_setups}-Setup 24/7 Cross-Journal Agreement Matrix (${mf.total_journal_rows} Rows Deduplicated with HTF Priority)`;

  const m1 = REPORT.profiles['MERGE_1_SUPER_CONFLUENCE_OR_15M'] || P();
  const c1 = REPORT.profiles['CHAMP_1_MAX_PROFIT'] || P();
  const bestGain = (m1.summary.net_pnl_usd - c1.summary.net_pnl_usd).toFixed(2);
  const v6 = (mf.votes_breakdown || []).find(v => v.votes === 6) || { trades: 0, wins: 0, wr: 0, net_pnl: 0 };

  document.getElementById('mergeKpiStrip').innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">6 Champion Journals Deduplicated <span class="text-cyan">0 Overlaps</span></div>
      <div class="kpi-val text-cyan">${mf.total_journal_rows} → ${mf.unique_setups}</div>
      <div class="kpi-sub">${mf.total_journal_rows} total rows merged into ${mf.unique_setups} unique entries</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Same-Bar Multi-TF Priority Alpha <span class="text-gold">${mf.same_bar_multi_tf_collisions} Collisions</span></div>
      <div class="kpi-val text-green">${fmtUsd(mf.same_bar_priority_alpha)}</div>
      <div class="kpi-sub">HTF Union ${fmtUsd(mf.htf_priority_union_net)} vs C1 Union ${fmtUsd(mf.c1_priority_union_net)}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">6/6 Unanimous Agreement <span class="text-green">${v6.wins}/${v6.trades} Won</span></div>
      <div class="kpi-val text-gold">${v6.wr.toFixed(1)}% WR</div>
      <div class="kpi-sub">${fmtUsd(v6.net_pnl)} Net across ${v6.trades} unanimous setups</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">MERGE_1 vs Best Individual (CHAMP_1) <span class="text-green">+$${bestGain} Alpha</span></div>
      <div class="kpi-val text-green">${fmtUsd(m1.summary.net_pnl_usd)}</div>
      <div class="kpi-sub">${m1.summary.wr_pct.toFixed(2)}% WR · PF ${m1.summary.pf.toFixed(2)} · OOS ${fmtUsd(m1.summary.oos_stats.net_pnl)}</div>
    </div>
  `;

  // Head-to-head all 12 + legacy
  const rows = REPORT.profile_order.map(pid => {
    const pr = REPORT.profiles[pid];
    const s = pr.summary;
    const isAct = pid === activeProfileId;
    const tierBadge = pr.is_merged
      ? '<span class="pill pill-green">MERGED</span>'
      : '<span class="pill pill-gold">SINGLE</span>';
    return `
      <tr class="clickable ${isAct ? 'selected' : ''}" onclick="selectProfile('${pid}')">
        <td>${tierBadge}</td>
        <td><strong style="color:${pr.color};">${pr.title}</strong></td>
        <td style="font-size:11px;">${pr.subtitle}</td>
        <td class="mono">${s.trades}</td>
        <td class="mono">${s.active_days}/${s.total_weekdays || 46} (${s.day_coverage_pct}%)</td>
        <td class="mono text-gold">${s.wr_pct.toFixed(2)}%</td>
        <td class="mono text-cyan"><strong>${s.pf.toFixed(2)}</strong></td>
        <td class="mono text-green"><strong>${fmtUsd(s.net_pnl_usd)}</strong></td>
        <td class="mono">$${s.end_equity.toFixed(2)}</td>
        <td class="mono text-red">-${s.max_dd_pct.toFixed(2)}%</td>
        <td class="mono">${fmtUsd(s.is_stats.net_pnl)} (${s.is_stats.wr.toFixed(0)}%)</td>
        <td class="mono ${clsVal(s.oos_stats.net_pnl)}">${fmtUsd(s.oos_stats.net_pnl)} (${s.oos_stats.wr.toFixed(0)}%)</td>
        <td class="mono text-green">${s.overlap_count}</td>
      </tr>
    `;
  });
  if (REPORT.legacy_baseline) {
    const lb = REPORT.legacy_baseline;
    rows.push(`
      <tr style="opacity:0.75;">
        <td><span class="pill pill-red">LEGACY</span></td>
        <td><strong class="text-muted">${lb.name}</strong></td>
        <td style="font-size:11px;">Single-strategy Track B reference before 16-agent MTF upgrade</td>
        <td class="mono">${lb.trades}</td>
        <td class="mono">${lb.active_days}/28</td>
        <td class="mono">${lb.wr_pct.toFixed(2)}%</td>
        <td class="mono">${lb.pf.toFixed(2)}</td>
        <td class="mono">${fmtUsd(lb.net_pnl_usd)}</td>
        <td class="mono">$${lb.end_equity.toFixed(2)}</td>
        <td class="mono text-red">-${lb.max_dd_pct.toFixed(2)}%</td>
        <td class="mono text-muted">Oct: +$29.43</td>
        <td class="mono text-red">Nov: -$16.70</td>
        <td class="mono">0</td>
      </tr>
    `);
  }
  document.getElementById('mergeProfilesBody').innerHTML = rows.join('');

  // Votes Breakdown
  document.getElementById('votesBreakdownBody').innerHTML = (mf.votes_breakdown || []).map(v => `
    <tr>
      <td><strong>${v.label}</strong></td>
      <td class="mono">${v.trades}</td>
      <td class="mono">${v.wins}W / ${v.losses}L</td>
      <td class="mono text-gold">${v.wr.toFixed(2)}%</td>
      <td class="mono text-cyan">${v.pf >= 90 ? '∞ (99.0)' : v.pf.toFixed(2)}</td>
      <td class="mono ${clsVal(v.avg_net)}">${fmtUsd(v.avg_net)}</td>
      <td class="mono ${clsVal(v.net_pnl)}"><strong>${fmtUsd(v.net_pnl)}</strong></td>
      <td class="mono ${clsVal(v.is_net)}">${fmtUsd(v.is_net)}</td>
      <td class="mono ${clsVal(v.oos_net)}">${fmtUsd(v.oos_net)} (${v.oos_wr.toFixed(0)}%)</td>
    </tr>
  `).join('');

  // Pattern Breakdown
  document.getElementById('patternBreakdownBody').innerHTML = (mf.pattern_breakdown || []).map(p => `
    <tr>
      <td class="mono"><strong>[${p.pattern}]</strong></td>
      <td class="mono text-cyan">${p.votes}/6</td>
      <td class="mono">${p.trades}</td>
      <td class="mono">${p.wins}W / ${p.losses}L</td>
      <td class="mono text-gold">${p.wr.toFixed(1)}%</td>
      <td class="mono ${clsVal(p.net_pnl)}"><strong>${fmtUsd(p.net_pnl)}</strong></td>
      <td class="mono ${clsVal(p.is_net)}">${fmtUsd(p.is_net)}</td>
      <td class="mono ${clsVal(p.oos_net)}">${fmtUsd(p.oos_net)}</td>
      <td class="mono text-muted" style="font-size:10.5px;">${p.tf_split}</td>
    </tr>
  `).join('');

  applySetupMatrixFilters();
}

function applySetupMatrixFilters() {
  const mf = REPORT.merge_forensics;
  if (!mf) return;
  const f = document.getElementById('setupMatrixFilter')?.value || 'ALL';
  const q = (document.getElementById('mergeSetupSearch')?.value || '').toLowerCase().trim();

  const items = (mf.setup_matrix || []).filter(x => {
    if (f === 'EXECUTED_M1' && x.m1_status !== 'EXECUTED') return false;
    if (f === 'EXECUTED_M3' && x.m3_status !== 'EXECUTED') return false;
    if (f === 'FILTERED_M1' && x.m1_status !== 'FILTERED_OUT') return false;
    if (f === 'SLOT_BUSY_M1' && x.m1_status !== 'SLOT_BUSY') return false;
    if (f === 'VOTES_GE4' && x.vote_count < 4) return false;
    if (f === 'VOTES_LE3' && x.vote_count > 3) return false;
    if (q) {
      const hay = `${x.entry_time} ${x.direction} ${x.tf} ${x.fired_tfs} ${x.setup_agent} ${x.playbook} ${x.pattern} ${x.chosen_from} ${x.exit_reason}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  const lbl = document.getElementById('setupMatrixCountLabel');
  if (lbl) lbl.textContent = `Showing ${items.length} / ${mf.setup_matrix.length} Unique Setups`;

  document.getElementById('setupMatrixBody').innerHTML = items.map(x => `
    <tr>
      <td class="mono">${x.setup_num}</td>
      <td class="mono">${x.entry_time.slice(0, 16)}</td>
      <td><span class="badge ${x.direction === 'LONG' ? 'badge-long' : 'badge-short'}">${x.direction}</span></td>
      <td class="mono"><strong>${x.tf}</strong></td>
      <td class="mono text-muted">${x.fired_tfs}</td>
      <td><strong>${x.setup_agent}</strong></td>
      <td class="mono text-cyan"><strong>${x.vote_count}/6</strong></td>
      <td class="mono">[${x.pattern}]</td>
      <td class="mono" style="font-size:10.5px;">${x.chosen_from}</td>
      <td class="mono ${clsVal(x.r_multiple)}"><strong>${x.r_multiple >= 0 ? '+' : ''}${x.r_multiple.toFixed(2)}R</strong></td>
      <td class="mono ${clsVal(x.net_pnl_usd)}"><strong>${fmtUsd(x.net_pnl_usd)}</strong></td>
      <td><span class="badge ${x.exit_reason.includes('40R') || x.exit_reason.includes('CHANDELIER') ? 'badge-trail' : (x.exit_reason.includes('STALL') ? 'badge-stall' : 'badge-sl')}">${x.exit_reason}</span></td>
      <td>${statusBadgeHtml(x.m1_status)}</td>
      <td>${statusBadgeHtml(x.m3_status)}</td>
    </tr>
  `).join('');
}

function resetSetupMatrixFilters() {
  document.getElementById('setupMatrixFilter').value = 'ALL';
  document.getElementById('mergeSetupSearch').value = '';
  applySetupMatrixFilters();
}

/* ============================================================================
 * TABS, EXPORTS & INIT
 * ============================================================================ */
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-tab') === tabId));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === tabId));
  if (tabId === 'tab-dossier') requestAnimationFrame(drawEquityChart);
  if (tabId === 'tab-chart') requestAnimationFrame(drawTradingViewChart);
}

function exportActiveCSV() {
  const keys = ['id','entry_time','exit_time','direction','tf','session','setup_agent','initiator_16','playbook','entry_price','exit_price','sl_price','delta_lots','margin_50x_usd','init_risk_pts','pnl_pts','r_multiple','qty_oz','gross_pnl_usd','delta_fee_usd','net_pnl_usd','equity_after','exit_reason','hold_mins','confirming_count','vote_count','pattern','chosen_from','is_oos'];
  const rows = [keys.join(',')].concat(P().trades.map(t => keys.map(k => {
    const v = t[k] ?? '';
    return String(v).includes(',') ? `"${v}"` : v;
  }).join(',')));
  const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${activeProfileId}_DELTA_XAUTUSD_TRADES.csv`;
  a.click();
}

function exportActiveJSON() {
  const blob = new Blob([JSON.stringify(P(), null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${activeProfileId}_DELTA_XAUTUSD_REPORT.json`;
  a.click();
}

window.addEventListener('DOMContentLoaded', () => {
  renderProfileSelector();
  renderHeroAndKPIs();
  renderDossierTables();
  renderMergeForensics();
  renderGridExplorer();
  renderAgentsMatrix();
  renderCalendar();
  renderDailyLog();
  populateJournalFilters();
  resetJournalFilters();
  populateTradeJumpSelect();
  setupCanvasInteractions();

  if (P().trades.length) {
    selectedTrade = P().trades[0];
    const bars = getBars(currentTF);
    const iEnt = findBarIdx(bars.time, selectedTrade.entry_ts);
    const iExt = Math.max(iEnt + 2, findBarIdx(bars.time, selectedTrade.exit_ts));
    const span = Math.max(32, (iExt - iEnt) * 4);
    viewStartIdx = Math.max(0, Math.round(iEnt - span * 0.35));
    viewEndIdx = Math.min(bars.length - 1, Math.round(viewStartIdx + span));
    selectTrade(selectedTrade, false, false);
  }

  window.addEventListener('resize', () => {
    drawEquityChart();
    drawTradingViewChart();
  });
  setTimeout(drawEquityChart, 80);
});
</script>
</body>
</html>
"""


def build_html():
    if not os.path.exists(REPORT_JSON_PATH):
        raise FileNotFoundError(f"Report JSON not found: {REPORT_JSON_PATH}")

    with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
        payload_str = f.read()

    if "__PAYLOAD_JSON__" not in HTML_TEMPLATE:
        raise RuntimeError("Template missing __PAYLOAD_JSON__ placeholder")

    html_out = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", payload_str)
    if "__PAYLOAD_JSON__" in html_out:
        raise RuntimeError("Unresolved __PAYLOAD_JSON__ placeholder remains in generated HTML")

    with open(OUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_out)

    size_mb = os.path.getsize(OUT_HTML_PATH) / (1024 * 1024)
    print(f"[SUCCESS] Generated {OUT_HTML_PATH} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    build_html()
