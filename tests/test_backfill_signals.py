import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from scripts.backfill_signals import (
    available_coverage,
    build_evidence_rows,
    build_rows_from_ohlcv,
    partial_coverage_warnings,
    upsert_rows,
    validate_signal_payloads
)


def sample_ohlcv():
    start = date(2026, 4, 1)
    rows = []
    current = start
    idx = 0

    while len(rows) < 35:
        if current.weekday() < 5:
            close = 100 + idx * 0.8
            rows.append({
                "stock_id": "3231",
                "trade_date": current,
                "open": close - 0.5,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000 + idx * 10,
                "source": "twse"
            })
            idx += 1

        current += timedelta(days=1)

    return rows


class BackfillSignalsTest(unittest.TestCase):
    def test_build_rows_preserves_ohlcv(self):
        rows = sample_ohlcv()
        start_date = rows[25]["trade_date"]
        end_date = rows[29]["trade_date"]
        price_rows, signal_rows = build_rows_from_ohlcv(
            "3231",
            rows,
            start_date,
            end_date,
            "v19.1.3"
        )

        self.assertEqual(len(price_rows), 5)
        self.assertEqual(len(signal_rows), 5)
        self.assertEqual(price_rows[0]["open"], rows[25]["open"])
        self.assertEqual(price_rows[0]["high"], rows[25]["high"])
        self.assertEqual(price_rows[0]["low"], rows[25]["low"])
        self.assertEqual(price_rows[0]["source"], "twse")
        self.assertEqual(validate_signal_payloads(signal_rows), [])
        market_rows, feature_rows, outcome_rows, audit_rows = build_evidence_rows(price_rows, signal_rows)
        self.assertEqual(len(market_rows), 5)
        self.assertEqual(len(feature_rows), 5)
        self.assertTrue(outcome_rows)
        self.assertEqual(feature_rows[0]["strategy_version"], "v19.1.3")
        self.assertIn("watch_category", feature_rows[0])

    def test_validate_payload_blocks_bad_best_candidate(self):
        errors = validate_signal_payloads([
            {
                "stock_id": "3231",
                "trade_date": "2026-05-22",
                "version": "v19.1.3",
                "close": 100,
                "volume_ratio": 1,
                "pattern": "LOCK_LIMIT",
                "market_state": "A",
                "structure_state": "STRONG",
                "position_state": "BREAKOUT",
                "rr": 0,
                "score": 3,
                "heat_level": 3,
                "action": "WAIT",
                "reasons": ["過熱 Lv.3"],
                "is_tradeable": False,
                "is_best_candidate": True
            }
        ])

        self.assertTrue(errors)

    def test_partial_coverage_can_validate_real_available_rows_only(self):
        rows = [
            {
                "stock_id": "3231",
                "trade_date": "2026-05-04",
                "version": "v20.4.5",
                "close": 100,
                "volume_ratio": 1,
                "pattern": "BREAKOUT",
                "market_state": "A",
                "structure_state": "STRONG",
                "position_state": "BREAKOUT",
                "rr": 1.5,
                "score": 4,
                "heat_level": 1,
                "action": "WAIT",
                "reasons": [],
                "is_tradeable": False,
                "is_best_candidate": False,
            }
        ]

        warnings, coverage = partial_coverage_warnings(
            rows,
            ["3231", "3035"],
            ["2026-05-01", "2026-05-04"],
        )

        self.assertEqual(coverage, available_coverage(rows))
        self.assertIn("missing source stock snapshots: 3035", warnings)
        self.assertIn("missing source trade dates: 2026-05-01", warnings)
        self.assertEqual(
            validate_signal_payloads(
                rows,
                coverage["stock_ids"],
                coverage["trade_dates"],
            ),
            [],
        )

    def test_upsert_rows_only_writes_current_production_tables(self):
        class Query:
            def __init__(self, name, calls):
                self.name = name
                self.calls = calls

            def upsert(self, rows, **kwargs):
                self.calls.append((self.name, "upsert", len(rows), kwargs))
                return self

            def execute(self):
                self.calls.append((self.name, "execute"))
                return SimpleNamespace(data=[])

        class Client:
            def __init__(self):
                self.calls = []

            def table(self, name):
                return Query(name, self.calls)

        client = Client()
        price_rows = [{
            "stock_id": "3231",
            "trade_date": "2026-05-04",
            "close": 100,
            "volume": 1000,
            "source": "twse",
        }]
        signal_rows = [{
            "stock_id": "3231",
            "trade_date": "2026-05-04",
            "version": "v20.4.5",
        }]
        deprecated_rows = ([{"stock_id": "3231"}], [{"stock_id": "3231"}], [{"stock_id": "3231"}], [{"stock_id": "3231"}])

        with patch("scripts.backfill_signals.get_supabase_client", return_value=client):
            upsert_rows(price_rows, signal_rows, deprecated_rows)

        table_names = [call[0] for call in client.calls if call[1] == "upsert"]
        self.assertEqual(table_names, ["daily_price", "daily_signal_snapshot"])
        self.assertNotIn("market_daily_bars", table_names)
        self.assertNotIn("strategy_feature_snapshots", table_names)
        self.assertNotIn("strategy_outcome_metrics", table_names)
        self.assertNotIn("strategy_classification_audit", table_names)


if __name__ == "__main__":
    unittest.main()
