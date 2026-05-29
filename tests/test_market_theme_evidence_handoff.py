import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from services.market_theme_evidence_store import (
    build_market_theme_evidence_handoff,
    build_market_theme_evidence_readonly_smoke,
    validate_market_theme_evidence_ingestion_payload,
)


def handoff_payload(**overrides):
    payload = {
        "market_index": "TAIEX",
        "sector_theme_key": "semiconductor",
        "trade_date": "2026-05-29",
        "as_of": "2026-05-29T13:40:00+08:00",
        "freshness": "fresh",
        "evidence_status": "confirmed",
        "support_level": "supporting",
        "evidence_value": {"market": "supportive"},
        "watchlist_breadth": {"supportive": 7, "tracked": 12},
        "source_family": "market_data",
        "source_name": "owner_reviewed_market_theme_handoff",
        "lineage": {"source": "manual_owner_handoff", "rule_version": "v20.4.3"},
        "metadata": {"reviewed_by": "owner"},
        "notes": "manual non-live handoff",
    }
    payload.update(overrides)
    return payload


class MarketThemeEvidenceHandoffTest(unittest.TestCase):
    def test_handoff_builder_generates_manual_sql_without_live_write(self):
        handoff = build_market_theme_evidence_handoff([handoff_payload()])

        self.assertEqual(handoff["status"], "ready")
        self.assertFalse(handoff["confirmed"])
        self.assertTrue(handoff["handoff_ready"])
        self.assertFalse(handoff["live_write"])
        self.assertEqual(handoff["target_table"], "public.market_theme_confirmed_evidence")
        self.assertEqual(handoff["rows"][0]["source_family"], "market_data")
        self.assertIn(
            "insert into public.market_theme_confirmed_evidence",
            handoff["sql"],
        )
        self.assertIn("on conflict", handoff["sql"])
        self.assertIn("Manual review/execution only", handoff["sql"])

    def test_handoff_builder_fails_closed_for_fake_or_non_confirming_sources(self):
        bad_payloads = [
            handoff_payload(source_family="cache"),
            handoff_payload(source_family="worktree"),
            handoff_payload(source_family="runtime_diagnostic"),
            handoff_payload(source_family="local"),
            handoff_payload(source_family="local_only_state"),
            handoff_payload(source_family="test_fixture"),
            handoff_payload(source_family="report_derived"),
            handoff_payload(source_family="synthetic"),
            handoff_payload(source_family="watchlist"),
            handoff_payload(source_family="theme_classifier"),
            handoff_payload(source_family="unknown_provider"),
            handoff_payload(evidence_status=""),
            handoff_payload(support_level="strong"),
            handoff_payload(support_level="weak"),
            handoff_payload(evidence_status="rejected"),
            handoff_payload(freshness="stale"),
            handoff_payload(evidence_value=None),
            handoff_payload(watchlist_breadth=[]),
        ]

        for payload in bad_payloads:
            with self.subTest(payload=payload):
                handoff = build_market_theme_evidence_handoff([payload])
                self.assertEqual(handoff["status"], "insufficient-data")
                self.assertFalse(handoff["confirmed"])
                self.assertFalse(handoff["live_write"])
                self.assertEqual(handoff["rows"], [])
                self.assertEqual(handoff["sql"], "")

    def test_raw_sql_renderer_fails_closed_for_invalid_rows(self):
        invalid_row = handoff_payload(source_family="runtime_diagnostic")
        handoff = build_market_theme_evidence_handoff([invalid_row])

        self.assertEqual(handoff["sql"], "")
        from services.market_theme_evidence_store import render_market_theme_evidence_handoff_sql

        self.assertEqual(render_market_theme_evidence_handoff_sql([invalid_row]), "")
        self.assertEqual(render_market_theme_evidence_handoff_sql([None]), "")
        self.assertEqual(render_market_theme_evidence_handoff_sql([]), "")
        self.assertEqual(render_market_theme_evidence_handoff_sql(None), "")

    def test_handoff_builder_fails_closed_without_valid_payload_rows(self):
        for payloads in ([], [None], ["runtime text"]):
            with self.subTest(payloads=payloads):
                handoff = build_market_theme_evidence_handoff(payloads)
                self.assertNotEqual(handoff["status"], "ready")
                self.assertFalse(handoff["confirmed"])
                self.assertFalse(handoff["handoff_ready"])
                self.assertFalse(handoff["live_write"])
                self.assertEqual(handoff["target_table"], "public.market_theme_confirmed_evidence")
                self.assertEqual(handoff["rows"], [])
                self.assertEqual(handoff["sql"], "")

    def test_ingestion_payload_validation_renders_sql_only_after_valid_dry_run(self):
        valid = validate_market_theme_evidence_ingestion_payload(
            [handoff_payload()],
            include_sql=True,
        )

        self.assertTrue(valid["valid"])
        self.assertTrue(valid["may_render_manual_sql"])
        self.assertFalse(valid["live_write"])
        self.assertEqual(valid["row_count"], 1)
        self.assertTrue(valid["sql_rendered"])
        self.assertIn("manual_sql", valid)

        invalid = validate_market_theme_evidence_ingestion_payload(
            [handoff_payload(source_family="runtime_diagnostic")],
            include_sql=True,
        )

        self.assertFalse(invalid["valid"])
        self.assertFalse(invalid["may_render_manual_sql"])
        self.assertFalse(invalid["live_write"])
        self.assertEqual(invalid["row_count"], 0)
        self.assertFalse(invalid["sql_rendered"])
        self.assertNotIn("manual_sql", invalid)

    def test_ingestion_cli_fails_closed_without_sql_for_fake_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "payload.json"
            path.write_text(
                json.dumps([handoff_payload(source_family="report_derived")]),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/validate_market_theme_evidence_ingestion.py",
                    "--input",
                    str(path),
                    "--include-sql",
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 2)
        output = json.loads(completed.stdout)
        self.assertFalse(output["valid"])
        self.assertFalse(output["may_render_manual_sql"])
        self.assertFalse(output["live_write"])
        self.assertNotIn("manual_sql", output)

    def test_readonly_smoke_matrix_fails_closed_except_valid_confirmed_rows(self):
        cases = [
            (
                {"status": "missing-source", "confirmed": False, "reason": "production DB config missing", "rows": []},
                "missing",
                "skipped",
                "fail-closed",
                False,
            ),
            (
                {"status": "source-error", "confirmed": False, "reason": "permission denied for table", "rows": []},
                "present",
                "permission-denied",
                "fail-closed",
                False,
            ),
            (
                {"status": "absent", "confirmed": False, "reason": "production table returned no rows", "rows": []},
                "present",
                "ok",
                "fail-closed",
                False,
            ),
            (
                {"status": "insufficient-data", "confirmed": False, "reason": "stale", "rows": [handoff_payload(freshness="stale")]},
                "present",
                "ok",
                "fail-closed",
                False,
            ),
            (
                {"status": "source-error", "confirmed": False, "reason": "unexpected support_level", "rows": [handoff_payload(support_level="strong")]},
                "present",
                "error",
                "fail-closed",
                False,
            ),
            (
                {"status": "confirmed", "confirmed": True, "reason": "", "rows": [handoff_payload(source_family="production_db")]},
                "present",
                "ok",
                "ok",
                True,
            ),
        ]

        for load_result, env, table_read, status, telegram_confirmed in cases:
            with self.subTest(load_result=load_result):
                smoke = build_market_theme_evidence_readonly_smoke(load_result)
                self.assertEqual(smoke["mode"], "read-only")
                self.assertEqual(smoke["write"], "disabled")
                self.assertEqual(smoke["env"], env)
                self.assertEqual(smoke["table_read"], table_read)
                self.assertEqual(smoke["status"], status)
                self.assertEqual(smoke["telegram_confirmed"], telegram_confirmed)


if __name__ == "__main__":
    unittest.main()
