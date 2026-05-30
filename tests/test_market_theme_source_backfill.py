import unittest

from scripts.backfill_market_theme_sources import (
    MARKET_INDEX,
    build_source_payloads,
    theme_member_rows,
)


class MarketThemeSourceBackfillTest(unittest.TestCase):
    def test_theme_member_rows_are_persistent_sources(self):
        rows = theme_member_rows("2026-05-30T00:00:00+00:00")

        self.assertTrue(rows)
        self.assertEqual({row["source_family"] for row in rows}, {"owner_approved_persistent"})
        self.assertIn("3231", {row["stock_code"] for row in rows})
        self.assertIn("memory", {row["sector_theme_key"] for row in rows})

    def test_build_source_payloads_from_daily_price_without_runtime_fallback(self):
        price_rows = [
            {"stock_id": "3231", "trade_date": "2026-05-28", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1000},
            {"stock_id": "3231", "trade_date": "2026-05-29", "open": 109, "high": 111, "low": 108, "close": 110, "volume": 2000},
            {"stock_id": "2356", "trade_date": "2026-05-28", "open": 50, "high": 51, "low": 49, "close": 50, "volume": 1000},
            {"stock_id": "2356", "trade_date": "2026-05-29", "open": 54, "high": 56, "low": 53, "close": 55, "volume": 2000},
            {"stock_id": "2376", "trade_date": "2026-05-28", "open": 300, "high": 301, "low": 299, "close": 300, "volume": 1000},
            {"stock_id": "2376", "trade_date": "2026-05-29", "open": 309, "high": 311, "low": 308, "close": 315, "volume": 2000},
            {"stock_id": "2301", "trade_date": "2026-05-28", "open": 200, "high": 201, "low": 199, "close": 200, "volume": 1000},
            {"stock_id": "2301", "trade_date": "2026-05-29", "open": 202, "high": 204, "low": 201, "close": 204, "volume": 2000},
        ]

        payloads = build_source_payloads(price_rows, "2026-05-29", "2026-05-29T13:30:00+00:00")

        self.assertEqual(payloads["status"], "ready")
        self.assertTrue(payloads["member_rows"])
        self.assertTrue(payloads["index_rows"])
        self.assertTrue(payloads["confirmed_rows"])
        self.assertFalse(any(row["index_scope"] == "market" for row in payloads["index_rows"]))
        ai_evidence = next(row for row in payloads["confirmed_rows"] if row["sector_theme_key"] == "ai_server")
        self.assertEqual(ai_evidence["market_index"], MARKET_INDEX)
        self.assertEqual(ai_evidence["source_family"], "production_db")
        self.assertEqual(ai_evidence["freshness"], "fresh")
        self.assertIn(ai_evidence["support_level"], {"confirmed", "supporting"})
        self.assertEqual(
            ai_evidence["lineage"]["source_tables"],
            ["daily_price", "sector_theme_members", "market_theme_index_daily_bars"],
        )

    def test_build_source_payloads_blocks_without_current_prices(self):
        payloads = build_source_payloads(
            [{"stock_id": "3231", "trade_date": "2026-05-28", "close": 100}],
            "2026-05-29",
            "2026-05-29T13:30:00+00:00",
        )

        self.assertEqual(payloads["status"], "blocked")
        self.assertEqual(payloads["index_rows"], [])
        self.assertEqual(payloads["confirmed_rows"], [])


if __name__ == "__main__":
    unittest.main()
