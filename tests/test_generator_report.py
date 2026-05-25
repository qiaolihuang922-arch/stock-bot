import unittest
from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime

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

        self.assertIn("【智原 3035】", report)
        self.assertIn("├─ 決策：加碼 10% 5股｜小幅轉強", report)
        self.assertIn("├─ 倉控：目標 55股｜分批加碼", report)
        self.assertIn("├─ 依據：小幅轉強、RR達標、信心達標", report)
        self.assertNotIn("├─ 阻斷：條件成立", report)

    def test_generate_reports_data_source_errors_when_all_quotes_fail(self):
        with patch.object(generator, "stocks", {"測試": "1234"}), \
             patch.object(generator, "get_twse", return_value=None), \
             patch.object(generator, "get_last_error", return_value="twse: DNS failed"):
            report = generator.generate()

        self.assertIn("⚠ 無有效數據：行情來源未返回可用日線", report)
        self.assertIn("測試(1234) twse: DNS failed", report)

    def test_hidden_rr_is_not_listed_as_advantage(self):
        result = {
            "decision": "NO_TRADE",
            "structure_phase": "WEAK_REBOUND",
            "price_behavior": "WEAK_REBOUND",
            "market_grade": "D",
            "structure_state": "NORMAL",
            "volume_price_state": "COILING",
            "volume_state": "WEAK",
            "rr": 2.5,
        }

        self.assertTrue(generator.should_hide_rr(result))
        self.assertNotIn("RR足夠", generator.entry_advantages(result))

    def test_backtest_context_uses_pattern_volume_and_position(self):
        result = {
            "decision": "BUY",
            "action": 1,
            "structure_phase": "BREAKOUT_CONFIRM",
            "price_behavior": "NORMAL",
            "trade_state": "LATE_ENTRY",
            "heat_state": "NORMAL",
            "rr": 0.5,
            "market_grade": "A+",
            "breakout_distance": -1,
        }
        signal_rows = []
        price_rows = []

        for day in range(1, 10):
            price_rows.append({
                "stock_id": "2421",
                "trade_date": f"2026-05-{day:02d}",
                "close": 100 + day,
            })

        for day in range(1, 7):
            signal_rows.append({
                "stock_id": "2421",
                "trade_date": f"2026-05-{day:02d}",
                "version": "v19.1",
                "pattern": "BREAKOUT_CONFIRM",
                "market_state": "A+",
                "structure_state": "STRONG",
                "position_state": "BREAKOUT",
                "volume_ratio": 2.5,
                "rr": 0.5,
                "heat_level": 0,
                "action": "BUY",
                "reasons": ["RR不足"],
                "is_tradeable": False,
                "is_best_candidate": False,
            })

        with patch.object(generator, "get_supabase_client", return_value=FakeClient(signal_rows, price_rows)):
            context = generator.load_backtest_context({
                "建準": {
                    "result": result,
                    "stock_code": "2421",
                    "volumes": [100] * 9 + [300],
                    "holding": None,
                }
            })

        self.assertIn("建準", context)
        self.assertEqual(context["建準"]["label"], "同型 突破確認/爆量/已突破")
        self.assertEqual(context["建準"]["scope"], "同型")
        self.assertEqual(context["建準"]["setup"], "突破確認/爆量/已突破")
        self.assertEqual(context["建準"]["sample"], 6)
        self.assertTrue(
            context["建準"]["action"] == "維持不買"
            or "不追價" in context["建準"]["action"]
            or "依今日阻斷" in context["建準"]["action"]
        )

    def test_setup_bucket_falls_back_to_price_position(self):
        closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122]
        result = {
            "structure_phase": "BREAKOUT_CONFIRM",
        }
        bucket = generator.setup_bucket_from_result(
            result,
            {
                "price": 122,
                "closes": closes,
                "volumes": [100] * 9 + [300],
            }
        )

        self.assertEqual(bucket, ("BREAKOUT_CONFIRM", "爆量", "BREAKOUT"))

    def test_market_forward_return_uses_same_day_universe(self):
        lookup = {
            "1111": [
                (generator.parse_trade_date("2026-05-01"), 100),
                (generator.parse_trade_date("2026-05-02"), 100),
                (generator.parse_trade_date("2026-05-03"), 100),
                (generator.parse_trade_date("2026-05-04"), 110),
            ],
            "2222": [
                (generator.parse_trade_date("2026-05-01"), 100),
                (generator.parse_trade_date("2026-05-02"), 100),
                (generator.parse_trade_date("2026-05-03"), 100),
                (generator.parse_trade_date("2026-05-04"), 90),
            ],
        }

        self.assertEqual(
            generator.market_forward_return(
                lookup,
                generator.parse_trade_date("2026-05-01"),
                3
            ),
            0
        )

    def test_holding_context_uses_holding_wording(self):
        result = {
            "decision": "WAIT",
            "action": 0,
            "structure_phase": "BREAKOUT_CONFIRM",
            "price_behavior": "NORMAL",
            "trade_state": "TRADEABLE",
            "heat_state": "NORMAL",
            "rr": 1.2,
            "market_grade": "A+",
            "breakout_distance": -1,
            "_holding_decision": {
                "level": "HOLD"
            }
        }
        signal_rows = []
        price_rows = []

        for stock_id in ["3035", "9999"]:
            for day in range(1, 10):
                price_rows.append({
                    "stock_id": stock_id,
                    "trade_date": f"2026-05-{day:02d}",
                    "close": 100 + day,
                })

        for day in range(1, 7):
            signal_rows.append({
                "stock_id": "3035",
                "trade_date": f"2026-05-{day:02d}",
                "version": "v19.1",
                "pattern": "BREAKOUT_CONFIRM",
                "market_state": "A+",
                "structure_state": "NORMAL",
                "position_state": "BREAKOUT",
                "volume_ratio": 1.4,
                "rr": 1.2,
                "heat_level": 0,
                "action": "WAIT",
                "reasons": ["突破確認"],
                "is_tradeable": False,
                "is_best_candidate": False,
            })

        with patch.object(generator, "get_supabase_client", return_value=FakeClient(signal_rows, price_rows)):
            context = generator.load_backtest_context({
                "智原": {
                    "result": result,
                    "stock_code": "3035",
                    "volumes": [100] * 9 + [150],
                    "holding": {
                        "shares": 50,
                        "avg_price": 100
                    },
                }
            })

        self.assertIn("智原", context)
        self.assertEqual(context["智原"]["label"], "持倉同型 突破確認/放量/已突破")
        self.assertTrue(
            "續抱" in context["智原"]["action"]
            or "持倉規則" in context["智原"]["action"]
        )

    def test_backtest_context_renders_data_and_explanation(self):
        text = generator.render_backtest_context({
            "version": "v19.1",
            "scope": "同型",
            "setup": "突破確認/爆量/已突破",
            "sample": 15,
            "win_rate": 60,
            "avg_return": 1.8,
            "metric": "3日相對股票池",
            "verdict": "歷史偏強，但今日阻斷仍有效",
            "action": "列觀察，不追價"
        })

        self.assertIn(
            "├─ 回測：未持倉｜突破確認/爆量/已突破｜樣本 15\n"
            "├─ 統計：3日勝率 60%｜相對 +1.8%｜偏強但阻斷有效",
            text
        )

    def test_backtest_context_renders_negative_relative_result(self):
        text = generator.render_backtest_context({
            "version": "v19.1",
            "scope": "持倉同型",
            "setup": "突破確認/放量/已突破",
            "sample": 35,
            "win_rate": 46,
            "avg_return": -0.6,
            "metric": "3日相對股票池",
            "verdict": "加碼樣本偏弱",
            "action": "依風控續抱，不加碼"
        })

        self.assertIn(
            "├─ 回測：持倉｜突破確認/放量/已突破｜樣本 35\n"
            "├─ 統計：3日勝率 46%｜相對 -0.6%｜加碼偏弱，不加碼",
            text
        )

    def test_execution_reply_markup_uses_compact_callback(self):
        markup = generator.execution_reply_markup({
            "英業達": {
                "stock_code": "2356",
                "price": 65.4,
                "holding": {
                    "shares": 550,
                    "avg_price": 52.15
                },
                "holding_decision": {
                    "level": "TAKE_PROFIT_25",
                    "action": "停利 25%",
                    "shares": 138
                },
                "result": {}
            }
        })

        self.assertEqual(
            markup["inline_keyboard"],
            [
                [{"text": "輸入買入：3231 300 149.5", "callback_data": "noop"}],
                [{"text": "輸入賣出：3231 500", "callback_data": "noop"}],
                [{"text": "輸入清倉：清倉 3231", "callback_data": "noop"}],
                [{"text": "輸入設定：設定 3231 440 140.92", "callback_data": "noop"}],
            ]
        )

    def test_telegram_messages_use_summary_cards_and_detail(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        watch_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        watch_payload["stock_code"] = "2421"
        watch_payload["result"]["rr"] = 0.5
        watch_payload["result"]["trade_state"] = "LATE_ENTRY"

        generator.render_stock("智原", holding_payload)
        generator.render_stock("建準", watch_payload)
        messages = generator.formatTelegramMessages(
            {
                "智原": holding_payload,
                "建準": watch_payload,
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
        )

        self.assertGreaterEqual(len(messages), 4)
        self.assertIn("📌 持倉：智原", messages[0])
        self.assertIn("觀察/不買：", messages[0])
        self.assertIn("【持倉標的】", messages[1])
        self.assertIn("倉位：50股", messages[1])
        self.assertIn("【觀察 / 不買標的】", messages[2])
        self.assertIn("回測：", messages[2])
        self.assertIn("【完整詳情備份】", messages[3])
        self.assertIn("FULL DETAIL", messages[3])


if __name__ == "__main__":
    unittest.main()
