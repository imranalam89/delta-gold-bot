"""
Renders the standalone `backtest_dashboard.html` file from `data/processed/dashboard_payload.json`.
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
<title>Syndicate Alpha — 16-Agent Institutional Gold Backtest, TradingView Chart & Self-Learner Terminal</title>
<style>
  :root {
    --bg-main: #090b10;
    --bg-panel: #11151f;
    --bg-card: #161b28;
    --bg-tv: #0f1219;
    --border: #232a3b;
    --text-main: #e2e8f0;
    --text-muted: #8b9bb4;
    --tv-green: #26a69a;
    --tv-red: #ef5350;
    --tv-blue: #3b82f6;
    --tv-cyan: #38bdf8;
    --gold: #f59e0b;
    --purple: #a855f7;
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
    padding: 14px 22px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
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
    font-weight: 700;
    color: #f8fafc;
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
  .container {
    max-width: 1760px;
    margin: 0 auto;
    padding: 16px 20px 60px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  /* KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(195px, 1fr));
    gap: 12px;
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

  /* Main Split: TradingView Chart + Forensic Trade Inspector */
  .tv-workspace {
    display: grid;
    grid-template-columns: 1.55fr 1fr;
    gap: 16px;
    align-items: stretch;
  }
  @media (max-width: 1250px) {
    .tv-workspace { grid-template-columns: 1fr; }
  }
  .panel {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
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
    height: 550px;
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

  /* Forensic Trade Inspector Panel */
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
  .agent-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }
  .agent-pill {
    font-size: 10.5px;
    padding: 2px 7px;
    border-radius: 4px;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #7dd3fc;
    font-weight: 600;
  }

  /* Calendar & Equity Row */
  .mid-grid {
    display: grid;
    grid-template-columns: 1.25fr 1fr;
    gap: 16px;
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

  /* 3-Column Analytics: Session, Day of Week, Seasonality */
  .analytics-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
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

  /* Self-Learner Meta-Coach Section */
  .learner-grid {
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    gap: 16px;
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
</style>
</head>
<body>

<header class="top-header">
  <div class="brand-title">
    <span class="brand-badge">SYNDICATE ALPHA · 16 AGENTS + SELF-LEARNER</span>
    <div>
      <h1>Institutional Gold (`GC.v.0`) Backtest Forensics, TradingView Chart & Daily P&L Calendar</h1>
      <div class="brand-sub">Google Drive 2-Year Dataset (699,702 1m Bars · 149,941 L2 MBP-10 Bars) · $100.00 Account · $5.00 Risk/Trade · Delta Exchange 0.01% Fee</div>
    </div>
  </div>
  <div class="controls-row">
    <label for="profileSelect" style="color:var(--text-muted);font-weight:600;">Strategy / Setting Profile:</label>
    <select id="profileSelect"></select>
    <button id="clearFiltersBtn">Reset All Filters</button>
  </div>
</header>

<div class="container">
  <!-- KPI Summary Strip -->
  <div class="kpi-grid" id="kpiGrid"></div>

  <!-- TradingView Chart + Per-Trade Forensic Journal -->
  <div class="tv-workspace">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <span style="color:var(--gold);">●</span>
          <span id="tvHeaderTitle">Gold Futures (GC.v.0) — Continuous Multi-Month TradingView Chart (All Trades &amp; #IDs)</span>
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
          <select id="fiveMonthWindowSelect" title="Select 5-Month Chart Window (or pan freely across all months with mouse)">
            <option value="2026-06_2026-10">5M Window: Jun 2026 – Oct 2026 (L2 MBP-10)</option>
            <option value="2026-01_2026-05" selected>5M Window: Jan 2026 – May 2026 (40 Trades)</option>
            <option value="2025-08_2025-12">5M Window: Aug 2025 – Dec 2025 (34 Trades)</option>
            <option value="2025-04_2025-08">5M Window: Apr 2025 – Aug 2025 (40 Trades)</option>
            <option value="2024-11_2025-03">5M Window: Nov 2024 – Mar 2025 (27 Trades)</option>
            <option value="ALL_24M">Full 24-Month Continuous Chart (All 150 Trades)</option>
          </select>
          <button id="fit5MonthBtn" class="active-btn">📅 Full 5-Month Chart</button>
          <button id="zoomTradeBtn">🔍 Zoom to Trade #</button>
          <button id="prevTradeBtn">◄ Prev</button>
          <select id="tradeJumpSelect" style="max-width:210px;"></select>
          <button id="nextTradeBtn">Next ►</button>
        </div>
      </div>
      <div class="tv-canvas-wrap" style="height:540px;">
        <canvas id="tvChart"></canvas>
      </div>
      <div style="background:#0b0e15;border-top:1px solid var(--border);padding:4px 10px 2px;height:62px;position:relative;user-select:none;">
        <div style="font-size:10px;color:var(--text-muted);display:flex;justify-content:space-between;margin-bottom:2px;">
          <span>🧭 <strong>Continuous Multi-Month Timeline Navigator</strong> — Drag Blue Box or Click Anywhere to Move Across Months · Green/Red Pins = All Trades (#1–#150)</span>
          <span id="visibleRangeSummary" style="color:var(--tv-cyan);font-weight:700;"></span>
        </div>
        <canvas id="tvNavChart" style="width:100%;height:38px;display:block;cursor:ew-resize;"></canvas>
      </div>
      <div class="tv-legend-bar">
        <div style="display:flex;gap:14px;flex-wrap:wrap;">
          <span class="legend-item"><span class="swatch" style="background:rgba(38,166,154,0.45);border:1px solid #26a69a;"></span>TP Target Zone (`TP HIT`)</span>
          <span class="legend-item"><span class="swatch" style="background:rgba(239,83,80,0.45);border:1px solid #ef5350;"></span>Stop Loss Zone (`SL HIT`)</span>
          <span class="legend-item"><span class="swatch" style="background:#3b82f6;"></span>`◄── TRAILING SL` (RYAN Phase 2 / Phase 4 Lock)</span>
          <span class="legend-item"><span class="swatch" style="background:#f59e0b;"></span>Trade `#ID` Badge (Click to Inspect · Double-Click to Zoom)</span>
        </div>
        <div>Mouse Drag: Pan Across Months · Scroll Wheel: Zoom In/Out · Click Any `#Trade` Badge on Chart to Read Journal</div>
      </div>
    </div>

    <!-- Right Column: Forensic Trade Card & Self-Learner Diagnosis -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <span style="color:var(--tv-cyan);">◆</span>
          <span>Per-Trade Forensic Journal & Self-Learner Post-Mortem</span>
        </div>
        <span id="inspectorBadge" class="badge badge-tp">TP HIT</span>
      </div>
      <div class="inspector-body" id="inspectorBody"></div>
    </div>
  </div>

  <!-- Monthly / Daily PnL Calendar + Equity & Drawdown Curve -->
  <div class="mid-grid">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <span style="color:var(--tv-green);">■</span>
          <span>Daily P&L Calendar Heatmap (Click Any Day to Filter Trades & Chart)</span>
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
          <span>$100 Account Equity Curve & Drawdown % Trajectory (Net of 0.01% Delta Exchange Fee)</span>
        </div>
        <span id="equityHeaderStat" style="font-size:12px;color:var(--tv-green);font-weight:700;"></span>
      </div>
      <div style="padding:12px;height:360px;position:relative;">
        <canvas id="equityCanvas" style="width:100%;height:100%;display:block;"></canvas>
      </div>
    </div>
  </div>

  <!-- Time, Session, Weekday & Seasonality Analytics -->
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
        <div class="panel-title"><span>🌦️ Seasonality & Setup Agent Breakdown</span></div>
      </div>
      <table class="stat-table" id="seasonTable"></table>
    </div>
  </div>

  <!-- Agent #17 Self-Learner Meta-Coach & 16-Agent Reliability Matrix -->
  <div class="learner-grid">
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <span style="color:var(--purple);">🧠 Agent #17 (ORACLE Self-Learner) — Mistake Audit & Directives for the 16 Agents</span>
        </div>
      </div>
      <div style="padding:14px;" id="selfLearnerPanel"></div>
    </div>

    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">
          <span style="color:var(--gold);">🛡️ 16-Agent Cross-Confirmation Accuracy & Mistake Distribution</span>
        </div>
      </div>
      <div class="table-scroll">
        <table class="stat-table" id="agentMatrixTable"></table>
      </div>
    </div>
  </div>

  <!-- Full Interactive Trade Journal Table -->
  <div class="panel">
    <div class="panel-header">
      <div class="panel-title">
        <span>📜 Complete Institutional Trade Journal (Click Any Trade to Load TradingView Replay)</span>
      </div>
      <div class="controls-row">
        <select id="filterAgent"><option value="ALL">All Lead Agents</option></select>
        <select id="filterDir">
          <option value="ALL">Long & Short</option>
          <option value="LONG">LONG Only</option>
          <option value="SHORT">SHORT Only</option>
        </select>
        <select id="filterOutcome">
          <option value="ALL">All Outcomes</option>
          <option value="TP">TP2 Full Runner Hit</option>
          <option value="TRAIL">Trailing SL Hit (Phase 2 / Phase 4)</option>
          <option value="REV">⚡ Reversal Exit (70%+ Agents Flip)</option>
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
            <th>#</th>
            <th>Entry Time (UTC)</th>
            <th>Day / Session</th>
            <th>Lead Agent & Setup</th>
            <th>Dir</th>
            <th>Entry → Exit</th>
            <th>SL / TP1 / TP2</th>
            <th>MFE / MAE (R)</th>
            <th>Post-Exit 60m</th>
            <th>Agents</th>
            <th>Gross / Fee / Net ($)</th>
            <th>Equity</th>
            <th>Exit Banner & Diagnosis</th>
          </tr>
        </thead>
        <tbody id="tradeTableBody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const PAYLOAD = __PAYLOAD_JSON__;

let currentProfileKey = "3_SNIPER_HIGH_RR_RUNNER";
if (!PAYLOAD.profiles[currentProfileKey]) {
  currentProfileKey = Object.keys(PAYLOAD.profiles)[0];
}
let currentTF = 5; // default 5m chart like user's TradingView screenshots
let filteredTrades = [];
let selectedTrade = null;
let hoveredTrade = null;
let selectedCalendarDate = null;
let currentMonthIdx = 0;
let availableMonths = [];

// Continuous multi-month candle cache by timeframe (minutes -> { length, time, open, high, low, close, vol })
const TF_CACHE = {};
let viewStartIdx = 0;
let viewEndIdx = 1000;
let isDragging = false;
let isNavDragging = false;
let dragStartX = 0;
let dragMovedPx = 0;
let hoverMouse = null;
let tradeHitBoxes = []; // Clickable trade badges & position boxes on the chart

function b64ToBytes(b64) {
  const bin = atob(b64);
  const len = bin.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

function unpackContinuous1m() {
  if (TF_CACHE[1]) return TF_CACHE[1];
  const c = PAYLOAD.continuous_1m;
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
  for (let i = 0; i < n; i++) {
    if (i > 0) {
      curMin += dt[i];
      curOpenD += doArr[i];
    }
    time[i] = curMin * 60;
    const o = curOpenD * 0.1;
    open[i] = o;
    high[i] = (curOpenD + dh[i]) * 0.1;
    low[i] = (curOpenD - dl[i]) * 0.1;
    close[i] = (curOpenD + dc[i]) * 0.1;
    vol[i] = v[i];
  }
  TF_CACHE[1] = { length: n, time, open, high, low, close, vol };
  return TF_CACHE[1];
}

function getContinuousBars(tfMins) {
  if (TF_CACHE[tfMins]) return TF_CACHE[tfMins];
  const raw = unpackContinuous1m();
  if (tfMins === 1) return raw;

  const bucketSec = tfMins * 60;
  const n = raw.length;
  // First pass: count buckets
  let count = 0;
  let prevB = -1;
  for (let i = 0; i < n; i++) {
    const b = Math.floor(raw.time[i] / bucketSec) * bucketSec;
    if (b !== prevB) {
      count++;
      prevB = b;
    }
  }

  const time = new Int32Array(count);
  const open = new Float32Array(count);
  const high = new Float32Array(count);
  const low = new Float32Array(count);
  const close = new Float32Array(count);
  const vol = new Int32Array(count);

  let k = -1;
  prevB = -1;
  for (let i = 0; i < n; i++) {
    const b = Math.floor(raw.time[i] / bucketSec) * bucketSec;
    if (b !== prevB) {
      k++;
      prevB = b;
      time[k] = b;
      open[k] = raw.open[i];
      high[k] = raw.high[i];
      low[k] = raw.low[i];
      close[k] = raw.close[i];
      vol[k] = raw.vol[i];
    } else {
      if (raw.high[i] > high[k]) high[k] = raw.high[i];
      if (raw.low[i] < low[k]) low[k] = raw.low[i];
      close[k] = raw.close[i];
      vol[k] += raw.vol[i];
    }
  }

  TF_CACHE[tfMins] = { length: count, time, open, high, low, close, vol };
  return TF_CACHE[tfMins];
}

// Fast O(log N) binary search for timestamp in sorted Int32Array
function findBarIdx(timeArr, targetSec) {
  let lo = 0, hi = timeArr.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (timeArr[mid] < targetSec) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function initDashboard() {
  unpackContinuous1m();

  // Automatically default to the highest Net PnL profile
  let bestKey = currentProfileKey;
  let bestNet = -Infinity;
  Object.keys(PAYLOAD.profiles).forEach(k => {
    const net = PAYLOAD.profiles[k].trades.reduce((s, t) => s + t.net_pnl_usd, 0);
    if (net > bestNet) {
      bestNet = net;
      bestKey = k;
    }
  });
  currentProfileKey = bestKey;

  const profSelect = document.getElementById("profileSelect");
  profSelect.innerHTML = "";
  Object.keys(PAYLOAD.profiles).forEach(k => {
    const p = PAYLOAD.profiles[k];
    const net = p.trades.reduce((s, t) => s + t.net_pnl_usd, 0);
    const opt = document.createElement("option");
    opt.value = k;
    opt.textContent = `${k} — ${p.meta.label} (${p.trades.length} Trades | Net: +$${net.toFixed(2)})`;
    if (k === currentProfileKey) opt.selected = true;
    profSelect.appendChild(opt);
  });

  profSelect.addEventListener("change", () => {
    currentProfileKey = profSelect.value;
    selectedCalendarDate = null;
    populateFilterDropdowns();
    applyFilters(false);
  });

  document.getElementById("clearFiltersBtn").addEventListener("click", () => {
    selectedCalendarDate = null;
    document.getElementById("filterAgent").value = "ALL";
    document.getElementById("filterDir").value = "ALL";
    document.getElementById("filterOutcome").value = "ALL";
    document.getElementById("filterMistake").value = "ALL";
    applyFilters(false);
    fitFiveMonthWindow();
  });

  ["filterAgent", "filterDir", "filterOutcome", "filterMistake"].forEach(id => {
    document.getElementById(id).addEventListener("change", () => applyFilters(false));
  });

  document.querySelectorAll(".tf-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      // Preserve current visible start/end UTC timestamps when switching timeframe
      const oldBars = getContinuousBars(currentTF);
      const sSec = oldBars.time[Math.max(0, Math.min(oldBars.length - 1, Math.floor(viewStartIdx)))];
      const eSec = oldBars.time[Math.max(0, Math.min(oldBars.length - 1, Math.ceil(viewEndIdx)))];

      document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentTF = parseInt(btn.getAttribute("data-tf"), 10);

      const newBars = getContinuousBars(currentTF);
      viewStartIdx = findBarIdx(newBars.time, sSec);
      viewEndIdx = Math.max(viewStartIdx + 20, findBarIdx(newBars.time, eSec));
      drawTradingViewChart();
    });
  });

  document.getElementById("fiveMonthWindowSelect").addEventListener("change", () => {
    fitFiveMonthWindow();
  });

  document.getElementById("fit5MonthBtn").addEventListener("click", () => {
    document.getElementById("fit5MonthBtn").classList.add("active-btn");
    document.getElementById("zoomTradeBtn").classList.remove("active-btn");
    fitFiveMonthWindow();
  });

  document.getElementById("zoomTradeBtn").addEventListener("click", () => {
    document.getElementById("zoomTradeBtn").classList.add("active-btn");
    document.getElementById("fit5MonthBtn").classList.remove("active-btn");
    zoomToSelectedTrade();
  });

  document.getElementById("prevTradeBtn").addEventListener("click", () => stepTrade(-1));
  document.getElementById("nextTradeBtn").addEventListener("click", () => stepTrade(1));
  document.getElementById("tradeJumpSelect").addEventListener("change", e => {
    const id = parseInt(e.target.value, 10);
    const t = filteredTrades.find(x => x.id === id);
    if (t) selectTrade(t, false, true);
  });

  document.getElementById("prevMonthBtn").addEventListener("click", () => {
    if (currentMonthIdx > 0) {
      currentMonthIdx--;
      document.getElementById("monthSelect").value = availableMonths[currentMonthIdx];
      renderCalendar();
    }
  });
  document.getElementById("nextMonthBtn").addEventListener("click", () => {
    if (currentMonthIdx < availableMonths.length - 1) {
      currentMonthIdx++;
      document.getElementById("monthSelect").value = availableMonths[currentMonthIdx];
      renderCalendar();
    }
  });
  document.getElementById("monthSelect").addEventListener("change", e => {
    currentMonthIdx = availableMonths.indexOf(e.target.value);
    renderCalendar();
  });

  setupCanvasInteractions();
  populateFilterDropdowns();
  applyFilters(true);
  window.addEventListener("resize", () => {
    drawTradingViewChart();
    drawEquityChart();
  });
}

function fitFiveMonthWindow() {
  const val = document.getElementById("fiveMonthWindowSelect").value;
  const bars = getContinuousBars(currentTF);
  if (!bars.length) return;

  if (val === "ALL_24M") {
    viewStartIdx = 0;
    viewEndIdx = bars.length - 1;
  } else {
    const [mStart, mEnd] = val.split("_");
    const [ys, ms] = mStart.split("-").map(Number);
    const [ye, me] = mEnd.split("-").map(Number);
    const startSec = Date.UTC(ys, ms - 1, 1, 0, 0, 0) / 1000;
    const endSec = Date.UTC(ye, me, 0, 23, 59, 59) / 1000;
    viewStartIdx = findBarIdx(bars.time, startSec);
    viewEndIdx = Math.max(viewStartIdx + 50, findBarIdx(bars.time, endSec));
  }

  // Pick the first trade inside this 5-month window so the right-hand forensic journal matches
  const sSec = bars.time[Math.floor(viewStartIdx)];
  const eSec = bars.time[Math.min(bars.length - 1, Math.ceil(viewEndIdx))];
  const inWin = filteredTrades.find(t => t.entry_ts >= sSec && t.entry_ts <= eSec);
  if (inWin) {
    selectedTrade = inWin;
    document.getElementById("tradeJumpSelect").value = String(inWin.id);
    renderTradeInspector(inWin);
  }
  drawTradingViewChart();
}

function zoomToSelectedTrade() {
  if (!selectedTrade) return;
  const bars = getContinuousBars(currentTF);
  const bucketSec = currentTF * 60;
  const entBucket = Math.floor(selectedTrade.entry_ts / bucketSec) * bucketSec;
  const extBucket = Math.floor(selectedTrade.exit_ts / bucketSec) * bucketSec;
  const iEnt = findBarIdx(bars.time, entBucket);
  const iExt = Math.max(iEnt + 2, findBarIdx(bars.time, extBucket));
  const holdBars = Math.max(8, iExt - iEnt);
  const padL = Math.max(24, Math.round(holdBars * 1.6));
  const padR = Math.max(24, Math.round(holdBars * 1.4));
  viewStartIdx = Math.max(0, iEnt - padL);
  viewEndIdx = Math.min(bars.length - 1, Math.max(iExt + padR, viewStartIdx + 50));
  drawTradingViewChart();
}

function ensureTradeInViewport(trade) {
  const bars = getContinuousBars(currentTF);
  const iEnt = findBarIdx(bars.time, trade.entry_ts);
  const span = viewEndIdx - viewStartIdx;
  if (iEnt < viewStartIdx + span * 0.05 || iEnt > viewEndIdx - span * 0.05) {
    viewStartIdx = Math.max(0, Math.round(iEnt - span * 0.45));
    viewEndIdx = Math.min(bars.length - 1, Math.round(viewStartIdx + span));
  }
}

function populateFilterDropdowns() {
  const trades = PAYLOAD.profiles[currentProfileKey].trades;
  const agents = [...new Set(trades.map(t => t.setup_agent))];
  const mistakes = [...new Set(trades.map(t => t.mistake_code))];

  const agSel = document.getElementById("filterAgent");
  agSel.innerHTML = `<option value="ALL">All Lead Agents</option>` +
    agents.map(a => `<option value="${a}">${a}</option>`).join("");

  const mSel = document.getElementById("filterMistake");
  mSel.innerHTML = `<option value="ALL">All Journal Diagnoses</option>` +
    mistakes.map(m => `<option value="${m}">${m}</option>`).join("");

  availableMonths = [...new Set(trades.map(t => t.month))].sort();
  currentMonthIdx = Math.max(0, availableMonths.length - 1);
  const moSel = document.getElementById("monthSelect");
  moSel.innerHTML = availableMonths.map(m => `<option value="${m}">${m}</option>`).join("");
  if (availableMonths.length) moSel.value = availableMonths[currentMonthIdx];
}

function applyFilters(initialLoad = false) {
  const allTrades = PAYLOAD.profiles[currentProfileKey].trades;
  const fAg = document.getElementById("filterAgent").value;
  const fDir = document.getElementById("filterDir").value;
  const fOut = document.getElementById("filterOutcome").value;
  const fMis = document.getElementById("filterMistake").value;

  filteredTrades = allTrades.filter(t => {
    if (selectedCalendarDate && t.date !== selectedCalendarDate) return false;
    if (fAg !== "ALL" && t.setup_agent !== fAg) return false;
    if (fDir !== "ALL" && t.direction !== fDir) return false;
    if (fMis !== "ALL" && t.mistake_code !== fMis) return false;
    if (fOut !== "ALL") {
      if (fOut === "TP" && !t.exit_reason.includes("TP2")) return false;
      if (fOut === "TRAIL" && !t.exit_reason.includes("TRAIL_STOP")) return false;
      if (fOut === "REV" && !t.exit_reason.includes("REVERSAL_EXIT")) return false;
      if (fOut === "SL" && t.exit_reason !== "STOP_LOSS") return false;
      if (fOut === "TIME" && !t.exit_reason.includes("TIME_EXIT")) return false;
    }
    return true;
  });

  renderKPIs(allTrades);
  renderCalendar();
  drawEquityChart();
  renderAnalyticsTables(allTrades);
  renderSelfLearner(allTrades);
  renderTradeTable();

  const jumpSel = document.getElementById("tradeJumpSelect");
  jumpSel.innerHTML = filteredTrades.map(t =>
    `<option value="${t.id}">#${t.id} · ${t.date} · ${t.direction} (${t.net_pnl_usd >= 0 ? '+' : ''}$${t.net_pnl_usd.toFixed(2)})</option>`
  ).join("");

  if (initialLoad) {
    fitFiveMonthWindow();
  } else if (filteredTrades.length > 0) {
    selectTrade(filteredTrades[0], false, selectedCalendarDate !== null);
  } else {
    drawTradingViewChart();
  }
}

function renderKPIs(trades) {
  const n = trades.length;
  const wins = trades.filter(t => t.net_pnl_usd > 0);
  const losses = trades.filter(t => t.net_pnl_usd <= 0);
  const wr = n ? (wins.length / n * 100) : 0;
  const grossPnl = trades.reduce((s, t) => s + t.gross_pnl_usd, 0);
  const fees = trades.reduce((s, t) => s + t.delta_fee_usd, 0);
  const netPnl = trades.reduce((s, t) => s + t.net_pnl_usd, 0);
  const winSum = wins.reduce((s, t) => s + t.net_pnl_usd, 0);
  const lossSum = Math.abs(losses.reduce((s, t) => s + t.net_pnl_usd, 0));
  const pf = lossSum > 0 ? (winSum / lossSum) : winSum;
  const avgR = n ? trades.reduce((s, t) => s + t.r_multiple, 0) / n : 0;
  const endEq = 100.0 + netPnl;

  let peak = 100.0, maxDDPct = 0, maxDDUsd = 0, curEq = 100.0;
  trades.forEach(t => {
    curEq = t.equity_after;
    if (curEq > peak) peak = curEq;
    const ddUsd = curEq - peak;
    const ddPct = (ddUsd / peak) * 100.0;
    if (ddPct < maxDDPct) maxDDPct = ddPct;
    if (ddUsd < maxDDUsd) maxDDUsd = ddUsd;
  });

  const givebacks = losses.filter(t => t.mfe_r >= 0.80).length;
  const whipsaws = losses.filter(t => t.hold_mins <= 18 && t.post_60m_r >= 1.15).length;

  document.getElementById("kpiGrid").innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Account Growth ($100 Start)</div>
      <div class="kpi-val ${netPnl >= 0 ? 'pos' : 'neg'}">$${endEq.toFixed(2)} (${netPnl >= 0 ? '+' : ''}${netPnl.toFixed(2)}%)</div>
      <div class="kpi-sub">Fixed $5.00 Risk / Trade · CME GC.v.0</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Net Profit (After 0.01% Fee)</div>
      <div class="kpi-val ${netPnl >= 0 ? 'pos' : 'neg'}">${netPnl >= 0 ? '+' : ''}$${netPnl.toFixed(2)}</div>
      <div class="kpi-sub">Gross: +$${grossPnl.toFixed(2)} · Delta Fee: -$${fees.toFixed(2)}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Win Rate & Trade Count</div>
      <div class="kpi-val blue">${wr.toFixed(2)}%</div>
      <div class="kpi-sub">${n} Total Trades (${wins.length} W / ${losses.length} L)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Net Profit Factor & Avg R</div>
      <div class="kpi-val ${pf >= 1.15 ? 'pos' : 'gold'}">${pf.toFixed(2)} PF</div>
      <div class="kpi-sub">Avg R-Multiple: ${avgR >= 0 ? '+' : ''}${avgR.toFixed(2)} R / trade</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Max Equity Drawdown</div>
      <div class="kpi-val neg">${maxDDPct.toFixed(2)}%</div>
      <div class="kpi-sub">Max Peak-to-Valley: $${maxDDUsd.toFixed(2)}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">RYAN Lifecycle Efficiency</div>
      <div class="kpi-val pos">${trades.filter(t => t.exit_reason.includes('TRAIL') || t.exit_reason.includes('TP2')).length} Runners</div>
      <div class="kpi-sub">TP2 Hits: ${trades.filter(t => t.exit_reason.includes('TP2')).length} · Trail Locks: ${trades.filter(t => t.exit_reason.includes('TRAIL')).length}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Self-Learner Recoverable SL</div>
      <div class="kpi-val gold">${givebacks + whipsaws} Trades</div>
      <div class="kpi-sub">${givebacks} Givebacks (>=+0.8R) · ${whipsaws} Stop-Hunts</div>
    </div>
  `;
}

function stepTrade(delta) {
  if (!filteredTrades.length || !selectedTrade) return;
  const idx = filteredTrades.findIndex(t => t.id === selectedTrade.id);
  const nextIdx = Math.max(0, Math.min(filteredTrades.length - 1, idx + delta));
  selectTrade(filteredTrades[nextIdx], false, true);
}

function selectTrade(trade, scrollToChart = true, panToTrade = true) {
  selectedTrade = trade;
  document.getElementById("tradeJumpSelect").value = String(trade.id);
  document.querySelectorAll("#tradeTableBody tr").forEach(tr => {
    tr.classList.toggle("selected-row", parseInt(tr.getAttribute("data-id"), 10) === trade.id);
  });
  if (panToTrade) {
    ensureTradeInViewport(trade);
  }
  drawTradingViewChart();
  renderTradeInspector(trade);
  if (scrollToChart) {
    document.querySelector(".tv-workspace").scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function getOutcomeBanner(trade) {
  if (trade.exit_reason.includes("TP2")) return { label: "TP HIT", short: "TP", cls: "badge-tp", type: "TP" };
  if (trade.exit_reason.includes("TRAIL_STOP")) return { label: "TRAILING SL", short: "TR", cls: "badge-trail", type: "TRAIL" };
  if (trade.exit_reason.includes("REVERSAL_EXIT")) {
    return {
      label: "⚡ REVERSAL EXIT (" + (trade.r_multiple >= 0 ? "+" : "") + trade.r_multiple.toFixed(2) + "R)",
      short: "REV",
      cls: "badge-time",
      type: "REV"
    };
  }
  if (trade.exit_reason === "STOP_LOSS") return { label: "SL HIT", short: "SL", cls: "badge-sl", type: "SL" };
  return { label: "TIME EXIT (" + (trade.r_multiple >= 0 ? "+" : "") + trade.r_multiple.toFixed(2) + "R)", short: "TM", cls: "badge-time", type: "TRAIL" };
}

function drawTradingViewChart() {
  const canvas = document.getElementById("tvChart");
  if (!canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = rect.height;
  const rightAxisW = 82;
  const bottomAxisH = 28;
  const topHeaderH = 46;
  const plotW = W - rightAxisW;
  const plotH = H - bottomAxisH - topHeaderH;

  ctx.fillStyle = "#0f1117";
  ctx.fillRect(0, 0, W, H);

  const bars = getContinuousBars(currentTF);
  if (!bars.length) return;

  const sIdx = Math.max(0, Math.min(bars.length - 10, Math.floor(viewStartIdx)));
  const eIdx = Math.max(sIdx + 10, Math.min(bars.length - 1, Math.ceil(viewEndIdx)));
  const visibleCount = eIdx - sIdx + 1;
  const sSec = bars.time[sIdx];
  const eSec = bars.time[eIdx];

  // Find all trades visible in (or overlapping) the current multi-month / zoomed viewport
  const visibleTrades = [];
  for (let i = 0; i < filteredTrades.length; i++) {
    const t = filteredTrades[i];
    if (t.exit_ts >= sSec && t.entry_ts <= eSec) {
      const entIdx = findBarIdx(bars.time, t.entry_ts);
      const extIdx = Math.max(entIdx + 1, findBarIdx(bars.time, t.exit_ts));
      visibleTrades.push({ trade: t, entIdx, extIdx });
    }
  }

  // Compute Y-Scale across visible candles + visible trade SL/TP2 levels
  let minP = Infinity;
  let maxP = -Infinity;
  const strideScan = Math.max(1, Math.floor(visibleCount / 1500));
  for (let i = sIdx; i <= eIdx; i += strideScan) {
    if (bars.low[i] < minP) minP = bars.low[i];
    if (bars.high[i] > maxP) maxP = bars.high[i];
  }
  visibleTrades.forEach(({ trade }) => {
    const lo = Math.min(trade.sl_price, trade.tp2_price, trade.entry_price, trade.exit_price);
    const hi = Math.max(trade.sl_price, trade.tp2_price, trade.entry_price, trade.exit_price);
    if (lo < minP) minP = lo;
    if (hi > maxP) maxP = hi;
  });
  if (!isFinite(minP) || !isFinite(maxP)) { minP = 2600; maxP = 2800; }
  const padP = Math.max(2.0, (maxP - minP) * 0.14);
  minP -= padP;
  maxP += padP;

  const yOf = p => topHeaderH + plotH * (1.0 - (p - minP) / (maxP - minP));
  const stepX = plotW / Math.max(1, visibleCount);
  const xOfGlobal = globalIdx => (globalIdx - sIdx + 0.5) * stepX;

  // Grid Lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
  ctx.lineWidth = 1;
  const pSteps = 8;
  for (let i = 0; i <= pSteps; i++) {
    const py = topHeaderH + (plotH / pSteps) * i;
    ctx.beginPath();
    ctx.moveTo(0, py);
    ctx.lineTo(plotW, py);
    ctx.stroke();
  }
  const tSteps = 10;
  const tStride = Math.max(1, Math.floor(visibleCount / tSteps));
  for (let i = sIdx; i <= eIdx; i += tStride) {
    const px = xOfGlobal(i);
    ctx.beginPath();
    ctx.moveTo(px, topHeaderH);
    ctx.lineTo(px, topHeaderH + plotH);
    ctx.stroke();
  }

  // =========================================================================
  // 1. DRAW ALL VISIBLE TRADE POSITION BOXES (TP HIT, SL HIT, TRAILING SL)
  // =========================================================================
  tradeHitBoxes = [];
  const isOverview = visibleCount > 900; // Full 5-month or multi-week view
  const minBoxWidthPx = visibleCount > 4000 ? 16 : (visibleCount > 900 ? 26 : Math.max(stepX * 3.5, 48));

  visibleTrades.forEach(({ trade, entIdx, extIdx }) => {
    const xEnt = Math.max(2, Math.min(plotW - 6, xOfGlobal(entIdx)));
    const xExtRaw = xOfGlobal(extIdx);
    const xExt = Math.min(plotW - 2, Math.max(xEnt + minBoxWidthPx, xExtRaw));
    const boxW = Math.max(8, xExt - xEnt);

    const yEnt = yOf(trade.entry_price);
    const ySL = yOf(trade.sl_price);
    const yTP1 = yOf(trade.tp1_price);
    const yTP2 = yOf(trade.tp2_price);
    const yExit = yOf(trade.exit_price);
    const outcome = getOutcomeBanner(trade);
    const isSel = selectedTrade && selectedTrade.id === trade.id;
    const isHov = hoveredTrade && hoveredTrade.id === trade.id;

    // Outer Target Profit Zone (Entry -> TP2)
    const topTP = Math.min(yEnt, yTP2);
    const hTP = Math.max(3, Math.abs(yTP2 - yEnt));
    ctx.fillStyle = outcome.type === "TP"
      ? (isSel ? "rgba(38, 166, 154, 0.36)" : "rgba(38, 166, 154, 0.24)")
      : "rgba(38, 166, 154, 0.15)";
    ctx.fillRect(xEnt, topTP, boxW, hTP);
    ctx.strokeStyle = isSel ? "#2dd4bf" : "rgba(38, 166, 154, 0.55)";
    ctx.lineWidth = isSel ? 1.6 : 1;
    ctx.strokeRect(xEnt, topTP, boxW, hTP);

    // Inner Locked Profit Zone for TRAILING SL wins or REVERSAL EXIT cuts (matching TradingView Reversal Cut visual)
    if (outcome.type === "TRAIL" && ((trade.direction === "LONG" && trade.exit_price > trade.entry_price) ||
        (trade.direction === "SHORT" && trade.exit_price < trade.entry_price))) {
      const topLock = Math.min(yEnt, yExit);
      const hLock = Math.max(2, Math.abs(yExit - yEnt));
      ctx.fillStyle = "rgba(38, 166, 154, 0.34)";
      ctx.fillRect(xEnt, topLock, boxW, hLock);
      ctx.strokeStyle = "rgba(59, 130, 246, 0.80)";
      ctx.strokeRect(xEnt, topLock, boxW, hLock);
    } else if (outcome.type === "REV") {
      const topRev = Math.min(yEnt, yExit);
      const hRev = Math.max(2, Math.abs(yExit - yEnt));
      ctx.fillStyle = trade.r_multiple >= 0 ? "rgba(245, 158, 11, 0.32)" : "rgba(168, 85, 247, 0.32)";
      ctx.fillRect(xEnt, topRev, boxW, hRev);
      ctx.strokeStyle = trade.r_multiple >= 0 ? "#f59e0b" : "#a855f7";
      ctx.strokeRect(xEnt, topRev, boxW, hRev);
    }

    // Stop Loss Risk Zone (Entry -> SL)
    const topSL = Math.min(yEnt, ySL);
    const hSL = Math.max(3, Math.abs(ySL - yEnt));
    ctx.fillStyle = outcome.type === "SL"
      ? (isSel ? "rgba(239, 83, 80, 0.38)" : "rgba(239, 83, 80, 0.28)")
      : "rgba(239, 83, 80, 0.20)";
    ctx.fillRect(xEnt, topSL, boxW, hSL);
    ctx.strokeStyle = isSel ? "#f87171" : "rgba(239, 83, 80, 0.55)";
    ctx.strokeRect(xEnt, topSL, boxW, hSL);

    // Highlight outline when selected or hovered
    const fullTop = Math.min(topTP, topSL);
    const fullBot = Math.max(topTP + hTP, topSL + hSL);
    if (isSel || isHov) {
      ctx.save();
      ctx.strokeStyle = isSel ? "#f59e0b" : "#38bdf8";
      ctx.lineWidth = isSel ? 2.0 : 1.4;
      ctx.strokeRect(xEnt - 1, fullTop - 1, boxW + 2, (fullBot - fullTop) + 2);
      ctx.restore();
    }

    // Entry line + TP1 line + Diagonal execution line
    ctx.strokeStyle = "rgba(226, 232, 240, 0.85)";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(xEnt, yEnt);
    ctx.lineTo(xExt, yEnt);
    ctx.stroke();

    if (boxW >= 24) {
      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = "rgba(245, 158, 11, 0.45)";
      ctx.beginPath();
      ctx.moveTo(xEnt, yTP1);
      ctx.lineTo(xExt, yTP1);
      ctx.stroke();

      ctx.strokeStyle = "rgba(226, 232, 240, 0.60)";
      ctx.beginPath();
      ctx.moveTo(xEnt, yEnt);
      ctx.lineTo(Math.min(xExt, Math.max(xEnt + 4, xExtRaw)), yExit);
      ctx.stroke();
      ctx.restore();
    }

    // Record hitBox for clicking the position box itself
    tradeHitBoxes.push({
      x1: xEnt,
      y1: fullTop,
      x2: xExt,
      y2: fullBot,
      trade
    });
  });

  // =========================================================================
  // 2. DRAW CONTINUOUS GC.v.0 CANDLESTICKS (60 FPS ADAPTIVE LOD FOR 5-MONTH VIEW)
  // =========================================================================
  if (visibleCount <= plotW * 0.65) {
    // Individual candlesticks
    const bodyW = Math.max(1.8, Math.min(14, stepX * 0.68));
    for (let i = sIdx; i <= eIdx; i++) {
      const cx = xOfGlobal(i);
      const o = bars.open[i], h = bars.high[i], l = bars.low[i], c = bars.close[i];
      const isBull = c >= o;
      const color = isBull ? "#26a69a" : "#ef5350";
      const yH = yOf(h), yL = yOf(l), yO = yOf(o), yC = yOf(c);

      ctx.strokeStyle = color;
      ctx.lineWidth = 1.1;
      ctx.beginPath();
      ctx.moveTo(cx, yH);
      ctx.lineTo(cx, yL);
      ctx.stroke();

      const bTop = Math.min(yO, yC);
      const bH = Math.max(1.4, Math.abs(yC - yO));
      ctx.fillStyle = color;
      ctx.fillRect(cx - bodyW / 2, bTop, bodyW, bH);
    }
  } else {
    // Pixel-column aggregated candlesticks for silky-smooth 60 FPS Full 5-Month / 24-Month view
    const numCols = Math.max(180, Math.floor(plotW / 3.2));
    const barsPerCol = visibleCount / numCols;
    const colW = plotW / numCols;
    const bodyW = Math.max(1.6, colW * 0.68);

    for (let col = 0; col < numCols; col++) {
      const b0 = Math.min(bars.length - 1, Math.floor(sIdx + col * barsPerCol));
      const b1 = Math.min(bars.length - 1, Math.max(b0, Math.floor(sIdx + (col + 1) * barsPerCol) - 1));
      const o = bars.open[b0];
      const c = bars.close[b1];
      let h = bars.high[b0];
      let l = bars.low[b0];
      for (let k = b0 + 1; k <= b1; k++) {
        if (bars.high[k] > h) h = bars.high[k];
        if (bars.low[k] < l) l = bars.low[k];
      }
      const cx = (col + 0.5) * colW;
      const isBull = c >= o;
      const color = isBull ? "#26a69a" : "#ef5350";
      const yH = yOf(h), yL = yOf(l), yO = yOf(o), yC = yOf(c);

      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx, yH);
      ctx.lineTo(cx, yL);
      ctx.stroke();

      const bTop = Math.min(yO, yC);
      const bH = Math.max(1.4, Math.abs(yC - yO));
      ctx.fillStyle = color;
      ctx.fillRect(cx - bodyW / 2, bTop, bodyW, bH);
    }
  }

  // =========================================================================
  // 3. DRAW TRADE OUTCOME LABELS & PROMINENT TRADE NUMBER BADGES (#1, #2, #3...)
  // =========================================================================
  const tierRightEdge = [-9999, -9999, -9999, -9999, -9999, -9999];

  visibleTrades.forEach(({ trade, entIdx, extIdx }) => {
    const xEnt = Math.max(4, Math.min(plotW - 8, xOfGlobal(entIdx)));
    const xExtRaw = xOfGlobal(extIdx);
    const xExt = Math.min(plotW - 2, Math.max(xEnt + minBoxWidthPx, xExtRaw));
    const boxW = Math.max(8, xExt - xEnt);

    const yEnt = yOf(trade.entry_price);
    const ySL = yOf(trade.sl_price);
    const yTP2 = yOf(trade.tp2_price);
    const yExit = yOf(trade.exit_price);
    const outcome = getOutcomeBanner(trade);
    const isSel = selectedTrade && selectedTrade.id === trade.id;
    const isWin = trade.net_pnl_usd > 0;

    // When zoomed in enough (boxW >= 44px), render exact TradingView interior labels ("TP HIT", "SL HIT", "◄── TRAILING SL")
    if (boxW >= 44) {
      const boxCenterX = (xEnt + xExt) / 2;
      ctx.font = "bold 11.5px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
      ctx.textAlign = "center";

      if (outcome.type === "TP") {
        ctx.fillStyle = "#38bdf8";
        ctx.fillText(`#${trade.id} · TP HIT`, boxCenterX, (yEnt + yTP2) / 2 + 4);
      } else if (outcome.type === "SL") {
        ctx.fillStyle = "#38bdf8";
        ctx.fillText(`#${trade.id} · SL HIT`, boxCenterX, (yEnt + yTP2) / 2 + 4);
      } else {
        const lineLeft = Math.max(8, xEnt - 18);
        const lineRight = Math.min(plotW - 12, xExt + 8);
        const isRev = outcome.type === "REV";
        ctx.strokeStyle = isRev ? "#f59e0b" : "#3b82f6";
        ctx.lineWidth = isRev ? 1.8 : 1.6;
        ctx.beginPath();
        ctx.moveTo(lineLeft, yExit);
        ctx.lineTo(lineRight, yExit);
        ctx.stroke();

        const arrowTipX = lineRight + 3;
        ctx.fillStyle = isRev ? "#f59e0b" : "#3b82f6";
        ctx.beginPath();
        ctx.moveTo(arrowTipX, yExit);
        ctx.lineTo(arrowTipX + 11, yExit - 6);
        ctx.lineTo(arrowTipX + 11, yExit + 6);
        ctx.closePath();
        ctx.fill();

        ctx.textAlign = "left";
        ctx.fillStyle = isRev ? "#fbbf24" : "#60a5fa";
        ctx.fillText(`#${trade.id} · ${outcome.label}`, arrowTipX + 15, yExit + 4);
      }
    }

    // Prominent Clickable Trade Number Pill (#1, #2, #3...) above/below every trade on the chart
    const pillText = isOverview
      ? `#${trade.id}`
      : `#${trade.id} ${outcome.short} (${trade.r_multiple >= 0 ? '+' : ''}${trade.r_multiple.toFixed(1)}R)`;

    ctx.font = isSel ? "bold 11.5px -apple-system, BlinkMacSystemFont, sans-serif" : "bold 10.5px -apple-system, BlinkMacSystemFont, sans-serif";
    const textW = ctx.measureText(pillText).width;
    const pillW = Math.ceil(textW + 10);
    const pillH = 17;

    // Choose non-overlapping vertical tier for the #Trade badge
    let chosenTier = 0;
    for (let t = 0; t < tierRightEdge.length; t++) {
      if (xEnt - pillW / 2 > tierRightEdge[t] + 4) {
        chosenTier = t;
        break;
      }
      chosenTier = t;
    }
    tierRightEdge[chosenTier] = xEnt + pillW / 2;

    const topBoxY = Math.min(yEnt, ySL, yTP2);
    const botBoxY = Math.max(yEnt, ySL, yTP2);
    let pillY = topBoxY - 22 - chosenTier * 20;
    if (pillY < topHeaderH + 4) {
      pillY = Math.min(topHeaderH + plotH - pillH - 4, botBoxY + 6 + chosenTier * 19);
    }
    const pillX = Math.max(2, Math.min(plotW - pillW - 2, xEnt - pillW / 2));

    // Connector stem from #Trade pill to exact entry point (xEnt, yEnt)
    ctx.save();
    ctx.strokeStyle = isSel ? "#f59e0b" : (isWin ? "rgba(45, 212, 191, 0.65)" : "rgba(248, 113, 113, 0.65)");
    ctx.lineWidth = isSel ? 1.5 : 1;
    ctx.setLineDash([2, 2]);
    ctx.beginPath();
    ctx.moveTo(xEnt, pillY + (pillY < yEnt ? pillH : 0));
    ctx.lineTo(xEnt, yEnt);
    ctx.stroke();
    ctx.restore();

    // Draw #Trade Number Pill Box
    ctx.fillStyle = isSel
      ? "#f59e0b"
      : (outcome.type === "TP" ? "#065f46" : (outcome.type === "REV" ? "#78350f" : (outcome.type === "TRAIL" ? "#1e3a8a" : "#7f1d1d")));
    ctx.fillRect(pillX, pillY, pillW, pillH);

    ctx.strokeStyle = isSel
      ? "#fde68a"
      : (outcome.type === "TP" ? "#10b981" : (outcome.type === "REV" ? "#f59e0b" : (outcome.type === "TRAIL" ? "#60a5fa" : "#f87171")));
    ctx.lineWidth = isSel ? 1.8 : 1.1;
    ctx.strokeRect(pillX, pillY, pillW, pillH);

    ctx.fillStyle = isSel ? "#090b10" : "#f8fafc";
    ctx.textAlign = "center";
    ctx.fillText(pillText, pillX + pillW / 2, pillY + 12);

    // Register clickable hitbox for the #Trade number badge (priority at end of array)
    tradeHitBoxes.push({
      x1: pillX - 2,
      y1: pillY - 2,
      x2: pillX + pillW + 2,
      y2: pillY + pillH + 2,
      trade
    });
  });

  // =========================================================================
  // 4. RIGHT PRICE AXIS & TRADINGVIEW PRICE PILLS
  // =========================================================================
  ctx.fillStyle = "#131722";
  ctx.fillRect(plotW, 0, rightAxisW, H);
  ctx.strokeStyle = "#232a3b";
  ctx.beginPath();
  ctx.moveTo(plotW, 0);
  ctx.lineTo(plotW, H);
  ctx.stroke();

  ctx.fillStyle = "#8b9bb4";
  ctx.font = "11px -apple-system, BlinkMacSystemFont, monospace";
  ctx.textAlign = "left";
  for (let i = 0; i <= pSteps; i++) {
    const py = topHeaderH + (plotH / pSteps) * i;
    const pVal = maxP - ((maxP - minP) / pSteps) * i;
    ctx.fillText(pVal.toFixed(2), plotW + 8, py + 4);
  }

  function drawPricePill(price, bgColor, textColor = "#fff") {
    const py = yOf(price);
    if (py < topHeaderH || py > topHeaderH + plotH) return;
    ctx.fillStyle = bgColor;
    ctx.fillRect(plotW + 2, py - 9, rightAxisW - 4, 18);
    ctx.fillStyle = textColor;
    ctx.font = "bold 11px monospace";
    ctx.textAlign = "left";
    ctx.fillText(price.toFixed(2), plotW + 7, py + 4);
  }

  const activeT = hoveredTrade || selectedTrade;
  if (activeT) {
    drawPricePill(activeT.tp2_price, "#26a69a");
    drawPricePill(activeT.tp1_price, "#d97706");
    drawPricePill(activeT.entry_price, "#475569");
    drawPricePill(activeT.sl_price, "#ef5350");
    if (getOutcomeBanner(activeT).type === "TRAIL") {
      drawPricePill(activeT.exit_price, "#2563eb");
    } else if (getOutcomeBanner(activeT).type === "REV") {
      drawPricePill(activeT.exit_price, "#d97706");
    }
  }

  // =========================================================================
  // 5. BOTTOM TIME AXIS (ADAPTIVE MULTI-MONTH / MULTI-DAY / INTRADAY UTC)
  // =========================================================================
  ctx.fillStyle = "#131722";
  ctx.fillRect(0, topHeaderH + plotH, plotW, bottomAxisH);
  ctx.strokeStyle = "#232a3b";
  ctx.beginPath();
  ctx.moveTo(0, topHeaderH + plotH);
  ctx.lineTo(W, topHeaderH + plotH);
  ctx.stroke();

  ctx.fillStyle = "#8b9bb4";
  ctx.font = "11px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.textAlign = "center";
  const spanSec = eSec - sSec;
  const monthsShort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  for (let i = sIdx; i <= eIdx; i += tStride) {
    const px = xOfGlobal(i);
    if (px < 35 || px > plotW - 35) continue;
    const d = new Date(bars.time[i] * 1000);
    const mo = monthsShort[d.getUTCMonth()];
    const dd = String(d.getUTCDate()).padStart(2, "0");
    const yr = String(d.getUTCFullYear()).slice(-2);
    const hh = String(d.getUTCHours()).padStart(2, "0");
    const mm = String(d.getUTCMinutes()).padStart(2, "0");
    const lbl = spanSec > 86400 * 12
      ? `${dd} ${mo} '${yr}`
      : (spanSec > 86400 * 2 ? `${dd} ${mo} ${hh}:${mm}` : `${dd} ${mo} ${hh}:${mm}`);
    ctx.fillText(lbl, px, topHeaderH + plotH + 18);
  }

  // =========================================================================
  // 6. TOP-LEFT TRADINGVIEW SYMBOL & ACTIVE TRADE WATERMARK HEADER
  // =========================================================================
  ctx.fillStyle = "rgba(15, 17, 23, 0.90)";
  ctx.fillRect(0, 0, plotW, topHeaderH);

  let inspectIdx = activeT ? findBarIdx(bars.time, activeT.entry_ts) : eIdx;
  inspectIdx = Math.max(0, Math.min(bars.length - 1, inspectIdx));

  if (hoverMouse && hoverMouse.x < plotW && hoverMouse.y > topHeaderH && hoverMouse.y < topHeaderH + plotH) {
    const hIdx = Math.max(sIdx, Math.min(eIdx, Math.floor(sIdx + (hoverMouse.x / plotW) * visibleCount)));
    inspectIdx = hIdx;

    ctx.save();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = "rgba(148, 163, 184, 0.45)";
    ctx.beginPath();
    ctx.moveTo(xOfGlobal(hIdx), topHeaderH);
    ctx.lineTo(xOfGlobal(hIdx), topHeaderH + plotH);
    ctx.moveTo(0, hoverMouse.y);
    ctx.lineTo(plotW, hoverMouse.y);
    ctx.stroke();
    ctx.restore();

    const hoverPrice = maxP - ((hoverMouse.y - topHeaderH) / plotH) * (maxP - minP);
    drawPricePill(hoverPrice, "#334155");
  }

  const iO = bars.open[inspectIdx], iH = bars.high[inspectIdx], iL = bars.low[inspectIdx], iC = bars.close[inspectIdx], iV = bars.vol[inspectIdx];
  const chg = iC - iO;
  const chgPct = (chg / iO) * 100;
  const tfMap = { 1: "1m", 3: "3m", 5: "5m", 15: "15m", 30: "30m", 60: "1H", 240: "4H", 1440: "1D" };
  const tfLabel = tfMap[currentTF] || `${currentTF}m`;

  const dStart = new Date(sSec * 1000).toISOString().slice(0, 10);
  const dEnd = new Date(eSec * 1000).toISOString().slice(0, 10);

  ctx.textAlign = "left";
  ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = "#e2e8f0";
  ctx.fillText(
    `Gold Futures (GC.v.0 · ${tfLabel} · ${dStart} → ${dEnd} · ${visibleTrades.length} Trades in View)   O ${iO.toFixed(2)}   H ${iH.toFixed(2)}   L ${iL.toFixed(2)}   C ${iC.toFixed(2)}   ${chg >= 0 ? "+" : ""}${chg.toFixed(2)} (${chg >= 0 ? "+" : ""}${chgPct.toFixed(2)}%)   Vol ${iV}`,
    12, 18
  );

  ctx.font = "11px -apple-system, BlinkMacSystemFont, sans-serif";
  if (activeT) {
    ctx.fillStyle = hoveredTrade ? "#38bdf8" : "#f59e0b";
    ctx.fillText(
      `Selected Trade #${activeT.id} (${activeT.date}) · ${activeT.setup_agent} (${activeT.setup_type}) · ${activeT.direction} @ ${activeT.entry_price.toFixed(2)} → ${activeT.exit_price.toFixed(2)} · ${activeT.r_multiple >= 0 ? "+" : ""}${activeT.r_multiple.toFixed(2)}R (${activeT.net_pnl_usd >= 0 ? "+" : ""}$${activeT.net_pnl_usd.toFixed(2)} Net after $${activeT.delta_fee_usd.toFixed(2)} Delta 0.01% Fee)`,
      12, 36
    );
  }

  document.getElementById("visibleRangeSummary").textContent =
    `Viewing: ${dStart} to ${dEnd} (${visibleTrades.length} of ${filteredTrades.length} Trades Visible on Chart)`;

  drawNavigatorBar(bars, sIdx, eIdx);
}

// ============================================================================
// CONTINUOUS MULTI-MONTH TIMELINE NAVIGATOR / MINIMAP BAR
// ============================================================================
function drawNavigatorBar(bars, sIdx, eIdx) {
  const nav = document.getElementById("tvNavChart");
  if (!nav || !bars.length) return;
  const rect = nav.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  nav.width = rect.width * dpr;
  nav.height = rect.height * dpr;
  const ctx = nav.getContext("2d");
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = rect.height;
  ctx.fillStyle = "#090c12";
  ctx.fillRect(0, 0, W, H);

  const n = bars.length;
  const step = Math.max(1, Math.floor(n / 600));
  let minP = Infinity, maxP = -Infinity;
  for (let i = 0; i < n; i += step) {
    if (bars.close[i] < minP) minP = bars.close[i];
    if (bars.close[i] > maxP) maxP = bars.close[i];
  }
  const yOf = p => 3 + (H - 6) * (1 - (p - minP) / Math.max(1, maxP - minP));

  // Price polyline across all 24 months
  ctx.strokeStyle = "rgba(148, 163, 184, 0.55)";
  ctx.lineWidth = 1.1;
  ctx.beginPath();
  for (let i = 0; i < n; i += step) {
    const x = (i / (n - 1)) * W;
    const y = yOf(bars.close[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Plot all trade pins (#1..#150) along the multi-month navigator
  filteredTrades.forEach(t => {
    const idx = findBarIdx(bars.time, t.entry_ts);
    const x = (idx / Math.max(1, n - 1)) * W;
    const isSel = selectedTrade && selectedTrade.id === t.id;
    ctx.fillStyle = isSel ? "#f59e0b" : (t.net_pnl_usd > 0 ? "#26a69a" : "#ef5350");
    ctx.fillRect(x - (isSel ? 2 : 1), isSel ? 1 : (t.net_pnl_usd > 0 ? 4 : H - 12), isSel ? 4 : 2, isSel ? H - 2 : 8);
  });

  // Shaded current viewport window
  const x1 = (sIdx / Math.max(1, n - 1)) * W;
  const x2 = Math.max(x1 + 6, (eIdx / Math.max(1, n - 1)) * W);
  ctx.fillStyle = "rgba(59, 130, 246, 0.22)";
  ctx.fillRect(x1, 0, x2 - x1, H);
  ctx.strokeStyle = "#3b82f6";
  ctx.lineWidth = 1.5;
  ctx.strokeRect(x1, 0.5, x2 - x1, H - 1);
}

function setupCanvasInteractions() {
  const canvas = document.getElementById("tvChart");
  const nav = document.getElementById("tvNavChart");

  canvas.addEventListener("wheel", e => {
    e.preventDefault();
    const bars = getContinuousBars(currentTF);
    if (!bars.length) return;
    const rect = canvas.getBoundingClientRect();
    const plotW = Math.max(100, rect.width - 82);
    const mouseRatio = Math.max(0, Math.min(1, (e.clientX - rect.left) / plotW));

    const span = viewEndIdx - viewStartIdx;
    const factor = e.deltaY > 0 ? 1.22 : 0.82;
    const newSpan = Math.max(20, Math.min(bars.length - 1, span * factor));
    const anchor = viewStartIdx + span * mouseRatio;
    viewStartIdx = Math.max(0, Math.min(bars.length - newSpan, anchor - newSpan * mouseRatio));
    viewEndIdx = Math.min(bars.length - 1, viewStartIdx + newSpan);
    drawTradingViewChart();
  }, { passive: false });

  canvas.addEventListener("mousedown", e => {
    isDragging = true;
    dragStartX = e.clientX;
    dragMovedPx = 0;
  });

  // Click on any #Trade badge or trade box on the chart to inspect its forensic journal
  canvas.addEventListener("click", e => {
    if (dragMovedPx > 6) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    for (let i = tradeHitBoxes.length - 1; i >= 0; i--) {
      const b = tradeHitBoxes[i];
      if (mx >= b.x1 && mx <= b.x2 && my >= b.y1 && my <= b.y2) {
        selectTrade(b.trade, false, false);
        return;
      }
    }
  });

  // Double-click any #Trade badge or trade box on the chart to zoom closely into that trade
  canvas.addEventListener("dblclick", e => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    for (let i = tradeHitBoxes.length - 1; i >= 0; i--) {
      const b = tradeHitBoxes[i];
      if (mx >= b.x1 && mx <= b.x2 && my >= b.y1 && my <= b.y2) {
        selectTrade(b.trade, false, false);
        document.getElementById("zoomTradeBtn").classList.add("active-btn");
        document.getElementById("fit5MonthBtn").classList.remove("active-btn");
        zoomToSelectedTrade();
        return;
      }
    }
  });

  function jumpNavigatorAt(clientX) {
    const bars = getContinuousBars(currentTF);
    if (!bars.length) return;
    const rect = nav.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / Math.max(1, rect.width)));
    const span = viewEndIdx - viewStartIdx;
    const center = ratio * (bars.length - 1);
    viewStartIdx = Math.max(0, Math.min(bars.length - span, center - span / 2));
    viewEndIdx = Math.min(bars.length - 1, viewStartIdx + span);
    drawTradingViewChart();
  }

  nav.addEventListener("mousedown", e => {
    isNavDragging = true;
    jumpNavigatorAt(e.clientX);
  });

  window.addEventListener("mouseup", () => {
    isDragging = false;
    isNavDragging = false;
  });

  window.addEventListener("mousemove", e => {
    if (isNavDragging) {
      jumpNavigatorAt(e.clientX);
      return;
    }
    const rect = canvas.getBoundingClientRect();
    if (e.target === canvas) {
      hoverMouse = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      // Check if hovering over a trade badge or trade box
      let foundHov = null;
      for (let i = tradeHitBoxes.length - 1; i >= 0; i--) {
        const b = tradeHitBoxes[i];
        if (hoverMouse.x >= b.x1 && hoverMouse.x <= b.x2 && hoverMouse.y >= b.y1 && hoverMouse.y <= b.y2) {
          foundHov = b.trade;
          break;
        }
      }
      hoveredTrade = foundHov;
      canvas.style.cursor = isDragging ? "grabbing" : (foundHov ? "pointer" : "crosshair");
    } else {
      hoverMouse = null;
      hoveredTrade = null;
    }

    if (isDragging) {
      const bars = getContinuousBars(currentTF);
      const span = viewEndIdx - viewStartIdx;
      const dx = e.clientX - dragStartX;
      dragMovedPx += Math.abs(dx);
      dragStartX = e.clientX;
      const barShift = -(dx / Math.max(100, rect.width - 82)) * span;
      viewStartIdx = Math.max(0, Math.min(bars.length - span, viewStartIdx + barShift));
      viewEndIdx = Math.min(bars.length - 1, viewStartIdx + span);
    }
    if (e.target === canvas || isDragging) drawTradingViewChart();
  });

  canvas.addEventListener("mouseleave", () => {
    hoverMouse = null;
    hoveredTrade = null;
    drawTradingViewChart();
  });
}

function renderTradeInspector(t) {
  const outcome = getOutcomeBanner(t);
  const badge = document.getElementById("inspectorBadge");
  badge.className = "badge " + outcome.cls;
  badge.textContent = `${outcome.label} · ${t.r_multiple >= 0 ? '+' : ''}${t.r_multiple.toFixed(2)}R`;

  const isWin = t.net_pnl_usd > 0;
  document.getElementById("inspectorBody").innerHTML = `
    <div class="trade-banner" style="border-left-color:${isWin ? 'var(--tv-green)' : 'var(--tv-red)'}">
      <div>
        <div style="font-weight:800;font-size:14px;">
          Trade #${t.id} · <span class="badge ${t.direction === 'LONG' ? 'badge-long' : 'badge-short'}">${t.direction}</span>
          ${t.setup_agent} — ${t.setup_type}
        </div>
        <div style="color:var(--text-muted);font-size:11.5px;margin-top:2px;">
          ${t.entry_time} → ${t.exit_time} (${t.hold_mins} mins) · ${t.day_of_week} · ${t.session}
        </div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:18px;font-weight:800;" class="${isWin ? 'pos' : 'neg'}">
          ${t.net_pnl_usd >= 0 ? '+' : ''}$${t.net_pnl_usd.toFixed(2)}
        </div>
        <div style="font-size:11px;color:var(--text-muted);">
          Gross: ${t.gross_pnl_usd >= 0 ? '+' : ''}$${t.gross_pnl_usd.toFixed(2)} | Fee: -$${t.delta_fee_usd.toFixed(2)}
        </div>
      </div>
    </div>

    <div class="spec-grid">
      <div class="spec-box"><div class="lbl">Entry → Exit</div><div class="val">${t.entry_price.toFixed(2)} → ${t.exit_price.toFixed(2)}</div></div>
      <div class="spec-box"><div class="lbl">SL / TP1 / TP2</div><div class="val"><span class="neg">${t.sl_price.toFixed(1)}</span> / <span class="gold">${t.tp1_price.toFixed(1)}</span> / <span class="pos">${t.tp2_price.toFixed(1)}</span></div></div>
      <div class="spec-box"><div class="lbl">MFE (Peak Profit)</div><div class="val pos">+${t.mfe_r.toFixed(2)}R (+${t.mfe_pts.toFixed(1)}p)</div></div>
      <div class="spec-box"><div class="lbl">MAE (Max Drawdown)</div><div class="val neg">-${t.mae_r.toFixed(2)}R (-${t.mae_pts.toFixed(1)}p)</div></div>
      <div class="spec-box"><div class="lbl">Post-Exit 60m Move</div><div class="val blue">+${t.post_60m_r.toFixed(2)}R (+${t.post_60m_pts.toFixed(1)}p)</div></div>
      <div class="spec-box"><div class="lbl">Delta Notional / Qty</div><div class="val">$${t.notional_usd.toFixed(0)} (${t.qty_oz.toFixed(2)} oz)</div></div>
      <div class="spec-box"><div class="lbl">15M CHOP / ADX</div><div class="val">${t.chop_15m} / ${t.adx_15m}</div></div>
      <div class="spec-box"><div class="lbl">Vol Z / L2 / 5m CVD</div><div class="val">+${t.vol_z}σ / ${t.l2_ratio} / ${t.delta_5m >= 0 ? '+' : ''}${t.delta_5m}</div></div>
    </div>

    <div class="journal-box" style="border-left:3px solid var(--tv-green);">
      <h4 class="pos">✓ What Went Right (Entry Confluence & Pros)</h4>
      <ul>
        ${t.pros.map(p => `<li>${p}</li>`).join("")}
      </ul>
    </div>

    <div class="journal-box" style="border-left:3px solid ${t.exit_reason === 'STOP_LOSS' ? 'var(--tv-red)' : 'var(--tv-cyan)'};">
      <h4 class="${t.exit_reason === 'STOP_LOSS' ? 'neg' : 'blue'}">
        ⚡ Forensic Diagnosis: [${t.mistake_code}] — ${t.mistake_title}
      </h4>
      <p style="font-size:12px;color:#cbd5e1;margin-bottom:6px;">${t.mistake_desc}</p>
      <div style="background:rgba(168,85,247,0.12);border:1px solid rgba(168,85,247,0.35);padding:7px 10px;border-radius:5px;font-size:11.5px;color:#e9d5ff;">
        <strong>🧠 Self-Learner Agent (ORACLE) Guidance:</strong> ${t.learner_fix}
      </div>
    </div>

    <div class="journal-box">
      <h4 style="color:var(--gold);display:flex;justify-content:space-between;align-items:center;">
        <span>🏛️ 3-Part Agent Hierarchy & Quorum (${t.confirming_count} Active · ${t.consensus_pct.toFixed(1)}% Consensus)</span>
        ${t.scalper_bypass ? '<span class="badge" style="background:rgba(245,158,11,0.18);color:#f59e0b;border:1px solid #f59e0b;">⚡ SCALPER BYPASSED HTF WAIT</span>' : ''}
      </h4>
      <div style="font-size:11.5px;color:#cbd5e1;margin-bottom:6px;line-height:1.45;">
        <div style="margin-bottom:4px;"><strong style="color:#38bdf8;">Part 1 (Analyser #17 LUCAS):</strong> ${t.analyser_brief || 'Filtered minority noise & verified >60% conviction voters.'}</div>
        <div style="margin-bottom:4px;"><strong style="color:#a855f7;">Part 2 & 3 (Psychologist + Expert Trader + Mathematician → CEO Master):</strong> ${t.council_verdict || 'Senior Council co-signed -> VICTOR executed.'}</div>
      </div>
      <div style="font-size:10.5px;color:var(--text-muted);margin-bottom:4px;font-weight:700;">ACTIVE VOTING & CONFIRMING AGENTS (&gt;60% CERTAINTY):</div>
      <div class="agent-pills" style="margin-bottom:6px;">
        ${t.confirming_agents.map(a => `<span class="agent-pill">${a}</span>`).join("")}
      </div>
      ${t.skipped_agents && t.skipped_agents.length ? `
        <div style="font-size:10.5px;color:var(--text-muted);margin-bottom:4px;font-weight:700;">SKIPPED / ABSTAINED AGENTS (&le;60% UNCLEAR — DID NOT BLOCK TRADE):</div>
        <div class="agent-pills">
          ${t.skipped_agents.map(a => `<span class="agent-pill" style="opacity:0.6;border-style:dashed;">${a}</span>`).join("")}
        </div>
      ` : ''}
    </div>
  `;
}

// ============================================================================
// MONTHLY & DAILY P&L CALENDAR HEATMAP
// ============================================================================
function renderCalendar() {
  const allTrades = PAYLOAD.profiles[currentProfileKey].trades;
  const monthStr = availableMonths[currentMonthIdx] || "2026-10";
  const [yr, mo] = monthStr.split("-").map(Number);

  const firstDay = new Date(Date.UTC(yr, mo - 1, 1));
  const startDow = firstDay.getUTCDay(); // 0=Sun..6=Sat
  const daysInMonth = new Date(Date.UTC(yr, mo, 0)).getUTCDate();

  const dayMap = {};
  let monthNet = 0, monthTrades = 0, monthWins = 0;
  allTrades.forEach(t => {
    if (t.month === monthStr) {
      if (!dayMap[t.date]) dayMap[t.date] = { pnl: 0, count: 0, wins: 0, trades: [] };
      dayMap[t.date].pnl += t.net_pnl_usd;
      dayMap[t.date].count += 1;
      if (t.net_pnl_usd > 0) dayMap[t.date].wins += 1;
      dayMap[t.date].trades.push(t);
      monthNet += t.net_pnl_usd;
      monthTrades += 1;
      if (t.net_pnl_usd > 0) monthWins += 1;
    }
  });

  const mWr = monthTrades ? (monthWins / monthTrades * 100).toFixed(0) : "0";
  const sumEl = document.getElementById("monthSummaryText");
  sumEl.className = monthNet >= 0 ? "pos" : "neg";
  sumEl.textContent = `${monthStr}: ${monthNet >= 0 ? '+' : ''}$${monthNet.toFixed(2)} (${monthTrades} Trades · ${mWr}% WR)`;

  const headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Week Total"];
  let html = headers.map(h => `<div class="cal-head">${h}</div>`).join("");

  let dayCounter = 1;
  for (let week = 0; week < 6; week++) {
    if (dayCounter > daysInMonth) break;
    let weekPnl = 0, weekCount = 0;

    for (let dow = 0; dow < 7; dow++) {
      if ((week === 0 && dow < startDow) || dayCounter > daysInMonth) {
        html += `<div class="cal-cell empty"></div>`;
      } else {
        const dStr = `${monthStr}-${String(dayCounter).padStart(2, "0")}`;
        const info = dayMap[dStr];
        if (info) {
          weekPnl += info.pnl;
          weekCount += info.count;
          const cls = info.pnl >= 0 ? "win-day" : "loss-day";
          const sel = selectedCalendarDate === dStr ? "selected-day" : "";
          const wrDay = Math.round((info.wins / info.count) * 100);
          html += `
            <div class="cal-cell ${cls} ${sel}" onclick="onCalendarDayClick('${dStr}')">
              <div class="cal-day-num"><span>${dayCounter}</span><span>${info.count}T</span></div>
              <div class="cal-pnl ${info.pnl >= 0 ? 'pos' : 'neg'}">${info.pnl >= 0 ? '+' : ''}$${info.pnl.toFixed(2)}</div>
              <div class="cal-meta">${wrDay}% Win</div>
            </div>
          `;
        } else {
          html += `
            <div class="cal-cell" style="opacity:0.45;">
              <div class="cal-day-num"><span>${dayCounter}</span></div>
              <div class="cal-pnl" style="color:#475569;font-size:11px;">—</div>
              <div class="cal-meta">No trades</div>
            </div>
          `;
        }
        dayCounter++;
      }
    }

    // Weekly summary cell
    html += `
      <div class="cal-cell" style="background:#0e131d;cursor:default;">
        <div class="cal-day-num"><span>Wk ${week + 1}</span><span>${weekCount}T</span></div>
        <div class="cal-pnl ${weekPnl > 0 ? 'pos' : (weekPnl < 0 ? 'neg' : '')}">
          ${weekCount ? (weekPnl >= 0 ? '+' : '') + '$' + weekPnl.toFixed(2) : '—'}
        </div>
        <div class="cal-meta">Weekly Net</div>
      </div>
    `;
  }

  document.getElementById("calendarGrid").innerHTML = html;
}

window.onCalendarDayClick = function(dateStr) {
  if (selectedCalendarDate === dateStr) {
    selectedCalendarDate = null;
  } else {
    selectedCalendarDate = dateStr;
  }
  applyFilters();
};

// ============================================================================
// EQUITY & DRAWDOWN CHART
// ============================================================================
function drawEquityChart() {
  const canvas = document.getElementById("equityCanvas");
  if (!canvas) return;
  const trades = PAYLOAD.profiles[currentProfileKey].trades;
  const rect = canvas.parentElement.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = (rect.width - 24) * dpr;
  canvas.height = (rect.height - 24) * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const W = rect.width - 24;
  const H = rect.height - 24;
  ctx.fillStyle = "#0f1117";
  ctx.fillRect(0, 0, W, H);
  if (!trades.length) return;

  const eqPts = [100.0, ...trades.map(t => t.equity_after)];
  let peak = 100.0;
  const ddPts = eqPts.map(e => {
    if (e > peak) peak = e;
    return ((e - peak) / peak) * 100.0;
  });

  const minEq = Math.min(80, ...eqPts);
  const maxEq = Math.max(120, ...eqPts) * 1.04;
  const padL = 48, padR = 48, padT = 16, padB = 26;
  const pW = W - padL - padR;
  const pH = H - padT - padB;

  const xOf = i => padL + (i / Math.max(1, eqPts.length - 1)) * pW;
  const yEq = v => padT + pH * (1 - (v - minEq) / (maxEq - minEq));

  // Baseline $100
  ctx.strokeStyle = "rgba(255,255,255,0.12)";
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(padL, yEq(100));
  ctx.lineTo(padL + pW, yEq(100));
  ctx.stroke();
  ctx.setLineDash([]);

  // Equity Area & Line
  const grad = ctx.createLinearGradient(0, padT, 0, padT + pH);
  grad.addColorStop(0, "rgba(38, 166, 154, 0.32)");
  grad.addColorStop(1, "rgba(38, 166, 154, 0.0)");

  ctx.beginPath();
  ctx.moveTo(xOf(0), padT + pH);
  eqPts.forEach((v, i) => ctx.lineTo(xOf(i), yEq(v)));
  ctx.lineTo(xOf(eqPts.length - 1), padT + pH);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.strokeStyle = "#26a69a";
  ctx.lineWidth = 2;
  ctx.beginPath();
  eqPts.forEach((v, i) => {
    if (i === 0) ctx.moveTo(xOf(i), yEq(v));
    else ctx.lineTo(xOf(i), yEq(v));
  });
  ctx.stroke();

  // Left Axis labels
  ctx.fillStyle = "#8b9bb4";
  ctx.font = "10.5px monospace";
  ctx.textAlign = "right";
  for (let k = 0; k <= 4; k++) {
    const val = minEq + ((maxEq - minEq) / 4) * k;
    ctx.fillText("$" + val.toFixed(0), padL - 6, yEq(val) + 3);
  }

  const finalEq = eqPts[eqPts.length - 1];
  document.getElementById("equityHeaderStat").textContent =
    `$100.00 → $${finalEq.toFixed(2)} (${finalEq >= 100 ? '+' : ''}${(finalEq - 100).toFixed(2)}%) | Max DD: ${Math.min(...ddPts).toFixed(2)}%`;
}

// ============================================================================
// SESSION, WEEKDAY & SEASONALITY TABLES
// ============================================================================
function renderGroupTable(trades, keyFn, orderList = null) {
  const groups = {};
  trades.forEach(t => {
    const k = keyFn(t);
    if (!groups[k]) groups[k] = { n: 0, w: 0, r: 0, net: 0, fee: 0 };
    groups[k].n++;
    if (t.net_pnl_usd > 0) groups[k].w++;
    groups[k].r += t.r_multiple;
    groups[k].net += t.net_pnl_usd;
    groups[k].fee += t.delta_fee_usd;
  });
  const keys = orderList ? orderList.filter(k => groups[k]) : Object.keys(groups).sort((a, b) => groups[b].net - groups[a].net);
  return `
    <thead>
      <tr><th>Segment</th><th>Trades</th><th>Win %</th><th>Avg R</th><th>Net PnL ($)</th></tr>
    </thead>
    <tbody>
      ${keys.map(k => {
        const g = groups[k];
        const wr = (g.w / g.n * 100).toFixed(1);
        const ar = (g.r / g.n);
        return `
          <tr>
            <td style="font-weight:600;">${k}</td>
            <td>${g.n}</td>
            <td>${wr}%</td>
            <td class="${ar >= 0 ? 'pos' : 'neg'}">${ar >= 0 ? '+' : ''}${ar.toFixed(2)}R</td>
            <td class="${g.net >= 0 ? 'pos' : 'neg'}" style="font-weight:700;">${g.net >= 0 ? '+' : ''}$${g.net.toFixed(2)}</td>
          </tr>
        `;
      }).join("")}
    </tbody>
  `;
}

function renderAnalyticsTables(trades) {
  document.getElementById("sessionTable").innerHTML = renderGroupTable(trades, t => t.session);
  document.getElementById("dayTable").innerHTML = renderGroupTable(
    trades,
    t => t.day_of_week,
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
  );
  document.getElementById("seasonTable").innerHTML = renderGroupTable(
    trades,
    t => `${t.season} · ${t.setup_agent.split(" ")[0]}`
  );
}

// ============================================================================
// AGENT #17 (SELF-LEARNER META-COACH) & 16-AGENT RELIABILITY MATRIX
// ============================================================================
function renderSelfLearner(trades) {
  const slTrades = trades.filter(t => t.exit_reason === "STOP_LOSS");
  const givebacks = slTrades.filter(t => t.mistake_code === "UNBANKED_PROFIT_GIVEBACK");
  const whipsaws = slTrades.filter(t => t.mistake_code === "STOP_HUNT_WHIPSAW");
  const cvdFades = slTrades.filter(t => t.mistake_code === "COUNTER_CVD_MOMENTUM");
  const runners = trades.filter(t => t.exit_reason.includes("TP2") || t.exit_reason.includes("PHASE_4"));
  const revExits = trades.filter(t => t.exit_reason.includes("REVERSAL_EXIT"));
  const revNetPnl = revExits.reduce((s, t) => s + t.net_pnl_usd, 0);

  const givebackPotential = givebacks.length * 5.0;
  const whipsawPotential = whipsaws.length * 5.0;

  let trustHtml = "";
  if (PAYLOAD.trust_benchmark && PAYLOAD.trust_benchmark.best_by_context) {
    const bbc = PAYLOAD.trust_benchmark.best_by_context;
    const cells = [];
    ["ASIA", "LONDON", "NEW_YORK"].forEach(sess => {
      ["TRENDING", "SIDEWAYS"].forEach(mkt => {
        if (bbc[sess] && bbc[sess][mkt]) {
          const topInd = (bbc[sess][mkt].top_individual || [])[0];
          const topCmb = (bbc[sess][mkt].top_combos || [])[0];
          if (topInd) {
            cells.push(`
              <div style="background:#0f1420;border:1px solid #1e293b;border-radius:6px;padding:8px;">
                <div style="font-size:11px;font-weight:800;color:var(--tv-cyan);margin-bottom:4px;">🌐 ${sess} · ${mkt}</div>
                <div style="font-size:11px;color:#e2e8f0;">🏆 <strong>${topInd.agent_or_combo}</strong> (${topInd.timeframe})</div>
                <div style="font-size:10.5px;color:#94a3b8;">WR: <span class="pos">${topInd.win_rate}%</span> · PF: <strong>${topInd.profit_factor}</strong> · Net: <span class="pos">+$${topInd.net_pnl_usd.toFixed(2)}</span> · Weight: <span class="gold" style="font-weight:800;">${topInd.trust_weight}x</span></div>
                ${topCmb ? `<div style="font-size:10px;color:#cbd5e1;margin-top:3px;border-top:1px dashed #1e293b;padding-top:3px;">🤝 Best Combo: <strong>${topCmb.agent_or_combo.replace('COMBO: ','')}</strong> (${topCmb.timeframe}, WR ${topCmb.win_rate}%, ${topCmb.trust_weight}x)</div>` : ''}
              </div>
            `);
          }
        }
      });
    });
    if (cells.length) {
      trustHtml = `
        <div class="directive-card" style="border-left-color:var(--tv-cyan);">
          <h5><span>🏛️ 17:LUCAS Dynamic Voting Trust Weights (1m / 5m / 15m / 1h × Session × Regime)</span><span class="blue">374 Benchmark Cells Saved</span></h5>
          <p style="margin-bottom:8px;">
            Instead of equal 1.0x votes, <strong>17:LUCAS (Analysis Agent)</strong> assigns higher voting weight (up to <strong>2.25x</strong>) to the top historical specialist for the active session and regime—tipping close <strong>4 vs 5</strong> votes while still respecting strong <strong>6 vs 2</strong> majorities:
          </p>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px;">${cells.join("")}</div>
        </div>
      `;
    }
  }

  document.getElementById("selfLearnerPanel").innerHTML = `
    ${trustHtml}
    <div class="directive-card" style="border-left-color:var(--gold);">
      <h5><span>1. VICTOR & RYAN — Instant Agent Reversal Exit (&ge;70% Agents Flip)</span><span class="gold">⚡ ${revExits.length} Trades Rescued (${revNetPnl >= 0 ? '+' : ''}$${revNetPnl.toFixed(2)} Net)</span></h5>
      <p>
        When <strong>70% to 100% of active in-trade agents</strong> simultaneously flag an opposite structural break + CVD flip threatening our
        <strong>SL or Trailing SL</strong>, the trade is cut instantly at market price. Across <strong>${revExits.length} reversal exits</strong>,
        this rule banked <strong>${revNetPnl >= 0 ? '+' : ''}$${revNetPnl.toFixed(2)} net</strong> and saved dozens of full -1.00R stop-outs!
      </p>
    </div>
    <div class="directive-card">
      <h5><span>1. RYAN (Lifecycle Engine) — Unbanked Giveback Protection</span><span class="gold">${givebacks.length} SL Trades Reached >= +0.80R First</span></h5>
      <p>
        Forensic MFE audit shows <strong>${givebacks.length} out of ${slTrades.length} Stop-Loss trades</strong> actually moved at least
        <strong>+0.80R in profit</strong> before reversing to hit -1.0R SL ($${givebackPotential.toFixed(2)} in preventable losses).
        <strong>Self-Learner Rule:</strong> When 15M CHOP &gt; 50 or ADX &lt; 22, trigger an early defensive stop-to-entry lock at <strong>+0.85R</strong>.
      </p>
    </div>
    <div class="directive-card">
      <h5><span>2. NINA & ELENA (Liquidity Sweep Entry Timing) — Stop-Hunt Whipsaw Filter</span><span class="blue">${whipsaws.length} Fast Stop-Hunts Reversed +1.15R+</span></h5>
      <p>
        <strong>${whipsaws.length} Stop-Loss trades</strong> stopped out within 18 minutes and then immediately rallied
        <strong>+1.15R or more</strong> in our predicted direction over the next 60 minutes.
        <strong>Self-Learner Rule:</strong> On London/NY open sweeps, wait for the second 1M structure candle close or add +0.15x ATR wick buffer.
      </p>
    </div>
    <div class="directive-card">
      <h5><span>3. OMAR & SAM (Order Flow & L2 DOM Gate) — Counter-Delta Veto</span><span class="neg">${cvdFades.length} Counter-CVD Stop-Outs</span></h5>
      <p>
        <strong>${cvdFades.length} losses</strong> occurred when fading a 4H level while 15-minute Cumulative Volume Delta exceeded ±30 contracts against the trade.
        <strong>Self-Learner Rule:</strong> Require 5m delta deceleration + L2 Bid/Ask ratio &gt;= 1.15 before fading high-momentum 15m impulses.
      </p>
    </div>
    <div class="directive-card" style="border-left-color:var(--tv-green);">
      <h5><span>4. KAI + ELENA & MARCUS — High-Conviction Runner Amplification</span><span class="pos">${runners.length} Structure Runners Banked</span></h5>
      <p>
        When <strong>15/16 or 16/16 agents confirm</strong> during Silver Bullet / Killzone windows with MAE &lt; 0.45R in the first 15 minutes,
        runner probability jumps above 60%. <strong>Self-Learner Rule:</strong> Hold runner to full +3.25R TP2 without premature tightening.
      </p>
    </div>
  `;

  // 16-Agent Matrix
  const agentStats = {};
  trades.forEach(t => {
    t.confirming_agents.forEach(ag => {
      if (!agentStats[ag]) agentStats[ag] = { n: 0, w: 0, r: 0, net: 0 };
      agentStats[ag].n++;
      if (t.net_pnl_usd > 0) agentStats[ag].w++;
      agentStats[ag].r += t.r_multiple;
      agentStats[ag].net += t.net_pnl_usd;
    });
  });

  const sortedAgents = Object.keys(agentStats).sort((a, b) => agentStats[b].net - agentStats[a].net);
  document.getElementById("agentMatrixTable").innerHTML = `
    <thead>
      <tr><th>Confirming Agent Tag</th><th>Trades Confirmed</th><th>Win Rate</th><th>Avg R</th><th>Net PnL Contribution</th></tr>
    </thead>
    <tbody>
      ${sortedAgents.map(ag => {
        const s = agentStats[ag];
        const wr = (s.w / s.n * 100).toFixed(1);
        const ar = s.r / s.n;
        return `
          <tr>
            <td><span class="agent-pill">${ag}</span></td>
            <td>${s.n}</td>
            <td>${wr}%</td>
            <td class="${ar >= 0 ? 'pos' : 'neg'}">${ar >= 0 ? '+' : ''}${ar.toFixed(2)}R</td>
            <td class="${s.net >= 0 ? 'pos' : 'neg'}" style="font-weight:700;">${s.net >= 0 ? '+' : ''}$${s.net.toFixed(2)}</td>
          </tr>
        `;
      }).join("")}
    </tbody>
  `;
}

// ============================================================================
// TRADE JOURNAL TABLE
// ============================================================================
function renderTradeTable() {
  document.getElementById("filteredCountLabel").textContent =
    `Showing ${filteredTrades.length} Trades` + (selectedCalendarDate ? ` on ${selectedCalendarDate}` : "");

  const tbody = document.getElementById("tradeTableBody");
  tbody.innerHTML = filteredTrades.map(t => {
    const out = getOutcomeBanner(t);
    const isSel = selectedTrade && selectedTrade.id === t.id;
    return `
      <tr data-id="${t.id}" class="${isSel ? 'selected-row' : ''}" onclick="onTableRowClick(${t.id})" style="cursor:pointer;">
        <td style="font-weight:700;">#${t.id}</td>
        <td>${t.entry_time}</td>
        <td>${t.day_of_week.slice(0,3)} · ${t.session.split(' (')[0]}</td>
        <td><strong>${t.setup_agent}</strong><br/><span style="color:var(--text-muted);font-size:11px;">${t.setup_type}</span></td>
        <td><span class="badge ${t.direction === 'LONG' ? 'badge-long' : 'badge-short'}">${t.direction}</span></td>
        <td style="font-variant-numeric:tabular-nums;">${t.entry_price.toFixed(2)} → <strong>${t.exit_price.toFixed(2)}</strong><br/><span style="color:var(--text-muted);font-size:10.5px;">${t.hold_mins}m hold</span></td>
        <td style="font-variant-numeric:tabular-nums;font-size:11px;">
          SL: <span class="neg">${t.sl_price.toFixed(1)}</span><br/>
          TP1: <span class="gold">${t.tp1_price.toFixed(1)}</span> · TP2: <span class="pos">${t.tp2_price.toFixed(1)}</span>
        </td>
        <td style="font-variant-numeric:tabular-nums;">
          <span class="pos">+${t.mfe_r.toFixed(2)}R</span> / <span class="neg">-${t.mae_r.toFixed(2)}R</span>
        </td>
        <td class="blue" style="font-variant-numeric:tabular-nums;">+${t.post_60m_r.toFixed(2)}R</td>
        <td><span class="agent-pill">${t.confirming_count}/16 (${t.consensus_pct.toFixed(0)}%)</span></td>
        <td style="font-variant-numeric:tabular-nums;">
          <strong class="${t.net_pnl_usd >= 0 ? 'pos' : 'neg'}">${t.net_pnl_usd >= 0 ? '+' : ''}$${t.net_pnl_usd.toFixed(2)}</strong>
          <span style="color:var(--text-muted);font-size:10.5px;">(${t.r_multiple >= 0 ? '+' : ''}${t.r_multiple.toFixed(2)}R)</span><br/>
          <span style="color:var(--text-muted);font-size:10px;">G: ${t.gross_pnl_usd >= 0 ? '+' : ''}$${t.gross_pnl_usd.toFixed(2)} | Fee: -$${t.delta_fee_usd.toFixed(2)}</span>
        </td>
        <td style="font-weight:700;font-variant-numeric:tabular-nums;">$${t.equity_after.toFixed(2)}</td>
        <td>
          <span class="badge ${out.cls}">${out.label}</span><br/>
          <span style="font-size:10.5px;color:var(--text-muted);">${t.mistake_code}</span>
        </td>
      </tr>
    `;
  }).join("");
}

window.onTableRowClick = function(id) {
  const t = filteredTrades.find(x => x.id === id);
  if (t) selectTrade(t, true);
};

initDashboard();
</script>
</body>
</html>
"""


def main():
    with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
        payload_str = f.read()
    html_out = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", payload_str)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"[SUCCESS] Generated standalone interactive dashboard: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
