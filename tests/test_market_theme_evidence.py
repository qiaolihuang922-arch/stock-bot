import unittest
from datetime import datetime
from unittest.mock import patch

from core import generator
from core.market_theme_evidence import (
    build_market_theme_evidence,
    build_market_theme_evidence_provider,
    format_market_theme_summary_lines,
)
from services import market_theme_evidence_store
from services.market_theme_evidence_store import load_confirmed_market_theme_evidence
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
        "source_family": overrides.pop("source_family", "production_db"),
        **overrides,
    }


class EvidenceTable:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.calls = []

    def select(self, fields):
        self.calls.append(("select", fields))
        return self

    def eq(self, key, value):
        self.calls.append(("eq", key, value))
        return self

    def order(self, key, desc=False):
        self.calls.append(("order", key, desc))
        return self

    def limit(self, limit):
        self.calls.append(("limit", limit))
        return self

    def execute(self):
        if self.error:
            raise self.error
        return type("Result", (), {"data": self.rows})()


class EvidenceClient:
    def __init__(self, rows=None, error=None):
        self.table_obj = EvidenceTable(rows, error=error)
        self.tables = []

    def table(self, name):
        self.tables.append(name)
        return self.table_obj


def confirmed_row(**overrides):
    row = {
        "market_index": "TAIEX",
        "sector_theme_key": "semiconductor",
        "trade_date": "2026-05-29",
        "as_of": "2026-05-29T13:40:00+08:00",
        "freshness": "fresh",
        "evidence_status": "confirmed",
        "support_level": "supporting",
        "evidence_value": {"market": "supportive"},
        "watchlist_breadth": {"supportive": 7, "tracked": 12},
        "source_family": "production_db",
        "source_name": "market_theme_confirmed_evidence",
        "lineage": {"table": "market_theme_confirmed_evidence"},
    }
    row.update(overrides)
    return row


