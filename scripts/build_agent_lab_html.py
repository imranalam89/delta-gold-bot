"""
Builds `agent_lab_dashboard.html` — The Complete 11-Field-Specialist Individual Backtest & Self-Learner Lab
Supports interactive switching across ALL 11 Field Specialist Agents (`1:ALEX` through `11:LIAM`):
  - High-Cadence ~2 to 3 Trades/Day (225 to 286 trades across the 5-month window)
  - All 11 Specialists > 62.7% to 67.6% Win Rate with 12:SARAH Psychologist + 18:ORACLE Greed-Guard Trail
  - Master 11-Agent Leaderboard Table + 3-Stage Evolution + Multi-TF (1m, 5m, 15m, 1h) + Interactive Chart
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_JSON = os.path.join(BASE_DIR, "data", "processed", "all_11_agents_lab_bundle.json")
CANDLES_JSON = os.path.join(BASE_DIR, "data", "processed", "lab_candles_15m.json")
OUT_HTML = os.path.join(BASE_DIR, "agent_lab_dashboard.html")


def build_html():
    with open(BUNDLE_JSON, "r", encoding="utf-8") as f:
        agents_bundle = json.load(f)
    with open(CANDLES_JSON, "r", encoding="utf-8") as f:
        candles_15m = json.load(f)

    # Deduplicate TF_1m (which is identical to v3.0_ORACLE_CHAMPION) & remove redundant top_combos to keep HTML fast
    for aid, data in agents_bundle.items():
        data.pop("top_combos", None)
        if "1m" in data.get("timeframes", {}):
            tf1m = dict(data["timeframes"]["1m"])
            tf1m.pop("trades", None)
            data["timeframes"]["1m"] = tf1m

    bundle_json = json.dumps(agents_bundle, separators=(",", ":"))
    candles_json = json.dumps(candles_15m, separators=(",", ":"))

    roadmap_pills = []
    for aid, data in agents_bundle.items():
        g3 = data["generations"]["v3.0_ORACLE_CHAMPION"]
        roadmap_pills.append(
            f'<div class="agent-step clickable" id="step-{aid}" onclick="selectAgent(\'{aid}\')">'
            f'<div class="num">{aid}</div>'
            f'<div class="role">{data["agent_role"]}</div>'
            f'<span class="st done">✓ {g3["win_rate"]:.1f}% ({g3["trades_per_day"]}/d)</span>'
            f'</div>'
        )
    roadmap_html = "\n  ".join(roadmap_pills)

    leaderboard_rows = []
    for aid, data in agents_bundle.items():
        g1 = data["generations"]["v1.0_BASELINE"]
        g2 = data["generations"]["v2.0_GRID_OPTIMIZED"]
        g3 = data["generations"]["v3.0_ORACLE_CHAMPION"]
        tfs = data["timeframes"]
        leaderboard_rows.append(
            f'<tr onclick="selectAgent(\'{aid}\')">'
            f'<td><b>{aid}</b></td>'
            f'<td>{data["agent_role"]}</td>'
            f'<td style="color:#94a3b8;font-size:11px">{data["agent_focus"]}</td>'
            f'<td style="color:#f87171">{g1["win_rate"]}% (${g1["net_pnl"]:+.0f})</td>'
            f'<td style="color:#60a5fa">{g2["win_rate"]}% (${g2["net_pnl"]:+.0f})</td>'
            f'<td><b>{g3["trades_count"]}</b> <span class="pill" style="background:#1e293b;color:#93c5fd">{g3["trades_per_day"]}/day</span></td>'
            f'<td style="color:#34d399;font-weight:800">{g3["win_rate"]}%</td>'
            f'<td style="color:#fbbf24;font-weight:700">{g3["profit_factor"]}</td>'
            f'<td style="color:#34d399;font-weight:800">+${g3["net_pnl"]:.2f}</td>'
            f'<td><b>${g3["end_equity"]:.2f}</b></td>'
            f'<td style="color:#f87171">-{g3["max_dd_pct"]}%</td>'
            f'<td style="color:#34d399;font-size:11px"><b>1m:</b> {tfs["1m"]["win_rate"]}% ({tfs["1m"]["trades_count"]}t) | <b>5m:</b> {tfs["5m"]["win_rate"]}% ({tfs["5m"]["trades_count"]}t) | <b>15m:</b> {tfs["15m"]["win_rate"]}% ({tfs["15m"]["trades_count"]}t) | <b>1h:</b> {tfs["1h"]["win_rate"]}% ({tfs["1h"]["trades_count"]}t)</td>'
            f'</tr>'
        )
    leaderboard_html = "\n        ".join(leaderboard_rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Syndicate 11-Agent Specialist Lab — All 11 Specialists Backtested (2-3 Trades/Day, &gt;62% WR)</title>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<style>
  :root {{
    --bg: #070b14;
    --panel: #0f1626;
    --panel2: #131c31;
    --border: #1e2d4a;
    --text: #e2e8f0;
    --muted: #8b9bb4;
    --green: #10b981;
    --red: #ef4444;
    --amber: #f59e0b;
    --blue: #3b82f6;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    font-size: 13px;
    line-height: 1.45;
    padding: 14px;
  }}
  .top-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(90deg, #0f172a, #172554);
    border: 1px solid #2563eb;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 12px;
  }}
  .top-header h1 {{
    font-size: 17px;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: 0.3px;
  }}
  .top-header .sub {{
    color: #93c5fd;
    font-size: 12px;
    margin-top: 2px;
  }}
  .roadmap-bar {{
    display: grid;
    grid-template-columns: repeat(11, 1fr);
    gap: 6px;
    margin-bottom: 12px;
  }}
  .agent-step {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 7px 6px;
    text-align: center;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.15s;
  }}
  .agent-step:hover {{
    border-color: #60a5fa;
    transform: translateY(-1px);
  }}
  .agent-step.active {{
    background: linear-gradient(180deg, rgba(16,185,129,0.22), rgba(15,23,42,0.95));
    border: 1.5px solid var(--green);
    box-shadow: 0 0 12px rgba(16,185,129,0.25);
  }}
  .agent-step .num {{ font-weight: 800; color: #f8fafc; font-size: 11.5px; }}
  .agent-step .role {{ color: var(--muted); font-size: 10px; }}
  .agent-step .st {{
    display: inline-block;
    margin-top: 3px;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 9.5px;
    font-weight: 700;
    background: rgba(16,185,129,0.2);
    color: #34d399;
  }}

  .mode-tabs {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
    background: var(--panel);
    padding: 10px;
    border-radius: 9px;
    border: 1px solid var(--border);
    align-items: center;
  }}
  .mode-btn {{
    background: #16213a;
    color: #cbd5e1;
    border: 1px solid #2a3f66;
    padding: 7px 13px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 700;
    font-size: 12px;
    transition: all 0.15s;
  }}
  .mode-btn:hover {{ border-color: #60a5fa; color: #fff; }}
  .mode-btn.active {{
    background: linear-gradient(90deg, #059669, #10b981);
    color: #04130d;
    border-color: #34d399;
  }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 8px;
    margin-bottom: 12px;
  }}
  .kpi-card {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
  }}
  .kpi-card .lbl {{ color: var(--muted); font-size: 11px; text-transform: uppercase; }}
  .kpi-card .val {{ font-size: 18px; font-weight: 800; margin-top: 3px; }}
  .kpi-card .sub {{ color: var(--muted); font-size: 11px; margin-top: 2px; }}

  .main-grid {{
    display: grid;
    grid-template-columns: 2.25fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
  }}
  .panel {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px;
  }}
  .panel-title {{
    font-size: 13.5px;
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  #tv-chart {{
    width: 100%;
    height: 450px;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #1e293b;
  }}
  .evo-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 12px;
  }}
  .evo-card {{
    background: var(--panel2);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 12px;
  }}
  .evo-card.champ {{
    border: 1.5px solid var(--green);
    background: linear-gradient(180deg, rgba(16,185,129,0.10), rgba(15,23,42,0.95));
  }}
  .tf-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 12px;
  }}
  .tf-card {{
    background: var(--panel2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  th, td {{
    padding: 7px 8px;
    border-bottom: 1px solid #1e293b;
    text-align: left;
  }}
  th {{
    background: #131d33;
    color: #93c5fd;
    position: sticky;
    top: 0;
    z-index: 2;
    font-weight: 700;
  }}
  tr:hover {{ background: rgba(59,130,246,0.10); cursor: pointer; }}
  .pill {{
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 10.5px;
  }}
  .pill.long {{ background: rgba(16,185,129,0.2); color: #34d399; }}
  .pill.short {{ background: rgba(239,68,68,0.2); color: #f87171; }}
  .pill.rev {{ background: rgba(245,158,11,0.25); color: #fbbf24; }}
  .filter-row {{
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
    align-items: center;
    flex-wrap: wrap;
  }}
  select, input {{
    background: #0b1324;
    color: #f8fafc;
    border: 1px solid #2a3f66;
    padding: 5px 9px;
    border-radius: 6px;
    font-size: 12px;
  }}
  .cal-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 5px;
  }}
  .cal-day {{
    background: #111a2e;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 6px;
    min-height: 54px;
    font-size: 11px;
  }}
  .cal-day.win {{ background: rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.45); }}
  .cal-day.loss {{ background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.45); }}
</style>
</head>
<body>

<div class="top-header">
  <div>
    <h1 id="header-title">🧪 SYNDICATE 11-AGENT SPECIALIST LAB — ALL 11 FIELD SPECIALISTS BACKTESTED (2–3 TRADES/DAY, &gt;62% WR)</h1>
    <div class="sub" id="header-sub">
      All 11 Field Specialists (<code>1:ALEX</code> through <code>11:LIAM</code>) Individually Backtested •
      High-Cadence <b>2.05 to 2.60 Trades/Day (225–286 Trades)</b> •
      Iterative Journal Upgrades by <code>12:SARAH (Psychologist)</code>, <code>17:LUCAS (Analyser)</code> &amp; <code>18:ORACLE (Self-Learner)</code>
    </div>
  </div>
  <div style="text-align:right">
    <div style="font-size:12px;font-weight:800;color:#34d399">✅ ALL 11 OF 11 FIELD SPECIALISTS COMPLETED (&gt;62.7% WR)</div>
    <div style="font-size:11px;color:#94a3b8" id="header-gen">Click any Agent Pill or Leaderboard Row below to inspect!</div>
  </div>
</div>

<!-- 11-AGENT ROADMAP BAR (ALL 11 CLICKABLE) -->
<div class="roadmap-bar">
  {roadmap_html}
</div>

<!-- MASTER 11-AGENT COMPARISON LEADERBOARD -->
<div class="panel" style="margin-bottom:12px">
  <div class="panel-title">
    <span>🏆 Master 11-Field-Specialist Comparison Leaderboard (Click Any Agent Row to Load Its Full Lab &amp; Trade Journal)</span>
    <span style="font-size:11px;color:#34d399">$100 Start | $5.00 Risk/Trade | 0.01% Delta Exchange Fee | 2–3 Trades/Day Target</span>
  </div>
  <div style="overflow-x:auto;border:1px solid #1e293b;border-radius:8px">
    <table>
      <thead>
        <tr>
          <th>Agent</th>
          <th>Specialist Role</th>
          <th>Core Domain Trigger</th>
          <th>Gen 1 (Raw)</th>
          <th>Gen 2 (Wide Trail)</th>
          <th>Gen 3 Trades (Cadence)</th>
          <th>Gen 3 Win Rate</th>
          <th>Profit Factor</th>
          <th>Net Profit ($)</th>
          <th>End Equity</th>
          <th>Max DD</th>
          <th>Multi-TF Win Rates (1m / 5m / 15m / 1h)</th>
        </tr>
      </thead>
      <tbody>
        {leaderboard_html}
      </tbody>
    </table>
  </div>
</div>

<!-- MODE / GENERATION / TIMEFRAME SWITCHER -->
<div class="mode-tabs">
  <span style="font-weight:800;color:#93c5fd;margin-right:4px" id="mode-lbl">SELECT JOURNAL VIEW:</span>
  <button class="mode-btn active" id="btn-v3" onclick="selectJournal('v3.0_ORACLE_CHAMPION', this)">🏆 Gen 3: v3.0 12:SARAH + 18:ORACLE Champion (2–3 Trades/Day)</button>
  <button class="mode-btn" onclick="selectJournal('v2.0_GRID_OPTIMIZED', this)">⚡ Gen 2: v2.0 + 12:SARAH Entry (Classic Wide Trail)</button>
  <button class="mode-btn" onclick="selectJournal('v1.0_BASELINE', this)">📉 Gen 1: v1.0 Raw Unfiltered Baseline</button>
  <span style="margin-left:10px;font-weight:800;color:#fbbf24">MULTI-TIMEFRAME VIEWS (v3.0):</span>
  <button class="mode-btn" onclick="selectJournal('TF_1m', this)">⏱️ 1m (2–3/Day)</button>
  <button class="mode-btn" onclick="selectJournal('TF_5m', this)">⏱️ 5m Timeframe</button>
  <button class="mode-btn" onclick="selectJournal('TF_15m', this)">⏱️ 15m Timeframe</button>
  <button class="mode-btn" onclick="selectJournal('TF_1h', this)">⏱️ 1h Timeframe</button>
</div>

<!-- KPI SUMMARY ROW -->
<div class="kpi-grid" id="kpi-row"></div>

<!-- 3-STAGE EVOLUTION & SELF-LEARNER JOURNAL AUDIT -->
<div class="evo-grid" id="evo-cards"></div>

<!-- MULTI-TIMEFRAME BREAKDOWN CARDS (1m, 5m, 15m, 1h) -->
<div class="tf-grid" id="tf-cards"></div>

<!-- INTERACTIVE CHART + FORENSIC INSPECTOR -->
<div class="main-grid">
  <div class="panel">
    <div class="panel-title">
      <span id="chart-title">📈 Full 5-Month Interactive Chart — Trade Markers &amp; Trade #IDs</span>
      <div style="display:flex;gap:6px">
        <button class="mode-btn" style="padding:4px 9px;font-size:11px" onclick="fitFullChart()">🔍 Fit Full 5 Months</button>
      </div>
    </div>
    <div id="tv-chart"></div>
    <div style="margin-top:6px;font-size:11px;color:#94a3b8;display:flex;justify-content:space-between">
      <span>Use mouse wheel to zoom, click-drag to pan across all 5 months. Click any trade row below to jump to that exact candle!</span>
      <span>🟢 LONG | 🔴 SHORT | 🟠 REVERSAL_EXIT (Early Cut)</span>
    </div>
  </div>

  <!-- RIGHT FORENSIC INSPECTOR -->
  <div class="panel" id="forensic-box">
    <div class="panel-title">
      <span>🔬 12:SARAH, 17:LUCAS &amp; 18:ORACLE Trade Forensic Inspector</span>
      <span id="insp-badge" class="pill long">Select a Trade</span>
    </div>
    <div id="insp-content" style="font-size:12px;color:#cbd5e1">
      Click any trade in the journal table below to inspect specialist entry triggers, <code>12:SARAH</code> psychological filter notes, <code>17:LUCAS</code> session/regime analysis, and <code>18:ORACLE</code> SL/TP post-trade diagnosis.
    </div>
  </div>
</div>

<!-- COMBINATIONS MATRIX TABLE -->
<div class="panel" style="margin-bottom:12px">
  <div class="panel-title">
    <span id="combo-title">🧮 Backtested Parameter &amp; Trailing Stop Combinations</span>
    <span style="font-size:11px;color:#34d399" id="combo-count-lbl"></span>
  </div>
  <div class="filter-row">
    <label>Timeframe:</label>
    <select id="flt-tf" onchange="renderCombosTable()">
      <option value="ALL">ALL (1m, 5m, 15m, 1h)</option>
      <option value="1m">1m Only</option>
      <option value="5m">5m Only</option>
      <option value="15m">15m Only</option>
      <option value="1h">1h Only</option>
    </select>
    <label>Signal Variant:</label>
    <select id="flt-ema" onchange="renderCombosTable()">
      <option value="ALL">ALL Signal Variants</option>
    </select>
    <label>Sort By:</label>
    <select id="flt-sort" onchange="renderCombosTable()">
      <option value="net_pnl">Net Profit ($)</option>
      <option value="win_rate">Win Rate (%)</option>
      <option value="profit_factor">Profit Factor</option>
      <option value="trades">Trade Count</option>
    </select>
  </div>
  <div style="max-height:320px;overflow-y:auto;border:1px solid #1e293b;border-radius:8px">
    <table>
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
          <th>Best Session</th>
          <th>Best Regime</th>
        </tr>
      </thead>
      <tbody id="combos-tbody"></tbody>
    </table>
  </div>
</div>

<!-- MONTHLY CALENDAR + TRADE JOURNAL -->
<div class="main-grid">
  <div class="panel">
    <div class="panel-title">
      <span id="journal-title">📜 Trade Journal (Click Any Row to Jump on Chart &amp; Inspect)</span>
      <span id="journal-count-lbl" style="font-size:11px;color:#93c5fd"></span>
    </div>
    <div style="max-height:360px;overflow-y:auto;border:1px solid #1e293b;border-radius:8px">
      <table>
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
            <th>Exit Reason</th>
            <th>R-Mult</th>
            <th>Fee</th>
            <th>Net PnL</th>
            <th>Equity</th>
          </tr>
        </thead>
        <tbody id="journal-tbody"></tbody>
      </table>
    </div>
  </div>

  <div class="panel">
    <div class="panel-title">
      <span>📅 Monthly Daily PnL Calendar</span>
      <select id="cal-month" onchange="renderCalendar()"></select>
    </div>
    <div class="cal-grid" id="cal-grid"></div>
  </div>
</div>

<script>
const AGENTS = {bundle_json};
const CANDLES_15M = {candles_json};
let currentAgentId = '3:MARCUS';
let LAB = AGENTS[currentAgentId];
let currentKey = 'v3.0_ORACLE_CHAMPION';
let currentDataset = LAB.generations['v3.0_ORACLE_CHAMPION'];
let chart, candleSeries, priceLines = [];

function getJournalData(key) {{
  if (key === 'TF_1m') {{
    return LAB.generations['v3.0_ORACLE_CHAMPION'];
  }}
  if (key.startsWith('TF_')) {{
    const tf = key.replace('TF_', '');
    return LAB.timeframes[tf];
  }}
  return LAB.generations[key];
}}

function initChart() {{
  const container = document.getElementById('tv-chart');
  chart = LightweightCharts.createChart(container, {{
    layout: {{ background: {{ color: '#070b14' }}, textColor: '#94a3b8' }},
    grid: {{ vertLines: {{ color: '#111c33' }}, horzLines: {{ color: '#111c33' }} }},
    crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
    rightPriceScale: {{ borderColor: '#1e293b' }},
    timeScale: {{ borderColor: '#1e293b', timeVisible: true, secondsVisible: false }},
  }});
  candleSeries = chart.addCandlestickSeries({{
    upColor: '#10b981', downColor: '#ef4444',
    borderUpColor: '#10b981', borderDownColor: '#ef4444',
    wickUpColor: '#10b981', wickDownColor: '#ef4444',
  }});
  candleSeries.setData(CANDLES_15M);
  chart.timeScale().fitContent();
}}

function fitFullChart() {{
  if (chart) chart.timeScale().fitContent();
}}

function selectAgent(agentId) {{
  currentAgentId = agentId;
  LAB = AGENTS[agentId];
  document.querySelectorAll('.roadmap-bar .agent-step').forEach(el => el.classList.remove('active'));
  const stepEl = document.getElementById('step-' + agentId);
  if (stepEl) stepEl.classList.add('active');

  const g3 = LAB.generations['v3.0_ORACLE_CHAMPION'];
  document.getElementById('header-title').innerHTML = `🧪 SYNDICATE 11-AGENT SPECIALIST LAB — <code>${{LAB.agent_name}}</code> (${{g3.win_rate}}% WR • ${{g3.trades_per_day}} Trades/Day)`;
  document.getElementById('header-sub').innerHTML = `Focus: <b>${{LAB.agent_focus}}</b> • <b>${{g3.trades_count}} Trades (${{g3.trades_per_day}}/day)</b> • Win Rate: <b>${{g3.win_rate}}%</b> • Net Profit: <b>+$${{g3.net_pnl.toFixed(2)}} ($${{g3.end_equity.toFixed(2)}} Eq)</b> • Audited by <code>12:SARAH</code>, <code>17:LUCAS</code> &amp; <code>18:ORACLE</code>`;
  document.getElementById('mode-lbl').textContent = `SELECT ${{agentId}} JOURNAL VIEW:`;
  document.getElementById('chart-title').textContent = `📈 Full 5-Month Interactive Chart — ${{agentId}} Trade Markers & Trade #IDs`;
  document.getElementById('combo-title').textContent = `🧮 ${{agentId}} — All ${{LAB.total_combinations_tested}} Valid Backtested Combinations (${{LAB.high_wr_combinations_count}} Combos >= 60% WR)`;
  document.getElementById('journal-title').textContent = `📜 ${{agentId}} Trade Journal (Click Any Row to Jump on Chart & Inspect)`;

  const structSet = [...new Set(LAB.all_combos_summary.map(r => r.ema_setting))];
  const fltEma = document.getElementById('flt-ema');
  fltEma.innerHTML = `<option value="ALL">ALL Signal Variants</option>` + structSet.map(s => `<option value="${{s}}">${{s}}</option>`).join('');

  renderEvolutionCards();
  renderTimeframeCards();
  renderCombosTable();
  selectJournal('v3.0_ORACLE_CHAMPION', document.getElementById('btn-v3'));
}}

function renderEvolutionCards() {{
  const g1 = LAB.generations['v1.0_BASELINE'];
  const g2 = LAB.generations['v2.0_GRID_OPTIMIZED'];
  const g3 = LAB.generations['v3.0_ORACLE_CHAMPION'];

  document.getElementById('evo-cards').innerHTML = `
    <div class="evo-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:800;color:#f87171">GEN 1: v1.0 RAW UNFILTERED</span>
        <span class="pill short">No 12:SARAH Filter</span>
      </div>
      <div style="margin:6px 0;font-size:12px;color:#cbd5e1">
        Trades: <b>${{g1.trades_count}}</b> | Win Rate: <b>${{g1.win_rate}}%</b> | PF: <b>${{g1.profit_factor}}</b> |
        Net PnL: <b style="color:${{g1.net_pnl>=0?'#34d399':'#f87171'}}">${{g1.net_pnl>=0?'+':''}}$${{g1.net_pnl.toFixed(2)}}</b> | Max DD: <b>${{g1.max_dd_pct}}%</b>
      </div>
      <div style="font-size:11.5px;color:#94a3b8;border-top:1px solid #1e293b;padding-top:6px">
        <b>🧠 12:SARAH &amp; 17:LUCAS Diagnosis:</b><br/>
        • ${{LAB.diag_g1}}
      </div>
    </div>

    <div class="evo-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:800;color:#60a5fa">GEN 2: v2.0 + 12:SARAH ENTRY (WIDE TRAIL)</span>
        <span class="pill" style="background:rgba(59,130,246,0.2);color:#93c5fd">${{g2.win_rate}}% WR (No Stall Lock)</span>
      </div>
      <div style="margin:6px 0;font-size:12px;color:#cbd5e1">
        Trades: <b>${{g2.trades_count}} (${{g2.trades_per_day}}/day)</b> | Win Rate: <b>${{g2.win_rate}}%</b> | PF: <b>${{g2.profit_factor}}</b> |
        Net PnL: <b style="color:${{g2.net_pnl>=0?'#34d399':'#f87171'}}">${{g2.net_pnl>=0?'+':''}}$${{g2.net_pnl.toFixed(2)}}</b> | Max DD: <b>${{g2.max_dd_pct}}%</b>
      </div>
      <div style="font-size:11.5px;color:#94a3b8;border-top:1px solid #1e293b;padding-top:6px">
        <b>🔍 18:ORACLE Audit of Gen 2:</b><br/>
        • ${{LAB.diag_g2}}
      </div>
    </div>

    <div class="evo-card champ">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:800;color:#34d399">🏆 GEN 3: v3.0 12:SARAH + 18:ORACLE (2–3/DAY)</span>
        <span class="pill long">${{g3.win_rate}}% WR • ${{g3.trades_per_day}}/Day!</span>
      </div>
      <div style="margin:6px 0;font-size:12px;color:#cbd5e1">
        Trades: <b>${{g3.trades_count}} (${{g3.trades_per_day}}/day)</b> | Win Rate: <b style="color:#34d399">${{g3.win_rate}}%</b> | PF: <b style="color:#fbbf24">${{g3.profit_factor}}</b> |
        Net PnL: <b style="color:#34d399">+$${{g3.net_pnl.toFixed(2)}} ($${{g3.end_equity.toFixed(2)}} Eq)</b> | Max DD: <b>${{g3.max_dd_pct}}%</b>
      </div>
      <div style="font-size:11.5px;color:#d1fae5;border-top:1px solid rgba(16,185,129,0.3);padding-top:6px">
        <b>✅ 12:SARAH Psychologist + 18:ORACLE Greed-Guard Trail:</b><br/>
        • ${{LAB.diag_g3}}
      </div>
    </div>
  `;
}}

function renderTimeframeCards() {{
  const tfs = ['1m', '5m', '15m', '1h'];
  document.getElementById('tf-cards').innerHTML = tfs.map(tf => {{
    const d = LAB.timeframes[tf];
    return `
      <div class="tf-card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <span style="font-weight:800;color:#f8fafc">⏱️ ${{currentAgentId}} on <code>${{tf}}</code> Timeframe</span>
          <span class="pill ${{d.net_pnl>=0?'long':'short'}}">${{d.net_pnl>=0?'+':''}}$${{d.net_pnl.toFixed(2)}}</span>
        </div>
        <div style="font-size:11.5px;color:#cbd5e1">
          Trades: <b>${{d.trades_count}}</b> | WR: <b style="color:#34d399">${{d.win_rate}}%</b> | PF: <b>${{d.profit_factor}}</b> | Avg R: <b>${{d.avg_r}}R</b> | Max DD: <b>${{d.max_dd_pct}}%</b>
        </div>
        <div style="font-size:11px;color:#94a3b8;margin-top:4px">
          ASIA: <b>$${{d.sess_stats.ASIA.pnl.toFixed(1)}}</b> |
          LONDON: <b>$${{d.sess_stats.LONDON.pnl.toFixed(1)}}</b> |
          NY: <b>$${{d.sess_stats.NEW_YORK.pnl.toFixed(1)}}</b>
        </div>
      </div>
    `;
  }}).join('');
}}

function selectJournal(key, btn) {{
  currentKey = key;
  currentDataset = getJournalData(key);
  document.querySelectorAll('.mode-tabs .mode-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderKPIs();
  renderChartMarkers();
  renderJournalTable();
  initCalendarMonths();
  if (currentDataset.trades && currentDataset.trades.length > 0) {{
    inspectTrade(currentDataset.trades[0]);
  }}
}}

function renderKPIs() {{
  const d = currentDataset;
  const revCount = (d.reasons && d.reasons.REVERSAL_EXIT) || 0;
  const stallCount = (d.reasons && d.reasons.SMART_STALL_LOCK) || 0;
  document.getElementById('kpi-row').innerHTML = `
    <div class="kpi-card"><div class="lbl">Active Specialist</div><div class="val" style="font-size:14px;color:#60a5fa">${{currentAgentId}} (${{currentKey}})</div><div class="sub">${{LAB.agent_role}}</div></div>
    <div class="kpi-card"><div class="lbl">Total Trades</div><div class="val">${{d.trades_count}} <span style="font-size:12px;color:#93c5fd">(${{d.trades_per_day || (d.trades_count/110).toFixed(2)}}/d)</span></div><div class="sub">${{d.wins}}W / ${{d.losses}}L</div></div>
    <div class="kpi-card"><div class="lbl">Win Rate</div><div class="val" style="color:#34d399">${{d.win_rate}}%</div><div class="sub">Stall Locks: ${{stallCount}}</div></div>
    <div class="kpi-card"><div class="lbl">Profit Factor</div><div class="val" style="color:#fbbf24">${{d.profit_factor}}</div><div class="sub">Gross W / Gross L</div></div>
    <div class="kpi-card"><div class="lbl">Expected Value</div><div class="val" style="color:#34d399">${{d.avg_r>=0?'+':''}}${{d.avg_r}}R</div><div class="sub">$5.00 Risk / R</div></div>
    <div class="kpi-card"><div class="lbl">Net Profit ($100)</div><div class="val" style="color:${{d.net_pnl>=0?'#34d399':'#f87171'}}">${{d.net_pnl>=0?'+':''}}$${{d.net_pnl.toFixed(2)}}</div><div class="sub">After 0.01% Fee</div></div>
    <div class="kpi-card"><div class="lbl">Ending Equity</div><div class="val" style="color:#34d399">$${{d.end_equity.toFixed(2)}}</div><div class="sub">Start: $100.00</div></div>
    <div class="kpi-card"><div class="lbl">Max Drawdown</div><div class="val" style="color:#f87171">-${{d.max_dd_pct}}%</div><div class="sub">Rev Cuts: ${{revCount}}</div></div>
  `;
}}

function renderChartMarkers() {{
  if (!candleSeries) return;
  const trades = currentDataset.trades || [];
  const markers = [];
  trades.forEach(t => {{
    const snapTs = Math.floor(t.entry_ts / 900) * 900;
    const isLong = t.direction === 'LONG';
    markers.push({{
      time: snapTs,
      position: isLong ? 'belowBar' : 'aboveBar',
      color: isLong ? '#10b981' : '#ef4444',
      shape: isLong ? 'arrowUp' : 'arrowDown',
      text: `#${{t.id}} ${{t.direction}}`,
    }});
  }});
  markers.sort((a, b) => a.time - b.time);
  candleSeries.setMarkers(markers);
}}

function inspectTrade(t) {{
  if (!t) return;
  priceLines.forEach(pl => candleSeries.removePriceLine(pl));
  priceLines = [];

  priceLines.push(candleSeries.createPriceLine({{ price: t.entry_price, color: '#3b82f6', lineWidth: 2, title: `#${{t.id}} ENTRY` }}));
  priceLines.push(candleSeries.createPriceLine({{ price: t.sl_price, color: '#ef4444', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, title: `#${{t.id}} SL` }}));
  priceLines.push(candleSeries.createPriceLine({{ price: t.tp2_price, color: '#10b981', lineWidth: 2, lineStyle: LightweightCharts.LineStyle.Dashed, title: `#${{t.id}} TP2` }}));

  const snapTs = Math.floor(t.entry_ts / 900) * 900;
  chart.timeScale().setVisibleRange({{ from: snapTs - 3600 * 18, to: snapTs + 3600 * 24 }});

  const badge = document.getElementById('insp-badge');
  badge.className = 'pill ' + (t.direction === 'LONG' ? 'long' : 'short');
  badge.textContent = `Trade #${{t.id}} • ${{t.direction}} (${{t.exit_reason}})`;

  document.getElementById('insp-content').innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px">
      <div><b>Entry Time:</b> ${{t.entry_time}}</div>
      <div><b>Exit Time:</b> ${{t.exit_time}}</div>
      <div><b>Session / Regime:</b> <code>${{t.session}} · ${{t.regime}}</code></div>
      <div><b>Timeframe:</b> <code>${{t.tf}}</code></div>
      <div><b>Entry Price:</b> $${{t.entry_price.toFixed(2)}}</div>
      <div><b>Exit Price:</b> $${{t.exit_price.toFixed(2)}}</div>
      <div><b>Stop Loss (SL):</b> <span style="color:#f87171">$${{t.sl_price.toFixed(2)}}</span> ($${{t.sl_dist}} dist)</div>
      <div><b>Target (TP1 / TP2):</b> <span style="color:#34d399">$${{t.tp1_price.toFixed(2)}} / $${{t.tp2_price.toFixed(2)}}</span></div>
      <div><b>Position Qty ($5 Risk):</b> ${{t.qty}} oz</div>
      <div><b>Brokerage Fee (0.01%):</b> $${{t.fee_usd.toFixed(2)}}</div>
      <div><b>Net PnL:</b> <b style="color:${{t.net_pnl>=0?'#34d399':'#f87171'}}">${{t.net_pnl>=0?'+':''}}$${{t.net_pnl.toFixed(2)}} (${{t.r_multiple>=0?'+':''}}${{t.r_multiple}}R)</b></div>
      <div><b>Equity After:</b> <b>$${{t.equity_after.toFixed(2)}}</b></div>
    </div>
    <div style="background:#0b1324;padding:8px;border-radius:6px;border:1px solid #1e293b;margin-bottom:6px">
      <div style="color:#c084fc;font-weight:700;margin-bottom:2px">🧘‍♀️ Trading Psychologist (12:SARAH) Behavioral Audit:</div>
      <div>${{t.sarah_note}}</div>
    </div>
    <div style="background:#0b1324;padding:8px;border-radius:6px;border:1px solid #1e293b;margin-bottom:6px">
      <div style="color:#93c5fd;font-weight:700;margin-bottom:2px">🧠 Part 1 Analyser (17:LUCAS) Input Brief:</div>
      <div>${{t.lucas_note}}</div>
    </div>
    <div style="background:#0b1324;padding:8px;border-radius:6px;border:1px solid #1e293b">
      <div style="color:#fbbf24;font-weight:700;margin-bottom:2px">🔮 Self-Learner (18:ORACLE) Journal Audit:</div>
      <div>${{t.oracle_note}}</div>
    </div>
  `;
}}

function renderJournalTable() {{
  const trades = currentDataset.trades || [];
  document.getElementById('journal-count-lbl').textContent = `Showing ${{trades.length}} trades`;
  const tbody = document.getElementById('journal-tbody');
  tbody.innerHTML = trades.map((t, idx) => `
    <tr onclick="inspectTrade(currentDataset.trades[${{idx}}])">
      <td><b>#${{t.id}}</b></td>
      <td><code>${{t.tf}}</code></td>
      <td>${{t.entry_time}}</td>
      <td><span class="pill ${{t.direction==='LONG'?'long':'short'}}">${{t.direction}}</span></td>
      <td>${{t.session}} · ${{t.regime}}</td>
      <td>$${{t.entry_price.toFixed(2)}}</td>
      <td style="color:#f87171">$${{t.sl_price.toFixed(2)}}</td>
      <td style="color:#34d399">$${{t.tp2_price.toFixed(2)}}</td>
      <td>$${{t.exit_price.toFixed(2)}}</td>
      <td><span class="pill ${{t.exit_reason==='REVERSAL_EXIT'?'rev':(t.net_pnl>=0?'long':'short')}}">${{t.exit_reason}}</span></td>
      <td style="color:${{t.r_multiple>=0?'#34d399':'#f87171'}};font-weight:700">${{t.r_multiple>=0?'+':''}}${{t.r_multiple}}R</td>
      <td>$${{t.fee_usd.toFixed(2)}}</td>
      <td style="color:${{t.net_pnl>=0?'#34d399':'#f87171'}};font-weight:700">${{t.net_pnl>=0?'+':''}}$${{t.net_pnl.toFixed(2)}}</td>
      <td><b>$${{t.equity_after.toFixed(2)}}</b></td>
    </tr>
  `).join('');
}}

function renderCombosTable() {{
  const tfFlt = document.getElementById('flt-tf').value;
  const emaFlt = document.getElementById('flt-ema').value;
  const sortKey = document.getElementById('flt-sort').value;

  let rows = LAB.all_combos_summary.filter(r => {{
    if (tfFlt !== 'ALL' && r.timeframe !== tfFlt) return false;
    if (emaFlt !== 'ALL' && r.ema_setting !== emaFlt) return false;
    return true;
  }});

  rows.sort((a, b) => b[sortKey] - a[sortKey]);
  document.getElementById('combo-count-lbl').textContent = `Showing ${{rows.length}} of ${{LAB.total_combinations_tested}} valid combinations (${{LAB.high_wr_combinations_count}} combos >= 60% WR)`;

  document.getElementById('combos-tbody').innerHTML = rows.map(r => `
    <tr>
      <td><b>#${{r.combo_id}}</b></td>
      <td><span class="pill" style="background:#1e293b;color:#93c5fd">${{r.timeframe}}</span></td>
      <td>${{r.ema_setting}}</td>
      <td>${{r.rsi_macd_setting}}</td>
      <td>${{r.vol_filter}}</td>
      <td>${{r.sl_tp_profile}}</td>
      <td><b>${{r.trades}}</b></td>
      <td style="color:${{r.win_rate>=60?'#34d399':(r.win_rate>=50?'#fbbf24':'#cbd5e1')}};font-weight:700">${{r.win_rate}}%</td>
      <td style="color:${{r.profit_factor>=1.3?'#fbbf24':'#cbd5e1'}};font-weight:700">${{r.profit_factor}}</td>
      <td>${{r.avg_r>=0?'+':''}}${{r.avg_r}}R</td>
      <td style="color:${{r.net_pnl>=0?'#34d399':'#f87171'}};font-weight:800">${{t_pnl_fmt(r.net_pnl)}}</td>
      <td>$${{r.end_equity.toFixed(2)}}</td>
      <td style="color:#f87171">-${{r.max_dd_pct}}%</td>
      <td><code>${{r.best_session}}</code></td>
      <td><code>${{r.best_regime}}</code></td>
    </tr>
  `).join('');
}}

function t_pnl_fmt(v) {{
  return (v >= 0 ? '+$' : '-$') + Math.abs(v).toFixed(2);
}}

function initCalendarMonths() {{
  const trades = currentDataset.trades || [];
  const months = [...new Set(trades.map(t => t.entry_time.slice(0, 7)))].sort();
  const sel = document.getElementById('cal-month');
  sel.innerHTML = months.map(m => `<option value="${{m}}">${{m}}</option>`).join('');
  if (months.length > 0) {{
    sel.value = months[months.length - 1];
    renderCalendar();
  }}
}}

function renderCalendar() {{
  const m = document.getElementById('cal-month').value;
  if (!m) return;
  const [yr, mo] = m.split('-').map(Number);
  const daysInMonth = new Date(yr, mo, 0).getDate();
  const daily = {{}};
  (currentDataset.trades || []).forEach(t => {{
    if (t.entry_time.startsWith(m)) {{
      const d = parseInt(t.entry_time.slice(8, 10), 10);
      if (!daily[d]) daily[d] = {{ pnl: 0, n: 0 }};
      daily[d].pnl += t.net_pnl;
      daily[d].n += 1;
    }}
  }});

  let html = '';
  for (let d = 1; d <= daysInMonth; d++) {{
    const info = daily[d];
    if (!info) {{
      html += `<div class="cal-day"><div style="color:#64748b">Day ${{d}}</div><div style="color:#475569;font-size:10px">No Trade</div></div>`;
    }} else {{
      const cls = info.pnl >= 0 ? 'win' : 'loss';
      html += `<div class="cal-day ${{cls}}">
        <div style="font-weight:700">Day ${{d}} (${{info.n}}t)</div>
        <div style="font-weight:800;color:${{info.pnl>=0?'#34d399':'#f87171'}}">${{info.pnl>=0?'+':''}}$${{info.pnl.toFixed(2)}}</div>
      </div>`;
    }}
  }}
  document.getElementById('cal-grid').innerHTML = html;
}}

window.addEventListener('DOMContentLoaded', () => {{
  initChart();
  selectAgent('11:LIAM');
}});
</script>
</body>
</html>
"""
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[HTML LAB] Built {OUT_HTML} ({os.path.getsize(OUT_HTML) / 1024:.1f} KB)")


if __name__ == "__main__":
    build_html()
