import io
import json
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from unittest.mock import patch

from core import generator
from scripts import smoke_market_theme_evidence_readonly
from core.market_theme_evidence import (
    build_market_theme_evidence,
    build_market_theme_evidence_provider,
    format_market_theme_summary_lines,
)
from services import market_theme_evidence_store
from services.market_theme_evidence_store import load_confirmed_market_theme_evidence
from tests.test_generator_report import render_payload, summary_message


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
    def __init__(self, rows=None, error=None, calls=None):
        self.rows = rows or []
        self.error = error
        self.calls = calls if calls is not None else []
        self.filters = []
        self.orders = []

    def select(self, fields):
        self.calls.append(("select", fields))
        return self

    def eq(self, key, value):
        self.calls.append(("eq", key, value))
        self.filters.append(("eq", key, value))
        return self

    def lte(self, key, value):
        self.calls.append(("lte", key, value))
        self.filters.append(("lte", key, value))
        return self

    def order(self, key, desc=False):
        self.calls.append(("order", key, desc))
        self.orders.append((key, desc))
        return self

    def limit(self, limit):
        self.calls.append(("limit", limit))
        return self

    def execute(self):
        if self.error:
            raise self.error
        rows = list(self.rows)
        for method, key, value in self.filters:
            if method == "eq":
                rows = [
                    row for row in rows
                    if str(row.get(key)) == str(value)
                ]
            if method == "lte":
                rows = [
                    row for row in rows
                    if str(row.get(key)) <= str(value)
                ]
        for key, desc in reversed(self.orders):
            rows = sorted(rows, key=lambda row: str(row.get(key) or ""), reverse=desc)
        return type("Result", (), {"data": rows})()


class EvidenceClient:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.calls = []
        self.table_obj = EvidenceTable(self.rows, error=self.error, calls=self.calls)
        self.tables = []

    def table(self, name):
        self.tables.append(name)
        self.table_obj = EvidenceTable(self.rows, error=self.error, calls=self.calls)
        return self.table_obj


