import unittest

from core.signal_validator import validate_snapshots


class SignalValidatorTest(unittest.TestCase):
    def test_tradeable_with_blocking_reason_fails(self):
        errors = validate_snapshots([
            {
                "stock_id": "x",
                "trade_date": "2026-05-22",
                "action": "BUY",
                "pattern": "BREAKOUT_CONFIRM",
                "rr": 2,
                "heat_level": 0,
                "reasons": ["RR不足"],
                "is_tradeable": True,
                "is_best_candidate": False
            }
        ])
        self.assertTrue(errors)

    def test_best_candidate_must_be_tradeable(self):
        errors = validate_snapshots([
            {
                "stock_id": "x",
                "trade_date": "2026-05-22",
                "action": "WAIT",
                "pattern": "LOCK_LIMIT",
                "rr": 0,
                "heat_level": 3,
                "reasons": ["過熱 Lv.3"],
                "is_tradeable": False,
                "is_best_candidate": True
            }
        ])
        self.assertTrue(errors)

    def test_failed_breakout_requires_reason(self):
        errors = validate_snapshots([
            {
                "stock_id": "x",
                "trade_date": "2026-05-22",
                "action": "FAIL",
                "pattern": "FAILED_BREAKOUT",
                "rr": 0,
                "heat_level": 0,
                "reasons": [],
                "is_tradeable": False,
                "is_best_candidate": False
            }
        ])
        self.assertTrue(errors)

    def test_limit_lock_requires_blocking_reason(self):
        errors = validate_snapshots([
            {
                "stock_id": "x",
                "trade_date": "2026-05-22",
                "action": "WAIT",
                "pattern": "LOCK_LIMIT",
                "rr": 1.2,
                "heat_level": 1,
                "reasons": [],
                "is_tradeable": False,
                "is_best_candidate": False
            }
        ])
        self.assertTrue(errors)

    def test_expected_stock_ids_require_complete_daily_rows(self):
        errors = validate_snapshots(
            [
                {
                    "stock_id": "3231",
                    "trade_date": "2026-05-22",
                    "action": "WAIT",
                    "pattern": "BASE",
                    "rr": 1.2,
                    "heat_level": 0,
                    "reasons": ["市場弱"],
                    "is_tradeable": False,
                    "is_best_candidate": False
                }
            ],
            expected_stock_ids=["3231", "2356"]
        )
        self.assertTrue(errors)

    def test_expected_trade_dates_require_daily_rows(self):
        errors = validate_snapshots(
            [],
            expected_stock_ids=["3231"],
            expected_trade_dates=["2026-05-22"]
        )
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
