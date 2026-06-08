import unittest
from datetime import datetime
from unittest.mock import patch

from core import generator
from core.trade_state_machine import (
    build_state_artifact,
    evaluate_position_state,
    evaluate_unheld_state,
    visible_state_line,
)


def _watch_payload():
    return {
        "stock_code": "3231",
        "price": 163.5,
        "change": -4.39,
        "volume_ratio": 0.68,
        "result": {
            "decision": "WAIT",
            "action": 0,
            "rr": 1.6,
            "trade_state": "NO_VOLUME",
            "structure_phase": "BREAKOUT",
            "price_behavior": "NORMAL",
            "market_grade": "D",
            "volume_state": "WEAK",
            "entry_quality": "D",
            "breakout_distance": 19.25,
        },
        "holding": None,
    }


def _holding_payload():
    return {
        "stock_code": "2303",
        "price": 120,
        "change": -4.0,
        "volume_ratio": 1.2,
        "result": {
            "decision": "WAIT",
            "action": 0,
            "rr": 0.8,
            "trade_state": "WAIT",
            "structure_phase": "WEAK",
            "market_grade": "D",
        },
        "holding": {
            "shares": 100,
            "avg_price": 130,
            "warning_price": 124,
            "stop_price": 121,
        },
    }


class TradeStateMachineTest(unittest.TestCase):
    def test_unheld_volume_wait_stays_wait_volume_not_blocked(self):
        payload = _watch_payload()
        state = evaluate_unheld_state(
            "緯創",
            payload,
            funnel_state="等量能",
            watch_state="等量能",
            trigger="量能回升且重新接近買點",
            source_status="missing-source",
        )

        self.assertEqual(state["schema_version"], "v21.0")
        self.assertEqual(state["state"], "WAIT_VOLUME")
        self.assertEqual(state["action"], "WAIT")
        self.assertEqual(state["trigger"], "量能回升且重新接近買點")
        self.assertFalse(state["db_write"])
        self.assertFalse(state["schema_change"])
        self.assertIn("交易狀態：等量能", visible_state_line(state))

    def test_holding_stop_loss_maps_to_single_exit_state(self):
        payload = _holding_payload()
        state = evaluate_position_state(
            "聯電",
            payload,
            summary_action="停損",
            trigger="清出後等重新買點",
        )

        self.assertEqual(state["state"], "STOP_LOSS")
        self.assertEqual(state["action"], "STOP_LOSS")
        self.assertEqual(state["state_label"], "停損")
        self.assertEqual(state["trigger"], "清出後等重新買點")

    def test_artifact_is_readonly_and_contains_each_stock_once(self):
        payload = _watch_payload()
        payload["trade_state_machine"] = evaluate_unheld_state(
            "緯創",
            payload,
            funnel_state="等量能",
            watch_state="等量能",
        )

        artifact = build_state_artifact({"緯創": payload})

        self.assertEqual(artifact["schema_version"], "v21.0")
        self.assertFalse(artifact["db_write"])
        self.assertFalse(artifact["schema_change"])
        self.assertEqual(len(artifact["items"]), 1)
        self.assertEqual(artifact["items"][0]["state"], "WAIT_VOLUME")

    def test_report_cards_include_trade_state_line(self):
        payload = _watch_payload()
        with patch.object(generator, "get_market_phase", return_value="盤後"):
            messages = generator.formatTelegramMessages(
                {"緯創": payload},
                "FULL DETAIL",
                None,
                None,
                "🟡 局部機會",
                datetime(2026, 6, 8),
                strategy_evidence_summary="📊 策略證據 v20.0\n狀態：可用\n樣本 35 筆",
            )

        unheld = messages[1]
        self.assertIn("【06/08 盤後｜v21.0】", unheld)
        self.assertIn("交易狀態：等量能｜動作：等待｜觸發：量能回升且重新接近買點", unheld)
        self.assertNotIn("交易狀態：不可行動", unheld)


if __name__ == "__main__":
    unittest.main()