class MarketThemeEvidenceTest(unittest.TestCase):
    def test_loader_reads_production_row_and_builds_provider_sources(self):
        client = EvidenceClient([confirmed_row()])

        loaded = load_confirmed_market_theme_evidence(
            client=client,
            trade_date="2026-05-29",
        )

        self.assertEqual(client.tables, ["market_theme_confirmed_evidence"])
        self.assertIn(("eq", "trade_date", "2026-05-29"), client.table_obj.calls)
        self.assertEqual(loaded["status"], "confirmed")
        self.assertTrue(loaded["confirmed"])
        self.assertEqual(loaded["source_of_truth"], "production_db")
        self.assertEqual(loaded["support_level"], "supporting")

        evidence = build_market_theme_evidence_provider(
            market_theme_evidence=loaded,
        )
        self.assertTrue(evidence["confirmed"])
        self.assertEqual(evidence["source_status"], "ready")
        self.assertEqual(evidence["source_family"], "production_db")
        self.assertEqual(
            evidence["confirmed_source_types"],
            ["watchlist_breadth", "sector_index"],
        )

    def test_loader_fails_closed_when_source_missing_or_empty_or_error(self):
        with patch.object(market_theme_evidence_store, "_build_client", return_value=None):
            self.assertEqual(
                load_confirmed_market_theme_evidence()["status"],
                "missing-source",
            )
        self.assertEqual(
            load_confirmed_market_theme_evidence(client=EvidenceClient([]))["status"],
            "absent",
        )
        self.assertEqual(
            load_confirmed_market_theme_evidence(
                client=EvidenceClient(error=RuntimeError("permission denied"))
            )["status"],
            "source-error",
        )

    def test_loader_fails_closed_for_non_confirming_rows_and_unsupported_enum(self):
        fail_closed_rows = [
            (confirmed_row(freshness="stale"), "insufficient-data"),
            (confirmed_row(evidence_status="rejected"), "insufficient-data"),
            (confirmed_row(support_level="weak"), "insufficient-data"),
            (confirmed_row(support_level="invalidated"), "insufficient-data"),
            (confirmed_row(evidence_value=None), "insufficient-data"),
            (confirmed_row(support_level="strong"), "source-error"),
        ]

        for row, expected in fail_closed_rows:
            with self.subTest(row=row):
                loaded = load_confirmed_market_theme_evidence(
                    client=EvidenceClient([row])
                )
                self.assertEqual(loaded["status"], expected)
                self.assertFalse(loaded["confirmed"])

    def test_provider_preserves_loader_fail_closed_statuses(self):
        for status in ["absent", "missing-source", "source-error", "insufficient-data"]:
            with self.subTest(status=status):
                evidence = build_market_theme_evidence_provider(
                    market_theme_evidence={
                        "status": status,
                        "confirmed": False,
                        "source_of_truth": "production_db",
                        "reason": f"{status} reason",
                    },
                )

                self.assertFalse(evidence["confirmed"])
                self.assertEqual(evidence["source_status"], status)
                self.assertEqual(evidence["source_family"], "production_db")
                self.assertEqual(evidence["source_of_truth"], "production_db")

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
        market_source = source("market_index")
        evidence = build_market_theme_evidence(
            sources=[
                market_source,
                {
                    **market_source,
                    "source_family": "owner_approved_persistent",
                    "supports_claims": ["sector strength"],
                    "limitations": ["same family"],
                },
            ],
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["theme_status"], "weak")
        self.assertEqual(evidence["source_family_count_for_confirmed"], 1)
        self.assertEqual(
            evidence["source_families"],
            ["production_db", "owner_approved_persistent"],
        )
        self.assertEqual(evidence["confirmed_source_types"], [])

    def test_watchlist_breadth_and_market_index_can_confirm(self):
        evidence = build_market_theme_evidence(
            sources=[
                source("watchlist_breadth"),
                source("market_index"),
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
        self.assertEqual(evidence["source_status"], "ready")
        self.assertEqual(evidence["source_family"], "production_db")
        self.assertEqual(evidence["freshness"], "fresh")
        self.assertEqual(evidence["confidence"], "confirmed")
        self.assertIn("supports_claims", evidence)

    def test_runtime_diagnostic_watchlist_breadth_cannot_confirm_even_with_market_index(self):
        evidence = build_market_theme_evidence(
            sources=[
                source(
                    "watchlist_breadth",
                    source_family="runtime_diagnostic",
                    source_name="watchlist_strategy_snapshot",
                    runtime_diagnostic=True,
                ),
                source("market_index"),
            ],
        )

        self.assertFalse(evidence["confirmed"])
        self.assertNotEqual(evidence["source_status"], "ready")
        self.assertIn(evidence["source_status"], {"insufficient-data", "missing-source"})
        self.assertEqual(evidence["source_family"], "runtime_diagnostic")
        self.assertEqual(evidence["confidence"], "weak")
        self.assertEqual(evidence["confirmed_source_types"], [])

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

    def test_runtime_watchlist_fallback_is_non_trading_diagnostic_when_db_evidence_missing(self):
        evidence = build_market_theme_evidence_provider(
            results_map={
                "台積電": {
                    "holding": None,
                    "result": {"decision": "WAIT", "market_grade": "A"},
                },
                "鴻海": {
                    "holding": None,
                    "result": {"decision": "WAIT", "market_grade": "A"},
                },
            },
            market_theme_evidence=None,
            as_of="2026-05-29",
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["level"], "absent")
        self.assertFalse(evidence["runtime_fallback"])
        self.assertFalse(evidence["runtime_supportive"])
        self.assertEqual(
            evidence["watchlist_breadth_diagnostic"]["level"],
            "supportive",
        )
        self.assertIn("缺 DB evidence table/cache", evidence["missing_source_reasons"])
        self.assertIn("缺 market_index", evidence["missing_source_reasons"])
        self.assertIn("缺 sector_index", evidence["missing_source_reasons"])
        self.assertEqual(evidence["source_status"], "missing-source")
        self.assertEqual(evidence["source_family"], "runtime_diagnostic")
        self.assertEqual(evidence["confidence"], "absent")
        self.assertIn("缺 DB evidence table/cache", evidence["source_name"])
        self.assertIn("不得 fake confirmed", evidence["forbidden_effects"])

        lines = format_market_theme_summary_lines(evidence)
        self.assertEqual(
            lines,
            [
                "證據：production 來源不足，不作確認。",
                "詳情：runtime 觀察僅供診斷，非確認來源。",
            ],
        )

    def test_runtime_missing_fallback_lists_missing_sources(self):
        evidence = build_market_theme_evidence_provider(
            results_map={},
            market_theme_evidence={"theme_status": "absent", "level": "absent"},
        )

        self.assertFalse(evidence["confirmed"])
        self.assertEqual(evidence["level"], "absent")
        self.assertIn("缺 DB evidence table/cache", evidence["missing_source_reasons"])
        self.assertIn("缺 runtime watchlist breadth", evidence["missing_source_reasons"])
        self.assertEqual(evidence["source_status"], "missing-source")
        self.assertEqual(evidence["source_family"], "production_db")

        lines = format_market_theme_summary_lines(evidence)
        self.assertEqual(
            lines,
            [
                "證據：production 來源不足，不作確認。",
                "詳情：缺結構化 market/theme production source。",
            ],
        )

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
        self.assertIn("【05/28 盤中｜v20.4.3】", summary)
        self.assertIn("證據：production 來源不足，不作確認。", summary)
        self.assertIn("詳情：runtime 觀察僅供診斷，非確認來源。", summary)
        self.assertIn("🧭 主線：市場偏多但買點未成立。", summary)
        self.assertNotIn("confirmed", summary)
        self.assertNotIn("AI/電子供應鏈偏多", summary)
        self.assertNotIn("今日可買：台積電", summary)
        self.assertLess(
            summary.index("🧭 新倉：無有效進場。"),
            summary.index("證據：production 來源不足，不作確認。"),
        )

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
                source("watchlist_breadth"),
                source("sector_index"),
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
        self.assertIn("證據：production confirmed，市場/題材支持成立。", summary)
        self.assertIn("限制：題材可追蹤，不代表可買", summary)
        self.assertIn("來源：watchlist_breadth same_trade_date; sector_index same_trade_date", summary)
        self.assertIn("🧭 新倉：無有效進場。", summary)
        self.assertIn("未持倉 1 檔僅追蹤", summary)
        self.assertLess(
            summary.index("🧭 新倉：無有效進場。"),
            summary.index("證據：production confirmed，市場/題材支持成立。"),
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
