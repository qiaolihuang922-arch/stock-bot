import unittest
from datetime import datetime

from core import generator
from core.market_theme_evidence import (
    build_market_theme_evidence,
    build_market_theme_evidence_provider,
)
from tests.test_generator_report import render_payload


def source(source_type, level="supportive", freshness="fresh", freshness_reason="same_trade_date", **overrides):
    return {
        "source_type": source_type,
        "source_name": overrides.pop("source_name", source_type),
        "as_of": overrides.pop("as_of", "2026-05-28"),
        "freshness": freshness,
        "freshness_reason": freshness_reason,
        "level": level,
        "supports_claims": overrides.pop("supports_claims", [f"{source_type} supportive"]),
        "limitations": overrides.pop("limitations", ["只佐證題材背景，不改變個股買點"]),
        "source_family": overrides.pop("source_family", source_type),
        **overrides,
    }


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
        self.assertEqual(evidence["source_family_count_for_confirmed"], 0)
        self.assertIn(
            "market_index 缺 freshness、freshness_reason、level、limitations，不可計入 confirmed",
            evidence["limitations"],
        )

    def test_same_source_type_does_not_confirm(self):
        market_source = source("market_index", source_family="market_state")
        evidence = build_market_theme_evidence(
            sources=[
                market_source,
                {
                    **market_source,
                    "supports_claims": ["sector strength"],
                    "limitations": ["same family"],
                },
            ],
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["theme_status"], "weak")
        self.assertEqual(evidence["source_family_count_for_confirmed"], 1)
        self.assertEqual(evidence["source_families"], ["market_state"])

    def test_watchlist_breadth_and_market_index_can_confirm(self):
        evidence = build_market_theme_evidence(
            sources=[
                source("watchlist_breadth", source_family="watchlist_theme_breadth"),
                source("market_index", source_family="market_state"),
            ],
        )

        self.assertTrue(evidence["confirmed"])
        self.assertEqual(evidence["theme_status"], "confirmed")
        self.assertEqual(evidence["theme_direction"], "supportive")
        self.assertEqual(
            evidence["confirmed_source_types"],
            ["watchlist_breadth", "market_index"],
        )
        self.assertEqual(evidence["level"], "confirmed")
        self.assertIn("supports_claims", evidence)

    def test_market_state_and_strategy_evidence_legacy_pair_no_longer_confirms_without_contract_fields(self):
        evidence = build_market_theme_evidence(
            market_state={
                "source_family": "market_state",
                "as_of": "2026-05-28",
                "freshness": "same_day",
                "supports_claims": ["risk_on", "electronics sector breadth"],
                "limitations": ["intraday may change"],
            },
            structured_strategy_evidence={
                "source_family": "structured_strategy_evidence",
                "as_of": "2026-05-28",
                "freshness": "same_day",
                "supports_claims": ["AI supply chain setup count rising"],
                "limitations": ["buy point still requires individual trigger"],
            },
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["level"], "weak")

    def test_stale_required_source_downgrades(self):
        evidence = build_market_theme_evidence(
            sources=[
                source("watchlist_breadth"),
                source(
                    "sector_index",
                    freshness="stale",
                    freshness_reason="older_than_threshold",
                ),
            ],
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["level"], "stale")

    def test_required_source_freshness_overrides_allowed_reason(self):
        for freshness in ["stale", "unavailable", "missing"]:
            with self.subTest(freshness=freshness):
                evidence = build_market_theme_evidence(
                    sources=[
                        source("watchlist_breadth"),
                        source(
                            "sector_index",
                            freshness=freshness,
                            freshness_reason="same_trade_date",
                        ),
                    ],
                )

                self.assertFalse(evidence["confirmed"])
                self.assertEqual(evidence["level"], "stale")

    def test_mixed_when_background_strong_but_watchlist_weak(self):
        evidence = build_market_theme_evidence(
            sources=[
                source("watchlist_breadth", level="weak"),
                source("official", level="supportive"),
            ],
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["level"], "mixed")

    def test_absent_when_no_runtime_or_report_source(self):
        evidence = build_market_theme_evidence()

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["level"], "absent")

    def test_provider_normalizes_existing_malformed_confirmed_dict(self):
        evidence = build_market_theme_evidence_provider(
            formatter_report_input={
                "market_theme_evidence": {
                    "confirmed": True,
                    "theme_status": "confirmed",
                    "theme_label": "AI/電子供應鏈",
                    "theme_direction": "bullish",
                    "source_families": ["report_derived"],
                }
            },
            market_theme_evidence={
                "confirmed": True,
                "theme_status": "confirmed",
                "theme_label": "AI/電子供應鏈",
                "theme_direction": "bullish",
                "source_families": ["report_derived"],
            },
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["level"], "weak")
        self.assertEqual(evidence["theme_label"], "AI/電子供應鏈")
        self.assertEqual(evidence["source_families"], ["report_derived"])

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
        self.assertIn("【05/28 盤中｜v20.2.4】", summary)
        self.assertIn("市場 / 題材證據：weak", summary)
        self.assertIn("限制：內部題材證據未達確認，仍依量價 / 風控判斷", summary)
        self.assertIn("🧭 主線：市場偏多但買點未成立。", summary)
        self.assertNotIn("confirmed", summary)
        self.assertNotIn("AI/電子供應鏈偏多", summary)
        self.assertNotIn("今日可買：台積電", summary)
        self.assertLess(summary.index("🧭 新倉：無有效進場。"), summary.index("市場 / 題材證據：weak"))

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
            sources=[
                source("watchlist_breadth", source_family="watchlist_theme_breadth"),
                source("sector_index", source_family="market_state"),
            ],
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
        self.assertIn("市場 / 題材證據：confirmed", summary)
        self.assertIn("限制：題材可追蹤，不代表可買", summary)
        self.assertIn("來源：watchlist_breadth same_trade_date; sector_index same_trade_date", summary)
        self.assertIn("🧭 新倉：無有效進場。", summary)
        self.assertIn("未持倉 1 檔僅追蹤", summary)
        self.assertLess(
            summary.index("🧭 新倉：無有效進場。"),
            summary.index("市場 / 題材證據：confirmed"),
        )
        self.assertNotIn("今日可買：台積電", summary)
        self.assertNotIn("台積電｜可買", summary)

    def test_formatter_does_not_trust_existing_malformed_evidence_dict(self):
        payload = render_payload(
            [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 126],
            None,
            price=126,
            change=3.1,
        )
        payload["result"].update({
            "decision": "WAIT",
            "action": 0,
            "breakout_distance": 7.5,
            "rr": 1.8,
            "market_grade": "A",
            "heat_state": "NORMAL",
            "trade_state": "WAIT",
        })

        messages = generator.formatTelegramMessages(
            {"台積電": payload},
            "FULL DETAIL",
            None,
            None,
            {
                "market_theme_evidence": {
                    "confirmed": True,
                    "theme_status": "confirmed",
                    "theme_label": "AI/電子供應鏈",
                    "theme_direction": "bullish",
                    "source_families": ["report_derived"],
                }
            },
            datetime(2026, 5, 28),
            report_phase="盤中",
        )

        summary = messages[-1]
        self.assertIn("市場 / 題材證據：weak", summary)
        self.assertIn("限制：內部題材證據未達確認，仍依量價 / 風控判斷", summary)
        self.assertNotIn("市場 / 題材證據：confirmed", summary)
        self.assertNotIn("🧭 主線：AI / 電子供應鏈仍偏多。", summary)


if __name__ == "__main__":
    unittest.main()
