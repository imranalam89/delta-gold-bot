"""
Upgrades `scripts/render_html.py` into the All-in-One Master Dashboard.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDER_PY = os.path.join(BASE_DIR, "scripts", "render_html.py")

with open(RENDER_PY, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add Lightweight Charts CDN to <head>
old_head = '<title>Syndicate Alpha — 16-Agent Institutional Gold Backtest, TradingView Chart & Self-Learner Terminal</title>'
new_head = """<title>Syndicate Alpha — All-in-One Master Operating System &amp; Backtest Lab</title>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>"""
code = code.replace(old_head, new_head)

# 2. Add Styles for Master Tab Bar, Hero Banner, Pod Matrix, and Specialist Lab
style_injection = """
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

  /* Specialist Lab Styles (Tab 2) */
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
    background: #141c2c;
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
    background: #141c2c;
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
"""
code = code.replace("  tr.selected-row td {", style_injection + "\n  tr.selected-row td {")

# 3. Add Export CSV button to top-header
old_controls = """  <div class="controls-row">
    <label for="profileSelect" style="color:var(--text-muted);font-weight:600;">Strategy / Setting Profile:</label>
    <select id="profileSelect"></select>
    <button id="clearFiltersBtn">Reset All Filters</button>
  </div>"""

new_controls = """  <div class="controls-row">
    <label for="profileSelect" style="color:var(--text-muted);font-weight:600;">Active Strategy / Pod:</label>
    <select id="profileSelect"></select>
    <button id="clearFiltersBtn">Reset Filters</button>
    <button id="exportCsvBtn" style="background:#1e3a5f;border-color:#3b82f6;color:#93c5fd;font-weight:700;">📥 Export CSV</button>
  </div>"""
code = code.replace(old_controls, new_controls)

# 4. Insert Master Tab Bar after </header>
master_tab_bar_html = """
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
"""
code = code.replace("</header>\n\n<div class=\"container\">", "</header>\n" + master_tab_bar_html + "\n<div class=\"container\">")

# 5. Wrap Container content into Tab Panes
# Let's inspect where container contents start and end
tab1_html = """
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
"""

# Replace top of container with tab1 and tab2, then open tab3
old_container_top = """<div class="container">
  <!-- KPI Summary Strip -->
  <div class="kpi-grid" id="kpiGrid"></div>

  <!-- TradingView Chart + Per-Trade Forensic Journal -->
  <div class="tv-workspace">"""

new_container_top = """<div class="container">
""" + tab1_html + """
  <!-- ========================================== -->
  <!-- TAB 3: TRADINGVIEW CONTINUOUS CHART        -->
  <!-- ========================================== -->
  <div id="tab-chart" class="tab-pane">
  <div class="tv-workspace">"""

code = code.replace(old_container_top, new_container_top)

# Close tab3 before Calendar and open tab4
old_cal_top = """  <!-- Monthly / Daily PnL Calendar + Equity & Drawdown Curve -->
  <div class="mid-grid">"""

new_cal_top = """  </div> <!-- /tab-chart -->

  <!-- ========================================== -->
  <!-- TAB 4: CALENDAR & EQUITY GROWTH           -->
  <!-- ========================================== -->
  <div id="tab-calendar" class="tab-pane">
  <div class="mid-grid">"""
code = code.replace(old_cal_top, new_cal_top)

# Close tab4 before Journal and open tab5
old_journal_top = """  <!-- Agent #17 Self-Learner Meta-Coach & 16-Agent Reliability Matrix -->
  <div class="learner-grid">"""

new_journal_top = """  </div> <!-- /tab-calendar -->

  <!-- ========================================== -->
  <!-- TAB 5: TRADE JOURNAL & FORENSIC AUDITOR   -->
  <!-- ========================================== -->
  <div id="tab-journal" class="tab-pane">
  <div class="learner-grid">"""
code = code.replace(old_journal_top, new_journal_top)

# Close tab5 at the end of the container
old_container_end = """    </div>
  </div>

</div>

<script>"""

new_container_end = """    </div>
  </div>
  </div> <!-- /tab-journal -->

</div>

<script>"""
code = code.replace(old_container_end, new_container_end)

# Also in tab4, let's make sure the second equity canvas has id="equityCanvasTab4"
code = code.replace('<canvas id="equityCanvas" style="width:100%;height:100%;display:block;"></canvas>', '<canvas id="equityCanvasTab4" style="width:100%;height:100%;display:block;"></canvas>', 1)
# Note: the first equity canvas is inside Tab 1, and the second is in Tab 4

# Now update JavaScript:
# 6. Set default profile to 1_ALL_11_AGENTS_NON_OVERLAPPING_MASTER
code = code.replace(
    'let currentProfileKey = "3_SNIPER_HIGH_RR_RUNNER";',
    'let currentProfileKey = "1_ALL_11_AGENTS_NON_OVERLAPPING_MASTER";'
)

# 7. Inject master additions (switchMasterTab, renderPodMatrixTable, exportTradesCSV, and lab functions)
# Let's append master additions before `initDashboard();`
master_js_code = """
// =========================================================================
// ALL-IN-ONE MASTER TERMINAL EXTENSIONS (TABS, POD MATRIX, 11-AGENT LAB)
// =========================================================================

