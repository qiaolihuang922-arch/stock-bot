#!/usr/bin/env python3
"""Generate read-only Telegram structural evidence coverage artifacts."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.generator import build_structural_evidence_artifact


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
        ],
        default="all_sources_available",
    )
    args = parser.parse_args(argv)
    artifact = build_structural_evidence_artifact(args.case)
    print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if artifact["verifier"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
