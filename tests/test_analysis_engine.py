import unittest

from core.signal_snapshot import (
    analyze_ohlcv_snapshot,
    apply_snapshot_boundaries,
    is_tradeable_result,
    mark_best_candidate
)
from services.analysis import calc_rr, extended_level, holding_signal


VOL_NORMAL = [1000] * 20
VOL_ATTACK = [1000] * 19 + [1800]
VOL_LOW = [1000] * 19 + [500]


def snap(name, closes, volumes=None):
    return analyze_ohlcv_snapshot(
        name,
        "2026-05-22",
        closes,
        volumes or VOL_NORMAL
    )


class AnalysisEngineTest(unittest.TestCase):
    def test_breakout_confirmed_tradeable(self):
        item = snap("breakout", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119], VOL_ATTACK)
        self.assertEqual(item["pattern"], "BREAKOUT_CONFIRM")
        self.assertEqual(item["market_state"], "A+")
        self.assertEqual(item["structure_state"], "STRONG")
        self.assertEqual(item["action"], "BUY")
        self.assertTrue(item["is_tradeable"])
        self.assertIn("RR足夠", item["reasons"])

    def test_near_breakout_state(self):
        item = snap("near", [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 119, 118.5, 118, 117.5, 118, 118.5, 119, 119.2, 119.5], VOL_ATTACK)
        self.assertEqual(item["pattern"], "BREAKOUT_WATCH")
        self.assertEqual(item["position_state"], "NEAR_BREAKOUT")
        self.assertNotIn("停利", "、".join(item["reasons"]))

    def test_weak_rebound_no_trade(self):
        item = snap("weak_rebound", [120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100, 98, 96, 94, 92, 90, 88, 86, 84, 88], VOL_ATTACK)
        self.assertEqual(item["pattern"], "WEAK_REBOUND")
        self.assertEqual(item["market_state"], "D")
        self.assertEqual(item["action"], "NO_TRADE")
        self.assertFalse(item["is_tradeable"])

    def test_limit_up_locked_is_not_tradeable(self):
        item = snap("limit_lock", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130], VOL_ATTACK)
        self.assertEqual(item["pattern"], "LOCK_LIMIT")
        self.assertEqual(item["raw_result"]["price_behavior"], "LIMIT_LOCK")
        self.assertIn("不追高", item["reasons"])
        self.assertFalse(item["is_tradeable"])

    def test_rr_insufficient_marks_reason(self):
        item = snap("rr_low", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122], VOL_ATTACK)
        self.assertLess(item["rr"], 1)
        self.assertIn("RR不足", item["reasons"])
        self.assertFalse(item["is_tradeable"])

    def test_rr_and_heat_helpers_are_none_safe(self):
        self.assertEqual(calc_rr(None, 10, 20), 0)
        self.assertEqual(calc_rr(10, None, 20), 0)
        self.assertEqual(calc_rr(10, 9, None), 0)
        self.assertEqual(extended_level(None, 20), 0)
        self.assertEqual(extended_level(10, None), 0)

    def test_rr_enough_marks_tradeable(self):
        item = snap("rr_ok", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119], VOL_ATTACK)
        self.assertGreaterEqual(item["rr"], 1)
        self.assertTrue(item["is_tradeable"])

    def test_overheat_lv2_limits_trade(self):
        item = snap("hot", [100] * 19 + [117], VOL_ATTACK)
        self.assertEqual(item["heat_level"], 2)
        self.assertFalse(item["is_tradeable"])

    def test_overheat_lv3_limits_trade_without_covering_pattern(self):
        item = snap("extreme", [100] * 19 + [130], VOL_ATTACK)
        self.assertEqual(item["heat_level"], 3)
        self.assertNotEqual(item["pattern"], "EXTENDED_RISK")
        self.assertIn("過熱 Lv.3", item["reasons"])
        self.assertFalse(item["is_tradeable"])

    def test_low_volume_blocks_trade(self):
        item = snap("low_volume", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119], VOL_LOW)
        self.assertEqual(item["raw_result"]["trade_state"], "NO_VOLUME")
        self.assertIn("量能不足", item["reasons"])
        self.assertFalse(item["is_tradeable"])

    def test_attack_volume_state(self):
        item = snap("attack", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 120], VOL_ATTACK)
        self.assertEqual(item["raw_result"]["volume_price_state"], "EXPANSION")

    def test_coiling_state(self):
        item = snap("coiling", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119], VOL_LOW)
        self.assertEqual(item["raw_result"]["volume_price_state"], "COILING")

    def test_holding_continue_hold(self):
        item = snap("hold", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119], VOL_ATTACK)
        signal = holding_signal(item["raw_result"], 119, 118, "realtime", 1.0)
        self.assertIn(signal["level"], ["HOLD", "ADD_10"])
        self.assertNotIn("停損", signal["action"])

    def test_holding_shakeout_observation(self):
        item = snap("shakeout", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 116], VOL_LOW)
        signal = holding_signal(item["raw_result"], 116, 117, "realtime", -1.0)
        self.assertEqual(signal["level"], "SHAKEOUT_WARN")
        self.assertEqual(signal["action"], "洗盤警戒")
        self.assertFalse(item["is_tradeable"])

    def test_holding_weak_far_pullback_is_not_shakeout_protected(self):
        result = {
            "decision": "WAIT",
            "structure_phase": "WEAK",
            "price_behavior": "NORMAL",
            "market_regime": "RISK_ON",
            "multi_day_bias": "UP",
            "heat_state": "NORMAL",
            "trade_state": "NO_VOLUME",
            "extended_level": 1,
            "trend": "UP",
            "volume_state": "WEAK",
            "volume_price_state": "COILING",
            "rr": 4.5,
            "breakout_distance": 11,
            "entry_quality": "D",
            "confidence_score": 39,
        }

        signal = holding_signal(result, 308.75, 298, "realtime", 4.3)

        self.assertEqual(signal["level"], "HOLD_WATCH")
        self.assertEqual(signal["action"], "續抱觀察")

    def test_high_profit_hot_pullback_becomes_core_hold(self):
        result = {
            "decision": "WAIT",
            "structure_phase": "BREAKOUT_CONFIRM",
            "price_behavior": "VOLUME_DROP",
            "market_regime": "RISK_ON",
            "multi_day_bias": "UP",
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "extended_level": 2,
            "trend": "UP",
            "volume_state": "STRONG",
            "volume_price_state": "NORMAL",
            "rr": 0,
            "breakout_distance": -12,
            "entry_quality": "D",
            "confidence_score": 49,
        }

        signal = holding_signal(result, 62.25, 52.15, "realtime", -4.8)

        self.assertEqual(signal["level"], "HOLD_CORE")
        self.assertEqual(signal["action"], "核心續抱")
        self.assertIn("高浮盈回落", signal["reason"])

    def test_holding_take_profit_25(self):
        item = snap("limit_hold", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130], VOL_ATTACK)
        signal = holding_signal(item["raw_result"], 130, 100, "realtime", 9.9)
        self.assertEqual(signal["level"], "TAKE_PROFIT_25")
        self.assertIn("漲停過熱", signal["reason"])

    def test_holding_after_profit_taken_does_not_repeat_take_profit(self):
        item = snap("profit_taken", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130], VOL_ATTACK)
        signal = holding_signal(
            item["raw_result"],
            130,
            100,
            "realtime",
            9.9,
            realized_profit_taken_ratio=0.5
        )
        self.assertEqual(signal["level"], "TAKE_PROFIT_25")
        self.assertEqual(signal["action"], "停利 25%")
        self.assertIn("續鎖一段利潤", signal["reason"])

    def test_holding_after_second_profit_taken_does_not_repeat_take_profit(self):
        item = snap("profit_taken_again", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130], VOL_ATTACK)
        signal = holding_signal(
            item["raw_result"],
            130,
            100,
            "realtime",
            9.9,
            realized_profit_taken_ratio=0.75
        )
        self.assertEqual(signal["level"], "HOLD_CORE")
        self.assertEqual(signal["action"], "續抱核心倉")

    def test_same_day_profit_taken_blocks_second_take_profit(self):
        item = snap("same_day_profit_taken", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130], VOL_ATTACK)
        signal = holding_signal(
            item["raw_result"],
            130,
            100,
            "realtime",
            9.9,
            realized_profit_taken_ratio=0.5,
            realized_profit_taken_date="2026-05-25",
            signal_date="2026-05-25"
        )
        self.assertEqual(signal["level"], "HOLD_CORE")
        self.assertEqual(signal["action"], "續抱核心倉")
        self.assertIn("同日不連續賣", signal["reason"])

    def test_profit_taken_does_not_lock_after_heat_cools(self):
        item = snap("cooled_profit_taken", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 114], VOL_ATTACK)
        signal = holding_signal(
            item["raw_result"],
            114,
            100,
            "realtime",
            -1.0,
            realized_profit_taken_ratio=0.5
        )
        self.assertNotEqual(signal["level"], "HOLD_CORE")
        self.assertNotIn("已完成50%停利", signal["reason"])

    def test_non_holding_limit_up_not_chasing(self):
        item = snap("limit_no_hold", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130], VOL_ATTACK)
        self.assertEqual(item["raw_result"]["price_behavior"], "LIMIT_LOCK")
        self.assertFalse(item["is_tradeable"])

    def test_strong_but_not_tradeable_when_rr_low(self):
        item = snap("strong_low_rr", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122], VOL_ATTACK)
        self.assertEqual(item["market_state"], "A+")
        self.assertLess(item["rr"], 1)
        self.assertFalse(item["is_tradeable"])

    def test_no_valid_best_stock(self):
        snapshots = [
            snap("rr_low", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 122], VOL_ATTACK),
            snap("limit", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 130], VOL_ATTACK),
            snap("weak", [120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100, 98, 96, 94, 92, 90, 88, 86, 84, 83], VOL_ATTACK)
        ]
        mark_best_candidate(snapshots)
        self.assertFalse(any(item["is_best_candidate"] for item in snapshots))

    def test_holding_stock_is_excluded_from_tradeable_and_best(self):
        snapshots = [
            snap("2356", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119], VOL_ATTACK)
        ]
        self.assertTrue(snapshots[0]["is_tradeable"])

        apply_snapshot_boundaries(snapshots, {"2356"})

        self.assertFalse(snapshots[0]["is_tradeable"])
        self.assertFalse(snapshots[0]["is_best_candidate"])

    def test_failed_breakout_has_reason(self):
        item = snap("fail", [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 124, 125, 123, 116], VOL_ATTACK)
        self.assertEqual(item["pattern"], "FAILED_BREAKOUT")
        self.assertIn("突破失敗", item["reasons"])


if __name__ == "__main__":
    unittest.main()
