import unittest
from datetime import datetime

from core.watchlist import WATCHLIST_CODES
from services.analysis import strategy
from services.daily_snapshot_store import build_daily_snapshot_payloads
from services.signal_store import record_daily_signals


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


def sample_payload(stock_code, holding=None, with_ohlcv=False):
    result, closes, volumes = sample_result()
    payload = {
        "stock_code": stock_code,
        "result": result.copy(),
        "price": 119,
        "price_source": "twse",
        "volume_ratio": 1.8,
        "volumes": volumes,
        "closes": closes,
    }

    if holding:
        payload["holding"] = holding

    if with_ohlcv:
        payload["ohlcv"] = {
            "open": 118,
            "high": 120,
            "low": 117,
            "close": 119,
            "volume": 1800,
            "source": "twse"
        }

    return payload


def watchlist_results(codes=None, with_ohlcv=False):
    return {
        f"測試{stock_code}": sample_payload(stock_code, with_ohlcv=with_ohlcv)
        for stock_code in (codes or WATCHLIST_CODES)
    }


class DailySnapshotStoreTest(unittest.TestCase):
    def test_skip_before_close(self):
        result, closes, volumes = sample_result()
        payloads = build_daily_snapshot_payloads(
            "v19.1.3",
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
            datetime(2026, 5, 22, 10, 0),
            expected_stock_ids=["9999"]
        )

        self.assertFalse(payloads["recorded"])
        self.assertEqual(payloads["reason"], "skip_phase")

    def test_build_after_close_payloads(self):
        result, closes, volumes = sample_result()
        payloads = build_daily_snapshot_payloads(
            "v19.1.3",
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
            datetime(2026, 5, 22, 13, 30),
            expected_stock_ids=["9999"]
        )

        self.assertTrue(payloads["recorded"])
        self.assertEqual(len(payloads["price_rows"]), 0)
        self.assertEqual(len(payloads["signal_rows"]), 1)
        self.assertEqual(payloads["signal_rows"][0]["version"], "v19.1.3")

    def test_daily_price_requires_complete_ohlcv(self):
        result, closes, volumes = sample_result()
        payloads = build_daily_snapshot_payloads(
            "v19.1.3",
            "收盤",
            {
                "測試": {
                    "stock_code": "9999",
                    "result": result,
                    "price": 119,
                    "price_source": "twse",
                    "volume_ratio": 1.8,
                    "volumes": volumes,
                    "closes": closes,
                    "ohlcv": {
                        "open": 118,
                        "high": 120,
                        "low": 117,
                        "close": 119,
                        "volume": 1800,
                        "source": "twse"
                    }
                }
            },
            datetime(2026, 5, 22, 13, 30),
            expected_stock_ids=["9999"]
        )

        self.assertTrue(payloads["recorded"])
        self.assertEqual(len(payloads["price_rows"]), 1)
        self.assertEqual(payloads["price_rows"][0]["stock_id"], "9999")
        self.assertEqual(payloads["price_rows"][0]["open"], 118)
        self.assertEqual(payloads["price_rows"][0]["source"], "twse")

    def test_holding_snapshot_is_not_new_entry_tradeable(self):
        result, closes, volumes = sample_result()
        payloads = build_daily_snapshot_payloads(
            "v19.1.3",
            "收盤",
            {
                "持倉股": {
                    "stock_code": "9999",
                    "result": result,
                    "price": 119,
                    "price_source": "twse",
                    "volume_ratio": 1.8,
                    "volumes": volumes,
                    "closes": closes,
                    "holding": {
                        "shares": 100,
                        "avg_price": 110
                    }
                }
            },
            datetime(2026, 5, 22, 13, 30),
            expected_stock_ids=["9999"]
        )

        self.assertTrue(payloads["recorded"])
        self.assertFalse(payloads["signal_rows"][0]["is_tradeable"])
        self.assertFalse(payloads["signal_rows"][0]["is_best_candidate"])

    def test_complete_watchlist_allows_daily_snapshot_recording(self):
        payloads = build_daily_snapshot_payloads(
            "v19.3.1",
            "收盤",
            watchlist_results(with_ohlcv=True),
            datetime(2026, 5, 22, 13, 30)
        )

        self.assertTrue(payloads["recorded"])
        self.assertEqual(payloads["reason"], "ready")
        self.assertEqual(len(payloads["signal_rows"]), len(WATCHLIST_CODES))
        self.assertEqual(len(payloads["price_rows"]), len(WATCHLIST_CODES))

    def test_incomplete_watchlist_blocks_all_daily_rows(self):
        missing_code = WATCHLIST_CODES[-1]
        partial_codes = WATCHLIST_CODES[:-1]
        payloads = build_daily_snapshot_payloads(
            "v19.3.1",
            "收盤",
            watchlist_results(partial_codes, with_ohlcv=True),
            datetime(2026, 5, 22, 13, 30)
        )

        self.assertFalse(payloads["recorded"])
        self.assertEqual(payloads["reason"], "incomplete_watchlist")
        self.assertEqual(payloads["missing_stock_ids"], [missing_code])
        self.assertEqual(payloads["price_rows"], [])
        self.assertEqual(payloads["signal_rows"], [])

    def test_holding_stock_in_complete_watchlist_is_not_tradeable_or_best(self):
        results = watchlist_results()
        holding_code = WATCHLIST_CODES[0]
        results[f"測試{holding_code}"]["holding"] = {
            "shares": 100,
            "avg_price": 110
        }

        payloads = build_daily_snapshot_payloads(
            "v19.3.1",
            "收盤",
            results,
            datetime(2026, 5, 22, 13, 30)
        )

        self.assertTrue(payloads["recorded"])
        holding_rows = [
            row for row in payloads["signal_rows"]
            if row["stock_id"] == holding_code
        ]
        self.assertEqual(len(holding_rows), 1)
        self.assertFalse(holding_rows[0]["is_tradeable"])
        self.assertFalse(holding_rows[0]["is_best_candidate"])

    def test_incomplete_watchlist_blocks_signal_run_before_db_write(self):
        missing_code = WATCHLIST_CODES[-1]
        payloads = record_daily_signals(
            "v19.3.1",
            "收盤",
            "message",
            watchlist_results(WATCHLIST_CODES[:-1]),
            None,
            "⏳ 觀望",
            datetime(2026, 5, 22, 13, 30)
        )

        self.assertFalse(payloads["recorded"])
        self.assertEqual(payloads["reason"], "incomplete_watchlist")
        self.assertEqual(payloads["missing_stock_ids"], [missing_code])


if __name__ == "__main__":
    unittest.main()
