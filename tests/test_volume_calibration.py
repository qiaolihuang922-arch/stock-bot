import unittest
from datetime import date, timedelta

from services.volume_calibration import build_volume_calibration, volume_bucket


def _price_rows(stock_id, closes):
    start = date(2026, 1, 1)
    rows = []
    for offset, close in enumerate(closes):
        day = start + timedelta(days=offset)
        rows.append({
            "stock_id": stock_id,
            "trade_date": day.isoformat(),
            "open": close,
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": 1000 + offset,
        })
    return rows


class VolumeCalibrationTest(unittest.TestCase):
    def test_volume_bucket_edges(self):
        self.assertEqual(volume_bucket(None), "missing")
        self.assertEqual(volume_bucket(0.69), "lt_0_7")
        self.assertEqual(volume_bucket(0.7), "0_7_0_9")
        self.assertEqual(volume_bucket(0.9), "0_9_1_1")
        self.assertEqual(volume_bucket(1.1), "1_1_1_4")
        self.assertEqual(volume_bucket(1.4), "gte_1_4")

    def test_build_calibration_uses_raw_signal_context(self):
        signal_rows = [{
            "stock_id": "3231",
            "trade_date": "2026-01-01",
            "version": "v21.0.1",
            "close": 100,
            "volume_ratio": 0.55,
            "volume_ratio_20": 1.2,
            "pattern": "NORMAL",
            "market_state": "D",
            "structure_state": "WEAK",
            "position_state": "FAR",
            "rr": 1.5,
            "score": 40,
            "heat_level": 1,
            "action": "WAIT",
            "reasons": ["量能不足"],
            "is_tradeable": False,
            "is_best_candidate": False,
        }]
        price_rows = _price_rows("3231", [100, 101, 102, 103])

        artifact = build_volume_calibration(
            signal_rows,
            price_rows,
            horizon_days=3,
            min_sample=1,
        )

        self.assertEqual(artifact["source"], "daily_signal_snapshot+daily_price")
        self.assertFalse(artifact["db_write"])
        self.assertFalse(artifact["schema_change"])
        self.assertEqual(artifact["volume_window"], "volume_ratio_20_fallback_volume_ratio")
        self.assertEqual(artifact["source_status"], "available")
        bucket = artifact["contexts"]["far_weak_market"]["1_1_1_4"]
        self.assertEqual(bucket["sample"], 1)
        self.assertTrue(bucket["decision_eligible"])
        self.assertEqual(bucket["source_status"], "available")
        self.assertEqual(bucket["median_return"], 3.0)


if __name__ == "__main__":
    unittest.main()
