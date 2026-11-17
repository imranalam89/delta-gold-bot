---
name: syndicate-trading-desk
description: Institutional multi-agent quantitative day trading floor for Gold (GC) and CME Globex futures with live consensus, order book depth, and risk circuit breakers.
---

# Syndicate Alpha — Multi-Agent Day Trading Desk Skill

A high-performance algorithmic trading floor combining 16 specialized agents for institutional day trading on Gold futures (`GC.v.0`).

## Architecture & Floor Hierarchy

### 1. Command & Consensus (`trading_desk/command/`)
* **Victor Boss (`victor_boss.py`)**: Master 3-state consensus engine (`INSTANT_ACTION`, `PENDING_SETUP`, `HARD_VETO`). Boosts initiator setups by 2.5x and verifies quorum consensus.

### 2. Specialist Setup Agents (`trading_desk/agents/`)
* **Ben News (`ben_news.py`)**: Red-Folder News Sentinel (CPI / FOMC / NFP lockout shields).
* **Maya & Elena (`elena_price_action.py`)**: Price action microstructure, pinbars, and market structure shifts (MSS).
* **Liam & Jack (`jack_vsa.py`)**: Volume Spread Analysis (VSA), stopping volume, and absorption detection.
* **Sam & Omar (`sam_l2.py`, `omar_flow.py`)**: Level 2 order book heatmap imbalance and cumulative volume delta.
* **Kai & Nina (`kai_smc.py`, `nina_range.py`)**: Smart Money Concepts (SMC), fair value gaps (FVG), and liquidity sweeps.
* **Marcus & Max (`marcus_breakout.py`, `max_trend.py`)**: Box breakouts and multi-timeframe EMA trend alignment.
* **Arthur & David (`arthur_vet.py`, `david_veteran.py`)**: Senior clearance and historical regime validation.
* **Sarah (`sarah_psych.py`)**: Floor psychologist enforcing anti-greed, anti-revenge, and volatility discipline.

### 3. Quantitative Risk & Execution (`trading_desk/execution/`)
* **Ethan Math (`ethan_math.py`)**: Quantitative risk manager enforcing:
  * $5.00 fixed-risk per setup with 0.01% Delta Exchange fee accounting.
  * **Consecutive Loss Dampener**: Automatically drops risk to $2.50 (50%) after 2 consecutive stop-outs.
  * **Daily Drawdown Circuit Breaker**: Hard locks floor when daily loss exceeds -$15.00.
  * **Killzone Gate**: Eliminates low-edge midday churn (12:00-16:59 EST).
* **Ryan Exec (`ryan_exec.py`)**: Trade lifecycle executor handling trailing consensus runners, partial profit locks, and stop movements.

## Backtest Performance (5-Month CME Globex Gold: May - Oct 2026)

* **Dataset**: 151,343 1-Minute CME Globex bars (~110 active trading days).
* **Profile**: `DTS_ELITE_LOW_DD` (Enhanced with Day-Trader-Skill Guardrails).
* **Starting Equity**: $100.00
* **Ending Equity**: **$986.80** (+886.8% net return)
* **Net Profit**: **+$886.80**
* **Win Rate**: **66.11%** (199 Wins / 102 Losses)
* **Profit Factor**: **2.76**
* **Max Drawdown**: **-15.74%** (slashed by ~40% from baseline -25.94%)
* **Calmar Ratio**: **56.34**

## Interactive Dashboard
Open `backtest_dashboard.html` in your browser to inspect interactive equity curves, session heatmaps, trade-by-trade analytics, and full execution logs.
