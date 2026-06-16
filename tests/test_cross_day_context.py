import unittest
from datetime import datetime
from types import SimpleNamespace

from services.cross_day_context import build_cross_day_contexts


class Query:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class Client:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        value = self.rows.get(name)
        if isinstance(value, Exception):
            raise value
        return Query(value or [])


def payload(stock_code="2337", **result_overrides):
    result = {
        "decision": "WAIT",
        "action": 0,
        "rr": 0.8,
        "market_grade": "B",
        "entry_quality": "B",
        "structure_phase": "BREAKOUT_NEAR",
        "price_behavior": "NORMAL",
        "heat_state": "NORMAL",
        "trade_state": "WAIT",
    }
    result.update(result_overrides)
    return {"stock_code": stock_code, "result": result, "price": 100, "change": 1.2}


class CrossDayContextTest(unittest.TestCase):
    def test_missing_source_does_not_fake_history(self):
        contexts = build_cross_day_contexts({"旺宏": payload()}, client=None)

        context = contexts["旺宏"]
        self.assertEqual(context["source_status"], "missing-source")
        self.assertEqual(context["previous_state"], "unknown")
        self.assertEqual(context["consecutive_observe_days"], 0)
        self.assertEqual(context["historical_evidence_weight"], 0)
        self.assertEqual(context["dedupe_guard"], "unknown")

    def test_ready_history_calculates_repair_weight_and_same_day_guard(self):
        client = Client({
            "daily_signal_snapshot": [
                {"stock_id": "2337", "trade_date": "2026-05-28", "action": "FAIL", "is_tradeable": False, "position_state": "WAIT"},
                {"stock_id": "2337", "trade_date": "2026-05-27", "action": "WAIT", "is_tradeable": False, "position_state": "WAIT"},
            ],
            "position_events": [
                {"stock_code": "2337", "stock_name": "旺宏", "event_date": "2026-05-29", "action_label": "買入", "shares_delta": 100},
            ],
        })

        contexts = build_cross_day_contexts(
            {"旺宏": payload()},
            client=client,
            now=datetime(2026, 5, 29),
        )

        context = contexts["旺宏"]
        self.assertEqual(context["source_status"], "ready")
        self.assertNotIn("local_position_events", context["source_of_truth"])
        self.assertEqual(context["previous_state"], "eliminated")
        self.assertEqual(context["repair_status"], "improving")
        self.assertEqual(context["dedupe_guard"], "same_day_executed")
        self.assertEqual(context["previous_action"], "buy")
        self.assertIsNone(context["same_run_guard"])
        self.assertGreaterEqual(context["historical_evidence_weight"], 1)
        self.assertIn("cannot_flip_to_buy_alone", context["forbidden_effects"])
        self.assertIn("cannot_use_same_run_as_cross_day_memory", context["forbidden_effects"])

    def test_local_today_events_do_not_become_cross_day_memory(self):
        client = Client({})

        contexts = build_cross_day_contexts(
            {"旺宏": payload()},
            client=client,
            today_position_events={
                "旺宏": {
                    "bought_shares": 0,
                    "sold_shares": 40,
                    "labels": ["減碼"],
                }
            },
            now=datetime(2026, 5, 29),
        )

        context = contexts["旺宏"]
        self.assertEqual(context["source_status"], "insufficient-data")
        self.assertEqual(context["source_of_truth"], [])
        self.assertEqual(context["previous_action"], "unknown")
        self.assertIsNone(context["previous_action_date"])
        self.assertEqual(context["consecutive_observe_days"], 0)
        self.assertEqual(context["historical_evidence_weight"], 0)
        self.assertEqual(context["dedupe_guard"], "unknown")
        self.assertEqual(context["same_run_guard"], "same_day_executed")
        self.assertEqual(context["same_run_action"], "reduce")
        self.assertEqual(context["same_run_source"], "today_position_events")

    def test_source_error_fails_closed_even_with_partial_rows_and_local_events(self):
        client = Client({
            "daily_signal_snapshot": [
                {"stock_id": "2337", "trade_date": "2026-05-28", "action": "WAIT", "is_tradeable": False, "position_state": "WAIT"},
            ],
            "position_events": RuntimeError("events unavailable"),
        })

        contexts = build_cross_day_contexts(
            {"旺宏": payload()},
            client=client,
            today_position_events={
                "旺宏": {
                    "bought_shares": 100,
                    "sold_shares": 0,
                    "labels": ["買入"],
                }
            },
            now=datetime(2026, 5, 29),
        )

        context = contexts["旺宏"]
        self.assertEqual(context["source_status"], "source-error")
        self.assertEqual(context["previous_state"], "unknown")
        self.assertEqual(context["previous_action"], "unknown")
        self.assertIsNone(context["previous_action_date"])
        self.assertEqual(context["consecutive_observe_days"], 0)
        self.assertEqual(context["historical_evidence_weight"], 0)
        self.assertEqual(context["dedupe_guard"], "unknown")
        self.assertEqual(context["same_run_guard"], "same_day_executed")

    def test_daily_signal_snapshot_ignores_other_versions(self):
        client = Client({
            "daily_signal_snapshot": [
                {"stock_id": "2337", "trade_date": "2026-05-28", "version": "v19.0", "action": "FAIL", "is_tradeable": False, "position_state": "WAIT"},
                {"stock_id": "2337", "trade_date": "2026-05-27", "version": "v20.4.5", "action": "WAIT", "is_tradeable": False, "position_state": "WAIT"},
            ],
            "position_events": [],
        })

        contexts = build_cross_day_contexts(
            {"旺宏": payload()},
            client=client,
            now=datetime(2026, 5, 29),
            version="v20.4.5",
        )

        context = contexts["旺宏"]
        self.assertEqual(context["source_status"], "ready")
        self.assertEqual(context["source_of_truth"], ["daily_signal_snapshot"])
        self.assertEqual(context["previous_state"], "observe")
        self.assertEqual(context["repair_status"], "repaired")

    def test_daily_price_points_are_persistent_cross_day_source(self):
        client = Client({
            "daily_signal_snapshot": [],
            "position_events": [],
            "daily_price": [
                {"stock_id": "2337", "trade_date": "2026-06-16", "close": 159},
                {"stock_id": "2337", "trade_date": "2026-06-15", "close": 155},
                {"stock_id": "2337", "trade_date": "2026-06-14", "close": 150},
                {"stock_id": "2337", "trade_date": "2026-06-13", "close": 148},
                {"stock_id": "3481", "trade_date": "2026-06-16", "close": 51.4},
            ],
        })

        contexts = build_cross_day_contexts(
            {"旺宏": payload()},
            client=client,
            now=datetime(2026, 6, 16),
        )

        context = contexts["旺宏"]
        self.assertEqual(context["source_status"], "ready")
        self.assertEqual(context["source_of_truth"], ["daily_price"])
        self.assertEqual(
            [point["close"] for point in context["recent_daily_price_points"]],
            [148.0, 150.0, 155.0, 159.0],
        )


if __name__ == "__main__":
    unittest.main()
