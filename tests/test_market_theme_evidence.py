import unittest
from datetime import datetime

from core import generator
from core.market_theme_evidence import build_market_theme_evidence
from tests.test_generator_report import render_payload


class MarketThemeEvidenceTest(unittest.TestCase):
    def test_report_derived_results_and_watchlist_cannot_confirm_theme(self):
        evidence = build_market_theme_evidence(
            results_map={
                "台積電": {"theme": "AI/電子供應鏈", "score": 82},
            },
            watchlist_groups={
                "AI/電子供應鏈": ["2330", "2382"],
            },
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["theme_status"], "weak")
        self.assertIsNone(evidence["theme_direction"])
        self.assertEqual(evidence["theme_label"], "AI/電子供應鏈")
        self.assertEqual(evidence["actionability"], "track_only")
        self.assertEqual(evidence["source_families"], ["report_derived"])
        self.assertIn("來源不足，僅來自報文衍生資料", evidence["limitations"])

    def test_theme_string_only_stays_weak_and_not_bullish(self):
        evidence = build_market_theme_evidence(
            formatter_report_input="AI/電子供應鏈仍偏多"
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["theme_status"], "weak")
        self.assertEqual(evidence["theme_label"], "AI/電子供應鏈")
        self.assertIsNone(evidence["theme_direction"])

    def test_missing_required_structured_field_does_not_count_for_confirmed(self):
        evidence = build_market_theme_evidence(
            market_state={
                "source_family": "market_state",
                "as_of": "2026-05-28",
                "confidence": 0.8,
                "supports_claims": ["risk_on"],
            },
            structured_strategy_evidence={
                "source_family": "structured_strategy_evidence",
                "as_of": "2026-05-28",
                "freshness": "same_day",
                "confidence": 0.7,
                "supports_claims": ["AI breadth improving"],
                "limitations": ["sample limited"],
            },
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["theme_status"], "weak")
        self.assertEqual(evidence["source_family_count_for_confirmed"], 1)
        self.assertIn(
            "market_state 缺 freshness、limitations，不可計入 confirmed",
            evidence["limitations"],
        )

    def test_same_source_family_does_not_confirm(self):
        source = {
            "source_family": "market_state",
            "as_of": "2026-05-28",
            "freshness": "same_day",
            "confidence": 0.8,
            "supports_claims": ["risk_on"],
            "limitations": ["index only"],
        }
        evidence = build_market_theme_evidence(
            sources=[
                source,
                {
                    **source,
                    "confidence": 0.7,
                    "supports_claims": ["sector strength"],
                    "limitations": ["same family"],
                },
            ],
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["theme_status"], "weak")
        self.assertEqual(evidence["source_family_count_for_confirmed"], 1)
        self.assertEqual(evidence["source_families"], ["market_state"])

    def test_market_state_and_strategy_evidence_can_confirm(self):
        evidence = build_market_theme_evidence(
            market_state={
                "source_family": "market_state",
                "as_of": "2026-05-28",
                "freshness": "same_day",
                "confidence": 0.82,
                "supports_claims": ["risk_on", "electronics sector breadth"],
                "limitations": ["intraday may change"],
            },
            structured_strategy_evidence={
                "source_family": "structured_strategy_evidence",
                "as_of": "2026-05-28",
                "freshness": "same_day",
                "confidence": 0.76,
                "supports_claims": ["AI supply chain setup count rising"],
                "limitations": ["buy point still requires individual trigger"],
            },
        )

        self.assertTrue(evidence["confirmed"])
        self.assertEqual(evidence["theme_status"], "confirmed")
        self.assertEqual(evidence["theme_direction"], "bullish")
        self.assertEqual(
            evidence["confirmed_source_families"],
            ["market_state", "structured_strategy_evidence"],
        )

    def test_formatter_report_derived_only_shows_weak_track_only(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 132],
            None,
            price=132,
            change=6.4,
        )
        payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 1,
            "price_behavior": "NORMAL",
            "heat_state": "HOT",
            "trade_state": "EXTENDED",
            "rr": 1.4,
            "market_grade": "A",
            "theme": "AI/電子供應鏈",
        })

        messages = generator.formatTelegramMessages(
            {"台積電": payload},
            "FULL DETAIL",
            None,
            None,
            "AI/電子供應鏈仍偏多",
            datetime(2026, 5, 28),
            report_phase="盤中",
        )

        summary = messages[-1]
        self.assertIn("【05/28 盤中｜v20.1.1】", summary)
        self.assertIn("市場主題：AI/電子供應鏈", summary)
        self.assertIn("狀態：weak｜來源不足｜只追蹤", summary)
        self.assertIn("行動：不可買，等 structured evidence 補強", summary)
        self.assertIn("🧭 主線：市場偏多但買點未成立。", summary)
        self.assertNotIn("confirmed", summary)
        self.assertNotIn("AI/電子供應鏈偏多", summary)
        self.assertNotIn("今日可買：台積電", summary)

    def test_confirmed_theme_without_stock_entry_stays_track_only(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 126],
            None,
            price=126,
            change=3.1,
        )
        payload["stock_code"] = "2330"
        payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 7.5,
            "rr": 1.8,
            "market_grade": "A",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
        })
        evidence = build_market_theme_evidence(
            theme="AI/電子供應鏈",
            market_state={
                "source_family": "market_state",
                "as_of": "2026-05-28",
                "freshness": "same_day",
                "confidence": 0.82,
                "supports_claims": ["risk_on", "electronics sector breadth"],
                "limitations": ["intraday may change"],
            },
            structured_strategy_evidence={
                "source_family": "structured_strategy_evidence",
                "as_of": "2026-05-28",
                "freshness": "same_day",
                "confidence": 0.76,
                "supports_claims": ["AI supply chain setup count rising"],
                "limitations": ["buy point still requires individual trigger"],
            },
        )

        messages = generator.formatTelegramMessages(
            {"台積電": payload},
            "FULL DETAIL",
            None,
            None,
            {"market_theme_evidence": evidence},
            datetime(2026, 5, 28),
            report_phase="盤中",
        )

        summary = messages[-1]
        self.assertIn("市場主題：AI/電子供應鏈偏多", summary)
        self.assertIn("狀態：confirmed｜2 類 structured sources", summary)
        self.assertIn("🧭 新倉：無有效進場。", summary)
        self.assertIn("未持倉 1 檔僅追蹤", summary)
        self.assertNotIn("今日可買：台積電", summary)
        self.assertNotIn("台積電｜可買", summary)


if __name__ == "__main__":
    unittest.main()