class MultiTableEvidenceClient:
    def __init__(self, rows_by_table):
        self.rows_by_table = rows_by_table
        self.calls = []
        self.tables = []

    def table(self, name):
        self.tables.append(name)
        rows = self.rows_by_table.get(name, [])
        return EvidenceTable(rows, calls=self.calls)


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

        self.assertGreaterEqual(client.tables.count("market_theme_confirmed_evidence"), 1)
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

    def test_confirmed_summary_shows_historical_trend(self):
        loaded = {
            **load_confirmed_market_theme_evidence(
                client=EvidenceClient([
                    confirmed_row(trade_date="2026-05-29"),
                    confirmed_row(trade_date="2026-05-28"),
                    confirmed_row(trade_date="2026-05-27"),
                ]),
                trade_date="2026-05-29",
            )
        }

        lines = format_market_theme_summary_lines(
            build_market_theme_evidence_provider(market_theme_evidence=loaded)
        )

        self.assertIn("證據：production confirmed，市場/題材支持成立。", lines)
        self.assertIn("證據日期：latest_trade_date=2026-05-29", lines)
        self.assertIn(
            "趨勢：連續支持｜近3個證據日｜連續3日支持｜lookback_range=2026-05-27~2026-05-29",
            lines,
        )
        self.assertIn("市場/題材輔助", lines)
        self.assertIn("- 題材：semiconductor", lines)
        self.assertIn("背景：延續順風；觀察區間 2026-05-27 至 2026-05-29；連續支持 3 天。", lines)
        self.assertIn(
            "解讀：背景有支持，但不等於個股買點，不追高；仍看個股進場與風控條件。",
            lines,
        )

    def test_loader_allows_previous_trade_date_for_holiday_report_date(self):
        client = EvidenceClient([confirmed_row(trade_date="2026-05-29")])

        loaded = load_confirmed_market_theme_evidence(
            client=client,
            trade_date="2026-05-30",
        )

        self.assertIn(("eq", "trade_date", "2026-05-30"), client.table_obj.calls)
        self.assertIn(("lte", "trade_date", "2026-05-30"), client.table_obj.calls)
        self.assertEqual(loaded["status"], "confirmed")
        self.assertEqual(loaded["trade_date"], "2026-05-29")
        self.assertEqual(loaded["requested_trade_date"], "2026-05-30")
        self.assertTrue(
            all(
                source["freshness_reason"] == "previous_trade_date_allowed"
                for source in loaded["sources"]
            )
        )

    def test_loader_rejects_stale_previous_trade_date(self):
        loaded = load_confirmed_market_theme_evidence(
            client=EvidenceClient([confirmed_row(trade_date="2026-05-20")]),
            trade_date="2026-05-30",
        )

        self.assertEqual(loaded["status"], "insufficient-data")
        self.assertFalse(loaded["confirmed"])

    def test_loader_builds_historical_evidence_trend(self):
        client = EvidenceClient([
            confirmed_row(trade_date="2026-05-27", sector_theme_key="electronics"),
            confirmed_row(trade_date="2026-05-29", sector_theme_key="semiconductor"),
            confirmed_row(trade_date="2026-05-28", sector_theme_key="computer"),
        ])

        loaded = load_confirmed_market_theme_evidence(
            client=client,
            trade_date="2026-05-29",
        )

        trend = loaded["evidence_trend"]
        self.assertEqual(loaded["trade_date"], "2026-05-29")
        self.assertEqual(trend["status"], "confirmed_trend")
        self.assertEqual(trend["observed_days"], 3)
        self.assertEqual(trend["support_streak_days"], 3)
        self.assertEqual(trend["lookback_range"], "2026-05-27~2026-05-29")
        self.assertEqual(
            [day["trade_date"] for day in trend["days"]],
            ["2026-05-29", "2026-05-28", "2026-05-27"],
        )

    def test_holiday_summary_shows_actual_evidence_dates_not_same_trade_date_only(self):
        loaded = load_confirmed_market_theme_evidence(
            client=EvidenceClient([
                confirmed_row(trade_date="2026-05-29", sector_theme_key="semiconductor"),
                confirmed_row(trade_date="2026-05-28", sector_theme_key="computer"),
                confirmed_row(trade_date="2026-05-27", sector_theme_key="electronics"),
                confirmed_row(trade_date="2026-05-26", sector_theme_key="ai_server"),
            ]),
            trade_date="2026-05-31",
        )

        lines = format_market_theme_summary_lines(
            build_market_theme_evidence_provider(market_theme_evidence=loaded)
        )
        text = "\n".join(lines)

        self.assertIn("證據日期：latest_trade_date=2026-05-29", text)
        self.assertIn("report_date=2026-05-31 uses latest trading day evidence", text)
        self.assertIn("來源：watchlist_breadth latest_trade_date=2026-05-29", text)
        self.assertIn("趨勢：連續支持｜近4個證據日｜連續4日支持", text)
        self.assertIn("lookback_range=2026-05-26~2026-05-29", text)
        self.assertNotIn("來源：watchlist_breadth same_trade_date; sector_index same_trade_date", text)

    def test_generator_consumption_check_uses_production_trend_on_fresh_run(self):
        client = MultiTableEvidenceClient({
            "market_theme_confirmed_evidence": [
                confirmed_row(trade_date="2026-05-29", sector_theme_key="semiconductor"),
                confirmed_row(trade_date="2026-05-28", sector_theme_key="computer"),
            ],
            "daily_signal_snapshot": [
                {"stock_id": "2330", "trade_date": "2026-05-29", "action": "BUY"},
            ],
        })

        report = generator.build_market_theme_production_trend_consumption_check(
            client=client,
            trade_date="2026-05-29",
        )

        self.assertEqual(report["mode"], "market-theme-production-trend-consumption-check")
        self.assertFalse(report["schema_change"])
        self.assertFalse(report["data_write"])
        self.assertFalse(report["live_telegram"])
        self.assertTrue(report["local_context_cleared"])
        self.assertEqual(report["fresh_runner_rebuild"], "passed")
        self.assertEqual(
            report["generator_consumption"]["entrypoint"],
            "core.generator.market_theme_summary_evidence",
        )
        self.assertTrue(
            report["generator_consumption"]["uses_market_theme_confirmed_evidence_history"]
        )
        self.assertFalse(report["generator_consumption"]["uses_only_daily_signal_snapshot"])
        self.assertFalse(
            report["generator_consumption"]["uses_runtime_or_local_cache_as_history"]
        )
        self.assertEqual(report["generator_consumption"]["observed_days"], 2)
        self.assertEqual(report["generator_consumption"]["recent_supporting_days"], 2)
        self.assertEqual(report["generator_consumption"]["support_streak_days"], 2)
        self.assertEqual(
            report["table_status"],
            {
                "market_theme_confirmed_evidence": "consumed",
                "sector_theme_members": "latest-only-blocked",
                "market_theme_index_daily_bars": "not-consumed",
            },
        )
        self.assertEqual(report["blocked_reasons"], [])
        self.assertIn("market_theme_confirmed_evidence", client.tables)
        self.assertNotIn("daily_signal_snapshot", client.tables)

    def test_generator_consumption_check_fails_closed_without_production_rows(self):
        report = generator.build_market_theme_production_trend_consumption_check(
            client=EvidenceClient([]),
            trade_date="2026-05-29",
        )

        self.assertEqual(report["fresh_runner_rebuild"], "blocked")
        self.assertFalse(
            report["generator_consumption"]["uses_market_theme_confirmed_evidence_history"]
        )
        self.assertFalse(report["generator_consumption"]["uses_only_daily_signal_snapshot"])
        self.assertFalse(
            report["generator_consumption"]["uses_runtime_or_local_cache_as_history"]
        )
        self.assertEqual(
            report["table_status"]["market_theme_confirmed_evidence"],
            "insufficient-data",
        )
        self.assertIn(
            "official generator path does not consume production evidence trend",
            report["blocked_reasons"],
        )

    def test_readonly_smoke_cli_outputs_consumption_check_json_with_mocked_persistent_rows(self):
        client = MultiTableEvidenceClient({
            "market_theme_confirmed_evidence": [
                confirmed_row(trade_date="2026-05-29"),
            ],
        })
        output = io.StringIO()

        with patch.object(
            smoke_market_theme_evidence_readonly,
            "_build_readonly_client",
            return_value=client,
        ), redirect_stdout(output):
            exit_code = smoke_market_theme_evidence_readonly.main([
                "--trade-date",
                "2026-05-29",
                "--production-trend-consumption-check-json",
            ])

        self.assertEqual(exit_code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["fresh_runner_rebuild"], "passed")
        self.assertTrue(
            report["generator_consumption"]["uses_market_theme_confirmed_evidence_history"]
        )
        self.assertFalse(report["data_write"])
        self.assertFalse(report["live_telegram"])
        self.assertNotIn("daily_signal_snapshot", client.tables)

    def test_readonly_smoke_cli_consumption_check_fails_closed_without_read_client(self):
        output = io.StringIO()

        with patch.object(
            smoke_market_theme_evidence_readonly,
            "_build_readonly_client",
            return_value=None,
        ), redirect_stdout(output):
            exit_code = smoke_market_theme_evidence_readonly.main([
                "--trade-date",
                "2026-05-29",
                "--production-trend-consumption-check-json",
            ])

        self.assertEqual(exit_code, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["fresh_runner_rebuild"], "blocked")
        self.assertEqual(
            report["table_status"]["market_theme_confirmed_evidence"],
            "missing-source",
        )
        self.assertFalse(
            report["generator_consumption"]["uses_market_theme_confirmed_evidence_history"]
        )
        self.assertIn(
            "missing required Supabase read credentials",
            report["blocked_reasons"],
        )

    def test_full_integrity_check_json_passes_with_production_rows_and_report_sample(self):
        client = MultiTableEvidenceClient({
            "market_theme_confirmed_evidence": [
                confirmed_row(trade_date="2026-05-29"),
                confirmed_row(trade_date="2026-05-28"),
            ],
        })
        messages = [
            "【持倉標的】\n\n【2330】📌 續抱觀察",
            "【未持倉標的】\n\n【2317】👀 等冷卻｜不可買",
            "\n".join([
                "【05/29 盤中｜v20.4.12】",
                "🧭 今日結論：R3 進攻偏熱；交易執行：無新增下單；未持倉 1 檔僅追蹤",
                "✅ 今日盤中交易執行",
                "無新增下單",
                "未持倉漏斗（非執行）：",
                "未持倉總數 1 檔",
                "可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 0",
            ]),
        ]

        report = generator.build_may_data_strategy_report_full_integrity_check(
            client=client,
            trade_date="2026-05-29",
            report_messages=messages,
        )

        self.assertEqual(report["mode"], "may-data-strategy-report-full-integrity-check")
        self.assertFalse(report["schema_change"])
        self.assertFalse(report["data_write"])
        self.assertFalse(report["live_telegram"])
        self.assertEqual(report["telegram_header_version"], "v20.4.12")
        self.assertEqual(report["source_integrity"]["production_db_readonly"], "passed")
        self.assertEqual(report["source_integrity"]["may_data_available"], "passed")
        self.assertEqual(
            report["source_integrity"]["market_theme_source_of_truth"],
            "production.market_theme_confirmed_evidence",
        )
        self.assertFalse(report["source_integrity"]["uses_fake_or_local_as_market_theme_evidence"])
        self.assertFalse(report["source_integrity"]["uses_daily_signal_snapshot_as_market_theme_evidence"])
        self.assertEqual(report["fresh_runner_dry_run"]["report_generated"], "passed")
        self.assertEqual(report["decision_display_consistency"]["strategy_vs_summary"], "passed")
        self.assertEqual(report["decision_display_consistency"]["strategy_vs_cards"], "passed")
        self.assertEqual(report["decision_display_consistency"]["strategy_vs_checklist"], "passed")
        self.assertEqual(report["decision_display_consistency"]["strategy_vs_funnel"], "passed")
        self.assertEqual(report["report_cross_section_consistency"]["version"], "passed")
        self.assertEqual(report["blocked_reasons"], [])
        self.assertNotIn("daily_signal_snapshot", client.tables)

    def test_full_integrity_check_blocks_summary_card_buy_conflict(self):
        messages = [
            "【持倉標的】\n\n無持倉",
            "【未持倉標的】\n\n【2317】👀 等冷卻｜不可買",
            "\n".join([
                "【05/29 盤中｜v20.4.12】",
                "🧭 今日結論：新倉：2317 可買",
                "✅ 今日盤中交易執行",
                "未持倉漏斗（非執行）：",
                "可買 1｜等冷卻 1",
            ]),
        ]

        report = generator.build_may_data_strategy_report_full_integrity_check(
            client=EvidenceClient([]),
            trade_date="2026-05-29",
            report_messages=messages,
        )

        self.assertEqual(report["source_integrity"]["production_db_readonly"], "blocked")
        self.assertEqual(report["decision_display_consistency"]["strategy_vs_summary"], "blocked")
        self.assertEqual(report["report_cross_section_consistency"]["actions"], "blocked")
        self.assertTrue(
            any("summary says BUY but report blocks 2317" in reason for reason in report["blocked_reasons"])
        )

    def test_readonly_smoke_cli_outputs_full_integrity_json_with_mocked_report(self):
        client = MultiTableEvidenceClient({
            "market_theme_confirmed_evidence": [
                confirmed_row(trade_date="2026-05-29"),
            ],
        })
        messages = [
            "【持倉標的】\n\n無持倉",
            "【未持倉標的】\n\n【2317】👀 等冷卻｜不可買",
            "\n".join([
                "【05/29 盤中｜v20.4.12】",
                "🧭 今日結論：交易執行：無新增下單；未持倉 1 檔僅追蹤",
                "✅ 今日盤中交易執行",
                "未持倉漏斗（非執行）：",
                "可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 0",
            ]),
        ]
        output = io.StringIO()

        with patch.object(
            smoke_market_theme_evidence_readonly,
            "_build_readonly_client",
            return_value=client,
        ), patch.object(
            generator,
            "generate_report",
            return_value=(messages, None),
        ), redirect_stdout(output):
            exit_code = smoke_market_theme_evidence_readonly.main([
                "--trade-date",
                "2026-05-29",
                "--full-integrity-check-json",
            ])

        self.assertEqual(exit_code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["mode"], "may-data-strategy-report-full-integrity-check")
        self.assertEqual(report["fresh_runner_dry_run"]["report_generated"], "passed")
        self.assertEqual(report["report_cross_section_consistency"]["version"], "passed")

    def test_readonly_smoke_cli_outputs_auxiliary_render_artifact(self):
        client = MultiTableEvidenceClient({
            "market_theme_confirmed_evidence": [
                confirmed_row(trade_date="2026-05-29"),
                confirmed_row(trade_date="2026-05-28"),
                confirmed_row(trade_date="2026-05-27"),
            ],
        })
        output = io.StringIO()

        with patch.object(
            smoke_market_theme_evidence_readonly,
            "_build_readonly_client",
            return_value=client,
        ), redirect_stdout(output):
            exit_code = smoke_market_theme_evidence_readonly.main([
                "--trade-date",
                "2026-05-29",
                "--auxiliary-render-artifact-json",
            ])

        self.assertEqual(exit_code, 0)
        artifact = json.loads(output.getvalue())
        self.assertEqual(
            artifact["artifact_type"],
            "production_readonly_market_theme_auxiliary_render",
        )
        self.assertFalse(artifact["schema_change"])
        self.assertFalse(artifact["data_write"])
        self.assertFalse(artifact["live_telegram"])
        self.assertFalse(artifact["credential_values_included"])
        self.assertEqual(artifact["generator_version"], "v20.4.12")
        self.assertEqual(artifact["load_status"], "confirmed")
        self.assertEqual(artifact["loaded_rows_count"], 1)
        self.assertTrue(artifact["provider_confirmed"])
        self.assertTrue(artifact["checks"]["has_auxiliary_block"])
        self.assertTrue(artifact["checks"]["has_lookback_range"])
        self.assertTrue(artifact["checks"]["has_support_streak_days"])
        self.assertTrue(artifact["checks"]["has_no_buy_warning"])
        self.assertFalse(artifact["checks"]["forbidden_buy_terms_present"])
        rendered = "\n".join(artifact["rendered_lines"])
        self.assertIn("市場/題材輔助", rendered)
        self.assertIn("觀察區間", rendered)
        self.assertIn("連續支持", rendered)
        self.assertIn("不等於個股買點", rendered)
        self.assertIn("不追高", rendered)

    def test_readonly_smoke_cli_full_integrity_json_captures_report_stdout_warning(self):
        messages = [
            "【持倉標的】\n\n無持倉",
            "【未持倉標的】\n\n【2317】👀 等冷卻｜不可買",
            "\n".join([
                "【05/29 盤中｜v20.4.12】",
                "🧭 今日結論：交易執行：無新增下單；未持倉 1 檔僅追蹤",
                "✅ 今日盤中交易執行",
                "未持倉漏斗（非執行）：",
                "可買 0｜可準備 0（不可買）｜僅追蹤 1｜淘汰 0",
            ]),
        ]

        def noisy_generate_report(dry_run=False):
            print("⚠ 持倉DB讀取失敗，持倉 / 今日交易狀態不可信")
            return (messages, None)

        output = io.StringIO()

        with patch.object(
            smoke_market_theme_evidence_readonly,
            "_build_readonly_client",
            return_value=None,
        ), patch.object(
            generator,
            "generate_report",
            side_effect=noisy_generate_report,
        ), redirect_stdout(output):
            exit_code = smoke_market_theme_evidence_readonly.main([
                "--trade-date",
                "2026-05-29",
                "--full-integrity-check-json",
            ])

        self.assertEqual(exit_code, 2)
        stdout = output.getvalue()
        report = json.loads(stdout)
        self.assertNotIn("持倉DB讀取失敗", stdout.splitlines()[0])
        self.assertEqual(report["fresh_runner_dry_run"]["report_generated"], "passed")
        self.assertEqual(report["source_integrity"]["production_db_readonly"], "blocked")
        self.assertEqual(report["source_integrity"]["may_data_available"], "blocked")
        self.assertEqual(report["source_integrity"]["market_theme_source_of_truth"], "blocked")
        self.assertTrue(
            any("持倉DB讀取失敗" in item["message"] for item in report["diagnostics"])
        )
        self.assertTrue(
            any("dry-run report generator wrote stdout warning" in reason for reason in report["blocked_reasons"])
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
                "市場/題材輔助：資料不足",
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
                "市場/題材輔助：資料不足",
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

        with patch.object(
            generator,
            "load_confirmed_market_theme_evidence",
            return_value={
                "status": "missing-source",
                "confirmed": False,
                "reason": "test isolated from production DB",
                "rows": [],
            },
        ):
            messages = generator.formatTelegramMessages(
                {"台積電": payload},
                "FULL DETAIL",
                None,
                None,
                "AI/電子供應鏈仍偏多",
                datetime(2026, 5, 28),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        self.assertIn("【05/28 盤中｜v20.4.12】", summary)
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

        summary = summary_message(messages)
        self.assertIn("證據：production confirmed，市場/題材支持成立。", summary)
        self.assertIn("限制：題材只能追蹤，不代表可買", summary)
        self.assertIn("來源：watchlist_breadth same_trade_date; sector_index same_trade_date", summary)
        self.assertIn("市場/題材輔助：資料不足", summary)
        self.assertIn("🧭 新倉：無有效進場。", summary)
        self.assertIn("未持倉 1 檔僅追蹤", summary)
        self.assertLess(
            summary.index("🧭 新倉：無有效進場。"),
            summary.index("證據：production confirmed，市場/題材支持成立。"),
        )
        self.assertNotIn("今日可買：台積電", summary)
        self.assertNotIn("台積電｜可買", summary)

    def test_confirmed_trend_auxiliary_layer_does_not_create_buy_signal(self):
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
        loaded = load_confirmed_market_theme_evidence(
            client=EvidenceClient([
                confirmed_row(trade_date="2026-05-29", sector_theme_key="AI infrastructure"),
                confirmed_row(trade_date="2026-05-28", sector_theme_key="AI infrastructure"),
                confirmed_row(trade_date="2026-05-27", sector_theme_key="AI infrastructure"),
            ]),
            trade_date="2026-05-29",
        )

        with patch.object(
            generator,
            "load_confirmed_market_theme_evidence",
            return_value=loaded,
        ):
            messages = generator.formatTelegramMessages(
                {"台積電": payload},
                "FULL DETAIL",
                None,
                None,
                {"trade_date": "2026-05-29", "as_of": "2026-05-29"},
                datetime(2026, 5, 29),
                report_phase="盤中",
            )

        summary = summary_message(messages)
        auxiliary = summary[summary.index("市場/題材輔助"):]
        self.assertIn("【05/29 盤中｜v20.4.12】", summary)
        self.assertIn("- 題材：AI infrastructure", summary)
        self.assertIn("背景：延續順風；觀察區間 2026-05-27 至 2026-05-29；連續支持 3 天。", summary)
        self.assertIn("不等於個股買點", summary)
        self.assertIn("🧭 新倉：無有效進場。", summary)
        self.assertIn("可買 0", summary)
        self.assertNotIn("建議買入", auxiliary)
        self.assertNotIn("立即進場", auxiliary)
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

        summary = summary_message(messages)
        self.assertIn("市場 / 題材證據：weak", summary)
        self.assertIn("限制：內部題材證據未達確認，仍依量價 / 風控判斷", summary)
        self.assertNotIn("市場 / 題材證據：confirmed", summary)
        self.assertNotIn("🧭 主線：AI / 電子供應鏈仍偏多。", summary)


if __name__ == "__main__":
    unittest.main()