window.switchMasterTab = function(tabId) {
  document.querySelectorAll('.master-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === tabId);
  });
  if (tabId === 'tab-chart') {
    requestAnimationFrame(() => {
      onWindowResize();
      drawTradingViewChart();
    });
  } else if (tabId === 'tab-calendar' || tabId === 'tab-master-floor') {
    requestAnimationFrame(() => {
      drawEquityChart();
    });
  } else if (tabId === 'tab-agent-lab') {
    if (labChart) {
      setTimeout(() => {
        labChart.timeScale().fitContent();
      }, 100);
    }
  }
};

const POD_PROFILES_META = [
  {
    key: "1_ALL_11_AGENTS_NON_OVERLAPPING_MASTER",
    title: "1. 🏆 ALL 11 AGENTS NON-OVERLAPPING MASTER",
    badge: "CHAMPION MASTER BOOK",
    desc: "Unified multi-agent execution across all 11 specialists. Zero overlapping trades. Highest net return and optimal 2.69 trades/day cadence.",
    agents: "All 11 Specialists (ALEX, MAYA, MARCUS, NINA, MAX, SOPHIA, DEREK, ELENA, SAM, OMAR, LIAM)"
  },
  {
    key: "2_POD_MARCUS_SOPHIA_BREAKOUT",
    title: "2. 🚀 POD: MARCUS + SOPHIA",
    badge: "HIGH WIN RATE BREAKOUT",
    desc: "Synergistic breakout pod: MARCUS Asian/London range box breaks confirmed by SOPHIA macro killzone timing.",
    agents: "3:MARCUS (Box Breakouts) + 6:SOPHIA (Macro Killzones)"
  },
  {
    key: "3_POD_MAYA_SAM_LIQUIDITY",
    title: "3. 💧 POD: MAYA + SAM",
    badge: "LOW DRAWDOWN LIQUIDITY",
    desc: "Liquidity trap hunter: SAM Level-2 deep book pool sweeps backed by MAYA price action rejection wicks.",
    agents: "2:MAYA (Price Action) + 9:SAM (Level-2 Liquidity Pools)"
  },
  {
    key: "4_POD_MAYA_LIAM_VSA_SCALP",
    title: "4. ⚡ POD: MAYA + LIAM",
    badge: "MOMENTUM SCALP POD",
    desc: "Ultra-fast order flow scalp: LIAM institutional volume spread analysis paired with MAYA structural flips.",
    agents: "2:MAYA (Price Action) + 11:LIAM (VSA / VWAP)"
  },
  {
    key: "5_POD_SOPHIA_LIAM_MOMENTUM",
    title: "5. 🎯 POD: SOPHIA + LIAM",
    badge: "MACRO TREND RUNNER",
    desc: "Macro trend capture: SOPHIA London/NY Silver Bullet timing aligned with LIAM institutional VWAP deviations.",
    agents: "6:SOPHIA (Macro Killzones) + 11:LIAM (VSA / VWAP)"
  },
  {
    key: "6_POD_ALL_STAR_COUNCIL_RELAY",
    title: "6. 🛡️ POD: ALL-STAR COUNCIL RELAY",
    badge: "BALANCED RELAY POD",
    desc: "Rotational all-star council relay combining top-scoring specialist signals with 16-agent cross-confirmation.",
    agents: "All-Star Relay (MARCUS, MAYA, SOPHIA, SAM, LIAM, ELENA)"
  }
];

