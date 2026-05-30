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
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    step = lines.index("      - name: Create runtime config")
    start = lines.index("        run: |", step) + 1
    end = next(
        index for index in range(start, len(lines))
        if lines[index].startswith("      - name:")
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

    def test_workflow_does_not_echo_service_role_secret_value(self):
        workflow_text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}", workflow_text)
        self.assertNotIn('echo "$SUPABASE_SERVICE_ROLE_KEY"', workflow_text)
        self.assertNotIn("echo $SUPABASE_SERVICE_ROLE_KEY", workflow_text)
        self.assertNotIn("print(service_role_key)", workflow_text)

    def test_workflow_dispatch_supports_git_runner_may_backfill(self):
        workflow_text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("run_mode:", workflow_text)
        self.assertIn("- backfill_may", workflow_text)
        self.assertIn("- backfill_and_bot", workflow_text)
        self.assertIn('default: "2026-05-01"', workflow_text)
        self.assertIn('default: "2026-05-29"', workflow_text)
        self.assertIn("python scripts/backfill_signals.py \\", workflow_text)
        self.assertIn('--start-date "$BACKFILL_START_DATE"', workflow_text)
        self.assertIn('--end-date "$BACKFILL_END_DATE"', workflow_text)
        self.assertIn('--version "$BACKFILL_VERSION"', workflow_text)
        self.assertIn("--write", workflow_text)
        self.assertIn("--confirm-write", workflow_text)
        self.assertIn('Run bot skipped for run_mode=$RUN_MODE', workflow_text)


if __name__ == "__main__":
    unittest.main()
