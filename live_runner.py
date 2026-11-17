"""
Syndicate Alpha — Live Floor Runner & Streaming Blackboard Daemon
------------------------------------------------------------------
Runs the live floor loop:
1. Receives incoming live market bars / stream
2. Dispatches bar data to all 16 specialized floor agents
3. Collects AgentPackets and computes 3-state consensus via VictorBlackboardConsensus
4. Emits real-time state to blackboard/live_state.json for dashboard & external consumers
5. Routes approved signals to ethan_math.py ($5 fee-adjusted sizing) & ryan_exec.py
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from trading_desk.command.victor_boss import AgentPacket, VictorBlackboardConsensus
from trading_desk.agents.kai_smc import KaiFibSMC
from trading_desk.agents.arthur_vet import ArthurRegimeVet
from trading_desk.agents.leo_sweep import LeoKillzoneSweep
from trading_desk.agents.nina_range import NinaSMCHunter
from trading_desk.agents.max_trend import MaxTrapSpecialist
from trading_desk.agents.sam_l2 import SamOrderBookDOM
from trading_desk.agents.jack_vsa import JackVSASpecialist
from trading_desk.agents.ben_news import BenNewsSentinel
from trading_desk.agents.elena_price_action import ElenaPriceAction
from trading_desk.agents.omar_flow import OmarOrderFlow
from trading_desk.agents.marcus_breakout import MarcusBreakoutSpecialist
from trading_desk.agents.sarah_psych import SarahPsychologist
from trading_desk.agents.david_veteran import DavidVeteranTrader
from trading_desk.execution.ethan_math import EthanRiskMath
from trading_desk.execution.ryan_exec import RyanExecutionLifecycle


class LiveFloorRunner:
    def __init__(self, blackboard_path: Optional[str] = None):
        if blackboard_path is None:
            blackboard_path = os.path.join(BASE_DIR, "blackboard", "live_state.json")
        self.blackboard_path = blackboard_path

        # Floor Command & Execution
        self.victor = VictorBlackboardConsensus(initiator_boost=2.5, pending_lean_mult=0.5, blackboard_path=self.blackboard_path, auto_publish_disk=True)
        self.ethan = EthanRiskMath(fixed_risk_usd=5.0, fee_rate=0.0001)
        self.ryan = RyanExecutionLifecycle(be_trigger_r=0.95, be_lock_r=0.25, trail_trigger_r=1.95)

        # Floor Setup & Filter Specialists
        self.agents = {
            "1:BEN": BenNewsSentinel("1:BEN"),
            "2:ARTHUR": ArthurRegimeVet("2:ARTHUR"),
            "3:MARCUS": MarcusBreakoutSpecialist("3:MARCUS"),
            "4:NINA": NinaSMCHunter("4:NINA"),
            "5:MAX": MaxTrapSpecialist("5:MAX"),
            "6:LEO": LeoKillzoneSweep("6:LEO"),
            "7:KAI": KaiFibSMC("7:KAI"),
            "8:ELENA": ElenaPriceAction("8:ELENA"),
            "9:SAM": SamOrderBookDOM("9:SAM"),
            "10:OMAR": OmarOrderFlow("10:OMAR"),
            "11:JACK": JackVSASpecialist("11:JACK"),
            "12:SARAH": SarahPsychologist("12:SARAH"),
            "13:DAVID": DavidVeteranTrader("13:DAVID"),
        }

        # Edge Matrix
        edge_path = os.path.join(BASE_DIR, "trading_desk", "agent_edge_matrix.json")
        self.edge_matrix = {}
        if os.path.exists(edge_path):
            with open(edge_path, "r", encoding="utf-8") as f:
                self.edge_matrix = json.load(f)

        self.bar_count = 0
        self.last_5m_close = None

    def process_incoming_bar(self, bar: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a single live 1-minute bar:
        - Evaluates in-trade management if in trade
        - Gathers agent packets
        - Computes Victor consensus & veto checks
        - Updates blackboard/live_state.json
        - Sizes and executes approved orders
        """
        self.bar_count += 1
        close_px = float(bar.get("close", 0.0))
        if self.last_5m_close is None or self.bar_count % 5 == 0:
            self.last_5m_close = close_px

        ts = bar.get("timestamp", datetime.utcnow().isoformat())
        bar_1m = {"close": close_px, "open": float(bar.get("open", close_px)), "high": float(bar.get("high", close_px)), "low": float(bar.get("low", close_px)), "timestamp": str(ts)}
        bar_5m = {"close": self.last_5m_close}

        # 1. Active trade lifecycle check
        if self.ryan.is_in_trade():
            exit_log = self.ryan.update_lifecycle(bar, self.bar_count)
            if exit_log is not None:
                print(f"[LIVE RUNNER] Trade Closed: {exit_log['direction']} exit at {exit_log['exit_price']} ({exit_log['exit_reason']}) | Net: ${exit_log['net_pnl_usd']:+.2f} ({exit_log['r_multiple']:+.2f}R)")
            # Re-publish live state with in-trade info
            self.victor.publish_live_state(bar_1m, bar_5m, {"decision": "IN_TRADE_LIFECYCLE", "active_trade": self.ryan.active_trade})
            return {"status": "IN_TRADE", "active_trade": self.ryan.active_trade, "exit_log": exit_log}

        # Determine session and regime for edge weights
        est_hr = (datetime.utcnow().hour - 5) % 24
        sess = "ASIA" if est_hr in (18, 19, 20, 21, 22, 23, 0, 1) else ("LONDON" if est_hr in (2, 3, 4, 5, 6, 7) else "NEW_YORK")
        reg = "TRENDING" if (bar.get("chop_index", 50.0) < 52.5 and bar.get("adx", 20.0) >= 20.0) else "SIDEWAYS"
        curr_edge_weights = self.edge_matrix.get(sess, {}).get(reg, {})

        # 2. Gather AgentPackets from floor specialists
        packets = {}
        for ag_name, ag_inst in self.agents.items():
            packets[ag_name] = ag_inst.evaluate(bar)

        # 3. VictorBoss 3-State Consensus & Veto Resolution
        decision = self.victor.update_and_evaluate(packets, bar_1m, bar_5m, curr_edge_weights)

        # 4. If approved trade, size via Ethan and execute via Ryan
        if decision["decision"] in ("EXECUTE_BUY", "EXECUTE_SELL"):
            direction = decision["side"]
            atr = float(bar.get("atr_5m", bar.get("atr_14", 3.5)))
            sized_order = self.ethan.size_trade(
                entry_price=close_px,
                stop_loss=decision.get("stop_loss"),
                tp1=decision.get("tp1"),
                tp2=decision.get("tp2"),
                direction=direction,
                atr=atr
            )
            trade_obj = self.ryan.open_trade(decision, sized_order, self.bar_count, ts)
            print(f"\n⚡ [LIVE RUNNER] EXECUTION APPROVED: {direction} @ ${close_px:.2f} | Size: {sized_order['qty_oz']} oz ($5 Risk) | SL: ${sized_order['stop_loss']:.2f} | TP1: ${sized_order['tp1']:.2f} | TP2: ${sized_order['tp2']:.2f}")
            print(f"   Initiators: {decision['initiators']} | Confirmers: {decision['confirming_agents']} | Score: {decision.get('weighted_buy_score') or decision.get('weighted_sell_score')}")

        return decision