function renderPodMatrixTable() {
  const tbody = document.getElementById("podMatrixBody");
  if (!tbody) return;
  tbody.innerHTML = POD_PROFILES_META.map(pm => {
    const pdata = PAYLOAD.profiles[pm.key];
    if (!pdata) return "";
    const trades = pdata.trades || [];
    const n = trades.length;
    const wins = trades.filter(t => t.net_pnl_usd > 0).length;
    const wr = n ? (wins / n * 100).toFixed(2) : "0.00";
    const net = trades.reduce((acc, t) => acc + t.net_pnl_usd, 0);
    const endEq = trades.length ? trades[trades.length - 1].equity_after : 100.0;
    
    let peak = 100.0;
    let maxDd = 0.0;
    trades.forEach(t => {
      if (t.equity_after > peak) peak = t.equity_after;
      const dd = (peak - t.equity_after) / peak * 100.0;
      if (dd > maxDd) maxDd = dd;
    });

    const gw = trades.filter(t => t.gross_pnl_usd > 0).reduce((a, t) => a + t.gross_pnl_usd, 0);
    const gl = Math.abs(trades.filter(t => t.gross_pnl_usd < 0).reduce((a, t) => a + t.gross_pnl_usd, 0));
    const pf = gl > 0 ? (gw / gl).toFixed(2) : "9.99";
    const cadence = (n / 110.0).toFixed(2);
    const isCur = (pm.key === currentProfileKey);

    return `
      <tr class="${isCur ? 'active-row' : ''}">
        <td>
          <b style="color:${isCur ? '#34d399' : '#f8fafc'};">${pm.title}</b><br/>
          <span class="badge ${pm.key.includes('MASTER') ? 'badge-tp' : 'badge-trail'}">${pm.badge}</span>
        </td>
        <td style="color:#cbd5e1;font-size:11.5px;max-width:280px;">${pm.desc}</td>
        <td style="font-size:11px;color:#93c5fd;">${pm.agents}</td>
        <td><b>${n}</b></td>
        <td><span class="pill" style="background:#1e293b;color:#93c5fd;font-weight:700;">${cadence}/day</span></td>
        <td style="color:#34d399;font-weight:800;">${wr}%</td>
        <td style="color:#fbbf24;font-weight:700;">${pf}</td>
        <td style="color:${net >= 0 ? '#34d399' : '#f87171'};font-weight:800;">${net >= 0 ? '+' : ''}$${net.toFixed(2)}</td>
        <td style="font-weight:800;color:#f8fafc;">$${endEq.toFixed(2)}</td>
        <td style="color:#f87171;font-weight:700;">-${maxDd.toFixed(2)}%</td>
        <td>
          <button class="pod-select-btn" onclick="selectProfileFromMatrix('${pm.key}')">
            ${isCur ? '✓ Active' : 'Select & Inspect'}
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

window.selectProfileFromMatrix = function(pname) {
  const sel = document.getElementById("profileSelect");
  if (sel) {
    sel.value = pname;
    currentProfileKey = pname;
    selectedCalendarDate = null;
    populateFilterDropdowns();
    applyFilters();
    renderPodMatrixTable();
  }
};

window.exportTradesCSV = function() {
  const trades = PAYLOAD.profiles[currentProfileKey]?.trades || [];
  if (!trades.length) {
    alert("No trades found in active profile to export.");
    return;
  }
  const headers = [
    "id","entry_time","exit_time","direction","setup_agent","setup_type","regime",
    "entry_price","exit_price","sl_price","tp1_price","tp2_price","init_risk_pts",
    "r_multiple","qty_oz","gross_pnl_usd","delta_fee_usd","net_pnl_usd","equity_after",
    "consensus_pct","confirming_count","exit_reason","hold_mins","mfe_r","mae_r","mistake_code"
  ];
  let csv = headers.join(",") + "\\n";
  trades.forEach(t => {
    const row = [
      t.id,
      `"${t.entry_time}"`,
      `"${t.exit_time}"`,
      t.direction,
      `"${t.setup_agent}"`,
      `"${t.setup_type}"`,
      `"${t.regime}"`,
      t.entry_price,
      t.exit_price,
      t.sl_price,
      t.tp1_price,
      t.tp2_price,
      t.init_risk_pts,
      t.r_multiple,
      t.qty_oz,
      t.gross_pnl_usd,
      t.delta_fee_usd,
      t.net_pnl_usd,
      t.equity_after,
      t.consensus_pct,
      t.confirming_count,
      `"${t.exit_reason}"`,
      t.hold_mins,
      t.mfe_r,
      t.mae_r,
      `"${t.mistake_code}"`
    ];
    csv += row.join(",") + "\\n";
  });
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `trades_${currentProfileKey}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

// 11-Agent Lab Engine
const LAB_AGENTS = PAYLOAD.agent_lab || {};
const LAB_CANDLES_15M = PAYLOAD.lab_candles || [];
let labCurrentAgentId = '1:ALEX';
if (!LAB_AGENTS[labCurrentAgentId]) {
  labCurrentAgentId = Object.keys(LAB_AGENTS)[0] || '1:ALEX';
}
let labCurrentKey = 'v3.0_ORACLE_CHAMPION';
let labChart = null;
let labCandleSeries = null;
let labPriceLines = [];

function initLab() {
  if (!Object.keys(LAB_AGENTS).length) return;
  renderLabRoadmap();
  renderLabLeaderboard();
  initLabChart();
  selectLabAgent(labCurrentAgentId);
}

function renderLabRoadmap() {
  const container = document.getElementById("labRoadmapBar");
  if (!container) return;
  const pills = Object.keys(LAB_AGENTS).map(aid => {
    const data = LAB_AGENTS[aid];
    const g3 = data.generations?.["v3.0_ORACLE_CHAMPION"] || {};
    const wr = g3.win_rate !== undefined ? g3.win_rate.toFixed(1) : "0.0";
    const cpd = g3.trades_per_day || "2.5";
    return `
      <div class="agent-step ${aid === labCurrentAgentId ? 'active' : ''}" id="lab-step-${aid}" onclick="selectLabAgent('${aid}')">
        <div class="num">${aid}</div>
        <div class="role">${data.agent_role || ''}</div>
        <span class="st">✓ ${wr}% (${cpd}/d)</span>
      </div>
    `;
  });
  container.innerHTML = pills.join("");
}

function renderLabLeaderboard() {
  const tbody = document.getElementById("labLeaderboardBody");
  if (!tbody) return;
  tbody.innerHTML = Object.keys(LAB_AGENTS).map(aid => {
    const data = LAB_AGENTS[aid];
    const g1 = data.generations?.["v1.0_BASELINE"] || {};
    const g2 = data.generations?.["v2.0_GRID_OPTIMIZED"] || {};
    const g3 = data.generations?.["v3.0_ORACLE_CHAMPION"] || {};
    const tfs = data.timeframes || {};
    const tf1m = tfs["1m"] || {};
    const tf5m = tfs["5m"] || {};
    const tf15m = tfs["15m"] || {};
    const tf1h = tfs["1h"] || {};
    return `
      <tr onclick="selectLabAgent('${aid}')" style="cursor:pointer;">
        <td><b>${aid}</b></td>
        <td>${data.agent_role || ''}</td>
        <td style="color:#94a3b8;font-size:11px;">${data.agent_focus || ''}</td>
        <td style="color:#f87171;">${g1.win_rate || 0}% ($${(g1.net_pnl || 0).toFixed(0)})</td>
        <td style="color:#60a5fa;">${g2.win_rate || 0}% ($${(g2.net_pnl || 0).toFixed(0)})</td>
        <td><b>${g3.trades_count || 0}</b> <span class="pill" style="background:#1e293b;color:#93c5fd;">${g3.trades_per_day || 0}/day</span></td>
        <td style="color:#34d399;font-weight:800;">${g3.win_rate || 0}%</td>
        <td style="color:#fbbf24;font-weight:700;">${g3.profit_factor || 0}</td>
        <td style="color:#34d399;font-weight:800;">+$${(g3.net_pnl || 0).toFixed(2)}</td>
        <td><b>$${(g3.end_equity || 100).toFixed(2)}</b></td>
        <td style="color:#f87171;">-${g3.max_dd_pct || 0}%</td>
        <td style="color:#34d399;font-size:11px;">
          <b>1m:</b> ${tf1m.win_rate || 0}% | <b>5m:</b> ${tf5m.win_rate || 0}% | <b>15m:</b> ${tf15m.win_rate || 0}% | <b>1h:</b> ${tf1h.win_rate || 0}%
        </td>
      </tr>
    `;
  }).join("");
}

function initLabChart() {
  const container = document.getElementById("lab-tv-chart");
  if (!container || !window.LightweightCharts) return;
  try {
    labChart = LightweightCharts.createChart(container, {
      layout: { background: { color: "#070b14" }, textColor: "#94a3b8" },
      grid: { vertLines: { color: "#111c33" }, horzLines: { color: "#111c33" } },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#1e293b" },
      timeScale: { borderColor: "#1e293b", timeVisible: true, secondsVisible: false },
    });
    labCandleSeries = labChart.addCandlestickSeries({
      upColor: "#10b981", downColor: "#ef4444",
      borderUpColor: "#10b981", borderDownColor: "#ef4444",
      wickUpColor: "#10b981", wickDownColor: "#ef4444",
    });
    if (LAB_CANDLES_15M && LAB_CANDLES_15M.length) {
      labCandleSeries.setData(LAB_CANDLES_15M);
      labChart.timeScale().fitContent();
    }
  } catch (e) {
    console.warn("LightweightCharts init error:", e);
  }
}

window.fitLabChart = function() {
  if (labChart) labChart.timeScale().fitContent();
};

window.selectLabAgent = function(agentId) {
  labCurrentAgentId = agentId;
  const lab = LAB_AGENTS[agentId];
  if (!lab) return;

  document.querySelectorAll(".roadmap-bar .agent-step").forEach(el => el.classList.remove("active"));
  const stepEl = document.getElementById("lab-step-" + agentId);
  if (stepEl) stepEl.classList.add("active");

  const g3 = lab.generations?.["v3.0_ORACLE_CHAMPION"] || {};
  const titleEl = document.getElementById("lab-header-title");
  if (titleEl) {
    titleEl.innerHTML = `🧪 SYNDICATE 11-AGENT SPECIALIST LAB — <code>${lab.agent_name || agentId}</code> (${g3.win_rate || 0}% WR • ${g3.trades_per_day || 0} Trades/Day)`;
  }
  const subEl = document.getElementById("lab-header-sub");
  if (subEl) {
    subEl.innerHTML = `Focus: <b>${lab.agent_focus || ''}</b> • <b>${g3.trades_count || 0} Trades (${g3.trades_per_day || 0}/day)</b> • Win Rate: <b>${g3.win_rate || 0}%</b> • Net Profit: <b>+$${(g3.net_pnl || 0).toFixed(2)} ($${(g3.end_equity || 100).toFixed(2)} Eq)</b> • Audited by <code>12:SARAH</code>, <code>17:LUCAS</code> &amp; <code>18:ORACLE</code>`;
  }

  const modeLbl = document.getElementById("lab-mode-lbl");
  if (modeLbl) modeLbl.textContent = `SELECT ${agentId} JOURNAL VIEW:`;
  const chartTitle = document.getElementById("lab-chart-title");
  if (chartTitle) chartTitle.textContent = `📈 Full 5-Month Interactive Chart — ${agentId} Trade Markers & Trade #IDs`;
  const comboTitle = document.getElementById("lab-combo-title");
  if (comboTitle) comboTitle.textContent = `🧮 ${agentId} — All ${lab.total_combinations_tested || 0} Valid Backtested Combinations (${lab.high_wr_combinations_count || 0} Combos >= 60% WR)`;
  const journalTitle = document.getElementById("lab-journal-title");
  if (journalTitle) journalTitle.textContent = `📜 ${agentId} Trade Journal`;

  const fltEma = document.getElementById("flt-lab-ema");
  if (fltEma && lab.all_combos_summary) {
    const structSet = [...new Set(lab.all_combos_summary.map(r => r.ema_setting))];
    fltEma.innerHTML = `<option value="ALL">ALL Signal Variants</option>` + structSet.map(s => `<option value="${s}">${s}</option>`).join("");
  }

  renderLabEvolutionCards();
  renderLabTimeframeCards();
  renderLabCombosTable();
  selectLabJournal("v3.0_ORACLE_CHAMPION", document.getElementById("lab-btn-v3"));
};

function getLabDataset(key) {
  const lab = LAB_AGENTS[labCurrentAgentId];
  if (!lab) return {};
  if (key === "TF_1m") {
    return lab.generations?.["v3.0_ORACLE_CHAMPION"] || {};
  }
  if (key.startsWith("TF_")) {
    const tf = key.replace("TF_", "");
    return lab.timeframes?.[tf] || {};
  }
  return lab.generations?.[key] || {};
}

window.selectLabJournal = function(key, btn) {
  labCurrentKey = key;
  const dataset = getLabDataset(key);
  document.querySelectorAll(".lab-mode-tabs .lab-mode-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  renderLabKPIs(dataset);
  renderLabChartMarkers(dataset);
  renderLabJournalTable(dataset);
  initLabCalendarMonths(dataset);
  if (dataset.trades && dataset.trades.length > 0) {
    inspectLabTrade(dataset.trades[0]);
  }
};

function renderLabEvolutionCards() {
  const lab = LAB_AGENTS[labCurrentAgentId];
  if (!lab) return;
  const g1 = lab.generations?.["v1.0_BASELINE"] || {};
  const g2 = lab.generations?.["v2.0_GRID_OPTIMIZED"] || {};
  const g3 = lab.generations?.["v3.0_ORACLE_CHAMPION"] || {};

  const container = document.getElementById("lab-evo-cards");
  if (!container) return;
  container.innerHTML = `
    <div class="evo-card">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-weight:800;color:#f87171;">GEN 1: v1.0 RAW UNFILTERED</span>
        <span class="pill short">No 12:SARAH Filter</span>
      </div>
      <div style="margin:6px 0;font-size:12px;color:#cbd5e1;">
        Trades: <b>${g1.trades_count || 0}</b> | Win Rate: <b>${g1.win_rate || 0}%</b> | PF: <b>${g1.profit_factor || 0}</b> |
        Net PnL: <b style="color:${(g1.net_pnl || 0) >= 0 ? '#34d399' : '#f87171'};">${(g1.net_pnl || 0) >= 0 ? '+' : ''}$${(g1.net_pnl || 0).toFixed(2)}</b> | Max DD: <b>${g1.max_dd_pct || 0}%</b>
      </div>
      <div style="font-size:11.5px;color:#94a3b8;border-top:1px solid #1e293b;padding-top:6px;">
        <b>🧠 12:SARAH &amp; 17:LUCAS Diagnosis:</b><br/>
        • ${lab.diag_g1 || 'No notes'}
      </div>
    </div>

    <div class="evo-card">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-weight:800;color:#60a5fa;">GEN 2: v2.0 + 12:SARAH ENTRY (WIDE TRAIL)</span>
        <span class="pill" style="background:rgba(59,130,246,0.2);color:#93c5fd;">${g2.win_rate || 0}% WR</span>
      </div>
      <div style="margin:6px 0;font-size:12px;color:#cbd5e1;">
        Trades: <b>${g2.trades_count || 0} (${g2.trades_per_day || 0}/day)</b> | Win Rate: <b>${g2.win_rate || 0}%</b> | PF: <b>${g2.profit_factor || 0}</b> |
        Net PnL: <b style="color:${(g2.net_pnl || 0) >= 0 ? '#34d399' : '#f87171'};">${(g2.net_pnl || 0) >= 0 ? '+' : ''}$${(g2.net_pnl || 0).toFixed(2)}</b> | Max DD: <b>${g2.max_dd_pct || 0}%</b>
      </div>
      <div style="font-size:11.5px;color:#94a3b8;border-top:1px solid #1e293b;padding-top:6px;">
        <b>🔍 18:ORACLE Audit of Gen 2:</b><br/>
        • ${lab.diag_g2 || 'No notes'}
      </div>
    </div>

    <div class="evo-card champ">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="font-weight:800;color:#34d399;">🏆 GEN 3: v3.0 12:SARAH + 18:ORACLE (2–3/DAY)</span>
        <span class="pill long">${g3.win_rate || 0}% WR • ${g3.trades_per_day || 0}/Day!</span>
      </div>
      <div style="margin:6px 0;font-size:12px;color:#cbd5e1;">
        Trades: <b>${g3.trades_count || 0} (${g3.trades_per_day || 0}/day)</b> | Win Rate: <b style="color:#34d399;">${g3.win_rate || 0}%</b> | PF: <b style="color:#fbbf24;">${g3.profit_factor || 0}</b> |
        Net PnL: <b style="color:#34d399;">+$${(g3.net_pnl || 0).toFixed(2)} ($${(g3.end_equity || 100).toFixed(2)} Eq)</b> | Max DD: <b>${g3.max_dd_pct || 0}%</b>
      </div>
      <div style="font-size:11.5px;color:#d1fae5;border-top:1px solid rgba(16,185,129,0.3);padding-top:6px;">
        <b>✅ 12:SARAH Psychologist + 18:ORACLE Greed-Guard Trail:</b><br/>
        • ${lab.diag_g3 || 'No notes'}
      </div>
    </div>
  `;
}

function renderLabTimeframeCards() {
  const lab = LAB_AGENTS[labCurrentAgentId];
  if (!lab) return;
  const container = document.getElementById("lab-tf-cards");
  if (!container) return;
  const tfs = ["1m", "5m", "15m", "1h"];
  container.innerHTML = tfs.map(tf => {
    const d = lab.timeframes?.[tf] || {};
    const ss = d.sess_stats || {};
    const aPnl = ss.ASIA?.pnl || 0;
    const lPnl = ss.LONDON?.pnl || 0;
    const nPnl = ss.NEW_YORK?.pnl || 0;
    return `
      <div class="tf-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
          <span style="font-weight:800;color:#f8fafc;">⏱️ ${labCurrentAgentId} on <code>${tf}</code></span>
          <span class="pill ${(d.net_pnl || 0) >= 0 ? 'long' : 'short'}">${(d.net_pnl || 0) >= 0 ? '+' : ''}$${(d.net_pnl || 0).toFixed(2)}</span>
        </div>
        <div style="font-size:11.5px;color:#cbd5e1;">
          Trades: <b>${d.trades_count || 0}</b> | WR: <b style="color:#34d399;">${d.win_rate || 0}%</b> | PF: <b>${d.profit_factor || 0}</b> | Avg R: <b>${d.avg_r || 0}R</b>
        </div>
        <div style="font-size:11px;color:#94a3b8;margin-top:4px;">
          ASIA: <b>$${aPnl.toFixed(1)}</b> | LONDON: <b>$${lPnl.toFixed(1)}</b> | NY: <b>$${nPnl.toFixed(1)}</b>
        </div>
      </div>
    `;
  }).join("");
}

function renderLabKPIs(d) {
  const lab = LAB_AGENTS[labCurrentAgentId] || {};
  const stallCount = d.reasons?.SMART_STALL_LOCK || 0;
  const revCount = d.reasons?.REVERSAL_EXIT || 0;
  const container = document.getElementById("lab-kpi-row");
  if (!container) return;
  container.innerHTML = `
    <div class="kpi-card"><div class="kpi-label">Active Specialist</div><div class="kpi-val" style="font-size:14px;color:#60a5fa;">${labCurrentAgentId} (${labCurrentKey})</div><div class="kpi-sub">${lab.agent_role || ''}</div></div>
    <div class="kpi-card"><div class="kpi-label">Total Trades</div><div class="kpi-val">${d.trades_count || 0} <span style="font-size:12px;color:#93c5fd;">(${d.trades_per_day || (d.trades_count ? (d.trades_count/110).toFixed(2) : '0')}/d)</span></div><div class="kpi-sub">${d.wins || 0}W / ${d.losses || 0}L</div></div>
    <div class="kpi-card"><div class="kpi-label">Win Rate</div><div class="kpi-val pos">${d.win_rate || 0}%</div><div class="kpi-sub">Stall Locks: ${stallCount}</div></div>
    <div class="kpi-card"><div class="kpi-label">Profit Factor</div><div class="kpi-val gold">${d.profit_factor || 0}</div><div class="kpi-sub">Gross W / Gross L</div></div>
    <div class="kpi-card"><div class="kpi-label">Expected Value</div><div class="kpi-val pos">${(d.avg_r || 0) >= 0 ? '+' : ''}${d.avg_r || 0}R</div><div class="kpi-sub">$5.00 Risk / R</div></div>
    <div class="kpi-card"><div class="kpi-label">Net Profit ($100)</div><div class="kpi-val ${(d.net_pnl || 0) >= 0 ? 'pos' : 'neg'}">${(d.net_pnl || 0) >= 0 ? '+' : ''}$${(d.net_pnl || 0).toFixed(2)}</div><div class="kpi-sub">After 0.01% Fee</div></div>
    <div class="kpi-card"><div class="kpi-label">Ending Equity</div><div class="kpi-val pos">$${(d.end_equity || 100).toFixed(2)}</div><div class="kpi-sub">Start: $100.00</div></div>
    <div class="kpi-card"><div class="kpi-label">Max Drawdown</div><div class="kpi-val neg">-${d.max_dd_pct || 0}%</div><div class="kpi-sub">Rev Cuts: ${revCount}</div></div>
  `;
}

function renderLabChartMarkers(dataset) {
  if (!labCandleSeries) return;
  const trades = dataset.trades || [];
  const markers = [];
  trades.forEach(t => {
    const snapTs = Math.floor(t.entry_ts / 900) * 900;
    const isLong = t.direction === "LONG";
    markers.push({
      time: snapTs,
      position: isLong ? "belowBar" : "aboveBar",
      color: isLong ? "#10b981" : "#ef4444",
      shape: isLong ? "arrowUp" : "arrowDown",
      text: `#${t.id} ${t.direction}`,
    });
  });
  markers.sort((a, b) => a.time - b.time);
  try {
    labCandleSeries.setMarkers(markers);
  } catch(e) {}
}

window.inspectLabTrade = function(t) {
  if (!t) return;
  if (labCandleSeries) {
    labPriceLines.forEach(pl => labCandleSeries.removePriceLine(pl));
    labPriceLines = [];
    try {
      labPriceLines.push(labCandleSeries.createPriceLine({ price: t.entry_price, color: '#3b82f6', lineWidth: 2, title: `#${t.id} ENTRY` }));
      labPriceLines.push(labCandleSeries.createPriceLine({ price: t.sl_price, color: '#ef4444', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, title: `#${t.id} SL` }));
      labPriceLines.push(labCandleSeries.createPriceLine({ price: t.tp2_price, color: '#10b981', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, title: `#${t.id} TP2` }));
      const snapTs = Math.floor(t.entry_ts / 900) * 900;
      labChart.timeScale().setVisibleRange({ from: snapTs - 3600 * 18, to: snapTs + 3600 * 24 });
    } catch(e) {}
  }

  const badge = document.getElementById("lab-insp-badge");
  if (badge) {
    badge.className = "badge " + (t.direction === "LONG" ? "badge-long" : "badge-short");
    badge.textContent = `Trade #${t.id} • ${t.direction} (${t.exit_reason})`;
  }

  const content = document.getElementById("lab-insp-content");
  if (content) {
    content.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;">
        <div><b>Entry Time:</b> ${t.entry_time}</div>
        <div><b>Exit Time:</b> ${t.exit_time}</div>
        <div><b>Session / Regime:</b> <code>${t.session} · ${t.regime}</code></div>
        <div><b>Timeframe:</b> <code>${t.tf}</code></div>
        <div><b>Entry Price:</b> $${t.entry_price.toFixed(2)}</div>
        <div><b>Exit Price:</b> $${t.exit_price.toFixed(2)}</div>
        <div><b>Stop Loss:</b> <span style="color:#f87171;">$${t.sl_price.toFixed(2)}</span></div>
        <div><b>Target (TP2):</b> <span style="color:#34d399;">$${t.tp2_price.toFixed(2)}</span></div>
        <div><b>Position Qty:</b> ${t.qty} oz</div>
        <div><b>Brokerage Fee:</b> $${(t.fee_usd || 0).toFixed(2)}</div>
        <div><b>Net PnL:</b> <b style="color:${(t.net_pnl || 0) >= 0 ? '#34d399' : '#f87171'};">${(t.net_pnl || 0) >= 0 ? '+' : ''}$${(t.net_pnl || 0).toFixed(2)} (${(t.r_multiple || 0) >= 0 ? '+' : ''}${t.r_multiple || 0}R)</b></div>
        <div><b>Equity After:</b> <b>$${(t.equity_after || 0).toFixed(2)}</b></div>
      </div>
      <div style="background:#0b1324;padding:8px;border-radius:6px;border:1px solid #1e293b;margin-bottom:6px;">
        <div style="color:#c084fc;font-weight:700;margin-bottom:2px;">🧘‍♀️ Trading Psychologist (12:SARAH) Behavioral Audit:</div>
        <div>${t.sarah_note || 'N/A'}</div>
      </div>
      <div style="background:#0b1324;padding:8px;border-radius:6px;border:1px solid #1e293b;margin-bottom:6px;">
        <div style="color:#93c5fd;font-weight:700;margin-bottom:2px;">🧠 Part 1 Analyser (17:LUCAS) Input Brief:</div>
        <div>${t.lucas_note || 'N/A'}</div>
      </div>
      <div style="background:#0b1324;padding:8px;border-radius:6px;border:1px solid #1e293b;">
        <div style="color:#fbbf24;font-weight:700;margin-bottom:2px;">🔮 Self-Learner (18:ORACLE) Journal Audit:</div>
        <div>${t.oracle_note || 'N/A'}</div>
      </div>
    `;
  }
};

function renderLabJournalTable(dataset) {
  const trades = dataset.trades || [];
  const lbl = document.getElementById("lab-journal-count-lbl");
  if (lbl) lbl.textContent = `Showing ${trades.length} trades`;
  const tbody = document.getElementById("lab-journal-tbody");
  if (!tbody) return;
  tbody.innerHTML = trades.map((t, idx) => `
    <tr onclick="inspectLabTrade(getLabDataset(labCurrentKey).trades[${idx}])" style="cursor:pointer;">
      <td><b>#${t.id}</b></td>
      <td><code>${t.tf}</code></td>
      <td>${t.entry_time}</td>
      <td><span class="badge ${t.direction === 'LONG' ? 'badge-long' : 'badge-short'}">${t.direction}</span></td>
      <td>${t.session} · ${t.regime}</td>
      <td>$${t.entry_price.toFixed(2)}</td>
      <td style="color:#f87171;">$${t.sl_price.toFixed(2)}</td>
      <td style="color:#34d399;">$${t.tp2_price.toFixed(2)}</td>
      <td>$${t.exit_price.toFixed(2)}</td>
      <td><span class="badge ${t.exit_reason === 'REVERSAL_EXIT' ? 'badge-time' : (t.net_pnl >= 0 ? 'badge-tp' : 'badge-sl')}">${t.exit_reason}</span></td>
      <td style="color:${t.r_multiple >= 0 ? '#34d399' : '#f87171'};font-weight:700;">${t.r_multiple >= 0 ? '+' : ''}${t.r_multiple}R</td>
      <td style="color:${t.net_pnl >= 0 ? '#34d399' : '#f87171'};font-weight:700;">${t.net_pnl >= 0 ? '+' : ''}$${t.net_pnl.toFixed(2)}</td>
    </tr>
  `).join("");
}

window.renderLabCombosTable = function() {
  const lab = LAB_AGENTS[labCurrentAgentId];
  if (!lab || !lab.all_combos_summary) return;

  const tfFlt = document.getElementById("flt-lab-tf")?.value || "ALL";
  const emaFlt = document.getElementById("flt-lab-ema")?.value || "ALL";
  const sortKey = document.getElementById("flt-lab-sort")?.value || "net_pnl";

  let rows = lab.all_combos_summary.filter(r => {
    if (tfFlt !== "ALL" && r.timeframe !== tfFlt) return false;
    if (emaFlt !== "ALL" && r.ema_setting !== emaFlt) return false;
    return true;
  });

  rows.sort((a, b) => (b[sortKey] || 0) - (a[sortKey] || 0));
  const countLbl = document.getElementById("lab-combo-count-lbl");
  if (countLbl) {
    countLbl.textContent = `Showing ${rows.length} of ${lab.total_combinations_tested || 0} valid combinations (${lab.high_wr_combinations_count || 0} combos >= 60% WR)`;
  }

  const tbody = document.getElementById("lab-combos-tbody");
  if (!tbody) return;
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><b>#${r.combo_id}</b></td>
      <td><span class="pill" style="background:#1e293b;color:#93c5fd;">${r.timeframe}</span></td>
      <td>${r.ema_setting}</td>
      <td>${r.rsi_macd_setting}</td>
      <td>${r.vol_filter}</td>
      <td>${r.sl_tp_profile}</td>
      <td><b>${r.trades}</b></td>
      <td style="color:${r.win_rate >= 60 ? '#34d399' : (r.win_rate >= 50 ? '#fbbf24' : '#cbd5e1')};font-weight:700;">${r.win_rate}%</td>
      <td style="color:${r.profit_factor >= 1.3 ? '#fbbf24' : '#cbd5e1'};font-weight:700;">${r.profit_factor}</td>
      <td>${r.avg_r >= 0 ? '+' : ''}${r.avg_r}R</td>
      <td style="color:${r.net_pnl >= 0 ? '#34d399' : '#f87171'};font-weight:800;">${r.net_pnl >= 0 ? '+' : ''}$${r.net_pnl.toFixed(2)}</td>
      <td>$${(r.end_equity || 0).toFixed(2)}</td>
      <td style="color:#f87171;">-${r.max_dd_pct}%</td>
    </tr>
  `).join("");
};

function initLabCalendarMonths(dataset) {
  const trades = dataset.trades || [];
  const months = [...new Set(trades.map(t => t.entry_time.slice(0, 7)))].sort();
  const sel = document.getElementById("lab-cal-month");
  if (!sel) return;
  sel.innerHTML = months.map(m => `<option value="${m}">${m}</option>`).join("");
  if (months.length > 0) {
    sel.value = months[months.length - 1];
    renderLabCalendar();
  }
}

window.renderLabCalendar = function() {
  const m = document.getElementById("lab-cal-month")?.value;
  if (!m) return;
  const [yr, mo] = m.split("-").map(Number);
  const daysInMonth = new Date(yr, mo, 0).getDate();
  const dataset = getLabDataset(labCurrentKey);
  const daily = {};
  (dataset.trades || []).forEach(t => {
    if (t.entry_time.startsWith(m)) {
      const d = parseInt(t.entry_time.slice(8, 10), 10);
      if (!daily[d]) daily[d] = { pnl: 0, n: 0 };
      daily[d].pnl += t.net_pnl;
      daily[d].n += 1;
    }
  });

  let html = "";
  for (let d = 1; d <= daysInMonth; d++) {
    const info = daily[d];
    if (!info) {
      html += `<div class="cal-cell empty"><div class="cal-day-num" style="color:#475569;">Day ${d}</div><div class="cal-meta">No Trade</div></div>`;
    } else {
      const isWin = info.pnl >= 0;
      html += `
        <div class="cal-cell ${isWin ? 'win-day' : 'loss-day'}">
          <div class="cal-day-num"><span>Day ${d}</span><span>${info.n}t</span></div>
          <div class="cal-pnl ${isWin ? 'pos' : 'neg'}">${isWin ? '+' : ''}$${info.pnl.toFixed(2)}</div>
        </div>
      `;
    }
  }
  const calGrid = document.getElementById("lab-cal-grid");
  if (calGrid) calGrid.innerHTML = html;
};

// Wire up CSV export button
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("exportCsvBtn");
  if (btn) btn.addEventListener("click", exportTradesCSV);
});
"""

# Call renderPodMatrixTable() and initLab() inside initDashboard()
insert_pos = code.find("function initDashboard() {")
brace_pos = code.find("{", insert_pos) + 1
code = code[:brace_pos] + "\n  renderPodMatrixTable();\n  initLab();\n" + code[brace_pos:]

# Append master_js_code before </script>
code = code.replace("initDashboard();\n</script>", master_js_code + "\ninitDashboard();\n</script>")

with open(RENDER_PY, "w", encoding="utf-8") as f:
    f.write(code)

print(f"[SUCCESS] Patched {RENDER_PY} (new length: {len(code)})")
