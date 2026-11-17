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
          <span id="tvHeaderTitle">Gold Futures (GC.v.0) — TradingView Position Execution Replay</span>
        </div>
        <div class="controls-row">
          <div class="tf-group" id="tfGroup">
            <button class="tf-btn" data-tf="1">1m</button>
            <button class="tf-btn" data-tf="3">3m</button>
            <button class="tf-btn active" data-tf="5">5m</button>
            <button class="tf-btn" data-tf="15">15m</button>
            <button class="tf-btn" data-tf="30">30m</button>
            <button class="tf-btn" data-tf="60">1H</button>
          </div>
          <button id="prevTradeBtn">◄ Prev Trade</button>
          <select id="tradeJumpSelect" style="max-width:230px;"></select>
          <button id="nextTradeBtn">Next Trade ►</button>
          <button id="resetZoomBtn">Reset View</button>
        </div>
      </div>
      <div class="tv-canvas-wrap">
        <canvas id="tvChart"></canvas>
      </div>
      <div class="tv-legend-bar">
        <div style="display:flex;gap:14px;flex-wrap:wrap;">
          <span class="legend-item"><span class="swatch" style="background:rgba(38,166,154,0.45);border:1px solid #26a69a;"></span>TP Target Zone (`TP HIT`)</span>
          <span class="legend-item"><span class="swatch" style="background:rgba(239,83,80,0.45);border:1px solid #ef5350;"></span>Stop Loss Zone (`SL HIT`)</span>
          <span class="legend-item"><span class="swatch" style="background:#3b82f6;"></span>`◄── TRAILING SL` (RYAN Phase 2 / Phase 4 Lock)</span>
          <span class="legend-item"><span class="swatch" style="background:#f59e0b;"></span>TP1 (50% Partial Bank)</span>
        </div>
        <div>Scroll Wheel: Zoom · Click & Drag: Pan · Click Any Calendar Day or Table Row to Inspect</div>
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
let selectedCalendarDate = null;
let currentMonthIdx = 0;
let availableMonths = [];

// Chart pan/zoom state
let viewStartIdx = 0;
let viewEndIdx = 80;
let isDragging = false;
let dragStartX = 0;
let hoverMouse = null;