def run_live_demo():
    print("[LIVE RUNNER] Initializing Live Trading Floor Daemon...")
    runner = LiveFloorRunner()
    print(f"[LIVE RUNNER] Blackboard linked to: {runner.blackboard_path}")

    # Simulate 5 live streaming sample bars to demonstrate floor consensus and blackboard emission
    demo_bars = [
        {"timestamp": datetime.utcnow().isoformat(), "open": 2680.0, "high": 2682.0, "low": 2679.5, "close": 2681.5, "volume": 120, "atr_5m": 3.2, "chop_index": 48.0, "adx": 26.0, "swing_high_20": 2685.0, "swing_low_20": 2675.0, "range_high_60": 2688.0, "range_low_60": 2672.0, "fib_240_long": 0.65, "lower_wick_ratio": 2.2, "upper_wick_ratio": 0.3, "bull_mss_1m": True, "vol_z_score": 1.45, "delta_sum_5": 75.0, "delta_sum_15": 110.0, "has_real_l2": True, "l2_bid_ask_ratio_mean": 1.45, "in_killzone": True},
        {"timestamp": datetime.utcnow().isoformat(), "open": 2681.5, "high": 2683.0, "low": 2681.0, "close": 2682.8, "volume": 140, "atr_5m": 3.2, "chop_index": 46.0, "adx": 27.0, "swing_high_20": 2685.0, "swing_low_20": 2675.0, "range_high_60": 2688.0, "range_low_60": 2672.0, "fib_240_long": 0.63, "lower_wick_ratio": 1.8, "upper_wick_ratio": 0.2, "bull_mss_1m": True, "vol_z_score": 1.60, "delta_sum_5": 95.0, "delta_sum_15": 140.0, "has_real_l2": True, "l2_bid_ask_ratio_mean": 1.60, "in_killzone": True},
    ]

    for b in demo_bars:
        res = runner.process_incoming_bar(b)
        print(f"Bar processed: Decision = {res.get('decision')} | Upcoming: {len(res.get('upcoming_setups', []))}")

    if os.path.exists(runner.blackboard_path):
        print(f"\n[LIVE RUNNER] Successfully verified live blackboard output at {runner.blackboard_path}:")
        with open(runner.blackboard_path, "r", encoding="utf-8") as f:
            snap = json.load(f)
        print(f"  Decision: {snap['decision']}, Initiators: {snap['initiators']}, Confirmers: {snap['confirming_agents']}")


if __name__ == "__main__":
    run_live_demo()
