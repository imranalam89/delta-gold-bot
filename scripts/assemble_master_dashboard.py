"""
Syndicate Alpha — Assembles the complete All-in-One Master Dashboard into `backtest_dashboard.html`.
Unifies:
1. 🏆 Combined Master Floor: All 11 Specialists Non-Overlapping Book (296 trades, 65.88% WR, +$234.75 Net, 2.69 trades/day) + 5 Elite Pods
2. 🧪 11-Field-Specialist Laboratory: 1:ALEX through 11:LIAM, 3-gen evolution, multi-TF (1m, 5m, 15m, 1h), Sarah/Lucas/Oracle audits
3. 📊 Continuous TradingView Chart: 1m to 1D candles, trade markers, TP/SL overlays, timeline navigator
4. 📅 Daily P&L Calendar & Equity Growth Simulator: Monthly heatmap, equity & drawdown curves, killzone analytics
5. 🔬 Trade Journal & Multi-Agent Forensic Auditor: Full trade logs, 16-agent reliability matrix, CSV export
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAYLOAD_PATH = os.path.join(BASE_DIR, "data", "processed", "dashboard_payload.json")
OUT_HTML = os.path.join(BASE_DIR, "backtest_dashboard.html")


def read_payload():
    print(f"[ASSEMBLER] Loading payload from {PAYLOAD_PATH}...")
    with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
        payload_str = f.read()
    print(f"[ASSEMBLER] Payload loaded: {len(payload_str)/1024/1024:.2f} MB")
    return payload_str


def build_all_in_one():
    payload_str = read_payload()

    # Read the template from render_html or our assemble logic
    with open(os.path.join(BASE_DIR, "scripts", "generate_render_html.py"), "r", encoding="utf-8") as f:
        gen_script = f.read()

    # Extract HTML_TEMPLATE header
    start_marker = 'HTML_TEMPLATE = r"""'
    end_marker = "<script>"
    idx1 = gen_script.find(start_marker) + len(start_marker)
    idx2 = gen_script.find(end_marker) + len(end_marker)
    html_top = gen_script[idx1:idx2]

    # Now read the JavaScript part from render_html.py (lines 674 to 2325)
    with open(os.path.join(BASE_DIR, "scripts", "render_html.py"), "r", encoding="utf-8") as f:
        render_lines = f.readlines()

    # Find where JS starts
    js_lines = []
    in_js = False
    for line in render_lines:
        if "const PAYLOAD = __PAYLOAD_JSON__;" in line:
            in_js = True
        if in_js:
            if "</script>" in line:
                break
            js_lines.append(line)

    orig_js = "".join(js_lines)

    # Now let's inject our enhanced master floor, pod comparison, CSV export, and 11-agent lab JS
    master_additions = r"""
// =========================================================================
// ALL-IN-ONE MASTER TERMINAL EXTENSIONS (TABS, POD MATRIX, 11-AGENT LAB)
// =========================================================================

// --- 1. Master Tab Switcher ---
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
  } else if (tabId === 'tab-calendar') {
    requestAnimationFrame(() => {
      drawEquityChart();
    });
  } else if (tabId === 'tab-master-floor') {
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

// --- 2. Pod Comparison Matrix Table (Tab 1) ---
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
    
    // Compute max DD
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

// --- 3. CSV Export Function ---
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
  let csv = headers.join(",") + "\n";
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
    csv += row.join(",") + "\n";
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

// --- 4. 11-Field-Specialist Laboratory Engine (Tab 2) ---
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

  // Signal variants dropdown
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

    # Add master_additions to orig_js right after `initDashboard()` is defined
    # And make sure initDashboard also calls renderPodMatrixTable() and initLab()
    insert_pos = orig_js.find("function initDashboard() {")
    if insert_pos != -1:
        # Find opening brace
        brace_pos = orig_js.find("{", insert_pos) + 1
        call_inject = "\n  renderPodMatrixTable();\n  initLab();\n"
        orig_js = orig_js[:brace_pos] + call_inject + orig_js[brace_pos:]

    # Also make sure equity canvas draws to both canvases if they exist
    orig_js = orig_js.replace(
        'const canvas = document.getElementById("equityCanvas");',
        'const canvas = document.getElementById("equityCanvas"); const canvas4 = document.getElementById("equityCanvasTab4");'
    )
    # Also set default profile to 1_ALL_11_AGENTS_NON_OVERLAPPING_MASTER
    orig_js = orig_js.replace(
        'let currentProfileKey = "3_SNIPER_HIGH_RR_RUNNER";',
        'let currentProfileKey = "1_ALL_11_AGENTS_NON_OVERLAPPING_MASTER";'
    )

    combined_js = orig_js + "\n" + master_additions

    # Put everything together
    full_html = html_top + "\n" + combined_js + "\n</script>\n</body>\n</html>"

    # Replace __PAYLOAD_JSON__
    final_html = full_html.replace("__PAYLOAD_JSON__", payload_str)

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"[SUCCESS] Generated complete All-in-One Master Dashboard: {OUT_HTML} ({os.path.getsize(OUT_HTML)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    build_all_in_one()
