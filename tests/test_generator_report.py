import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core import generator
from core.signal_snapshot import analyze_ohlcv_snapshot


VOL_ATTACK = [1000] * 19 + [1800]


class FakeTable:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def gte(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class FakeClient:
    def __init__(self, signal_rows, price_rows):
        self.signal_rows = signal_rows
        self.price_rows = price_rows

    def table(self, name):
        if name == "daily_signal_snapshot":
            return FakeTable(self.signal_rows)
        if name == "daily_price":
            return FakeTable(self.price_rows)
        return FakeTable([])


def render_payload(closes, holding=None, price=None, change=0):
    snap = analyze_ohlcv_snapshot("3035", "2026-05-22", closes, VOL_ATTACK)
    close = price if price is not None else closes[-1]
    return {
        "result": snap["raw_result"],
        "price": close,
        "change": change,
        "price_source": "realtime",
        "stock_code": "3035",
        "ma5": sum(closes[-5:]) / 5,
        "ma20": sum(closes[-20:]) / 20,
        "closes": closes,
        "volumes": VOL_ATTACK,
        "holding": holding,
    }


class GeneratorReportTest(unittest.TestCase):
    def test_limit_lock_conclusion_is_not_overridden_by_rr(self):
        result = {
            "decision": "BUY",
            "action": 1,
            "price_behavior": "LIMIT_LOCK",
            "trade_state": "EXTENDED",
            "heat_state": "HOT",
            "rr": 0.5,
            "market_grade": "A+",
        }

        self.assertEqual(generator.entry_conclusion(result), "漲停鎖價，不追高")

    def test_blocked_entry_does_not_get_validation_context(self):
        result = {
            "decision": "BUY",
            "action": 1,
            "price_behavior": "NORMAL",
            "trade_state": "LATE_ENTRY",
            "heat_state": "NORMAL",
            "rr": 0.5,
            "market_grade": "A+",
            "stock_code": "2421",
        }
        signal_rows = [
            {
                "stock_id": "2421",
                "trade_date": "2026-05-01",
                "version": "v19.1",
                "pattern": "BREAKOUT_CONFIRM",
                "market_state": "A+",
                "rr": 0.5,
                "heat_level": 0,
                "action": "BUY",
                "reasons": ["RR不足"],
                "is_tradeable": False,
                "is_best_candidate": False,
            }
        ]
        price_rows = [
            {"stock_id": "2421", "trade_date": "2026-05-01", "close": 100},
            {"stock_id": "2421", "trade_date": "2026-05-02", "close": 102},
            {"stock_id": "2421", "trade_date": "2026-05-03", "close": 103},
            {"stock_id": "2421", "trade_date": "2026-05-04", "close": 104},
        ]

        with patch.object(generator, "get_supabase_client", return_value=FakeClient(signal_rows, price_rows)):
            context = generator.load_backtest_context({
                "建準": {
                    "result": result,
                    "stock_code": "2421",
                    "holding": None,
                }
            })

        self.assertEqual(context, {})

    def test_holding_add_uses_basis_label(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )

        report = generator.render_stock("智原", payload)

        self.assertIn("├─ 加碼：成立", report)
        self.assertIn("├─ 依據：小幅轉強、RR達標、信心達標", report)
        self.assertNotIn("├─ 阻斷：條件成立", report)


if __name__ == "__main__":
    unittest.main()
