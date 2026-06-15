import unittest

from scripts.audit_db_table_health import audit_table


class AuditDbTableHealthTest(unittest.TestCase):
    def test_duplicate_profiles_use_table_specific_keys(self):
        event_rows = [
            {"stock_code": "2337", "stock_name": "Macronix", "event_id": "a"},
            {"stock_code": "2337", "stock_name": "Macronix", "event_id": "b"},
        ]
        report = audit_table(event_rows, "position_events", 0.95)

        self.assertEqual(report["duplicate_profiles"], [])

        price_rows = [
            {"stock_id": "2337", "trade_date": "2026-06-15", "close": 159},
            {"stock_id": "2337", "trade_date": "2026-06-15", "close": 159},
        ]
        report = audit_table(price_rows, "daily_price", 0.95)

        self.assertEqual(report["duplicate_profiles"][0]["key"], ["stock_id", "trade_date"])
        self.assertEqual(report["duplicate_profiles"][0]["duplicate_extra_rows"], 1)

    def test_mostly_null_columns_are_reported_without_guessing_values(self):
        rows = [
            {"stock_id": "2337", "trade_date": "2026-06-14", "retest_reference_price": None},
            {"stock_id": "2337", "trade_date": "2026-06-15", "retest_reference_price": 175.5},
        ]
        report = audit_table(rows, "daily_signal_snapshot", 0.5)

        columns = {item["column"] for item in report["mostly_null_columns"]}
        self.assertIn("retest_reference_price", columns)


if __name__ == "__main__":
    unittest.main()
