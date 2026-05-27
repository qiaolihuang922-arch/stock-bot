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
             patch.object(generator, "get_yahoo_history", return_value=None), \
             patch.object(generator, "get_last_error", return_value="twse: DNS failed"):
            report = generator.generate()

        self.assertIn("⚠ 無有效數據：行情來源未返回可用日線", report)
        self.assertIn("測試(1234) twse: DNS failed", report)

    def test_load_stock_signal_uses_yahoo_daily_fallback_when_twse_fails(self):
        closes = [
            100, 101, 102, 103, 104,
            105, 106, 107, 108, 109,
            110, 111, 112, 113, 114,
            115, 116, 117, 118, 119
        ]
        volumes = VOL_ATTACK
        daily = (
            119,
            1.4,
            sum(closes[-5:]) / 5,
            sum(closes[-20:]) / 20,
            closes,
            volumes
        )

        with patch.object(generator, "get_twse", return_value=None), \
             patch.object(generator, "get_yahoo_history", return_value=daily), \
             patch.object(generator, "get_last_error", return_value="twse: timeout"), \
             patch.object(generator, "get_realtime_price", return_value=None), \
             patch.object(generator, "get_yahoo", return_value=None), \
             patch.object(generator, "get_last_ohlcv", return_value={"source": "yahoo"}):
            name, data, decision, error = generator.load_stock_signal("測試", "1234")

        self.assertEqual(name, "測試")
        self.assertIsNone(error)
        self.assertIsNotNone(data)
        self.assertEqual(data["daily_source"], "yahoo")
        self.assertEqual(data["price_source"], "yahoo")
        self.assertIsNotNone(decision)

    def test_load_stock_signal_uses_minimal_yahoo_daily_without_twse_when_sufficient(self):
        closes = [
            100, 101, 102, 103, 104,
            105, 106, 107, 108, 109,
            110, 111, 112, 113, 114,
            115, 116, 117, 118, 119
        ]
        daily = (
            119,
            1.4,
            sum(closes[-5:]) / 5,
            sum(closes[-20:]) / 20,
            closes,
            VOL_ATTACK
        )

        with patch.object(generator, "get_yahoo_history", return_value=daily) as yahoo_history, \
             patch.object(generator, "get_twse") as twse, \
             patch.object(generator, "get_realtime_price", return_value=(120, 1.7)), \
             patch.object(generator, "get_yahoo") as yahoo_quote, \
             patch.object(generator, "get_last_ohlcv", return_value={"source": "yahoo"}):
            name, data, decision, error = generator.load_stock_signal("測試", "1234")

        self.assertEqual(name, "測試")
        self.assertIsNone(error)
        self.assertIsNotNone(data)
        self.assertEqual(data["daily_source"], "yahoo")
        self.assertEqual(data["price_source"], "realtime")
        self.assertIsNotNone(decision)
        yahoo_history.assert_called_once_with("1234", months=1, min_rows=generator.REPORT_DAILY_MIN_ROWS)
        twse.assert_not_called()
        yahoo_quote.assert_not_called()

    def test_load_report_daily_kline_falls_back_to_limited_twse_window(self):
        closes = [
            100, 101, 102, 103, 104,
            105, 106, 107, 108, 109,
            110, 111, 112, 113, 114,
            115, 116, 117, 118, 119
        ]
        daily = (
            119,
            1.4,
            sum(closes[-5:]) / 5,
            sum(closes[-20:]) / 20,
            closes,
            VOL_ATTACK
        )

        with patch.object(generator, "get_yahoo_history", return_value=None) as yahoo_history, \
             patch.object(generator, "get_twse", return_value=daily) as twse, \
             patch.object(generator, "get_last_error", return_value="yahoo_daily: timeout"):
            result, source, error = generator.load_report_daily_kline("1234")

        self.assertEqual(result, daily)
        self.assertEqual(source, "twse")
        self.assertIsNone(error)
        yahoo_history.assert_called_once_with("1234", months=1, min_rows=generator.REPORT_DAILY_MIN_ROWS)
        twse.assert_called_once_with(
            "1234",
            months=1,
            min_rows=generator.REPORT_DAILY_MIN_ROWS,
            max_months=2
        )

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

        self.assertEqual(len(messages), 3)
        self.assertIn("【持倉標的】", messages[0])
        self.assertIn("倉位：50股", messages[0])
        self.assertIn("【未持倉標的】", messages[1])
        self.assertIn("【建準 2421】👀 等RR修復｜RR不足", messages[1])
        self.assertIn("買點：不買｜RR不足", messages[1])
        self.assertIn("明日觸發：RR修復至達標，不追高", messages[1])
        self.assertIn("回測：", messages[1])
        self.assertIn("📊 市場：", messages[-1])
        self.assertIn("📌 持倉：智原", messages[-1])
        self.assertIn("🧭 今日結論：", messages[-1])
        self.assertIn("✅ 明日執行清單（持倉優先）", messages[-1])
        self.assertIn("1. 智原｜+0.85%｜加碼10｜加碼後守警戒價", messages[-1])
        self.assertIn("未持倉 1 檔只等觸發，不列入明日執行", messages[-1])
        self.assertNotIn("建準｜等RR修復｜不追價，等RR達標", messages[-1])
        self.assertIn("未持倉漏斗（非執行）：", messages[-1])
        self.assertIn("未持倉總數 1 檔", messages[-1])
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 0", messages[-1])
        self.assertIn("其中僅追蹤 1 檔拆分：等冷卻 0、等回測 0、等RR修復 1、等量能 0", messages[-1])
        self.assertIn("可準備 0（不可買）", messages[-1])
        self.assertIn("等RR修復 1", messages[-1])
        self.assertIn("📎 詳情索引：持倉 1｜執行 1｜未持倉追蹤 1｜淘汰 0", messages[-1])
        self.assertNotIn("完整詳情備份", "\n".join(messages))

    def test_position_cards_follow_summary_order_and_decision_wording(self):
        core_payload = render_payload(
            [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 65],
            {"shares": 550, "avg_price": 52.15},
            price=65.4,
            change=9.9,
        )
        core_payload["stock_code"] = "2356"
        core_payload["result"]["price_behavior"] = "LIMIT_LOCK"
        core_payload["result"]["heat_state"] = "EXTREME"
        core_payload["result"]["extended_level"] = 3
        core_payload["holding_decision"] = {
            "action": "續抱核心倉",
            "level": "HOLD_CORE",
            "warning_price": 62.13,
            "hard_stop_price": 58.86,
        }

        bottom_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 200, "avg_price": 136.8},
            price=149,
            change=3.1,
        )
        bottom_payload["stock_code"] = "3231"
        bottom_payload["position_events"] = {"event_count": 1, "sold_shares": 430, "sell_pct": 98}
        bottom_payload["holding_decision"] = {
            "action": "續抱",
            "level": "HOLD",
            "warning_price": 141.55,
            "hard_stop_price": 139.54,
        }

        buy_payload = render_payload(
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 336],
            {"shares": 30, "avg_price": 334.5},
            price=336.5,
            change=4.3,
        )
        buy_payload["stock_code"] = "2376"
        buy_payload["position_events"] = {"event_count": 1, "bought_shares": 30}

        weak_payload = render_payload(
            [300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 296],
            {"shares": 20, "avg_price": 298},
            price=296,
            change=-4.6,
        )
        weak_payload["stock_code"] = "2408"
        weak_payload["result"]["market_grade"] = "D"
        weak_payload["holding_decision"] = {
            "action": "續抱觀察",
            "level": "HOLD_WATCH",
            "note": "轉弱觀察，不加碼",
            "warning_price": 283.1,
            "hard_stop_price": 274.16,
        }

        messages = generator.formatTelegramMessages(
            {
                "技嘉": buy_payload,
                "南亞科": weak_payload,
                "緯創": bottom_payload,
                "英業達": core_payload,
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
        )

        position_msg = messages[0]
        self.assertLess(position_msg.index("【技嘉 2376】"), position_msg.index("【英業達 2356】"))
        self.assertLess(position_msg.index("【英業達 2356】"), position_msg.index("【緯創 3231】"))
        self.assertLess(position_msg.index("【技嘉 2376】"), position_msg.index("【南亞科 2408】"))
        self.assertIn("【技嘉 2376】📌 新倉風控觀察", position_msg)
        self.assertIn("【英業達 2356】📌 核心風控觀察", position_msg)
        self.assertIn("【緯創 3231】📌 減碼後觀察", position_msg)
        self.assertIn("【南亞科 2408】📌 續抱觀察", position_msg)
        self.assertIn("決策：新倉風控觀察，暫不加碼", position_msg)
        self.assertIn("決策：核心風控觀察，暫不加碼", position_msg)
        self.assertIn("決策：減碼後觀察，暫不加碼", position_msg)
        self.assertIn("條件：修復才恢復優先級，未修復續降級", position_msg)
        self.assertIn("決策：續抱觀察，暫不加碼", position_msg)

    def test_summary_with_holding_and_buy_has_no_zero_tracking_noise(self):
        holding_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 50, "avg_price": 118},
            price=119,
            change=1.4,
        )
        buy_payload = {
            "stock_code": "2421",
            "price": 120,
            "change": 1.2,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "action_type": "BUY",
                "rr": 2.0,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "breakout_distance": 0.5,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
        }

        messages = generator.formatTelegramMessages(
            {
                "智原": holding_payload,
                "建準": buy_payload,
            },
            "FULL DETAIL",
            "建準",
            9.2,
            "🟢 市場偏強",
            datetime(2026, 5, 26),
        )

        self.assertIn("明日執行 2 項，持倉 1、可買 1；未持倉無追蹤", messages[-1])
        self.assertIn("1. 智原｜+0.85%｜加碼10｜加碼後守警戒價", messages[-1])
        self.assertIn("2. 建準｜可買｜分批，不追價", messages[-1])
        self.assertIn("未持倉總數 1 檔", messages[-1])
        self.assertIn("可買 1｜可準備 0（不可買）｜僅追蹤 0｜淘汰 0", messages[-1])
        self.assertIn("其中僅追蹤 0 檔拆分：等冷卻 0、等回測 0、等RR修復 0、等量能 0", messages[-1])
        self.assertIn("📎 詳情索引：持倉 1｜執行 2｜未持倉追蹤 0｜淘汰 0", messages[-1])
        self.assertNotIn("未持倉 0 檔僅追蹤", messages[-1])
        self.assertNotIn("其餘 0 檔僅追蹤", messages[-1])

    def test_unheld_funnel_prepare_count_has_separate_tracking_parent(self):
        states = {
            "準備股": "可準備",
            "冷卻一": "等冷卻",
            "冷卻二": "等冷卻",
            "RR股": "等RR修復",
        }

        with patch.object(generator, "unheld_funnel_state", side_effect=lambda name, _data: states[name]):
            text = generator.format_unheld_funnel([(name, {}) for name in states])

        self.assertIn("未持倉總數 4 檔", text)
        self.assertIn("可買 0｜可準備 1（不可買）｜僅追蹤 3｜淘汰 0", text)
        self.assertIn("其中僅追蹤 3 檔拆分：等冷卻 2、等回測 0、等RR修復 1、等量能 0", text)
        self.assertIn("非執行追蹤合計 4 檔（可準備 + 僅追蹤）", text)
        self.assertNotIn("非執行追蹤 4 檔，僅追蹤不可買", text)
        self.assertNotIn("其中：等冷卻 2、等回測 0、等RR修復 1、等量能 0", text)

    def test_summary_includes_strategy_evidence_without_changing_actions(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        payload["stock_code"] = "2421"
        payload["result"]["decision"] = "BUY"
        payload["result"]["action"] = 0.1

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            9.2,
            "🟢 市場偏強",
            datetime(2026, 5, 26),
            strategy_evidence_summary="📊 策略證據 v20.0\nRR不足｜樣本 3｜樣本不足，不判讀",
        )

        self.assertIn("📊 策略證據 v20.0", messages[-1])
        self.assertIn("RR不足｜樣本 3｜樣本不足，不判讀", messages[-1])
        self.assertEqual(payload["result"]["decision"], "BUY")
        self.assertEqual(payload["result"]["action"], 0.1)

    def test_unheld_cards_follow_summary_group_order(self):
        limit_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 125],
            None,
            price=125,
            change=9.6,
        )
        limit_payload["stock_code"] = "2303"
        limit_payload["result"]["price_behavior"] = "LIMIT_LOCK"

        wait_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        wait_payload["stock_code"] = "2421"
        wait_payload["result"]["rr"] = 0.5

        hot_payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 123],
            None,
            price=123,
            change=4.2,
        )
        hot_payload["stock_code"] = "2301"
        hot_payload["result"]["heat_state"] = "HOT"
        hot_payload["result"]["trade_state"] = "EXTENDED"
        hot_payload["result"]["rr"] = 0.78

        weak_payload = render_payload(
            [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81],
            None,
            price=81,
            change=-2.0,
        )
        weak_payload["stock_code"] = "2337"
        weak_payload["result"]["market_grade"] = "D"

        messages = generator.formatTelegramMessages(
            {
                "旺宏": weak_payload,
                "建準": wait_payload,
                "光寶科": hot_payload,
                "聯電": limit_payload,
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
        )

        summary_msg = messages[-1]
        unheld_msg = messages[1]
        self.assertIn("未持倉漏斗（非執行）：", summary_msg)
        self.assertIn("未持倉總數 4 檔", summary_msg)
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 3｜淘汰 1", summary_msg)
        self.assertIn("其中僅追蹤 3 檔拆分：等冷卻 1、等回測 1、等RR修復 1、等量能 0", summary_msg)
        self.assertIn("非執行追蹤合計 3 檔（可準備 + 僅追蹤）", summary_msg)
        self.assertIn("未持倉 3 檔僅追蹤，等觸發，不列入明日執行", summary_msg)
        self.assertIn("淘汰 1 檔｜主因：市場弱｜詳情見未持倉卡", summary_msg)
        self.assertLess(unheld_msg.index("【聯電 2303】"), unheld_msg.index("【光寶科 2301】"))
        self.assertLess(unheld_msg.index("【光寶科 2301】"), unheld_msg.index("【建準 2421】"))
        self.assertLess(unheld_msg.index("【建準 2421】"), unheld_msg.index("【旺宏 2337】"))
        self.assertIn("【聯電 2303】⏳ 等回測", unheld_msg)
        self.assertIn("【光寶科 2301】⏳ 等冷卻", unheld_msg)
        self.assertIn("【建準 2421】👀 等RR修復", unheld_msg)
        self.assertIn("【旺宏 2337】⛔ 淘汰", unheld_msg)

    def test_unheld_price_line_keeps_closing_parenthesis(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 128.5],
            None,
            price=128.5,
            change=2.8,
        )
        payload["stock_code"] = "2344"

        card = generator.formatTelegramUnheldCard("華邦電", payload)

        self.assertIn("價格：128.5（+2.80%）", card)
        self.assertNotIn("價格：128.5（+2.80%\n", card)

    def test_daily_write_warning_is_in_default_summary_message(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        payload["stock_code"] = "2344"
        warning = generator.daily_write_warning_text(
            {"recorded": False, "missing_stock_ids": ["2421"]},
            {"recorded": False, "missing_stock_ids": ["3035"]}
        )

        messages = generator.formatTelegramMessages(
            {"華邦電": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
            daily_write_warning=warning,
        )

        self.assertEqual(len(messages), 3)
        self.assertIn("每日快照未寫入", messages[-1])
        self.assertIn("缺少 3035, 2421", messages[-1])
        self.assertNotIn("每日快照未寫入", messages[0])
        self.assertNotIn("每日快照未寫入", messages[1])

    def test_v19_3_2_intraday_summary_classifies_0526_cases(self):
        def payload(code, price, change, result, holding=None, decision=None):
            return {
                "stock_code": code,
                "price": price,
                "change": change,
                "price_source": "realtime",
                "daily_source": "yahoo",
                "result": {
                    "decision": "WAIT",
                    "action": 0,
                    "rr": 0,
                    "heat_state": "NORMAL",
                    "trade_state": "WAIT",
                    "structure_phase": "BASE",
                    "price_behavior": "NORMAL",
                    "market_grade": "B",
                    "volume_state": "NORMAL",
                    "volume_price_state": "NORMAL",
                    "structure_state": "NORMAL",
                    "entry_quality": "D",
                    "confidence_score": 49,
                    "breakout_distance": 0,
                    **result,
                },
                "holding": holding,
                "holding_decision": decision,
                "structure_score": 3,
                "volume_ratio": 1,
            }

        results = {
            "英業達": payload("2356", 62.25, -4.82, {"heat_state": "HOT", "trade_state": "EXTENDED"}, {"shares": 550, "avg_price": 52.15}, {"action": "核心續抱", "level": "HOLD_CORE", "note": "高浮盈回落，暫不加碼", "warning_price": 59.14, "hard_stop_price": 54.76}),
            "緯創": payload("3231", 146.75, -1.51, {"structure_phase": "SHAKEOUT", "volume_state": "WEAK"}, {"shares": 200, "avg_price": 136.8}, {"action": "洗盤續抱", "level": "SHAKEOUT", "note": "縮量回測，未見出貨", "warning_price": 139.41, "hard_stop_price": 125.86}),
            "南亞科": payload("2408", 308.75, 4.31, {"structure_phase": "WEAK", "volume_state": "WEAK", "breakout_distance": 11}, {"shares": 30, "avg_price": 298}, {"action": "續抱觀察", "level": "HOLD_WATCH", "note": "轉弱觀察，不加碼", "warning_price": 293.31, "hard_stop_price": 274.16}),
            "技嘉": payload("2376", 336.25, -0.07, {"structure_phase": "SHAKEOUT", "volume_state": "WEAK"}, {"shares": 30, "avg_price": 334.5}, {"action": "洗盤續抱", "level": "SHAKEOUT", "note": "縮量回測，未見出貨", "warning_price": 317.77, "hard_stop_price": 307.74}),
            "智原": payload("3035", 210.25, -3.78, {"structure_phase": "SHAKEOUT", "volume_state": "WEAK"}, {"shares": 40, "avg_price": 211.5}, {"action": "洗盤警戒", "level": "SHAKEOUT_WARN", "note": "小虧，暫不加碼", "warning_price": 200.92, "hard_stop_price": 194.58}),
            "華邦電": payload("2344", 141, 9.73, {"price_behavior": "LIMIT_LOCK", "structure_phase": "LOCK_LIMIT", "heat_state": "EXTREME", "trade_state": "AVOID", "rr": 0.23}),
            "聯電": payload("2303", 130.75, 4.6, {"heat_state": "EXTREME", "trade_state": "AVOID", "rr": 0}),
            "群創": payload("3481", 46.225, -5.86, {"heat_state": "EXTREME", "trade_state": "AVOID", "rr": 0}),
            "光寶科": payload("2301", 237.25, 4.29, {"heat_state": "HOT", "trade_state": "EXTENDED", "rr": 0.78}),
            "建準": payload("2421", 163.25, 0.46, {"trade_state": "LATE_ENTRY", "rr": 0.12, "volume_state": "WEAK", "market_grade": "A"}),
            "仁寶": payload("2324", 33.325, -3.82, {"trade_state": "LATE_ENTRY", "rr": 0.26, "market_grade": "A"}),
            "旺宏": payload("2337", 159.25, 4.43, {"structure_phase": "WEAK_REBOUND", "price_behavior": "WEAK_REBOUND", "market_grade": "D", "volume_state": "WEAK", "rr": 2.44, "breakout_distance": 8.55}),
        }

        with patch.object(generator, "get_market_phase", return_value="盤中"):
            messages = generator.formatTelegramMessages(
                results,
                "FULL DETAIL",
                None,
                None,
                "🚨 過熱控倉，先處理持倉",
                datetime(2026, 5, 26),
            )

        self.assertIn("v20.0.9", messages[-1])
        self.assertIn("📡 資料：即時價 realtime｜日線 yahoo", messages[-1])
        self.assertIn("🧭 今日結論：R3 進攻偏熱；持倉優先處理；未持倉 6 檔僅追蹤，不新增", messages[-1])
        self.assertIn("🧭 原因：強勢股多過熱，RR不足，不追高", messages[-1])
        self.assertIn("✅ 明日執行清單（持倉優先）", messages[-1])
        self.assertIn("1. 英業達｜+19.37%｜核心風控觀察｜守警戒價", messages[-1])
        self.assertIn("2. 智原｜-0.59%｜洗盤警戒｜跌破警戒升級風控", messages[-1])
        self.assertIn("未持倉 6 檔只等觸發，不列入明日執行", messages[-1])
        self.assertIn("未持倉漏斗（非執行）：", messages[-1])
        self.assertIn("未持倉總數 7 檔", messages[-1])
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 6｜淘汰 1", messages[-1])
        self.assertIn("其中僅追蹤 6 檔拆分：等冷卻 3、等回測 1、等RR修復 2、等量能 0", messages[-1])
        self.assertIn("非執行追蹤合計 6 檔（可準備 + 僅追蹤）", messages[-1])
        self.assertIn("📎 詳情索引：持倉 5｜執行 5｜未持倉追蹤 6｜淘汰 1", messages[-1])
        self.assertIn("淘汰 1 檔｜主因：弱反彈待確認｜詳情見未持倉卡", messages[-1])
        self.assertIn("【光寶科 2301】⏳ 等冷卻", messages[1])
        self.assertIn("【建準 2421】👀 等RR修復｜RR不足", messages[1])
        self.assertIn("【旺宏 2337】⛔ 淘汰｜弱反彈待確認", messages[1])
        self.assertIn("RR -（持倉不看新倉RR）", messages[0])
        self.assertIn("RR -（過熱）", messages[1])
        self.assertIn("RR -（弱勢）", messages[1])

    def test_v19_3_4_backtest_line_explains_confidence_and_verdict(self):
        self.assertEqual(
            generator.compact_backtest_line({
                "sample": 35,
                "win_rate": 46,
                "avg_return": -0.6,
            }),
            "回測：樣本35｜參考度高｜3日勝率46%｜相對-0.6%｜偏弱",
        )
        self.assertEqual(
            generator.compact_backtest_line({
                "sample": 8,
                "win_rate": 50,
                "avg_return": 0.3,
            }),
            "回測：樣本8｜參考度低｜3日勝率50%｜相對+0.3%｜無明顯優勢",
        )
        self.assertEqual(
            generator.compact_backtest_line({
                "sample": 15,
                "win_rate": 60,
                "avg_return": 1.8,
            }),
            "回測：樣本15｜參考度中｜3日勝率60%｜相對+1.8%｜略優",
        )
        self.assertEqual(generator.compact_backtest_line(None), "回測：-")

    def test_v19_3_4_new_position_loss_displays_risk_watch_and_next_step(self):
        payload = {
            "stock_code": "2376",
            "price": 99,
            "change": -1.0,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "WAIT",
                "action": 0,
                "rr": 1.2,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "BASE",
                "price_behavior": "NORMAL",
                "market_grade": "B",
                "volume_state": "NORMAL",
                "volume_price_state": "NORMAL",
                "structure_state": "NORMAL",
                "entry_quality": "D",
                "confidence_score": 49,
                "breakout_distance": 0,
            },
            "holding": {"shares": 30, "avg_price": 100},
            "holding_decision": {
                "action": "續抱",
                "level": "HOLD_WATCH",
                "note": "不加碼",
                "warning_price": 95,
                "hard_stop_price": 90,
            },
            "position_events": {"event_count": 1, "bought_shares": 30},
            "structure_score": 3,
            "volume_ratio": 1.0,
        }

        card = generator.formatTelegramPositionCard("技嘉", payload)

        self.assertIn("【技嘉 2376】📌 新倉風控觀察｜-1.00%", card)
        self.assertIn("決策：新倉風控觀察，暫不加碼", card)
        self.assertIn("條件：守警戒價，跌破停損或轉弱優先風控", card)
        self.assertIn("下一步：隔日未修復，降低優先級", card)

    def test_light_loss_shakeout_holding_displays_warning_even_when_decision_is_watch(self):
        payload = {
            "stock_code": "3035",
            "price": 209.75,
            "change": -0.8,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "WAIT",
                "action": 0,
                "rr": 1.2,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "SHAKEOUT",
                "price_behavior": "NORMAL",
                "market_grade": "B",
                "volume_state": "WEAK",
                "volume_price_state": "COILING",
                "structure_state": "NORMAL",
                "entry_quality": "D",
                "confidence_score": 49,
                "breakout_distance": 0,
            },
            "holding": {"shares": 40, "avg_price": 211.5},
            "holding_decision": {
                "action": "續抱",
                "level": "HOLD_WATCH",
                "note": "不加碼",
                "warning_price": 200.92,
                "hard_stop_price": 194.58,
            },
            "structure_score": 3,
            "volume_ratio": 0.7,
        }

        card = generator.formatTelegramPositionCard("智原", payload)

        self.assertIn("【智原 3035】📌 洗盤警戒｜-0.83%", card)
        self.assertIn("決策：洗盤警戒，暫不加碼", card)
        self.assertIn("條件：若跌破停損或轉弱，優先風控", card)

    def test_rr_zero_display_marks_insufficient_when_not_hidden(self):
        self.assertEqual(
            generator.rr_display_text({
                "rr": 0,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "market_grade": "B",
                "structure_phase": "BASE",
                "volume_state": "NORMAL",
                "breakout_distance": 0,
            }),
            "0.00（不足）"
        )

    def test_v19_3_3_valid_buy_is_summary_buy_group_not_watch_group(self):
        payload = {
            "stock_code": "2421",
            "price": 120,
            "change": 1.2,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "action_type": "BUY",
                "rr": 2.0,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "breakout_distance": 0.5,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
        }

        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            "建準",
            9.2,
            "🟢 市場偏強",
            datetime(2026, 5, 26),
        )

        self.assertIn("1. 建準｜可買｜分批，不追價", messages[-1])
        self.assertIn("未持倉總數 1 檔", messages[-1])
        self.assertIn("可買 1｜可準備 0（不可買）｜僅追蹤 0｜淘汰 0", messages[-1])
        self.assertIn("其中僅追蹤 0 檔拆分：等冷卻 0、等回測 0、等RR修復 0、等量能 0", messages[-1])
        self.assertNotIn("建準｜等", messages[-1])
        self.assertIn("【建準 2421】🟢 可買｜10%倉｜買點成立", messages[1])
        self.assertIn("買點：可買｜建議 10%倉｜現在可分批", messages[1])

    def test_v19_4_tracking_states_do_not_override_valid_buy_or_weak_reject(self):
        buy_payload = {
            "stock_code": "2421",
            "price": 120,
            "change": 1.2,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "BUY",
                "action": 0.1,
                "action_type": "BUY",
                "rr": 2.0,
                "heat_state": "NORMAL",
                "trade_state": "WAIT",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "A",
                "volume_state": "STRONG",
                "volume_price_state": "EXPANSION",
                "structure_state": "STRONG",
                "entry_quality": "A",
                "confidence_score": 86,
                "breakout_distance": 0.5,
            },
            "holding": None,
            "structure_score": 5,
            "volume_ratio": 1.4,
        }
        weak_payload = dict(buy_payload)
        weak_payload["stock_code"] = "2337"
        weak_payload["result"] = {
            **buy_payload["result"],
            "decision": "WAIT",
            "action": 0,
            "rr": 2.0,
            "market_grade": "D",
            "structure_phase": "WEAK_REBOUND",
            "price_behavior": "WEAK_REBOUND",
        }

        messages = generator.formatTelegramMessages(
            {"建準": buy_payload, "旺宏": weak_payload},
            "FULL DETAIL",
            "建準",
            9.2,
            "🟢 市場偏強",
            datetime(2026, 5, 26),
        )

        self.assertIn("1. 建準｜可買｜分批，不追價", messages[-1])
        self.assertIn("未持倉總數 2 檔", messages[-1])
        self.assertIn("可買 1｜可準備 0（不可買）｜僅追蹤 0｜淘汰 1", messages[-1])
        self.assertIn("其中僅追蹤 0 檔拆分：等冷卻 0、等回測 0、等RR修復 0、等量能 0", messages[-1])
        self.assertIn("淘汰 1 檔｜主因：弱反彈待確認｜詳情見未持倉卡", messages[-1])
        self.assertNotIn("建準｜等", messages[-1])
        self.assertNotIn("旺宏｜等", messages[-1])
        self.assertIn("【建準 2421】🟢 可買｜10%倉｜買點成立", messages[1])

    def test_v19_4_volume_blocked_non_weak_stock_enters_wait_volume(self):
        payload = {
            "stock_code": "2376",
            "price": 330,
            "change": 0.8,
            "price_source": "realtime",
            "daily_source": "yahoo",
            "result": {
                "decision": "WAIT",
                "action": 0,
                "rr": 1.6,
                "heat_state": "NORMAL",
                "trade_state": "NO_VOLUME",
                "structure_phase": "BREAKOUT_CONFIRM",
                "price_behavior": "NORMAL",
                "market_grade": "B",
                "volume_state": "WEAK",
                "volume_price_state": "COILING",
                "structure_state": "NORMAL",
                "entry_quality": "B",
                "confidence_score": 70,
                "breakout_distance": 1.2,
            },
            "holding": None,
            "structure_score": 4,
            "volume_ratio": 0.6,
        }

        messages = generator.formatTelegramMessages(
            {"技嘉": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 26),
        )

        self.assertIn("未持倉總數 1 檔", messages[-1])
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 0", messages[-1])
        self.assertIn("其中僅追蹤 1 檔拆分：等冷卻 0、等回測 0、等RR修復 0、等量能 1", messages[-1])
        self.assertIn("未持倉 1 檔僅追蹤，等觸發，不列入明日執行", messages[-1])
        self.assertNotIn("1. 技嘉｜等量能｜不買，等量能回升", messages[-1])
        self.assertIn("【技嘉 2376】👀 等量能｜量能不足", messages[1])

    def test_v19_4_backtest_changes_tracking_order_only(self):
        weak_context = {
            "sample": 35,
            "win_rate": 42,
            "avg_return": -0.8,
        }
        strong_context = {
            "sample": 35,
            "win_rate": 62,
            "avg_return": 1.4,
        }

        def rr_payload(code, context):
            return {
                "stock_code": code,
                "price": 120,
                "change": 1.0,
                "price_source": "realtime",
                "daily_source": "yahoo",
                "result": {
                    "decision": "WAIT",
                    "action": 0,
                    "rr": 0.8,
                    "heat_state": "NORMAL",
                    "trade_state": "LATE_ENTRY",
                    "structure_phase": "BREAKOUT_CONFIRM",
                    "price_behavior": "NORMAL",
                    "market_grade": "B",
                    "volume_state": "NORMAL",
                    "volume_price_state": "NORMAL",
                    "structure_state": "NORMAL",
                    "entry_quality": "B",
                    "confidence_score": 70,
                    "breakout_distance": 1.2,
                },
                "holding": None,
                "backtest_context": context,
                "structure_score": 4,
                "volume_ratio": 1.0,
            }

        messages = generator.formatTelegramMessages(
            {
                "建準": rr_payload("2421", weak_context),
                "仁寶": rr_payload("2324", strong_context),
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 26),
        )

        self.assertIn("未持倉 2 檔僅追蹤，等觸發，不列入明日執行", messages[-1])
        self.assertIn("未持倉總數 2 檔", messages[-1])
        self.assertIn("可買 0｜可準備 0（不可買）｜僅追蹤 2｜淘汰 0", messages[-1])
        self.assertIn("其中僅追蹤 2 檔拆分：等冷卻 0、等回測 0、等RR修復 2、等量能 0", messages[-1])
        self.assertNotIn("【可買", messages[-1])
        self.assertIn("【仁寶 2324】👀 等RR修復｜RR不足", messages[1])
        self.assertIn("【建準 2421】👀 等RR修復｜RR不足", messages[1])

    def test_v19_3_3_holding_add_levels_display_explicit_add_actions(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122],
            {"shares": 100, "avg_price": 110},
            price=122,
            change=2.1,
        )
        payload["stock_code"] = "2376"
        payload["holding_decision"] = {
            "action": "加碼 20%",
            "level": "ADD_20",
            "note": "趨勢延續",
            "warning_price": 115,
            "hard_stop_price": 108,
            "allow_add": True,
        }

        card = generator.formatTelegramPositionCard("技嘉", payload)

        self.assertIn("【技嘉 2376】📌 加碼20", card)
        self.assertIn("決策：加碼 20%，趨勢延續", card)
        self.assertIn("條件：RR足夠，品質達標", card)

    def test_today_buy_holding_overrides_add_level_in_all_summary_surfaces(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122],
            {"shares": 100, "avg_price": 110},
            price=122,
            change=2.1,
        )
        payload["stock_code"] = "2376"
        payload["holding_decision"] = {
            "action": "加碼 20%",
            "level": "ADD_20",
            "note": "趨勢延續",
            "warning_price": 115,
            "hard_stop_price": 108,
            "allow_add": True,
        }
        payload["position_events"] = {"event_count": 1, "bought_shares": 100}
        payload["today_action"] = "BUY"

        card = generator.formatTelegramPositionCard("技嘉", payload)
        messages = generator.formatTelegramMessages(
            {"技嘉": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 27),
        )

        self.assertIn("【技嘉 2376】📌 新倉風控觀察", card)
        self.assertIn("決策：新倉風控觀察，暫不加碼", card)
        self.assertIn("條件：守警戒價，跌破停損或轉弱優先風控", card)
        self.assertIn("1. 技嘉｜+10.91%｜新倉風控觀察｜明日未修復降級", messages[-1])
        self.assertNotIn("加碼20", card)
        self.assertNotIn("加碼 20%", card)
        self.assertNotIn("加碼20", messages[-1])
        self.assertNotIn("加碼 20%", messages[-1])

    def test_rejected_summary_shows_count_not_full_four_stock_names(self):
        def rejected_payload(code):
            return {
                "stock_code": code,
                "price": 81,
                "change": -2.0,
                "price_source": "realtime",
                "daily_source": "yahoo",
                "result": {
                    "decision": "WAIT",
                    "action": 0,
                    "rr": 2.0,
                    "heat_state": "NORMAL",
                    "trade_state": "WAIT",
                    "structure_phase": "WEAK_REBOUND",
                    "price_behavior": "WEAK_REBOUND",
                    "market_grade": "D",
                    "volume_state": "WEAK",
                    "volume_price_state": "COILING",
                    "structure_state": "WEAK",
                    "entry_quality": "D",
                    "confidence_score": 30,
                    "breakout_distance": 8,
                },
                "holding": None,
                "structure_score": 1,
                "volume_ratio": 0.5,
            }

        messages = generator.formatTelegramMessages(
            {
                "旺宏": rejected_payload("2337"),
                "群創": rejected_payload("3481"),
                "南亞科": rejected_payload("2408"),
                "仁寶": rejected_payload("2324"),
            },
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 27),
        )

        summary_msg = messages[-1]
        self.assertIn("淘汰 4 檔｜主因：弱反彈待確認｜詳情見未持倉卡", summary_msg)
        self.assertIn("【旺宏 2337】⛔ 淘汰", messages[1])
        self.assertIn("【群創 3481】⛔ 淘汰", messages[1])
        self.assertNotIn("旺宏", summary_msg)
        self.assertNotIn("群創", summary_msg)
        self.assertNotIn("南亞科", summary_msg)
        self.assertNotIn("仁寶", summary_msg)
        self.assertNotIn("淘汰 4：旺宏、群創、南亞科、仁寶", summary_msg)

    def test_v19_3_3_profit_reduce_stop_detail_lines_are_direct_actions(self):
        base = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            {"shares": 100, "avg_price": 120},
            price=108,
            change=-4,
        )
        base["stock_code"] = "3035"

        stop_payload = dict(base)
        stop_payload["holding_decision"] = {
            "action": "停損 100%",
            "level": "STOP_100",
            "note": "硬停損觸發",
            "warning_price": 114,
            "hard_stop_price": 110,
        }
        stop_card = generator.formatTelegramPositionCard("智原", stop_payload)
        self.assertIn("【智原 3035】📌 停損", stop_card)
        self.assertIn("決策：停損 100%，硬停損觸發", stop_card)
        self.assertIn("條件：停損優先，避免虧損擴大", stop_card)
        self.assertIn("原因：跌破停損線，避免虧損擴大", stop_card)
        self.assertIn("下一步：清出後不急回補，等重新出現買點", stop_card)

        reduce_payload = dict(base)
        reduce_payload["holding_decision"] = {
            "action": "減碼 25%",
            "level": "REDUCE_25",
            "note": "結構破壞，先降風險",
            "warning_price": 114,
            "hard_stop_price": 110,
        }
        reduce_card = generator.formatTelegramPositionCard("智原", reduce_payload)
        self.assertIn("【智原 3035】📌 減碼", reduce_card)
        self.assertIn("決策：減碼 25%，降低風險", reduce_card)
        self.assertIn("條件：結構轉弱或突破失敗，先降風險", reduce_card)
        self.assertIn("原因：突破失敗或結構轉弱，先降低風險", reduce_card)
        self.assertIn("下一步：若無法重新站回突破區，繼續降低優先級", reduce_card)

        profit_payload = dict(base)
        profit_payload["price"] = 140
        profit_payload["holding"] = {"shares": 100, "avg_price": 110}
        profit_payload["holding_decision"] = {
            "action": "停利 25%",
            "level": "TAKE_PROFIT_25",
            "note": "漲停過熱，保留核心倉",
            "warning_price": 133,
            "hard_stop_price": 126,
        }
        profit_card = generator.formatTelegramPositionCard("智原", profit_payload)
        self.assertIn("【智原 3035】📌 停利", profit_card)
        self.assertIn("決策：停利 25%，鎖定部分獲利", profit_card)
        self.assertIn("條件：高浮盈或過熱延伸，保留核心倉", profit_card)
        self.assertIn("原因：高浮盈且過熱延伸，先保留獲利", profit_card)
        self.assertIn("下一步：保留核心倉，等待冷卻後再評估", profit_card)

    def test_telegram_messages_can_include_detail_when_requested(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119],
            None,
            price=119,
            change=1.4,
        )
        generator.render_stock("建準", payload)
        messages = generator.formatTelegramMessages(
            {"建準": payload},
            "FULL DETAIL",
            None,
            None,
            "⏳ 觀望",
            datetime(2026, 5, 25),
            include_detail=True,
        )

        self.assertIn("【完整詳情備份】", messages[0])
        self.assertIn("FULL DETAIL", messages[0])
        self.assertIn("【持倉標的】", messages[1])
        self.assertIn("【未持倉標的】", messages[2])
        self.assertIn("｜v20.0.9】", messages[-1])


if __name__ == "__main__":
    unittest.main()
