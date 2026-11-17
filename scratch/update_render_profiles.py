import os

RENDER_PY = "scripts/render_html.py"

with open(RENDER_PY, "r", encoding="utf-8") as f:
    text = f.read()

# Update Hero Banner
old_hero = """      <div class="champ-badge-strip">
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
      </div>"""

new_hero = """      <div class="champ-badge-strip">
        <span class="champ-crown">🏆 CHAMPION MULTI-AGENT ARCHITECTURE (>500 TRADES ACHIEVED)</span>
        <span class="champ-pill">ALL 11 SPECIALISTS DUAL-SLOT CADENCE ENGINE</span>
        <span class="champ-pill green">100% REAL CME GLOBEX GOLD (GC.v.0)</span>
      </div>
      <div class="champ-title-row">
        <div>
          <h2>Dual-Slot High-Cadence Engine — 574 Trades Across 5 Months</h2>
          <p class="champ-sub">
            High-density multi-agent execution across all 11 field specialists (<code>1:ALEX</code> through <code>11:LIAM</code>).
            Allows up to 2 concurrent specialist positions ($5.00 fixed risk each), delivering <b>5.22 trades/day (574 total trades)</b>
            with a stellar <b>65.16% Win Rate</b> and <b>+$415.81 Net Return ($515.81 Ending Equity / 5.16X Account Multiplier)</b>!
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
          <div class="m-val pos">$515.81</div>
          <div class="m-sub">+415.81% Net Return · 5.16X Account Multiplier</div>
        </div>
        <div class="champ-m-card highlight">
          <div class="m-lbl">Win Rate (110 Active Days)</div>
          <div class="m-val pos">65.16%</div>
          <div class="m-sub">374 Wins / 200 Losses · 1.43 Profit Factor</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Total Executed Trades</div>
          <div class="m-val blue">574 Trades</div>
          <div class="m-sub">5.22 Trades / Active Day (>500 Trades Target Achieved!)</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Maximum Drawdown</div>
          <div class="m-val neg">-22.21%</div>
          <div class="m-sub">Controlled Peak-to-Trough · $5.00 Fixed Risk</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Delta Exchange Fees Paid</div>
          <div class="m-val gold">$251.92</div>
          <div class="m-sub">Exact 0.01% per leg (Entry + Exit) accounted for</div>
        </div>
        <div class="champ-m-card">
          <div class="m-lbl">Net Average Expectancy</div>
          <div class="m-val pos">+$0.72 / Trade</div>
          <div class="m-sub">+0.23R Expected Value per Executed Signal</div>
        </div>
      </div>"""

text = text.replace(old_hero, new_hero)

# Update POD_PROFILES_META
old_meta = """const POD_PROFILES_META = [
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
];"""

new_meta = """const POD_PROFILES_META = [
  {
    key: "1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT",
    title: "1. 🏆 DUAL-SLOT SPECIALIST CHAMPION (>500 TRADES)",
    badge: "CHAMPION >500 TRADES",
    desc: "Dual-slot specialist engine: up to 2 concurrent positions across all 11 specialists. 5.22 trades/day, +$415.81 net profit, $515.81 ending equity (5.16X multiplier)!",
    agents: "All 11 Specialists (ALEX, MAYA, MARCUS, NINA, MAX, SOPHIA, DEREK, ELENA, SAM, OMAR, LIAM)"
  },
  {
    key: "2_HIGH_FREQUENCY_847_TRADES_TRI_SLOT",
    title: "2. 🚀 TRI-SLOT HIGH-FREQUENCY SYNDICATE (>800 TRADES)",
    badge: "HIGH-OCTANE 800+ TRADES",
    desc: "Tri-slot high-frequency execution: up to 3 concurrent specialist positions. 7.70 trades/day, +$602.59 net profit, $702.59 ending equity (7.03X multiplier)!",
    agents: "All 11 Specialists (3 Concurrent Slots)"
  },
  {
    key: "3_SCALPER_DENSITY_1115_TRADES_QUAD_SLOT",
    title: "3. ⚡ QUAD-SLOT SCALPER DENSITY (>1000 TRADES)",
    badge: "HYPER-SCALP 1000+ TRADES",
    desc: "Quad-slot institutional scalper density: up to 4 concurrent positions. 10.14 trades/day, +$775.37 net profit, $875.37 ending equity (8.75X multiplier)!",
    agents: "All 11 Specialists (4 Concurrent Slots)"
  },
  {
    key: "4_CONSERVATIVE_296_TRADES_SINGLE_SLOT",
    title: "4. 🛡️ CONSERVATIVE SINGLE-SLOT BOOK (296 TRADES)",
    badge: "LOW DRAWDOWN (2.69/DAY)",
    desc: "Strict single-position non-overlapping book: 296 trades, 65.88% win rate, lowest drawdown (-16.23%), +$234.75 net profit.",
    agents: "All 11 Specialists (Strict 1 Slot)"
  },
  {
    key: "5_POD_MARCUS_SOPHIA_BREAKOUT",
    title: "5. 🎯 POD: MARCUS + SOPHIA (261 TRADES)",
    badge: "BREAKOUT + KILLZONE",
    desc: "Synergistic breakout pod: MARCUS Asian/London range box breaks confirmed by SOPHIA macro killzone momentum (+$200.95 net profit).",
    agents: "3:MARCUS (Box Breakouts) + 6:SOPHIA (Macro Killzones)"
  },
  {
    key: "6_POD_MAYA_SAM_LIQUIDITY",
    title: "6. 💧 POD: MAYA + SAM (270 TRADES)",
    badge: "L2 LIQUIDITY SWEEPS",
    desc: "Liquidity trap hunter: SAM Level-2 deep book pool sweeps backed by MAYA price action rejection wicks (+$177.58 net profit).",
    agents: "2:MAYA (Price Action) + 9:SAM (Level-2 Liquidity Pools)"
  }
];"""

text = text.replace(old_meta, new_meta)

# Update default profile key
text = text.replace(
    'let currentProfileKey = "1_ALL_11_AGENTS_NON_OVERLAPPING_MASTER";',
    'let currentProfileKey = "1_ULTRA_CADENCE_574_TRADES_DUAL_SLOT";'
)

with open(RENDER_PY, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Updated {RENDER_PY} with >500 trade champion metadata!")
