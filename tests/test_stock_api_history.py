import unittest
from datetime import date
from unittest.mock import patch

from services.stock_api import (
    clear_error,
    compact_error,
    get_last_error,
    get_twse,
    parse_twse_date,
    parse_twse_number,
    record_error
)


class StockApiHistoryTest(unittest.TestCase):
    def test_parse_twse_roc_date(self):
        self.assertEqual(parse_twse_date("115/05/22"), date(2026, 5, 22))

    def test_parse_twse_western_date(self):
        self.assertEqual(parse_twse_date("2026/05/22"), date(2026, 5, 22))

    def test_parse_twse_number(self):
        self.assertEqual(parse_twse_number("1,234,567"), 1234567.0)
        self.assertIsNone(parse_twse_number("--"))

    def test_quote_errors_are_recorded_per_stock(self):
        record_error("3231", "twse", "DNS failed")
        self.assertEqual(get_last_error("3231"), "twse: DNS failed")

        clear_error("3231")
        self.assertIsNone(get_last_error("3231"))

    def test_quote_errors_are_compact(self):
        self.assertEqual(
            compact_error("HTTPSConnectionPool failed: nodename nor servname provided"),
            "DNS failed"
        )

    def test_get_twse_stops_when_min_rows_are_met(self):
        calls = []

        class FakeResponse:
            def json(self):
                return {
                    "stat": "OK",
                    "data": [
                        [f"115/05/{day:02d}", "1,000", "0", "0", "0", "0", str(10 + day)]
                        for day in range(1, 24)
                    ]
                }

        def fake_get(url, **_kwargs):
            calls.append(url)
            return FakeResponse()

        with patch("services.stock_api.requests.get", side_effect=fake_get):
            result = get_twse("3231", months=2, min_rows=45, max_months=4)

        self.assertIsNotNone(result)
        self.assertEqual(len(calls), 2)

    def test_get_twse_adds_month_when_min_rows_are_missing(self):
        calls = []

        class FakeResponse:
            def json(self):
                return {
                    "stat": "OK",
                    "data": [
                        [f"115/05/{day:02d}", "1,000", "0", "0", "0", "0", str(10 + day)]
                        for day in range(1, 16)
                    ]
                }

        def fake_get(url, **_kwargs):
            calls.append(url)
            return FakeResponse()

        with patch("services.stock_api.requests.get", side_effect=fake_get):
            result = get_twse("3231", months=2, min_rows=45, max_months=4)

        self.assertIsNotNone(result)
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
