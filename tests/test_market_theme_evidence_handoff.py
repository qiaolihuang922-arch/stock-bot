import json
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch

from services.market_theme_evidence_store import (
    build_market_theme_write_client,
    build_market_theme_evidence_handoff,
    build_market_theme_evidence_readonly_smoke,
    load_confirmed_market_theme_evidence,
    validate_market_theme_evidence_ingestion_payload,
)
from scripts.generate_evidence_approval_package import build_approval_package
from scripts.write_market_theme_confirmed_evidence import main as write_evidence_main


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


def approval_payload(**overrides):
    payload = {
        "trade_date": "2026-05-29",
        "source_family": "owner_approved_persistent",
        "source_name": "owner_approved_market_theme_review",
        "evidence_status": "confirmed",
        "freshness": "fresh",
        "rows": [
            {
                "symbol": "2330",
                "theme": "AI supply chain",
                "support_level": "supporting",
                "evidence_url": "manual-owner-approved-reference",
                "reason": "Owner approved persistent evidence",
            }
        ],
    }
    payload.update(overrides)
    return payload


class EvidenceTable:
    def __init__(self, rows):
        self.rows = rows

    def select(self, fields):
        return self

    def order(self, key, desc=False):
        return self

    def limit(self, limit):
        return self

    def execute(self):
        return type("Result", (), {"data": self.rows})()


class EvidenceClient:
    def __init__(self, rows):
        self.table_obj = EvidenceTable(rows)

    def table(self, name):
        return self.table_obj


class WriteTable:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.mode = None

    def upsert(self, rows, on_conflict=None):
        self.mode = "upsert"
        self.client.calls.append(
            {
                "table": self.name,
                "rows": rows,
                "on_conflict": on_conflict,
            }
        )
        self.client.rows = rows
        return self

    def select(self, fields):
        self.mode = "select"
        return self

    def eq(self, key, value):
        self.client.rows = [row for row in self.client.rows if row.get(key) == value]
        return self

    def order(self, key, desc=False):
        self.client.rows = sorted(
            self.client.rows,
            key=lambda row: row.get(key) or "",
            reverse=desc,
        )
        return self

    def limit(self, limit):
        self.client.rows = self.client.rows[:limit]
        return self

    def execute(self):
        if self.mode == "upsert":
            return type("Result", (), {"data": self.client.calls[-1]["rows"]})()
        return type("Result", (), {"data": self.client.rows})()


class WriteClient:
    def __init__(self):
        self.calls = []
        self.rows = []

    def table(self, name):
        return WriteTable(self, name)


class WriteThenReadErrorTable(WriteTable):
    def select(self, fields):
        raise RuntimeError(
            "query failed for SUPABASE_SERVICE_ROLE_KEY=sentinel-service-secret "
            "at https://example.supabase.co token=sentinel-token secret=sentinel-secret"
        )


class WriteThenReadErrorClient(WriteClient):
    def table(self, name):
        return WriteThenReadErrorTable(self, name)


