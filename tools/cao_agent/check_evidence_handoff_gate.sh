#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
ARTIFACT="${2:-}"
cd "$ROOT"

required_files=(TASK.md CHANGELOG.md QA_REPORT.md AGENTS.md DISPATCH.md CURRENT_STATE.md)
for file in "${required_files[@]}"; do
  if [[ ! -s "$file" ]]; then
    echo "Evidence handoff gate failed: missing or empty $file." >&2
    exit 1
  fi
done

if ! rg -q 'task_id: (evidence-chain-maturity-100|telegram-evidence-human-readable-v20-4-20|pm-20260601-presentation-report-split)' TASK.md; then
  echo "Evidence handoff gate failed: TASK.md is not a supported evidence handoff task." >&2
  exit 1
fi

if [[ -z "$ARTIFACT" || ! -s "$ARTIFACT" ]]; then
  echo "Evidence handoff gate failed: maturity artifact path is required and must exist." >&2
  exit 1
fi

python3 - "$ARTIFACT" <<'PY'
import json
import hashlib
import subprocess
import sys
from pathlib import Path

path = Path(sys.argv[1])
artifact = json.loads(path.read_text(encoding="utf-8"))
if artifact.get("artifact_type") != "evidence_chain_maturity_report":
    raise SystemExit("Evidence handoff gate failed: artifact_type is not evidence_chain_maturity_report.")
if artifact.get("generator_version") != "v20.4.21":
    raise SystemExit("Evidence handoff gate failed: artifact generator_version is stale.")

def git_text(args):
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return ""

head = git_text(["rev-parse", "HEAD"]).strip() or "unknown"
status = git_text(["status", "--short"])
diff = git_text(["diff", "HEAD", "--"])
untracked_entries = []
ignored_status_paths = {".qa_tmp/evidence_maturity_report.json", str(path)}
status_lines = []
for line in status.splitlines():
    status_path = line[3:] if len(line) > 3 else ""
    if status_path in ignored_status_paths:
        continue
    status_lines.append(line)
    if line.startswith("?? "):
        candidate_path = line[3:]
        candidate = Path(candidate_path)
        try:
            content_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
        except Exception:
            content_hash = "unreadable"
        untracked_entries.append(f"{candidate_path}:{content_hash}")
status_payload = "\n".join(status_lines) + "\n".join(sorted(untracked_entries))
status_hash = hashlib.sha256(status_payload.encode("utf-8")).hexdigest()
diff_hash = hashlib.sha256((diff + status_payload).encode("utf-8")).hexdigest()
if artifact.get("repo_head") != head:
    raise SystemExit("Evidence handoff gate failed: artifact repo_head does not match current HEAD.")
if artifact.get("worktree_status_sha256") != status_hash:
    raise SystemExit("Evidence handoff gate failed: artifact worktree_status_sha256 does not match current worktree.")
if artifact.get("worktree_diff_sha256") != diff_hash:
    raise SystemExit("Evidence handoff gate failed: artifact worktree_diff_sha256 does not match current worktree.")
if artifact.get("maturity_score") != 100:
    raise SystemExit("Evidence handoff gate failed: maturity_score is not 100.")
if artifact.get("blocking_findings"):
    raise SystemExit("Evidence handoff gate failed: blocking_findings is not empty.")
for flag in ["schema_change", "data_write", "live_telegram", "credential_values_included"]:
    if artifact.get(flag) is not False:
        raise SystemExit(f"Evidence handoff gate failed: {flag} must be false.")

required_dimensions = {
    "data_source_anti_fake",
    "telegram_evidence_expression",
    "strategy_sample_evidence",
    "execution_memory_ledger_evidence",
    "repeatable_runner_process",
}
dimensions = artifact.get("dimensions")
if not isinstance(dimensions, dict) or set(dimensions) != required_dimensions:
    raise SystemExit("Evidence handoff gate failed: dimensions are missing or incomplete.")
for name, result in dimensions.items():
    if result.get("score") != 100 or result.get("status") != "pass":
        raise SystemExit(f"Evidence handoff gate failed: dimension {name} is not passing at 100.")

messages = artifact.get("telegram_messages")
if not isinstance(messages, list) or len(messages) != 3:
    raise SystemExit("Evidence handoff gate failed: telegram_messages must contain exactly three messages.")
if "【持倉標的】" not in messages[0] or "【未持倉標的】" not in messages[1] or "資料依據" not in messages[2]:
    raise SystemExit("Evidence handoff gate failed: telegram_messages order/content is invalid.")
for raw in ["source:", "status:", "use:", "limit:", "conflict:"]:
    if raw in messages[2]:
        raise SystemExit("Evidence handoff gate failed: telegram third message exposes raw evidence slot fields.")

artifacts = artifact.get("artifacts")
if not isinstance(artifacts, list) or len(artifacts) < 3:
    raise SystemExit("Evidence handoff gate failed: artifacts list is missing or incomplete.")
required_artifact_keys = {
    "artifact_id",
    "generated_at",
    "source_type",
    "source_name",
    "source_version_or_query_id",
    "schema_change",
    "data_write",
    "live_telegram",
    "credential_values_included",
    "status",
    "use",
    "limit",
    "conflict",
    "records_summary",
    "visible_refs",
    "verifier_result",
}
valid_source_types = {"production-readonly", "fixture", "synthetic", "runner-log"}
for index, item in enumerate(artifacts):
    missing = [key for key in required_artifact_keys if key not in item or item.get(key) in (None, "", [])]
    if missing:
        raise SystemExit(f"Evidence handoff gate failed: artifact {index} missing keys {missing}.")
    for flag in ["schema_change", "data_write", "live_telegram", "credential_values_included"]:
        if item.get(flag) is not False:
            raise SystemExit(f"Evidence handoff gate failed: artifact {index} has unsafe flag {flag}.")
    if item.get("source_type") not in valid_source_types:
        raise SystemExit(f"Evidence handoff gate failed: artifact {index} has invalid source_type.")
    verifier = item.get("verifier_result") or {}
    if verifier.get("pass") is not True:
        raise SystemExit(f"Evidence handoff gate failed: artifact {index} verifier did not pass.")
    if item.get("source_type") == "production-readonly":
        records = item.get("records_summary") or {}
        if not records.get("source_artifact_sha256") or not records.get("source_artifact_exists"):
            raise SystemExit(f"Evidence handoff gate failed: production-readonly artifact {index} lacks source artifact proof.")

structural = artifact.get("structural_artifact")
if not isinstance(structural, dict) or (structural.get("verifier") or {}).get("pass") is not True:
    raise SystemExit("Evidence handoff gate failed: structural artifact verifier is missing or failed.")
PY

echo "Evidence handoff gate passed: latest handoff files and maturity artifact are usable."
