import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/stock-bot.yml"


def _create_runtime_config_script():
    return _workflow_run_script("Create runtime config")


def _workflow_run_script(step_name):
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    step = lines.index(f"      - name: {step_name}")
    start = lines.index("        run: |", step) + 1
    end = next(
        (
            index for index in range(start, len(lines))
            if lines[index].startswith("      - name:")
        ),
        len(lines),
    )
    return "\n".join(line[10:] if line.startswith("          ") else line for line in lines[start:end])


class WorkflowRuntimeConfigTest(unittest.TestCase):
    def _run_create_runtime_config(self, env):
        script = _create_runtime_config_script().replace("python - <<'PY'", f'"{sys.executable}" - <<\'PY\'')
        runtime_env = os.environ.copy()
        runtime_env.update(env)
        with tempfile.TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                ["bash", "-e", "-c", script],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
                env=runtime_env,
            )
            config_path = Path(tmpdir) / "config.py"
            config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
        return completed, config_text

    def test_split_secret_runtime_config_writes_service_role_alias_without_leaking_values(self):
        completed, config_text = self._run_create_runtime_config(
            {
                "TELEGRAM_TOKEN": "telegram-token-secret",
                "TELEGRAM_CHAT_ID": "telegram-chat-secret",
                "SUPABASE_URL": "https://split.supabase.co",
                "SUPABASE_KEY": "read-key-secret",
                "SUPABASE_SERVICE_ROLE_KEY": "service-role-secret",
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('SUPABASE_KEY = "read-key-secret"', config_text)
        self.assertIn('SUPABASE_SERVICE_ROLE_KEY = "service-role-secret"', config_text)
        self.assertIn("SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY", config_text)
        self.assertIn("runtime config: SUPABASE_SERVICE_ROLE_KEY present", completed.stdout)
        self.assertIn("runtime config: SERVICE_ROLE_KEY alias present", completed.stdout)
        self.assertNotIn("read-key-secret", completed.stdout)
        self.assertNotIn("service-role-secret", completed.stdout)
        self.assertNotIn("https://split.supabase.co", completed.stdout)
        self.assertNotIn("read-key-secret", completed.stderr)
        self.assertNotIn("service-role-secret", completed.stderr)

    def test_stock_config_path_preserves_existing_config_and_appends_service_role_alias(self):
        stock_config = textwrap.dedent(
            """
            TOKEN = "stock-token-secret"
            CHAT_ID = "stock-chat-secret"
            SUPABASE_URL = "https://stock.supabase.co"
            SUPABASE_KEY = "stock-read-key-secret"
            """
        ).strip()
        completed, config_text = self._run_create_runtime_config(
            {
                "STOCK_CONFIG": stock_config,
                "SUPABASE_SERVICE_ROLE_KEY": "stock-service-role-secret",
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('SUPABASE_KEY = "stock-read-key-secret"', config_text)
        self.assertIn('SUPABASE_SERVICE_ROLE_KEY = "stock-service-role-secret"', config_text)
        self.assertIn("SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY", config_text)
        self.assertIn("runtime config: SUPABASE_KEY present", completed.stdout)
        self.assertIn("runtime config: SUPABASE_SERVICE_ROLE_KEY present", completed.stdout)
        self.assertNotIn("stock-read-key-secret", completed.stdout)
        self.assertNotIn("stock-service-role-secret", completed.stdout)

    def test_stock_config_without_service_role_secret_keeps_legacy_read_config_usable(self):
        stock_config = textwrap.dedent(
            """
            TOKEN = "legacy-token-secret"
            CHAT_ID = "legacy-chat-secret"
            SUPABASE_URL = "https://legacy.supabase.co"
            SUPABASE_KEY = "legacy-read-key-secret"
            """
        ).strip()
        completed, config_text = self._run_create_runtime_config({"STOCK_CONFIG": stock_config})

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('SUPABASE_KEY = "legacy-read-key-secret"', config_text)
        self.assertNotIn("SERVICE_ROLE_KEY =", config_text)
        self.assertIn("runtime config: SUPABASE_SERVICE_ROLE_KEY missing", completed.stdout)
        self.assertIn("runtime config: SERVICE_ROLE_KEY alias missing", completed.stdout)
        self.assertNotIn("legacy-read-key-secret", completed.stdout)

    def test_daily_evidence_runtime_config_does_not_require_telegram_secrets(self):
        completed, config_text = self._run_create_runtime_config(
            {
                "RUN_MODE": "daily_evidence",
                "SUPABASE_URL": "https://daily.supabase.co",
                "SUPABASE_KEY": "daily-read-key-secret",
                "SUPABASE_SERVICE_ROLE_KEY": "daily-service-role-secret",
            }
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('TOKEN = ""', config_text)
        self.assertIn('CHAT_ID = ""', config_text)
        self.assertIn('SUPABASE_KEY = "daily-read-key-secret"', config_text)
        self.assertIn("runtime config: SUPABASE_SERVICE_ROLE_KEY present", completed.stdout)
        self.assertNotIn("daily-read-key-secret", completed.stdout)
        self.assertNotIn("daily-service-role-secret", completed.stdout)

    def test_workflow_does_not_echo_service_role_secret_value(self):
        workflow_text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}", workflow_text)
        self.assertNotIn('echo "$SUPABASE_SERVICE_ROLE_KEY"', workflow_text)
        self.assertNotIn("echo $SUPABASE_SERVICE_ROLE_KEY", workflow_text)
        self.assertNotIn("print(service_role_key)", workflow_text)

    def test_workflow_dispatch_supports_git_runner_may_backfill(self):
        workflow_text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("push:", workflow_text)
        self.assertIn("branches:", workflow_text)
        self.assertIn("- main", workflow_text)
        self.assertIn("schedule:", workflow_text)
        self.assertIn('cron: "0 6 * * 1-5"', workflow_text)
        self.assertIn("run_mode:", workflow_text)
        self.assertIn("- daily_evidence", workflow_text)
        self.assertIn("- backfill_may", workflow_text)
        self.assertIn("- backfill_and_bot", workflow_text)
        self.assertIn('default: "2026-05-01"', workflow_text)
        self.assertIn('default: "2026-05-29"', workflow_text)
        self.assertIn("python scripts/backfill_signals.py \\", workflow_text)
        self.assertIn("python scripts/backfill_market_theme_sources.py \\", workflow_text)
        self.assertIn("--historical-range", workflow_text)
        self.assertIn('--start-date "$BACKFILL_START_DATE"', workflow_text)
        self.assertIn('--end-date "$BACKFILL_END_DATE"', workflow_text)
        self.assertIn('--version "$BACKFILL_VERSION"', workflow_text)
        self.assertIn("--allow-partial", workflow_text)
        self.assertIn("--write", workflow_text)
        self.assertIn("--confirm-write", workflow_text)
        self.assertIn('Run bot skipped for run_mode=$RUN_MODE', workflow_text)
        self.assertIn("Run Phase 3 evidence automation", workflow_text)
        self.assertIn("python scripts/run_phase3_evidence_automation.py --require-market-theme-payload $payload_arg", workflow_text)
        self.assertIn("github.event_name == 'schedule' && 'daily_evidence'", workflow_text)

    def _run_market_theme_backfill_step(self, run_mode, fake_python_exit=0):
        script = _workflow_run_script("Backfill official market/theme evidence (retry 3 times)")
        runtime_env = os.environ.copy()
        runtime_env["RUN_MODE"] = run_mode
        runtime_env["BACKFILL_START_DATE"] = "2026-06-01"
        runtime_env["BACKFILL_END_DATE"] = "2026-06-03"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            bin_path = tmp_path / "bin"
            bin_path.mkdir()
            calls_path = tmp_path / "python_calls.txt"
            fake_python = bin_path / "python"
            fake_python.write_text(
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env bash
                    echo "$@" >> "{calls_path}"
                    echo "ValueError: market_theme_confirmed_evidence blocked: source date outside requested range" >&2
                    exit {fake_python_exit}
                    """
                ),
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            fake_sleep = bin_path / "sleep"
            fake_sleep.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            fake_sleep.chmod(0o755)
            runtime_env["PATH"] = f"{bin_path}{os.pathsep}{runtime_env.get('PATH', '')}"
            completed = subprocess.run(
                ["bash", "-e", "-c", script],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
                env=runtime_env,
            )
            calls = calls_path.read_text(encoding="utf-8") if calls_path.exists() else ""
        return completed, calls

    def test_bot_mode_skips_may_market_theme_backfill_write_step(self):
        completed, calls = self._run_market_theme_backfill_step("bot", fake_python_exit=1)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("May market/theme evidence backfill skipped for run_mode=bot", completed.stdout)
        self.assertEqual(calls, "")
        self.assertNotIn("--write --confirm-write", calls)

    def test_backfill_modes_execute_may_market_theme_backfill_and_preserve_guard_failure(self):
        for run_mode in ("backfill_may", "backfill_and_bot"):
            with self.subTest(run_mode=run_mode):
                completed, calls = self._run_market_theme_backfill_step(run_mode, fake_python_exit=1)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(
                    f"May market/theme evidence backfill enabled for run_mode={run_mode}",
                    completed.stdout,
                )
                self.assertEqual(calls.count("scripts/backfill_market_theme_sources.py"), 3)
                self.assertIn("--write --confirm-write", calls)
                self.assertIn("--start-date 2026-06-01", calls)
                self.assertIn("--end-date 2026-06-03", calls)
                self.assertIn("source date outside requested range", completed.stderr)

    def test_scheduled_daily_evidence_mode_skips_live_bot_delivery(self):
        script = _workflow_run_script("Run bot (retry 3 times)")
        runtime_env = os.environ.copy()
        runtime_env["RUN_MODE"] = "daily_evidence"
        completed = subprocess.run(
            ["bash", "-e", "-c", script],
            text=True,
            capture_output=True,
            check=False,
            env=runtime_env,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Run bot skipped for run_mode=daily_evidence", completed.stdout)

    def test_phase3_evidence_step_preserves_market_theme_write_cli_path(self):
        script = _workflow_run_script("Run Phase 3 evidence automation")
        runtime_env = os.environ.copy()
        runtime_env["RUN_MODE"] = "daily_evidence"
        runtime_env["MARKET_THEME_APPROVED_PAYLOAD"] = '{"payloads":[]}'
        with tempfile.TemporaryDirectory() as tmpdir:
            bin_path = Path(tmpdir) / "bin"
            bin_path.mkdir()
            calls_path = Path(tmpdir) / "python_calls.txt"
            fake_python = bin_path / "python"
            fake_python.write_text(
                f"#!/usr/bin/env bash\necho \"$@\" >> \"{calls_path}\"\nexit 0\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            runtime_env["PATH"] = f"{bin_path}{os.pathsep}{runtime_env.get('PATH', '')}"
            completed = subprocess.run(
                ["bash", "-e", "-c", script],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
                env=runtime_env,
            )
            calls = calls_path.read_text(encoding="utf-8")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("scripts/run_phase3_evidence_automation.py", calls)
        self.assertIn("--require-market-theme-payload", calls)
        self.assertIn("--market-theme-payload market_theme_approved_payload.json", calls)

    def test_phase3_evidence_step_fails_closed_without_market_theme_payload_secret(self):
        script = _workflow_run_script("Run Phase 3 evidence automation")
        runtime_env = os.environ.copy()
        runtime_env["RUN_MODE"] = "daily_evidence"
        runtime_env["MARKET_THEME_APPROVED_PAYLOAD"] = ""
        with tempfile.TemporaryDirectory() as tmpdir:
            bin_path = Path(tmpdir) / "bin"
            bin_path.mkdir()
            calls_path = Path(tmpdir) / "python_calls.txt"
            fake_python = bin_path / "python"
            fake_python.write_text(
                f"#!/usr/bin/env bash\necho \"$@\" >> \"{calls_path}\"\ncase \"$*\" in *--require-market-theme-payload*) exit 2;; *) exit 0;; esac\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            runtime_env["PATH"] = f"{bin_path}{os.pathsep}{runtime_env.get('PATH', '')}"
            completed = subprocess.run(
                ["bash", "-e", "-c", script],
                cwd=tmpdir,
                text=True,
                capture_output=True,
                check=False,
                env=runtime_env,
            )
            calls = calls_path.read_text(encoding="utf-8")

        self.assertEqual(completed.returncode, 2)
        self.assertIn("--require-market-theme-payload", calls)
        self.assertNotIn("--market-theme-payload", calls)


if __name__ == "__main__":
    unittest.main()