class MarketThemeEvidenceHandoffTest(unittest.TestCase):
    def test_owner_template_and_samples_document_source_boundaries(self):
        root = Path(__file__).resolve().parents[1]
        template_path = root / "docs/examples/market_theme_owner_approved_payload.template.json"
        sample_path = root / "docs/examples/market_theme_owner_approved_payload.sample.json"
        forbidden_path = root / "docs/examples/market_theme_forbidden_runtime_payload.sample.json"

        template = json.loads(template_path.read_text(encoding="utf-8"))
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
        forbidden = json.loads(forbidden_path.read_text(encoding="utf-8"))

        self.assertIn("trade_date", template["_required_fields"])
        self.assertIn("rows[].evidence_url", template["_required_fields"])
        self.assertIn("owner_approved_persistent", template["_allowed_source_family"])
        self.assertIn("production_db", template["_allowed_source_family"])
        self.assertIn("market_data", template["_allowed_source_family"])
        self.assertIn("runtime", template["_forbidden_source_family"])
        self.assertIn("fixture", template["_forbidden_source_family"])
        self.assertIn("not production confirmed", template["_production_status"])
        self.assertIn("defaults to dry-run", template["_script_boundary"])
        self.assertIn("explicit --execute", template["_script_boundary"])

        self.assertEqual(sample["source_family"], "owner_approved_persistent")
        self.assertEqual(sample["evidence_status"], "confirmed")
        self.assertEqual(sample["freshness"], "fresh")
        self.assertEqual(sample["rows"][0]["support_level"], "supporting")
        self.assertIn("sample-only", sample["_production_status"])
        self.assertIn("defaults to dry-run", sample["_script_boundary"])

        self.assertEqual(forbidden["source_family"], "runtime")
        self.assertEqual(forbidden["rows"], [])
        self.assertIn("deterministic_sql=null", forbidden["_expected_result"])

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

    def test_approval_package_generator_builds_allowed_non_live_package(self):
        package = build_approval_package(approval_payload())

        self.assertEqual(package["schema_decision"], "no-schema-change")
        self.assertEqual(package["mode"], "non-live-approval-package")
        self.assertEqual(package["write_execution"], "disabled")
        self.assertEqual(package["payload_validation"]["status"], "passed")
        self.assertEqual(
            package["deterministic_sql_path"],
            "market_theme_confirmed_evidence_2026-05-29.sql",
        )
        self.assertIn("Owner manual approval required", package["deterministic_sql"])
        self.assertIn("Agent did not execute this SQL", package["deterministic_sql"])
        self.assertIn("not evidence of production deployment", package["deterministic_sql"])
        self.assertIn("insert into public.market_theme_confirmed_evidence", package["deterministic_sql"])
        self.assertIn(
            "python scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29",
            package["read_only_smoke_command"],
        )
        self.assertIn("live Supabase write", package["not_executed"])

    def test_approval_package_generator_fails_closed_for_forbidden_source_without_sql(self):
        for source_family in [
            "local",
            "runtime",
            "cache",
            "worktree",
            "report-derived",
            "synthetic",
            "default",
            "test",
            "fixture",
        ]:
            with self.subTest(source_family=source_family):
                package = build_approval_package(approval_payload(source_family=source_family))

                self.assertEqual(package["payload_validation"]["status"], "failed")
                self.assertEqual(package["payload_validation"]["reason"], "forbidden source_family")
                self.assertIsNone(package["deterministic_sql"])
                self.assertEqual(package["write_execution"], "disabled")

    def test_approval_package_generator_fails_closed_for_mixed_allowed_and_forbidden_source(self):
        payload = approval_payload(
            rows=[
                {
                    "symbol": "2330",
                    "theme": "AI supply chain",
                    "support_level": "supporting",
                    "evidence_url": "manual-owner-approved-reference",
                    "reason": "Owner approved persistent evidence",
                    "source_family": "runtime",
                }
            ]
        )

        package = build_approval_package(payload)

        self.assertEqual(package["payload_validation"]["status"], "failed")
        self.assertEqual(package["payload_validation"]["reason"], "forbidden source_family")
        self.assertIsNone(package["deterministic_sql"])

    def test_approval_package_sql_is_deterministic_for_same_payload(self):
        first = build_approval_package(approval_payload())
        second = build_approval_package(approval_payload())

        self.assertEqual(first["deterministic_sql"], second["deterministic_sql"])
        self.assertEqual(first["deterministic_sql_path"], second["deterministic_sql_path"])

    def test_approval_package_cli_writes_review_artifacts_only_for_allowed_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "approved_payload.json"
            output_dir = Path(tmpdir) / "package"
            payload_path.write_text(
                json.dumps(approval_payload()),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/generate_evidence_approval_package.py",
                    "--payload",
                    str(payload_path),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0)
            output = json.loads(completed.stdout)
            self.assertEqual(output["payload_validation"]["status"], "passed")
            self.assertTrue((output_dir / "approval_package.json").exists())
            self.assertTrue((output_dir / "approval_package.md").exists())
            sql_path = output_dir / "market_theme_confirmed_evidence_2026-05-29.sql"
            self.assertTrue(sql_path.exists())
            self.assertIn("Agent did not execute this SQL", sql_path.read_text(encoding="utf-8"))

    def test_approval_package_cli_sample_paths_match_handoff_docs(self):
        root = Path(__file__).resolve().parents[1]
        sample_path = root / "docs/examples/market_theme_owner_approved_payload.sample.json"
        forbidden_path = root / "docs/examples/market_theme_forbidden_runtime_payload.sample.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            allowed_output_dir = Path(tmpdir) / "allowed"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/generate_evidence_approval_package.py",
                    "--payload",
                    str(sample_path),
                    "--output-dir",
                    str(allowed_output_dir),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0)
            allowed = json.loads(completed.stdout)
            self.assertEqual(allowed["payload_validation"]["status"], "passed")
            self.assertEqual(allowed["write_execution"], "disabled")
            self.assertIn("Owner reviews package", allowed["manual_approval_required"])
            self.assertIn("live Supabase write", allowed["not_executed"])
            self.assertTrue((allowed_output_dir / "approval_package.json").exists())
            self.assertTrue((allowed_output_dir / "approval_package.md").exists())
            sql_path = allowed_output_dir / "market_theme_confirmed_evidence_2026-05-29.sql"
            self.assertTrue(sql_path.exists())
            sql = sql_path.read_text(encoding="utf-8")
            self.assertIn("Agent did not execute this SQL", sql)
            self.assertIn("not evidence of production deployment", sql)

            forbidden_output_dir = Path(tmpdir) / "forbidden"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/generate_evidence_approval_package.py",
                    "--payload",
                    str(forbidden_path),
                    "--output-dir",
                    str(forbidden_output_dir),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            forbidden = json.loads(completed.stdout)
            self.assertEqual(forbidden["payload_validation"]["status"], "failed")
            self.assertEqual(forbidden["payload_validation"]["reason"], "forbidden source_family")
            self.assertIsNone(forbidden["deterministic_sql"])
            self.assertEqual(forbidden["write_execution"], "disabled")
            self.assertTrue((forbidden_output_dir / "approval_package.json").exists())
            self.assertTrue((forbidden_output_dir / "approval_package.md").exists())
            self.assertIsNone(forbidden["output_paths"]["deterministic_sql"])
            self.assertFalse(any(forbidden_output_dir.glob("*.sql")))

    def test_handoff_docs_do_not_describe_samples_as_production_confirmed(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "docs/handoff/evidence_chain_market_theme_ops_artifacts.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("not production confirmed evidence", text)
        self.assertIn("not a GitHub fresh runner source of truth", text)
        self.assertIn("review-only", text)
        self.assertIn("does not execute SQL", text)
        self.assertIn("source_family=runtime", text)

    def test_write_cli_allowed_sample_dry_run_outputs_upsert_preview_without_write(self):
        root = Path(__file__).resolve().parents[1]
        sample_path = root / "docs/examples/market_theme_owner_approved_payload.sample.json"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/write_market_theme_confirmed_evidence.py",
                "--payload",
                str(sample_path),
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        output = json.loads(completed.stdout)
        self.assertEqual(output["mode"], "dry-run")
        self.assertEqual(
            output["source"],
            "approved_persistent_source:owner_approved_market_theme_review_sample",
        )
        self.assertEqual(output["source_type"], "approved_persistent_source")
        self.assertEqual(output["target_table"], "public.market_theme_confirmed_evidence")
        self.assertEqual(output["candidate_rows"], 1)
        self.assertEqual(output["validation"], "pass")
        self.assertEqual(output["write_mode"], "dry-run")
        self.assertEqual(output["secret_redaction"], "pass")
        self.assertEqual(output["write_execution"], "disabled")
        self.assertEqual(output["payload_validation"]["status"], "passed")
        self.assertEqual(output["rows_to_upsert"], 1)
        self.assertEqual(
            output["upsert_conflict_target"],
            "trade_date,market_index,sector_theme_key,source_family,source_name,as_of",
        )
        self.assertEqual(output["upsert_preview"][0]["source_family"], "owner_approved_persistent")
        self.assertIsNone(output["execute_payload"])

    def test_write_cli_forbidden_source_fails_closed_without_execute_payload(self):
        root = Path(__file__).resolve().parents[1]
        forbidden_path = root / "docs/examples/market_theme_forbidden_runtime_payload.sample.json"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/write_market_theme_confirmed_evidence.py",
                "--payload",
                str(forbidden_path),
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        output = json.loads(completed.stdout)
        self.assertEqual(output["mode"], "dry-run")
        self.assertEqual(output["write_execution"], "disabled")
        self.assertEqual(output["source"], "forbidden_or_unapproved_source:same_run_runtime_sample")
        self.assertEqual(output["source_type"], "forbidden_or_unapproved_source")
        self.assertEqual(output["payload_validation"]["status"], "failed")
        self.assertEqual(output["candidate_rows"], 0)
        self.assertEqual(output["validation"], "fail")
        self.assertEqual(output["write_mode"], "dry-run")
        self.assertEqual(output["secret_redaction"], "pass")
        self.assertEqual(output["payload_validation"]["reason"], "forbidden source_family")
        self.assertEqual(output["rows_to_upsert"], 0)
        self.assertEqual(output["upsert_preview"], [])
        self.assertIsNone(output["execute_payload"])

    def test_write_cli_execute_fails_closed_when_write_env_missing(self):
        root = Path(__file__).resolve().parents[1]
        sample_path = root / "docs/examples/market_theme_owner_approved_payload.sample.json"

        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout:
            old_stdout = sys.stdout
            try:
                sys.stdout = stdout
                returncode = write_evidence_main(
                    ["--payload", str(sample_path), "--execute"],
                    env={},
                    config_module=SimpleNamespace(),
                )
            finally:
                sys.stdout = old_stdout
            stdout.seek(0)
            stdout_text = stdout.read()
            output = json.loads(stdout_text)

        self.assertEqual(returncode, 2)
        self.assertEqual(output["mode"], "execute")
        self.assertEqual(output["write_execution"], "blocked")
        self.assertEqual(output["payload_validation"]["status"], "passed")
        self.assertEqual(output["attempted_rows"], 1)
        self.assertEqual(output["written_rows"], 0)
        self.assertEqual(output["skipped_rows"], 1)
        self.assertEqual(output["read_after_write"], "skipped")
        self.assertEqual(output["secret_redaction"], "pass")
        self.assertEqual(output["env_validation"]["status"], "failed")
        self.assertEqual(
            output["env_validation"]["missing"],
            ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY|SERVICE_ROLE_KEY"],
        )
        self.assertEqual(output["env_validation"]["url_source"], "")
        self.assertEqual(output["env_validation"]["key_source"], "")
        self.assertEqual(output["rows_written"], 0)
        self.assertNotIn("https://", stdout_text)
        self.assertNotIn("fake-key", stdout_text)

    def test_write_cli_execute_falls_back_to_service_role_key_config_without_leaking_secret(self):
        root = Path(__file__).resolve().parents[1]
        sample_path = root / "docs/examples/market_theme_owner_approved_payload.sample.json"
        client = WriteClient()
        config_module = SimpleNamespace(
            SUPABASE_URL="https://config.supabase.co",
            SERVICE_ROLE_KEY="config-service-secret",
        )

        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout:
            old_stdout = sys.stdout
            try:
                sys.stdout = stdout
                returncode = write_evidence_main(
                    ["--payload", str(sample_path), "--execute"],
                    client=client,
                    env={},
                    config_module=config_module,
                )
            finally:
                sys.stdout = old_stdout
            stdout.seek(0)
            stdout_text = stdout.read()
            output = json.loads(stdout_text)

        self.assertEqual(returncode, 0)
        self.assertEqual(output["write_execution"], "executed")
        self.assertEqual(output["env_validation"]["url_source"], "config.SUPABASE_URL")
        self.assertEqual(output["env_validation"]["key_source"], "config.SERVICE_ROLE_KEY")
        self.assertEqual(output["attempted_rows"], 1)
        self.assertEqual(output["written_rows"], 1)
        self.assertEqual(output["skipped_rows"], 0)
        self.assertEqual(output["validation"], "pass")
        self.assertEqual(output["write_mode"], "commit")
        self.assertEqual(output["secret_redaction"], "pass")
        self.assertEqual(output["read_after_write"], "pass")
        self.assertEqual(output["written_rows"], 1)
        self.assertEqual(output["rows_written"], 1)
        self.assertEqual(output["read_after_write_smoke"]["strategy_consumer"], "pass")
        self.assertEqual(output["read_after_write_smoke"]["source_family"], "owner_approved_persistent")
        self.assertEqual(output["rows_written"], 1)
        self.assertEqual(len(client.calls), 1)
        self.assertNotIn("https://config.supabase.co", stdout_text)
        self.assertNotIn("config-service-secret", stdout_text)

    def test_write_cli_execute_falls_back_to_supabase_service_role_key_config_alias(self):
        root = Path(__file__).resolve().parents[1]
        sample_path = root / "docs/examples/market_theme_owner_approved_payload.sample.json"
        client = WriteClient()
        config_module = SimpleNamespace(
            SUPABASE_URL="https://alias.supabase.co",
            SUPABASE_SERVICE_ROLE_KEY="config-alias-secret",
        )

        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout:
            old_stdout = sys.stdout
            try:
                sys.stdout = stdout
                returncode = write_evidence_main(
                    ["--payload", str(sample_path), "--execute"],
                    client=client,
                    env={},
                    config_module=config_module,
                )
            finally:
                sys.stdout = old_stdout
            stdout.seek(0)
            stdout_text = stdout.read()
            output = json.loads(stdout_text)

        self.assertEqual(returncode, 0)
        self.assertEqual(output["env_validation"]["url_source"], "config.SUPABASE_URL")
        self.assertEqual(output["env_validation"]["key_source"], "config.SUPABASE_SERVICE_ROLE_KEY")
        self.assertEqual(output["read_after_write"], "pass")
        self.assertEqual(len(client.calls), 1)
        self.assertNotIn("https://alias.supabase.co", stdout_text)
        self.assertNotIn("config-alias-secret", stdout_text)

    def test_write_client_uses_env_values_before_config_values(self):
        created = []

        def fake_create_client(url, key):
            created.append((url, key))
            return object()

        fake_supabase = SimpleNamespace(create_client=fake_create_client)
        with patch.dict(sys.modules, {"supabase": fake_supabase}):
            client = build_market_theme_write_client(
                env={
                    "SUPABASE_URL": "env-url-sentinel",
                    "SUPABASE_SERVICE_ROLE_KEY": "env-key-sentinel",
                },
                config_module=SimpleNamespace(
                    SUPABASE_URL="config-url-sentinel",
                    SERVICE_ROLE_KEY="config-key-sentinel",
                ),
            )

        self.assertIsNotNone(client)
        self.assertEqual(created, [("env-url-sentinel", "env-key-sentinel")])

    def test_write_cli_execute_uses_fake_client_upsert_payload(self):
        root = Path(__file__).resolve().parents[1]
        sample_path = root / "docs/examples/market_theme_owner_approved_payload.sample.json"
        client = WriteClient()

        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout:
            old_stdout = sys.stdout
            try:
                sys.stdout = stdout
                returncode = write_evidence_main(
                    ["--payload", str(sample_path), "--execute"],
                    client=client,
                    env={
                        "SUPABASE_URL": "https://example.supabase.co",
                        "SUPABASE_SERVICE_ROLE_KEY": "fake-key-for-unit-test",
                    },
                )
            finally:
                sys.stdout = old_stdout
            stdout.seek(0)
            output = json.loads(stdout.read())

        self.assertEqual(returncode, 0)
        self.assertEqual(output["write_execution"], "executed")
        self.assertEqual(output["env_validation"]["url_source"], "env")
        self.assertEqual(output["env_validation"]["key_source"], "env")
        self.assertEqual(output["read_after_write"], "pass")
        self.assertEqual(output["read_after_write_smoke"]["sample_fallback"], "disabled")
        self.assertEqual(output["read_after_write_smoke"]["runtime_fallback"], "disabled")
        self.assertEqual(output["read_after_write_smoke"]["strategy_consumer"], "pass")
        self.assertEqual(output["rows_written"], 1)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0]["table"], "market_theme_confirmed_evidence")
        self.assertEqual(
            client.calls[0]["on_conflict"],
            "trade_date,market_index,sector_theme_key,source_family,source_name,as_of",
        )
        row = client.calls[0]["rows"][0]
        self.assertEqual(row["source_family"], "owner_approved_persistent")
        self.assertEqual(row["source_name"], "owner_approved_market_theme_review_sample")
        self.assertIn("evidence_value", row)
        self.assertNotIn("id", row)
        self.assertNotIn("created_at", row)

    def test_write_cli_read_after_write_exception_redacts_secret_sentinels(self):
        root = Path(__file__).resolve().parents[1]
        sample_path = root / "docs/examples/market_theme_owner_approved_payload.sample.json"
        client = WriteThenReadErrorClient()

        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout:
            old_stdout = sys.stdout
            try:
                sys.stdout = stdout
                returncode = write_evidence_main(
                    ["--payload", str(sample_path), "--execute"],
                    client=client,
                    env={
                        "SUPABASE_URL": "https://example.supabase.co",
                        "SUPABASE_SERVICE_ROLE_KEY": "fake-key-for-unit-test",
                    },
                )
            finally:
                sys.stdout = old_stdout
            stdout.seek(0)
            stdout_text = stdout.read()
            output = json.loads(stdout_text)

        self.assertEqual(returncode, 2)
        self.assertEqual(output["write_execution"], "executed")
        self.assertEqual(output["read_after_write"], "fail")
        self.assertEqual(output["written_rows"], 0)
        self.assertEqual(output["rows_written"], 0)
        self.assertEqual(output["skipped_rows"], 1)
        self.assertEqual(output["secret_redaction"], "pass")
        self.assertEqual(output["read_after_write_smoke"]["status"], "fail-closed")
        self.assertEqual(
            output["read_after_write_smoke"]["note"],
            "read-after-write smoke failed; details redacted",
        )
        note_text = json.dumps(output["read_after_write_smoke"], ensure_ascii=False)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY", note_text)
        for forbidden in [
            "sentinel-service-secret",
            "https://example.supabase.co",
            "sentinel-token",
            "sentinel-secret",
        ]:
            self.assertNotIn(forbidden, stdout_text)

    def test_readonly_smoke_cli_prints_schema_decision_and_fails_closed_without_env(self):
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/smoke_market_theme_evidence_readonly.py",
            ],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
            capture_output=True,
            check=False,
            env={},
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("mode: read-only", completed.stdout)
        self.assertIn("write: disabled", completed.stdout)
        self.assertIn("schema_decision: no-schema-change", completed.stdout)
        self.assertIn("source: production", completed.stdout)
        self.assertIn("source_family: production_db", completed.stdout)
        self.assertIn("target: public.market_theme_confirmed_evidence", completed.stdout)
        self.assertIn("sample_fallback: disabled", completed.stdout)
        self.assertIn("runtime_fallback: disabled", completed.stdout)
        self.assertIn("strategy_consumer: fail-closed", completed.stdout)
        self.assertIn("source_family_allowed: false", completed.stdout)
        self.assertIn("status: fail-closed", completed.stdout)
        self.assertIn("telegram_confirmed: false", completed.stdout)

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
                self.assertEqual(smoke["schema_decision"], "no-schema-change")
                self.assertEqual(smoke["source"], "production")
                self.assertIn("source_family", smoke)
                self.assertEqual(smoke["target"], "public.market_theme_confirmed_evidence")
                self.assertEqual(smoke["sample_fallback"], "disabled")
                self.assertEqual(smoke["runtime_fallback"], "disabled")
                self.assertEqual(smoke["env"], env)
                self.assertEqual(smoke["table_read"], table_read)
                self.assertEqual(smoke["status"], status)
                self.assertEqual(smoke["telegram_confirmed"], telegram_confirmed)
                self.assertEqual(
                    smoke["strategy_consumer"],
                    "pass" if telegram_confirmed else "fail-closed",
                )
                self.assertEqual(smoke["source_family_allowed"], bool(load_result["rows"]))

    def test_readonly_smoke_helper_rejects_direct_runtime_confirmed_rows(self):
        smoke = build_market_theme_evidence_readonly_smoke(
            {
                "status": "confirmed",
                "confirmed": True,
                "reason": "",
                "rows": [
                    handoff_payload(
                        source_family="runtime",
                        source_name="same_run_context",
                    )
                ],
            }
        )

        self.assertEqual(smoke["status"], "insufficient-data")
        self.assertFalse(smoke["telegram_confirmed"])
        self.assertEqual(smoke["strategy_consumer"], "fail-closed")
        self.assertFalse(smoke["source_family_allowed"])
        self.assertEqual(smoke["source_family"], "runtime")

    def test_readonly_loader_rejects_forbidden_unknown_or_mixed_source_family_even_when_confirmed(self):
        for source_family in [
            "local",
            "local_only_state",
            "runtime",
            "runtime_diagnostic",
            "cache",
            "worktree",
            "report-derived",
            "synthetic",
            "default",
            "test_fixture",
            "fixture",
            "unknown_provider",
        ]:
            with self.subTest(source_family=source_family):
                loaded = load_confirmed_market_theme_evidence(
                    client=EvidenceClient([handoff_payload(source_family=source_family)])
                )
                smoke = build_market_theme_evidence_readonly_smoke(loaded)

                self.assertEqual(loaded["status"], "insufficient-data")
                self.assertFalse(loaded["confirmed"])
                self.assertEqual(smoke["status"], "insufficient-data")
                self.assertFalse(smoke["telegram_confirmed"])
                self.assertEqual(smoke["strategy_consumer"], "fail-closed")
                self.assertFalse(smoke["source_family_allowed"])

    def test_readonly_loader_rejects_mixed_allowed_and_forbidden_source_families(self):
        loaded = load_confirmed_market_theme_evidence(
            client=EvidenceClient(
                [
                    handoff_payload(source_family="production_db"),
                    handoff_payload(source_family="runtime"),
                ]
            )
        )
        smoke = build_market_theme_evidence_readonly_smoke(loaded)

        self.assertEqual(loaded["status"], "insufficient-data")
        self.assertFalse(loaded["confirmed"])
        self.assertEqual(smoke["status"], "insufficient-data")
        self.assertFalse(smoke["telegram_confirmed"])
        self.assertEqual(smoke["strategy_consumer"], "fail-closed")
        self.assertFalse(smoke["source_family_allowed"])
        self.assertEqual(smoke["source_family"], "production_db,runtime")

    def test_readonly_loader_accepts_allowed_persistent_source_family(self):
        for source_family in [
            "production_db",
            "owner_approved_persistent",
            "market_data",
        ]:
            with self.subTest(source_family=source_family):
                loaded = load_confirmed_market_theme_evidence(
                    client=EvidenceClient([handoff_payload(source_family=source_family)])
                )

                self.assertEqual(loaded["status"], "confirmed")
                self.assertTrue(loaded["confirmed"])
                self.assertEqual(loaded["source_of_truth"], "production_db")


if __name__ == "__main__":
    unittest.main()
