#!/usr/bin/env python3
"""Generate read-only Telegram structural evidence coverage artifacts."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.generator import build_evidence_maturity_report, build_structural_evidence_artifact


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate read-only structural evidence coverage artifact JSON."
    )
    parser.add_argument(
        "--case",
        choices=[
            "all_sources_available",
            "missing_strategy_sample_source",
            "ledger_position_conflict",
            "production_all_sources_available",
            "strategy_sample_missing_source",
            "strategy_sample_synthetic_only",
            "runner_stale_artifact_blocked",
        ],
        default="all_sources_available",
    )
    parser.add_argument(
        "--maturity-report",
        action="store_true",
        help="Output five-dimension evidence chain maturity report JSON.",
    )
    args = parser.parse_args(argv)
    if args.maturity_report:
        artifact = build_evidence_maturity_report(args.case)
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if artifact["maturity_score"] == 100 and not artifact["blocking_findings"] else 2
    structural_case = {
        "production_all_sources_available": "all_sources_available",
        "strategy_sample_missing_source": "missing_strategy_sample_source",
        "strategy_sample_synthetic_only": "missing_strategy_sample_source",
        "runner_stale_artifact_blocked": "all_sources_available",
    }.get(args.case, args.case)
    artifact = build_structural_evidence_artifact(structural_case)
    print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if artifact["verifier"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
