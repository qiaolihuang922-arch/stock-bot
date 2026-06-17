import unittest

from scripts.audit_db_data_quality import (
    build_quality_audit,
    constant_field_report,
    daily_price_quality,
    signal_snapshot_consistency,
    snapshot_coverage,
)


class AuditDbDataQualityTest(unittest.TestCase):
    def test_daily_price_quality_flags_invalid_ohlc(self):
        report = daily_price_quality([
            {
                "stock_id": "2337",
                "trade_date": "2026-06-16",
                "open": 100,
                "high": 99,
                "low": 98,
                "close": 100,
                "volume": 1000,
            }
        ])

        self.assertEqual(report["issues"][0]["type"], "daily_price_ohlc_range_invalid")

    def test_signal_snapshot_consistency_flags_close_mismatch(self):
        price_rows = []
        for index in range(20):
            price_rows.append(
                {
                    "stock_id": "2337",
                    "trade_date": f"2026-06-{index + 1:02d}",
                    "open": 100 + index,
                    "high": 101 + index,
                    "low": 99 + index,
                    "close": 100 + index,
                    "volume": 1000,
                }
            )
        signal_rows = [
            {
                "stock_id": "2337",
                "trade_date": "2026-06-20",
                "version": "v21.1",
                "close": 999,
                "volume_ratio": 1,
                "volume_ratio_10": 1,
                "volume_ratio_20": 1,
            }
        ]

        report = signal_snapshot_consistency(signal_rows, price_rows)

        close_issues = [
            item for item in report["issues"]
            if item["field"] == "close"
        ]
        self.assertEqual(close_issues[0]["expected_from_daily_price"], 119.0)

    def test_expected_constant_fields_are_not_review_items(self):
        rows = [
            {"version": "v21.1", "rr_formula": "(target-entry)/(entry-stop)"},
            {"version": "v21.1", "rr_formula": "(target-entry)/(entry-stop)"},
        ]

        report = constant_field_report("daily_signal_snapshot", rows)

        classifications = {item["column"]: item["classification"] for item in report}
        self.assertEqual(classifications["version"], "expected_constant")
        self.assertEqual(classifications["rr_formula"], "expected_constant")

    def test_build_quality_audit_counts_duplicate_business_keys(self):
        artifact = build_quality_audit({
            "daily_price": [
                {
                    "stock_id": "2337",
                    "trade_date": "2026-06-16",
                    "open": 100,
                    "high": 101,
                    "low": 99,
                    "close": 100,
                    "volume": 1000,
                },
                {
                    "stock_id": "2337",
                    "trade_date": "2026-06-16",
                    "open": 100,
                    "high": 101,
                    "low": 99,
                    "close": 100,
                    "volume": 1000,
                },
            ],
            "daily_signal_snapshot": [],
        })

        duplicate_issues = [
            item for item in artifact["fix_issues"]
            if item["type"] == "business_key_duplicate"
        ]
        self.assertEqual(duplicate_issues[0]["duplicate_extra_rows"], 1)

    def test_snapshot_coverage_separates_current_window_missing(self):
        price_rows = []
        for index, day in enumerate(["2024-06-10", "2024-06-17"]):
            price_rows.append(
                {
                    "stock_id": "2337",
                    "trade_date": day,
                    "open": 100 + index,
                    "high": 101 + index,
                    "low": 99 + index,
                    "close": 100 + index,
                    "volume": 1000,
                }
            )
        price_rows = price_rows * 20
        signal_rows = [
            {"stock_id": "2337", "trade_date": "2024-06-17", "version": "v21.1"}
        ]

        report = snapshot_coverage(signal_rows, price_rows, coverage_start_date="2024-06-17")

        self.assertGreater(report["missing_current_snapshot_rows"], 0)
        self.assertEqual(report["missing_current_window_snapshot_rows"], 0)


if __name__ == "__main__":
    unittest.main()