function initDashboard() {
  const profSelect = document.getElementById("profileSelect");
  profSelect.innerHTML = "";
  Object.keys(PAYLOAD.profiles).forEach(k => {
    const p = PAYLOAD.profiles[k];
    const opt = document.createElement("option");
    opt.value = k;
    opt.textContent = `${k} — ${p.meta.label} (${p.trades.length} Trades)`;
    if (k === currentProfileKey) opt.selected = true;
    profSelect.appendChild(opt);
  });

  profSelect.addEventListener("change", () => {
    currentProfileKey = profSelect.value;
    selectedCalendarDate = null;
    populateFilterDropdowns();
    applyFilters();
  });

  document.getElementById("clearFiltersBtn").addEventListener("click", () => {
    selectedCalendarDate = null;
    document.getElementById("filterAgent").value = "ALL";
    document.getElementById("filterDir").value = "ALL";
    document.getElementById("filterOutcome").value = "ALL";
    document.getElementById("filterMistake").value = "ALL";
    applyFilters();
  });

  ["filterAgent", "filterDir", "filterOutcome", "filterMistake"].forEach(id => {
    document.getElementById(id).addEventListener("change", applyFilters);
  });

  document.querySelectorAll(".tf-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentTF = parseInt(btn.getAttribute("data-tf"), 10);
      resetChartViewport();
      drawTradingViewChart();
    });
  });

  document.getElementById("prevTradeBtn").addEventListener("click", () => stepTrade(-1));
  document.getElementById("nextTradeBtn").addEventListener("click", () => stepTrade(1));
  document.getElementById("resetZoomBtn").addEventListener("click", () => {
    resetChartViewport();
    drawTradingViewChart();
  });
  document.getElementById("tradeJumpSelect").addEventListener("change", e => {
    const id = parseInt(e.target.value, 10);
    const t = filteredTrades.find(x => x.id === id);
    if (t) selectTrade(t, false);
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
  applyFilters();
  window.addEventListener("resize", () => {
    drawTradingViewChart();
    drawEquityChart();
  });
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

function applyFilters() {
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

  if (filteredTrades.length > 0) {
    selectTrade(filteredTrades[0], false);
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
  selectTrade(filteredTrades[nextIdx], false);
}

function selectTrade(trade, scrollToChart = true) {
  selectedTrade = trade;
  document.getElementById("tradeJumpSelect").value = String(trade.id);
  document.querySelectorAll("#tradeTableBody tr").forEach(tr => {
    tr.classList.toggle("selected-row", parseInt(tr.getAttribute("data-id"), 10) === trade.id);
  });
  resetChartViewport();
  drawTradingViewChart();
  renderTradeInspector(trade);
  if (scrollToChart) {
    document.querySelector(".tv-workspace").scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function getResampledCandles(trade, tfMins) {
  const raw = PAYLOAD.candles[trade.w_key] || [];
  if (tfMins === 1) {
    return raw.map(b => ({ time: b[0], open: b[1], high: b[2], low: b[3], close: b[4], vol: b[5] }));
  }
  const bucketSec = tfMins * 60;
  const map = new Map();
  for (let i = 0; i < raw.length; i++) {
    const b = raw[i];
    const bucket = Math.floor(b[0] / bucketSec) * bucketSec;
    let cur = map.get(bucket);
    if (!cur) {
      cur = { time: bucket, open: b[1], high: b[2], low: b[3], close: b[4], vol: b[5] };
      map.set(bucket, cur);
    } else {
      if (b[2] > cur.high) cur.high = b[2];
      if (b[3] < cur.low) cur.low = b[3];
      cur.close = b[4];
      cur.vol += b[5];
    }
  }
  return Array.from(map.values());
}

function resetChartViewport() {
  if (!selectedTrade) return;
  const bars = getResampledCandles(selectedTrade, currentTF);
  if (!bars.length) return;
  const bucketSec = currentTF * 60;
  const entBucket = Math.floor(selectedTrade.entry_ts / bucketSec) * bucketSec;
  const extBucket = Math.floor(selectedTrade.exit_ts / bucketSec) * bucketSec;
  let iEnt = bars.findIndex(b => b.time >= entBucket);
  let iExt = bars.findIndex(b => b.time >= extBucket);
  if (iEnt < 0) iEnt = Math.floor(bars.length / 3);
  if (iExt < iEnt) iExt = Math.min(bars.length - 1, iEnt + 10);
  const padLeft = Math.max(18, Math.round((iExt - iEnt) * 1.4));
  const padRight = Math.max(18, Math.round((iExt - iEnt) * 1.1));
  viewStartIdx = Math.max(0, iEnt - padLeft);
  viewEndIdx = Math.min(bars.length - 1, Math.max(iExt + padRight, viewStartIdx + 35));
}

function getOutcomeBanner(trade) {
  if (trade.exit_reason.includes("TP2")) return { label: "TP HIT", cls: "badge-tp", type: "TP" };
  if (trade.exit_reason.includes("TRAIL_STOP")) return { label: "TRAILING SL", cls: "badge-trail", type: "TRAIL" };
  if (trade.exit_reason === "STOP_LOSS") return { label: "SL HIT", cls: "badge-sl", type: "SL" };
  return { label: "TIME EXIT (" + (trade.r_multiple >= 0 ? "+" : "") + trade.r_multiple.toFixed(2) + "R)", cls: "badge-time", type: "TRAIL" };
}

function drawTradingViewChart() {
  const canvas = document.getElementById("tvChart");
  if (!canvas || !selectedTrade) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const W = rect.width;
  const H = rect.height;
  const rightAxisW = 78;
  const bottomAxisH = 28;
  const topHeaderH = 44;
  const plotW = W - rightAxisW;
  const plotH = H - bottomAxisH - topHeaderH;

  // TradingView Dark Canvas Background
  ctx.fillStyle = "#0f1117";
  ctx.fillRect(0, 0, W, H);

  const allBars = getResampledCandles(selectedTrade, currentTF);
  if (!allBars.length) return;

  const sIdx = Math.max(0, Math.min(allBars.length - 5, Math.floor(viewStartIdx)));
  const eIdx = Math.max(sIdx + 5, Math.min(allBars.length - 1, Math.ceil(viewEndIdx)));
  const bars = allBars.slice(sIdx, eIdx + 1);

  const bucketSec = currentTF * 60;
  const entBucket = Math.floor(selectedTrade.entry_ts / bucketSec) * bucketSec;
  const extBucket = Math.floor(selectedTrade.exit_ts / bucketSec) * bucketSec;

  let entBarIdx = bars.findIndex(b => b.time >= entBucket);
  let extBarIdx = bars.findIndex(b => b.time >= extBucket);
  if (entBarIdx === -1) entBarIdx = 0;
  if (extBarIdx === -1) extBarIdx = bars.length - 1;

  // Compute Price Y-Scale including trade SL, TP1, TP2, Entry, Exit
  let minP = Math.min(selectedTrade.sl_price, selectedTrade.tp2_price, selectedTrade.entry_price, selectedTrade.exit_price);
  let maxP = Math.max(selectedTrade.sl_price, selectedTrade.tp2_price, selectedTrade.entry_price, selectedTrade.exit_price);
  bars.forEach(b => {
    if (b.low < minP) minP = b.low;
    if (b.high > maxP) maxP = b.high;
  });
  const padP = Math.max(1.5, (maxP - minP) * 0.12);
  minP -= padP;
  maxP += padP;

  const yOf = p => topHeaderH + plotH * (1.0 - (p - minP) / (maxP - minP));
  const stepX = plotW / Math.max(1, bars.length);
  const xOf = idx => (idx + 0.5) * stepX;

  // Subtle Grid Lines
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
  const tSteps = Math.min(10, bars.length);
  const tStride = Math.max(1, Math.floor(bars.length / tSteps));
  for (let i = 0; i < bars.length; i += tStride) {
    const px = xOf(i);
    ctx.beginPath();
    ctx.moveTo(px, topHeaderH);
    ctx.lineTo(px, topHeaderH + plotH);
    ctx.stroke();
  }

  // =========================================================================
  // TRADINGVIEW POSITION DRAWING TOOL (EXACT MATCH TO USER'S 3 SCREENSHOTS)
  // =========================================================================
  const xEnt = xOf(entBarIdx);
  const xExt = Math.max(xEnt + Math.max(stepX * 4, 52), xOf(extBarIdx));
  const yEnt = yOf(selectedTrade.entry_price);
  const ySL = yOf(selectedTrade.sl_price);
  const yTP1 = yOf(selectedTrade.tp1_price);
  const yTP2 = yOf(selectedTrade.tp2_price);
  const yExit = yOf(selectedTrade.exit_price);

  const outcome = getOutcomeBanner(selectedTrade);

  // 1. Outer Target Profit Zone (Teal-Green Box: Entry -> TP2)
  const topTP = Math.min(yEnt, yTP2);
  const hTP = Math.abs(yTP2 - yEnt);
  ctx.fillStyle = outcome.type === "TP" ? "rgba(38, 166, 154, 0.24)" : "rgba(38, 166, 154, 0.14)";
  ctx.fillRect(xEnt, topTP, xExt - xEnt, hTP);
  ctx.strokeStyle = "rgba(38, 166, 154, 0.45)";
  ctx.lineWidth = 1;
  ctx.strokeRect(xEnt, topTP, xExt - xEnt, hTP);

  // 2. If TRAILING SL hit (or positive Time Exit), draw brighter inner locked-profit box (Entry -> Exit Price)
  if (outcome.type === "TRAIL" && ((selectedTrade.direction === "LONG" && selectedTrade.exit_price > selectedTrade.entry_price) ||
      (selectedTrade.direction === "SHORT" && selectedTrade.exit_price < selectedTrade.entry_price))) {
    const topLock = Math.min(yEnt, yExit);
    const hLock = Math.abs(yExit - yEnt);
    ctx.fillStyle = "rgba(38, 166, 154, 0.30)";
    ctx.fillRect(xEnt, topLock, xExt - xEnt, hLock);
    ctx.strokeStyle = "rgba(38, 166, 154, 0.65)";
    ctx.strokeRect(xEnt, topLock, xExt - xEnt, hLock);
  }

  // 3. Stop Loss Risk Zone (Crimson-Red Box: Entry -> SL)
  const topSL = Math.min(yEnt, ySL);
  const hSL = Math.abs(ySL - yEnt);
  ctx.fillStyle = outcome.type === "SL" ? "rgba(239, 83, 80, 0.28)" : "rgba(239, 83, 80, 0.20)";
  ctx.fillRect(xEnt, topSL, xExt - xEnt, hSL);
  ctx.strokeStyle = "rgba(239, 83, 80, 0.50)";
  ctx.strokeRect(xEnt, topSL, xExt - xEnt, hSL);

  // 4. Subtle TP1 (50% Partial Profit) internal dashed line
  ctx.save();
  ctx.setLineDash([4, 4]);
  ctx.strokeStyle = "rgba(245, 158, 11, 0.45)";
  ctx.beginPath();
  ctx.moveTo(xEnt, yTP1);
  ctx.lineTo(xExt, yTP1);
  ctx.stroke();
  ctx.restore();

  // 5. Crisp Horizontal Entry Separator Line
  ctx.strokeStyle = "rgba(226, 232, 240, 0.85)";
  ctx.lineWidth = 1.25;
  ctx.beginPath();
  ctx.moveTo(xEnt, yEnt);
  ctx.lineTo(xExt, yEnt);
  ctx.stroke();

  // 6. Diagonal Dashed Execution Path Line from (xEnt, yEnt) -> (xOf(extBarIdx), yExit)
  ctx.save();
  ctx.setLineDash([5, 4]);
  ctx.strokeStyle = "rgba(226, 232, 240, 0.55)";
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.moveTo(xEnt, yEnt);
  ctx.lineTo(xOf(extBarIdx), yExit);
  ctx.stroke();
  ctx.restore();

  // =========================================================================
  // DRAW REAL GC.v.0 OHLCV CANDLESTICKS
  // =========================================================================
  const bodyW = Math.max(2, Math.min(14, stepX * 0.68));
  for (let i = 0; i < bars.length; i++) {
    const b = bars[i];
    const cx = xOf(i);
    const isBull = b.close >= b.open;
    const color = isBull ? "#26a69a" : "#ef5350";

    const yH = yOf(b.high);
    const yL = yOf(b.low);
    const yO = yOf(b.open);
    const yC = yOf(b.close);

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.15;
    ctx.beginPath();
    ctx.moveTo(cx, yH);
    ctx.lineTo(cx, yL);
    ctx.stroke();

    const bTop = Math.min(yO, yC);
    const bHeight = Math.max(1.5, Math.abs(yC - yO));
    ctx.fillStyle = color;
    ctx.fillRect(cx - bodyW / 2, bTop, bodyW, bHeight);
  }

  // =========================================================================
  // LABELS OVERLAY (MATCHING SCREENSHOTS: "TP HIT", "SL HIT", "◄── TRAILING SL")
  // =========================================================================
  ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
  ctx.textAlign = "center";
  const boxCenterX = (xEnt + xExt) / 2;

  if (outcome.type === "TP") {
    ctx.fillStyle = "#38bdf8";
    ctx.fillText("TP HIT", boxCenterX, (yEnt + yTP2) / 2 + 4);
  } else if (outcome.type === "SL") {
    ctx.fillStyle = "#38bdf8";
    ctx.fillText("SL HIT", boxCenterX, (yEnt + yTP2) / 2 + 4);
  } else {
    // TRAILING SL Blue Line + Blue Left Arrow + "TRAILING SL" Text (matching Screenshot 3)
    const lineLeft = Math.max(10, xEnt - 24);
    const lineRight = Math.min(plotW - 10, xExt + 10);
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(lineLeft, yExit);
    ctx.lineTo(lineRight, yExit);
    ctx.stroke();

    // Blue Left-Pointing Arrowhead at right edge of box
    const arrowTipX = lineRight + 4;
    ctx.fillStyle = "#3b82f6";
    ctx.beginPath();
    ctx.moveTo(arrowTipX, yExit);
    ctx.lineTo(arrowTipX + 12, yExit - 7);
    ctx.lineTo(arrowTipX + 12, yExit + 7);
    ctx.closePath();
    ctx.fill();

    ctx.textAlign = "left";
    ctx.fillStyle = "#4f8ff7";
    ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif";
    ctx.fillText(outcome.label, arrowTipX + 18, yExit + 4);
  }

  // Dotted Horizontal Exit Price Line Across Chart
  ctx.save();
  ctx.setLineDash([2, 3]);
  ctx.strokeStyle = "rgba(38, 166, 154, 0.5)";
  ctx.beginPath();
  ctx.moveTo(0, yExit);
  ctx.lineTo(plotW, yExit);
  ctx.stroke();
  ctx.restore();

  // =========================================================================
  // RIGHT PRICE AXIS & TRADINGVIEW PRICE PILLS
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

  drawPricePill(selectedTrade.tp2_price, "#26a69a");
  drawPricePill(selectedTrade.tp1_price, "#d97706");
  drawPricePill(selectedTrade.entry_price, "#475569");
  drawPricePill(selectedTrade.sl_price, "#ef5350");
  if (outcome.type === "TRAIL") {
    drawPricePill(selectedTrade.exit_price, "#2563eb");
  }

  // =========================================================================
  // BOTTOM TIME AXIS (UTC)
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
  for (let i = 0; i < bars.length; i += tStride) {
    const px = xOf(i);
    const d = new Date(bars[i].time * 1000);
    const hh = String(d.getUTCHours()).padStart(2, "0");
    const mm = String(d.getUTCMinutes()).padStart(2, "0");
    ctx.fillText(`${hh}:${mm}`, px, topHeaderH + plotH + 18);
  }

  // =========================================================================
  // TOP-LEFT TRADINGVIEW SYMBOL & OHLC WATERMARK HEADER
  // =========================================================================
  ctx.fillStyle = "rgba(15, 17, 23, 0.88)";
  ctx.fillRect(0, 0, plotW, topHeaderH);

  let inspectBar = bars[entBarIdx] || bars[bars.length - 1];
  if (hoverMouse && hoverMouse.x < plotW && hoverMouse.y > topHeaderH && hoverMouse.y < topHeaderH + plotH) {
    const hIdx = Math.max(0, Math.min(bars.length - 1, Math.floor(hoverMouse.x / stepX)));
    inspectBar = bars[hIdx];

    // Crosshair lines
    ctx.save();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = "rgba(148, 163, 184, 0.45)";
    ctx.beginPath();
    ctx.moveTo(xOf(hIdx), topHeaderH);
    ctx.lineTo(xOf(hIdx), topHeaderH + plotH);
    ctx.moveTo(0, hoverMouse.y);
    ctx.lineTo(plotW, hoverMouse.y);
    ctx.stroke();
    ctx.restore();

    const hoverPrice = maxP - ((hoverMouse.y - topHeaderH) / plotH) * (maxP - minP);
    drawPricePill(hoverPrice, "#334155");
  }

  const chg = inspectBar.close - inspectBar.open;
  const chgPct = (chg / inspectBar.open) * 100;
  ctx.textAlign = "left";
  ctx.font = "bold 12px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = "#e2e8f0";
  const tfLabel = currentTF === 60 ? "1H" : `${currentTF}m`;
  ctx.fillText(
    `Gold Futures (GC.v.0 · ${tfLabel} · CME Globex)   O ${inspectBar.open.toFixed(2)}   H ${inspectBar.high.toFixed(2)}   L ${inspectBar.low.toFixed(2)}   C ${inspectBar.close.toFixed(2)}   ${chg >= 0 ? "+" : ""}${chg.toFixed(2)} (${chg >= 0 ? "+" : ""}${chgPct.toFixed(2)}%)   Vol ${inspectBar.vol}`,
    12, 17
  );
  ctx.font = "11px -apple-system, BlinkMacSystemFont, sans-serif";
  ctx.fillStyle = "#94a3b8";
  ctx.fillText(
    `Trade #${selectedTrade.id} · ${selectedTrade.setup_agent} (${selectedTrade.setup_type}) · ${selectedTrade.direction} @ ${selectedTrade.entry_price.toFixed(2)} → ${selectedTrade.exit_price.toFixed(2)} · ${selectedTrade.r_multiple >= 0 ? "+" : ""}${selectedTrade.r_multiple.toFixed(2)}R (${selectedTrade.net_pnl_usd >= 0 ? "+" : ""}$${selectedTrade.net_pnl_usd.toFixed(2)} Net after $${selectedTrade.delta_fee_usd.toFixed(2)} Delta 0.01% Fee)`,
    12, 35
  );
}

function setupCanvasInteractions() {
  const canvas = document.getElementById("tvChart");
  canvas.addEventListener("wheel", e => {
    e.preventDefault();
    if (!selectedTrade) return;
    const allBars = getResampledCandles(selectedTrade, currentTF);
    const span = viewEndIdx - viewStartIdx;
    const factor = e.deltaY > 0 ? 1.15 : 0.85;
    const newSpan = Math.max(18, Math.min(allBars.length, span * factor));
    const center = (viewStartIdx + viewEndIdx) / 2;
    viewStartIdx = Math.max(0, center - newSpan / 2);
    viewEndIdx = Math.min(allBars.length - 1, viewStartIdx + newSpan);
    drawTradingViewChart();
  }, { passive: false });

  canvas.addEventListener("mousedown", e => {
    isDragging = true;
    dragStartX = e.clientX;
  });
  window.addEventListener("mouseup", () => { isDragging = false; });
  window.addEventListener("mousemove", e => {
    const rect = canvas.getBoundingClientRect();
    if (e.target === canvas) {
      hoverMouse = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    } else {
      hoverMouse = null;
    }
    if (isDragging && selectedTrade) {
      const allBars = getResampledCandles(selectedTrade, currentTF);
      const span = viewEndIdx - viewStartIdx;
      const dx = e.clientX - dragStartX;
      dragStartX = e.clientX;
      const barShift = -(dx / Math.max(100, rect.width - 80)) * span;
      viewStartIdx = Math.max(0, Math.min(allBars.length - span, viewStartIdx + barShift));
      viewEndIdx = Math.min(allBars.length - 1, viewStartIdx + span);
    }
    if (e.target === canvas || isDragging) drawTradingViewChart();
  });
  canvas.addEventListener("mouseleave", () => {
    hoverMouse = null;
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
      <h4 style="color:var(--gold);">🤝 All-Agent Blackboard Quorum (${t.confirming_count}/16 Confirming · ${t.consensus_pct.toFixed(1)}% Consensus)</h4>
      <div class="agent-pills">
        ${t.confirming_agents.map(a => `<span class="agent-pill">${a}</span>`).join("")}
      </div>
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

  const givebackPotential = givebacks.length * 5.0;
  const whipsawPotential = whipsaws.length * 5.0;

  document.getElementById("selfLearnerPanel").innerHTML = `
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
