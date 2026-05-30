import unittest

from scripts.backfill_market_theme_sources import (
    MARKET_INDEX,
    build_confirmed_rows,
    build_index_rows,
    build_market_theme_history_backfill_report,
    build_market_breadth,
    build_member_rows,
    build_source_payloads,
    upsert_source_payloads,
)


class WriteTable:
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def upsert(self, rows, on_conflict=None):
        self.client.calls.append(
            {"table": self.name, "rows": rows, "on_conflict": on_conflict}
        )
        return self

    def execute(self):
        return type("Result", (), {"data": []})()


class WriteClient:
    def __init__(self):
        self.calls = []

    def table(self, name):
        return WriteTable(self, name)


class MarketThemeSourceBackfillTest(unittest.TestCase):
    def test_build_index_rows_uses_only_official_twse_index_names(self):
        rows = build_index_rows(
            [
                {
                    "日期": "1150529",
                    "指數": "發行量加權股價指數",
                    "收盤指數": "44,732.94",
                    "漲跌": "+",
                    "漲跌點數": "1,096.50",
                    "漲跌百分比": "2.51",
                },
                {
                    "日期": "1150529",
                    "指數": "半導體類指數",
                    "收盤指數": "1,530.59",
                    "漲跌": "+",
                    "漲跌點數": "32.22",
                    "漲跌百分比": "2.15",
                },
                {
                    "日期": "1150529",
                    "指數": "非本輪來源",
                    "收盤指數": "1",
                    "漲跌百分比": "1",
                },
            ],
            trade_date="2026-05-29",
            as_of="2026-05-29T06:00:00+00:00",
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["index_scope"], "market")
        self.assertIsNone(rows[0]["sector_theme_key"])
        self.assertEqual(rows[1]["index_scope"], "sector_theme")
        self.assertEqual(rows[1]["sector_theme_key"], "twse_semiconductor")
        self.assertEqual(rows[1]["source_family"], "market_data")
        self.assertEqual(rows[1]["index_method"], "external_index")

    def test_build_market_breadth_uses_official_twse_breadth(self):
        breadth = build_market_breadth(
            [
                {
                    "出表日期": "1150529",
                    "類型": "股票",
                    "上漲": "805",
                    "下跌": "202",
                    "持平": "69",
                    "漲停": "42",
                    "跌停": "0",
                }
            ],
            trade_date="2026-05-29",
        )

        self.assertEqual(breadth["denominator"], 1076)
        self.assertEqual(breadth["up_count"], 805)
        self.assertEqual(breadth["up_ratio"], round(805 / 1076, 4))

    def test_build_member_rows_uses_twse_company_profile_industry(self):
        rows = build_member_rows(
            [
                {"公司代號": "2303", "公司簡稱": "聯電", "產業別": "24"},
                {"公司代號": "3231", "公司簡稱": "緯創", "產業別": "25"},
                {"公司代號": "9999", "公司簡稱": "非觀察", "產業別": "24"},
            ],
            watchlist_codes={"2303", "3231"},
            as_of="2026-05-29T06:00:00+00:00",
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual({row["source_family"] for row in rows}, {"market_data"})
        self.assertEqual(
            {row["sector_theme_key"] for row in rows},
            {"twse_semiconductor", "twse_computer_peripheral"},
        )

    def test_build_confirmed_rows_from_official_index_and_breadth(self):
        index_rows = build_index_rows(
            [
                {"日期": "1150529", "指數": "發行量加權股價指數", "收盤指數": "44732.94", "漲跌百分比": "2.51"},
                {"日期": "1150529", "指數": "電子工業類指數", "收盤指數": "2928.42", "漲跌百分比": "2.62"},
            ],
            trade_date="2026-05-29",
            as_of="2026-05-29T06:00:00+00:00",
        )
        breadth = build_market_breadth(
            [{"出表日期": "1150529", "類型": "股票", "上漲": "805", "下跌": "202", "持平": "69"}],
            trade_date="2026-05-29",
        )

        confirmed = build_confirmed_rows(index_rows, breadth, as_of="2026-05-29T06:00:00+00:00")

        self.assertEqual(len(confirmed), 1)
        row = confirmed[0]
        self.assertEqual(row["market_index"], MARKET_INDEX)
        self.assertEqual(row["source_family"], "market_data")
        self.assertEqual(row["source_name"], "twse_openapi_mi_index")
        self.assertEqual(row["freshness"], "fresh")
        self.assertEqual(row["sector_theme_key"], "twse_electronics")
        self.assertEqual(row["metadata"]["source_quality"], "official_twse_openapi")
        self.assertTrue(row["metadata"]["external_market_index"])

    def test_build_source_payloads_blocks_without_official_index_rows(self):
        payloads = build_source_payloads([], [], [], trade_date="2026-05-29")

        self.assertEqual(payloads["status"], "blocked")
        self.assertEqual(payloads["index_rows"], [])
        self.assertEqual(payloads["confirmed_rows"], [])

    def test_history_backfill_report_skips_latest_membership_and_source_table_writes(self):
        payloads = build_source_payloads(
            [
                {"日期": "1150529", "指數": "發行量加權股價指數", "收盤指數": "44732.94", "漲跌百分比": "2.51"},
                {"日期": "1150529", "指數": "電子工業類指數", "收盤指數": "2928.42", "漲跌百分比": "2.62"},
            ],
            [{"出表日期": "1150529", "類型": "股票", "上漲": "805", "下跌": "202", "持平": "69"}],
            [{"公司代號": "2303", "公司簡稱": "聯電", "產業別": "24"}],
            trade_date="2026-05-29",
            as_of="2026-05-29T06:00:00+00:00",
        )

        report = build_market_theme_history_backfill_report(payloads)

        self.assertEqual(report["mode"], "market-theme-history-backfill")
        self.assertEqual(report["date_range"], {"start": "2026-05-01", "end": "2026-05-29"})
        self.assertEqual(report["write_execution"], "dry-run")
        self.assertFalse(report["live_telegram"])
        self.assertFalse(report["schema_change"])
        confirmed, index_table, member_table = report["tables"]
        self.assertEqual(confirmed["table"], "market_theme_confirmed_evidence")
        self.assertEqual(confirmed["historical_source_status"], "partial")
        self.assertEqual(confirmed["status"], "ready")
        self.assertEqual(confirmed["candidate_rows"], 1)
        self.assertEqual(confirmed["validated_rows"], 1)
        self.assertEqual(confirmed["coverage"]["first_trade_date"], "2026-05-29")
        self.assertEqual(index_table["historical_source_status"], "not-consumed")
        self.assertEqual(index_table["status"], "skipped")
        self.assertEqual(index_table["written_rows"], 0)
        self.assertEqual(member_table["table"], "sector_theme_members")
        self.assertEqual(member_table["historical_source_status"], "missing")
        self.assertEqual(member_table["status"], "blocked")
        self.assertIn("only latest company profile membership", member_table["blocked_reasons"][0])
        self.assertEqual(
            report["daily_price_signal_snapshot_rewrite"],
            "forbidden_as_primary_result",
        )
        self.assertFalse(
            report["strategy_consumption_check"]["uses_market_theme_confirmed_evidence_history"]
        )
        self.assertFalse(report["strategy_consumption_check"]["uses_only_daily_signal_snapshot"])

    def test_history_report_blocks_latest_source_outside_requested_may_range(self):
        payloads = build_source_payloads(
            [
                {"日期": "1150601", "指數": "發行量加權股價指數", "收盤指數": "44732.94", "漲跌百分比": "2.51"},
                {"日期": "1150601", "指數": "電子工業類指數", "收盤指數": "2928.42", "漲跌百分比": "2.62"},
            ],
            [{"出表日期": "1150601", "類型": "股票", "上漲": "805", "下跌": "202", "持平": "69"}],
            [],
            trade_date="2026-06-01",
        )

        report = build_market_theme_history_backfill_report(payloads)

        confirmed = report["tables"][0]
        self.assertEqual(confirmed["status"], "blocked")
        self.assertEqual(confirmed["validated_rows"], 0)
        self.assertIn("source date outside requested May range", confirmed["blocked_reasons"])

    def test_history_report_rejects_forbidden_daily_signal_snapshot_payload(self):
        payloads = build_source_payloads(
            [
                {"日期": "1150529", "指數": "發行量加權股價指數", "收盤指數": "44732.94", "漲跌百分比": "2.51"},
                {"日期": "1150529", "指數": "電子工業類指數", "收盤指數": "2928.42", "漲跌百分比": "2.62"},
            ],
            [{"出表日期": "1150529", "類型": "股票", "上漲": "805", "下跌": "202", "持平": "69"}],
            [],
            trade_date="2026-05-29",
        )
        payloads["confirmed_rows"][0]["source_family"] = "daily_signal_snapshot"
        payloads["confirmed_rows"][0]["source_name"] = "forbidden_snapshot"
        payloads["confirmed_rows"][0]["lineage"] = {
            "source_tables": ["daily_signal_snapshot"]
        }

        report = build_market_theme_history_backfill_report(payloads)

        confirmed = report["tables"][0]
        self.assertEqual(confirmed["candidate_rows"], 1)
        self.assertEqual(confirmed["validated_rows"], 0)
        self.assertEqual(confirmed["skipped_rows"], 1)
        self.assertEqual(confirmed["pollution_guard"], "blocked")
        self.assertEqual(confirmed["status"], "blocked")
        self.assertIn("forbidden source_family", confirmed["blocked_reasons"][0])
        self.assertIn("forbidden lineage source_tables", confirmed["blocked_reasons"][0])
        client = WriteClient()
        with self.assertRaisesRegex(ValueError, "forbidden source_family"):
            upsert_source_payloads(client, payloads)
        self.assertEqual(client.calls, [])

    def test_history_report_rejects_missing_required_confirmed_fields(self):
        payloads = build_source_payloads(
            [
                {"日期": "1150529", "指數": "發行量加權股價指數", "收盤指數": "44732.94", "漲跌百分比": "2.51"},
                {"日期": "1150529", "指數": "電子工業類指數", "收盤指數": "2928.42", "漲跌百分比": "2.62"},
            ],
            [{"出表日期": "1150529", "類型": "股票", "上漲": "805", "下跌": "202", "持平": "69"}],
            [],
            trade_date="2026-05-29",
        )
        payloads["confirmed_rows"][0].pop("as_of")

        report = build_market_theme_history_backfill_report(payloads)

        confirmed = report["tables"][0]
        self.assertEqual(confirmed["validated_rows"], 0)
        self.assertEqual(confirmed["pollution_guard"], "blocked")
        self.assertEqual(confirmed["status"], "blocked")
        self.assertIn("required fields missing: as_of", confirmed["blocked_reasons"])

    def test_execute_path_upserts_only_confirmed_evidence_rows(self):
        payloads = build_source_payloads(
            [
                {"日期": "1150529", "指數": "發行量加權股價指數", "收盤指數": "44732.94", "漲跌百分比": "2.51"},
                {"日期": "1150529", "指數": "電子工業類指數", "收盤指數": "2928.42", "漲跌百分比": "2.62"},
            ],
            [{"出表日期": "1150529", "類型": "股票", "上漲": "805", "下跌": "202", "持平": "69"}],
            [{"公司代號": "2303", "公司簡稱": "聯電", "產業別": "24"}],
            trade_date="2026-05-29",
        )
        client = WriteClient()

        counts = upsert_source_payloads(client, payloads)

        self.assertEqual(counts, {"market_theme_confirmed_evidence": 1})
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0]["table"], "market_theme_confirmed_evidence")
        self.assertNotIn("sector_theme_members", [call["table"] for call in client.calls])
        self.assertNotIn("market_theme_index_daily_bars", [call["table"] for call in client.calls])

    def test_executed_report_uses_read_after_write_trend_metrics(self):
        payloads = build_source_payloads(
            [
                {"日期": "1150529", "指數": "發行量加權股價指數", "收盤指數": "44732.94", "漲跌百分比": "2.51"},
                {"日期": "1150529", "指數": "電子工業類指數", "收盤指數": "2928.42", "漲跌百分比": "2.62"},
            ],
            [{"出表日期": "1150529", "類型": "股票", "上漲": "805", "下跌": "202", "持平": "69"}],
            [],
            trade_date="2026-05-29",
        )

        report = build_market_theme_history_backfill_report(
            payloads,
            write_execution="executed",
            written_confirmed_rows=1,
            read_after_write_result={
                "confirmed": True,
                "evidence_trend": {
                    "observed_days": 3,
                    "recent_supporting_days": 2,
                    "support_streak_days": 2,
                },
            },
        )

        confirmed = report["tables"][0]
        self.assertEqual(confirmed["status"], "executed")
        self.assertEqual(confirmed["read_after_write"], "passed")
        self.assertTrue(
            report["strategy_consumption_check"]["uses_market_theme_confirmed_evidence_history"]
        )
        self.assertFalse(report["strategy_consumption_check"]["uses_only_daily_signal_snapshot"])
        self.assertEqual(report["strategy_consumption_check"]["observed_days"], 3)


if __name__ == "__main__":
    unittest.main()
