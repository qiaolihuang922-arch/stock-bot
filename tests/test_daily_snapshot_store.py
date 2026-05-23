import unittest
from datetime import datetime

from services.analysis import strategy
from services.daily_snapshot_store import build_daily_snapshot_payloads


def sample_result():
    closes = [
        100, 101, 102, 103, 104,
        105, 106, 107, 108, 109,
        110, 111, 112, 113, 114,
        115, 116, 117, 118, 119
    ]
    volumes = [1000] * 19 + [1800]
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    return strategy(119, 1.0, ma5, ma20, closes, volumes), closes, volumes


class DailySnapshotStoreTest(unittest.TestCase):
    def test_skip_before_close(self):
        result, closes, volumes = sample_result()
        payloads = build_daily_snapshot_payloads(
            "v19.0",
            "盤後",
            {
                "測試": {
                    "stock_code": "9999",
                    "result": result,
                    "price": 119,
                    "price_source": "twse",
                    "volume_ratio": 1.8,
                    "volumes": volumes,
                    "closes": closes
                }
            },
            datetime(2026, 5, 22, 10, 0)
        )

        self.assertFalse(payloads["recorded"])
        self.assertEqual(payloads["reason"], "skip_phase")

    def test_build_after_close_payloads(self):
        result, closes, volumes = sample_result()
        payloads = build_daily_snapshot_payloads(
            "v19.0",
            "收盤",
            {
                "測試": {
                    "stock_code": "9999",
                    "result": result,
                    "price": 119,
                    "price_source": "twse",
                    "volume_ratio": 1.8,
                    "volumes": volumes,
                    "closes": closes
                }
            },
            datetime(2026, 5, 22, 13, 30)
        )

        self.assertTrue(payloads["recorded"])
        self.assertEqual(len(payloads["price_rows"]), 1)
        self.assertEqual(len(payloads["signal_rows"]), 1)
        self.assertEqual(payloads["price_rows"][0]["stock_id"], "9999")
        self.assertEqual(payloads["signal_rows"][0]["version"], "v19.0")


if __name__ == "__main__":
    unittest.main()
