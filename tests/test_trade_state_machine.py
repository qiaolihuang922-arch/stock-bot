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

        self.assertEqual(state["schema_version"], "v21.0.1")
        self.assertEqual(state["state"], "WAIT_VOLUME")
        self.assertEqual(state["phase"], "ENTRY_GATE")
        self.assertEqual(state["action"], "WAIT")
        self.assertFalse(state["is_actionable"])
        self.assertFalse(state["is_terminal"])
        self.assertEqual(state["transition_event"], "VOLUME_GATE_FAILED")
        self.assertEqual(state["transition_from"], "UNKNOWN")
        self.assertEqual(state["transition_to"], "WAIT_VOLUME")
        self.assertEqual(state["target_state"], "WAIT_VOLUME")
        self.assertTrue(state["allowed_transition"])
        self.assertEqual(state["transition_table"], "UNHELD_TRANSITION_TABLE")
        self.assertEqual(state["next_required_event"], "VOLUME_CONFIRMED")
        self.assertIn("DATA_MISSING", state["guards"])
        self.assertIn("VOLUME_WEAK", state["guards"])
        self.assertIn("VOLUME_WEAK", state["blocked_by"])
        self.assertFalse(state["requires_order_lifecycle"])
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

        self.assertEqual(artifact["schema_version"], "v21.0.1")
        self.assertFalse(artifact["db_write"])
        self.assertFalse(artifact["schema_change"])
        self.assertEqual(len(artifact["items"]), 1)
        self.assertEqual(artifact["items"][0]["state"], "WAIT_VOLUME")
        self.assertEqual(artifact["items"][0]["phase"], "ENTRY_GATE")
        self.assertEqual(artifact["items"][0]["transition_event"], "VOLUME_GATE_FAILED")
        self.assertEqual(artifact["items"][0]["transition_from"], "UNKNOWN")
        self.assertEqual(artifact["items"][0]["transition_to"], "WAIT_VOLUME")
        self.assertTrue(artifact["items"][0]["allowed_transition"])
        self.assertEqual(artifact["items"][0]["next_required_event"], "VOLUME_CONFIRMED")
        self.assertIn("VOLUME_WEAK", artifact["items"][0]["blocked_by"])

    def test_unheld_transition_table_replays_progression_to_buyable(self):
        payload = _watch_payload()
        payload["cross_day_context"] = {"previous_state": "WAIT_VOLUME"}
        ready = evaluate_unheld_state(
            "緯創",
            payload,
            funnel_state="可準備",
            watch_state="等量能",
            source_status="available",
        )
        self.assertEqual(ready["transition_from"], "WAIT_VOLUME")
        self.assertEqual(ready["transition_event"], "SETUP_READY")
        self.assertEqual(ready["state"], "READY")
        self.assertFalse(ready["is_actionable"])

        payload["cross_day_context"] = {"previous_state": "READY"}
        buyable = evaluate_unheld_state(
            "緯創",
            payload,
            funnel_state="可買",
            watch_state="可買",
            source_status="available",
        )
        self.assertEqual(buyable["transition_from"], "READY")
        self.assertEqual(buyable["transition_event"], "BUY_SIGNAL_CONFIRMED")
        self.assertEqual(buyable["state"], "BUYABLE")
        self.assertTrue(buyable["is_actionable"])
        self.assertEqual(buyable["next_required_event"], "SUBMIT_ORDER")

    def test_unheld_transition_uses_setup_guard_when_labels_are_missing(self):
        payload = _watch_payload()
        payload["result"]["market_grade"] = "B"
        state = evaluate_unheld_state(
            "緯創",
            payload,
            funnel_state=None,
            watch_state=None,
            source_status="available",
        )

        self.assertEqual(state["transition_event"], "SETUP_NOT_READY")
        self.assertEqual(state["state"], "WAIT_SETUP")
        self.assertEqual(state["target_state"], "WATCH")
        self.assertIn("SETUP_NOT_READY", state["guards"])
        self.assertIn("VOLUME_WEAK", state["guards"])
        self.assertIn("VOLUME_NOT_PRIMARY", state["guards"])
        self.assertIn("SETUP_NOT_READY", state["blocked_by"])

    def test_unheld_buyable_with_source_error_fails_closed_before_order_lifecycle(self):
        payload = _watch_payload()
        payload["result"].update({
            "decision": "BUY",
            "trade_state": "READY",
            "volume_state": "OK",
            "rr": 2.0,
            "entry_quality": "A",
            "breakout_distance": 1.0,
        })

        state = evaluate_unheld_state(
            "可買候選",
            payload,
            funnel_state="可買",
            watch_state="可買",
            source_status="source-error",
        )

        self.assertEqual(state["state"], "WAIT_DATA")
        self.assertEqual(state["phase"], "DATA_GATE")
        self.assertEqual(state["transition_event"], "DATA_GATE_FAILED")
        self.assertFalse(state["is_actionable"])
        self.assertFalse(state["requires_order_lifecycle"])
        self.assertIn("DATA_SOURCE_ERROR", state["guards"])
        self.assertIn("DATA_SOURCE_ERROR", state["blocked_by"])

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
        self.assertIn("【06/08 盤後｜v21.1】", unheld)
        self.assertIn("交易狀態：等接近｜動作：等待｜主因：個股弱勢｜還差：接近觸發", unheld)
        self.assertNotIn("交易狀態：不可行動", unheld)

    def test_breakout_distance_gate_only_blocks_breakout_setup(self):
        payload = _watch_payload()
        payload["result"].update({
            "market_grade": "B",
            "volume_state": "OK",
            "trade_state": "READY",
            "rr": 2.0,
            "entry_quality": "B",
            "decision_type": "wait_breakout_confirm",
            "breakout_distance": 9,
        })

        state = evaluate_unheld_state(
            "breakout",
            payload,
            funnel_state="等接近",
            watch_state="等接近",
            source_status="available",
        )

        self.assertIn("TOO_FAR_FROM_TRIGGER", state["guards"])

    def test_far_pullback_and_trend_continuation_are_not_blocked_by_breakout_distance(self):
        for decision_type, phase in [
            ("pullback", "HEALTHY_PULLBACK"),
            ("trend_continuation", "BREAKOUT"),
        ]:
            payload = _watch_payload()
            payload["result"].update({
                "market_grade": "B",
                "volume_state": "OK",
                "trade_state": "READY",
                "rr": 2.0,
                "entry_quality": "B",
                "decision_type": decision_type,
                "structure_phase": phase,
                "breakout_distance": 12,
            })

            state = evaluate_unheld_state(
                decision_type,
                payload,
                funnel_state="等回測",
                watch_state="等回測",
                source_status="available",
            )

            self.assertNotIn("TOO_FAR_FROM_TRIGGER", state["guards"])
            self.assertNotIn("TOO_FAR_FROM_TRIGGER", state["blocked_by"])


if __name__ == "__main__":
    unittest.main()



