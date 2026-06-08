import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import run_phase3_evidence_automation as phase3


class Phase3EvidenceAutomationTest(unittest.TestCase):
    def _freshness_client(self, rows_by_table):
        class Result:
            def __init__(self, rows):
                self.data = rows
                self.count = len(rows)

        class Table:
            def __init__(self, rows):
                self.rows = rows
                self.filters = {}

            def select(self, fields, count=None):
                return self

            def eq(self, field, value):
                self.filters[field] = value
                return self

            def limit(self, value):
                return self

            def execute(self):
                trade_date = self.filters.get("trade_date")
                rows = [
                    row for row in self.rows
                    if not trade_date or row.get("trade_date") == trade_date
                ]
                return Result(rows)

        class Client:
            def table(self, name):
                return Table(rows_by_table.get(name, []))

        return Client()

    def _confirmed_row(self, trade_date, sector_theme_key="twse_electronics"):
        return {
            "trade_date": trade_date,
            "market_index": "TAIEX",
            "sector_theme_key": sector_theme_key,
            "source_family": "market_data",
            "source_name": "twse_openapi_mi_index",
            "freshness": "fresh",
            "evidence_status": "confirmed",
            "support_level": "supporting",
        }

    def _confirmed_rows(self, trade_date):
        return [
            self._confirmed_row(trade_date, sector_theme_key)
            for sector_theme_key in phase3.EXPECTED_CONFIRMED_SECTOR_THEMES
        ]

    def _index_rows(self, trade_date):
        return [
            {
                "trade_date": trade_date,
                "index_scope": "market",
                "market_index": "TAIEX",
                "sector_theme_key": None,
                "source_family": "market_data",
                "source_name": "twse_openapi_mi_index",
                "close": 21000,
            },
            {
                "trade_date": trade_date,
                "index_scope": "sector_theme",
                "market_index": "TAIEX",
                "sector_theme_key": "twse_electronics",
                "source_family": "market_data",
                "source_name": "twse_openapi_mi_index",
                "close": 1200,
            },
        ]

    def test_time_guard_requires_confirmed_trading_day_after_close(self):
        saturday = phase3.parse_now("2026-06-06T13:25:00+08:00")
        before_close = phase3.parse_now("2026-06-02T12:30:00+08:00")
        after_close = phase3.parse_now("2026-06-02T13:25:00+08:00")

        self.assertEqual(phase3.should_run_evidence_writes(saturday), (False, "non_trading_day"))
        self.assertEqual(
            phase3.should_run_evidence_writes(before_close),
            (False, "before_after_close_window"),
        )
        self.assertEqual(
            phase3.should_run_evidence_writes(
                after_close,
                trading_day_checker=lambda trade_date: {
                    "confirmed": True,
                    "reason": "confirmed-trading-day",
                },
            ),
            (True, "after_close_trading_day"),
        )

    def test_weekday_holiday_or_unknown_calendar_skips_without_write_confirmation(self):
        holiday = phase3.parse_now("2026-02-16T13:25:00+08:00")
        unknown = phase3.parse_now("2026-06-02T13:25:00+08:00")

        self.assertEqual(
            phase3.should_run_evidence_writes(
                holiday,
                trading_day_checker=lambda trade_date: {
                    "confirmed": False,
                    "reason": "not-confirmed-trading-day",
                    "source_status": "missing-source",
                },
            ),
            (False, "not-confirmed-trading-day"),
        )
        self.assertEqual(
            phase3.should_run_evidence_writes(
                unknown,
                trading_day_checker=lambda trade_date: {
                    "confirmed": False,
                    "reason": "not-confirmed-trading-day",
                    "source_status": "source-error",
                },
            ),
            (False, "not-confirmed-trading-day"),
        )

    def test_confirm_trading_day_uses_official_twse_index_rows(self):
        status = phase3.confirm_trading_day(
            "2026-06-02",
            fetch_index_rows=lambda trade_date: [
                {
                    "日期": "2026-06-02",
                    "指數": "發行量加權股價指數",
                    "收盤指數": "21,000.00",
                    "漲跌百分比": "1.23",
                }
            ],
        )
        missing = phase3.confirm_trading_day("2026-02-16", fetch_index_rows=lambda trade_date: [])

        def source_error(_trade_date):
            raise RuntimeError("TWSE unavailable")

        unknown = phase3.confirm_trading_day("2026-06-02", fetch_index_rows=source_error)

        self.assertTrue(status["confirmed"])
        self.assertEqual(status["source"], "twse_official_mi_index")
        self.assertFalse(missing["confirmed"])
        self.assertEqual(missing["reason"], "not-confirmed-trading-day")
        self.assertEqual(missing["source_status"], "missing-source")
        self.assertFalse(unknown["confirmed"])
        self.assertEqual(unknown["reason"], "not-confirmed-trading-day")
        self.assertEqual(unknown["source_status"], "source-error")

    def test_main_skip_logs_both_sources_without_write(self):
        out = io.StringIO()
        with redirect_stdout(out):
            returncode = phase3.main(["--now", "2026-06-02T12:30:00+08:00"])

        self.assertEqual(returncode, 0)
        output = out.getvalue()
        self.assertIn(
            "EVIDENCE_WRITE_SKIPPED source=daily_signal_snapshot trading_day=2026-06-02 reason=before_after_close_window",
            output,
        )
        self.assertIn(
            "EVIDENCE_WRITE_SKIPPED source=market_theme_confirmed_evidence trading_day=2026-06-02 reason=before_after_close_window",
            output,
        )

    def test_main_weekday_without_confirmed_calendar_logs_not_confirmed_skip(self):
        out = io.StringIO()
        with patch.object(
            phase3,
            "confirm_trading_day",
            return_value={"confirmed": False, "reason": "not-confirmed-trading-day"},
        ), redirect_stdout(out):
            returncode = phase3.main(["--now", "2026-02-16T13:25:00+08:00"])

        self.assertEqual(returncode, 0)
        output = out.getvalue()
        self.assertIn(
            "EVIDENCE_WRITE_SKIPPED source=daily_signal_snapshot trading_day=2026-02-16 reason=not-confirmed-trading-day",
            output,
        )
        self.assertIn(
            "EVIDENCE_WRITE_SKIPPED source=market_theme_confirmed_evidence trading_day=2026-02-16 reason=not-confirmed-trading-day",
            output,
        )

    def test_main_confirmed_trading_day_after_close_runs_both_writes(self):
        calls = []

        def fake_daily(trading_day):
            calls.append(("daily", trading_day))
            return 0

        def fake_market(trading_day, payload_path=None):
            calls.append(("market", trading_day, payload_path))
            return 0

        out = io.StringIO()
        with patch.object(
            phase3,
            "confirm_trading_day",
            return_value={"confirmed": True, "reason": "confirmed-trading-day"},
        ), patch.object(
            phase3,
            "run_daily_signal_snapshot",
            fake_daily,
        ), patch.object(
            phase3,
            "run_market_theme_confirmed_evidence",
            fake_market,
        ), redirect_stdout(out):
            returncode = phase3.main(["--now", "2026-06-02T13:25:00+08:00"])

        self.assertEqual(returncode, 0)
        self.assertEqual(calls, [("daily", "2026-06-02"), ("market", "2026-06-02", None)])

    def test_stale_alert_counts_confirmed_trading_days_only(self):
        alerts = phase3.build_stale_alerts(
            {
                "market_theme_confirmed_evidence": [
                    {"trade_date": "2026-06-01", "status": "stale", "trading_day_confirmed": True},
                    {"trade_date": "2026-06-02", "status": "unavailable", "trading_day_confirmed": True},
                ],
                "daily_signal_snapshot": [
                    {"trade_date": "2026-06-05", "status": "stale", "trading_day_confirmed": True},
                    {"trade_date": "2026-06-06", "status": "stale", "trading_day_confirmed": False},
                ],
                "unknown_calendar_source": [
                    {"trade_date": "2026-06-01", "status": "stale"},
                    {"trade_date": "2026-06-02", "status": "unavailable"},
                ],
            }
        )

        self.assertEqual(
            alerts,
            [
                {
                    "source": "market_theme_confirmed_evidence",
                    "consecutive_days": 2,
                    "status": "unavailable",
                    "action": "fail_closed",
                }
            ],
        )

    def test_stale_alert_cli_outputs_grepable_fail_closed_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"
            status_path.write_text(
                json.dumps(
                    {
                        "market_theme_confirmed_evidence": [
                            {"trade_date": "2026-06-01", "status": "stale", "trading_day_confirmed": True},
                            {"trade_date": "2026-06-02", "status": "unavailable", "trading_day_confirmed": True},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            out = io.StringIO()
            with redirect_stdout(out):
                returncode = phase3.main(
                    [
                        "--now",
                        "2026-06-06T13:25:00+08:00",
                        "--stale-status-json",
                        str(status_path),
                    ]
                )

        self.assertEqual(returncode, 0)
        self.assertIn(
            "EVIDENCE_STALE_ALERT source=market_theme_confirmed_evidence consecutive_days=2 status=unavailable action=fail_closed",
            out.getvalue(),
        )

    def test_market_theme_write_uses_approved_cli_and_preserves_failure(self):
        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=2, stdout='{"read_after_write":"fail"}\n', stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "payload.json"
            payload_path.write_text(
                json.dumps([
                    {
                        "trade_date": "2026-06-02",
                        "market_index": "TAIEX",
                        "sector_theme_key": "market",
                    }
                ]),
                encoding="utf-8",
            )
            out = io.StringIO()
            with redirect_stdout(out):
                returncode = phase3.run_market_theme_confirmed_evidence(
                    "2026-06-02",
                    payload_path=str(payload_path),
                    runner=fake_runner,
                )

        self.assertEqual(returncode, 2)
        self.assertTrue(
            str(calls[0][1]).replace("\\", "/").endswith("scripts/write_market_theme_confirmed_evidence.py")
        )
        self.assertIn("--execute", calls[0])
        self.assertIn(
            "EVIDENCE_WRITE_FAILED source=market_theme_confirmed_evidence trading_day=2026-06-02 action=fail_closed",
            out.getvalue(),
        )

    def test_main_requires_market_theme_payload_when_gate_enabled(self):
        out = io.StringIO()
        with patch.object(
            phase3,
            "confirm_trading_day",
            return_value={"confirmed": True, "reason": "confirmed-trading-day"},
        ), redirect_stdout(out):
            returncode = phase3.main([
                "--now",
                "2026-06-02T13:25:00+08:00",
                "--require-market-theme-payload",
            ])

        self.assertEqual(returncode, 2)
        self.assertIn(
            "EVIDENCE_WRITE_FAILED source=market_theme_confirmed_evidence trading_day=2026-06-02 reason=missing-approved-payload action=fail_closed",
            out.getvalue(),
        )

    def test_market_theme_payload_trade_date_mismatch_fails_before_write(self):
        calls = []

        def fake_runner(args, **kwargs):
            calls.append(args)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "payload.json"
            payload_path.write_text(
                json.dumps([
                    {
                        "trade_date": "2026-05-29",
                        "market_index": "TAIEX",
                        "sector_theme_key": "market",
                    }
                ]),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "trade_date mismatch"):
                phase3.run_market_theme_confirmed_evidence(
                    "2026-06-02",
                    payload_path=str(payload_path),
                    runner=fake_runner,
                )

        self.assertEqual(calls, [])

    def test_market_theme_payload_uses_twse_historical_readonly_sources(self):
        with patch(
            "scripts.backfill_market_theme_sources.fetch_twse_historical_index_rows",
            return_value=[
                {"日期": "2026-06-02", "指數": "發行量加權股價指數", "收盤指數": "21000", "漲跌百分比": "1.0"},
                {"日期": "2026-06-02", "指數": "電子工業類指數", "收盤指數": "1200", "漲跌百分比": "1.2"},
            ],
        ) as fetch_index, patch(
            "scripts.backfill_market_theme_sources.fetch_twse_historical_breadth_rows",
            return_value=[
                {"類型": "上漲(漲停)", "股票": "600(20)"},
                {"類型": "下跌(跌停)", "股票": "300(0)"},
                {"類型": "持平", "股票": "100"},
            ],
        ) as fetch_breadth, patch(
            "scripts.backfill_market_theme_sources.fetch_twse_company_profiles",
            return_value=[],
        ):
            rows = phase3._twse_confirmed_rows_payload("2026-06-02")

        self.assertEqual(fetch_index.call_args.args, ("2026-06-02",))
        self.assertEqual(fetch_breadth.call_args.args, ("2026-06-02",))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["trade_date"], "2026-06-02")
        self.assertEqual(rows[0]["source_name"], "twse_openapi_mi_index")

    def test_recent_freshness_complete_dates_skip_without_backfill(self):
        client = self._freshness_client(
            {
                "market_theme_confirmed_evidence": self._confirmed_rows("2026-06-02"),
                "market_theme_index_daily_bars": self._index_rows("2026-06-02"),
            }
        )
        calls = []
        out = io.StringIO()
        with redirect_stdout(out):
            report = phase3.run_market_theme_freshness_check(
                now=phase3.parse_now("2026-06-02T14:05:00+08:00"),
                lookback_days=1,
                client=client,
                trading_day_checker=lambda trade_date: {"confirmed": True},
                backfill_func=lambda trade_date, client=None: calls.append(trade_date),
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["results"][0]["status"], "already-complete")
        self.assertEqual(calls, [])
        self.assertIn("status=already-complete", out.getvalue())

    def test_recent_freshness_partial_confirmed_rows_do_not_skip(self):
        rows_by_table = {
            "market_theme_confirmed_evidence": [self._confirmed_row("2026-06-02")],
            "market_theme_index_daily_bars": self._index_rows("2026-06-02"),
        }
        client = self._freshness_client(rows_by_table)
        calls = []

        def backfill(trade_date, client=None):
            calls.append(trade_date)
            rows_by_table["market_theme_confirmed_evidence"] = self._confirmed_rows(trade_date)

        report = phase3.run_market_theme_freshness_check(
            now=phase3.parse_now("2026-06-02T14:05:00+08:00"),
            lookback_days=1,
            client=client,
            trading_day_checker=lambda trade_date: {"confirmed": True},
            backfill_func=backfill,
        )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(calls, ["2026-06-02"])
        self.assertEqual(report["results"][0]["status"], "backfilled-and-verified")

    def test_recent_freshness_before_safe_write_time_reads_without_backfill(self):
        client = self._freshness_client(
            {
                "market_theme_confirmed_evidence": [],
                "market_theme_index_daily_bars": [],
            }
        )
        calls = []
        out = io.StringIO()
        with redirect_stdout(out):
            report = phase3.run_market_theme_freshness_check(
                now=phase3.parse_now("2026-06-03T13:55:00+08:00"),
                lookback_days=1,
                safe_write_time="14:00",
                client=client,
                trading_day_checker=lambda trade_date: {"confirmed": True},
                backfill_func=lambda trade_date, client=None: calls.append(trade_date),
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["results"][0]["status"], "skipped-before-safe-write-time")
        self.assertEqual(calls, [])
        self.assertIn("status=skipped-before-safe-write-time", out.getvalue())

    def test_recent_freshness_after_safe_write_time_backfills_and_verifies(self):
        rows_by_table = {
            "market_theme_confirmed_evidence": [],
            "market_theme_index_daily_bars": [],
        }
        client = self._freshness_client(rows_by_table)
        calls = []

        def backfill(trade_date, client=None):
            calls.append(trade_date)
            rows_by_table["market_theme_confirmed_evidence"].extend(self._confirmed_rows(trade_date))
            rows_by_table["market_theme_index_daily_bars"].extend(self._index_rows(trade_date))

        out = io.StringIO()
        with redirect_stdout(out):
            report = phase3.run_market_theme_freshness_check(
                now=phase3.parse_now("2026-06-02T14:05:00+08:00"),
                lookback_days=1,
                safe_write_time="14:00",
                client=client,
                trading_day_checker=lambda trade_date: {"confirmed": True},
                backfill_func=backfill,
            )

        self.assertEqual(report["status"], "ok")
        self.assertEqual(calls, ["2026-06-02"])
        self.assertEqual(report["results"][0]["status"], "backfilled-and-verified")
        self.assertIn("status=backfilled-and-verified", out.getvalue())

    def test_recent_freshness_read_after_write_mismatch_fails_closed(self):
        client = self._freshness_client(
            {
                "market_theme_confirmed_evidence": [],
                "market_theme_index_daily_bars": [],
            }
        )
        out = io.StringIO()
        with redirect_stdout(out):
            report = phase3.run_market_theme_freshness_check(
                now=phase3.parse_now("2026-06-02T14:05:00+08:00"),
                lookback_days=1,
                safe_write_time="14:00",
                client=client,
                trading_day_checker=lambda trade_date: {"confirmed": True},
                backfill_func=lambda trade_date, client=None: None,
            )

        self.assertEqual(report["status"], "fail-closed")
        self.assertEqual(report["failures"][0]["status"], "read-after-write-mismatch")
        self.assertIn("stage=read-after-write", out.getvalue())


if __name__ == "__main__":
    unittest.main()
