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
            "strategy_feature_snapshots": [
                {"stock_id": "2337", "trade_date": "2026-05-28", "watch_category": "弱勢淘汰", "reject_family": "弱勢"},
                {"stock_id": "2337", "trade_date": "2026-05-27", "watch_category": "淘汰", "reject_family": "弱勢"},
            ],
            "strategy_outcome_metrics": [
                {"stock_id": "2337", "trade_date": "2026-05-28", "close_return_pct": 3.5, "max_favorable_excursion_pct": 5.5},
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
        self.assertEqual(context["previous_state"], "eliminated")
        self.assertEqual(context["repair_status"], "improving")
        self.assertEqual(context["dedupe_guard"], "same_day_executed")
        self.assertEqual(context["previous_action"], "buy")
        self.assertGreaterEqual(context["historical_evidence_weight"], 1)
        self.assertIn("cannot_flip_to_buy_alone", context["forbidden_effects"])


if __name__ == "__main__":
    unittest.main()
