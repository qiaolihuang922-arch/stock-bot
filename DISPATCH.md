# DISPATCH.md

## Active

- task_md_holds: `dry_run_strategy_evidence_near_breakout_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner challenged why 聯電 would show `策略樣本證據不足`.
- Root cause:
  - 聯電行情 was not missing.
  - local `generate_report(dry_run=True)` skipped read-only strategy evidence loading, so the report context marked strategy evidence as missing.
  - after restoring read-only evidence, near-breakout C-quality tracking still fell through to `淘汰`; this was a state-machine bug.
- Implemented:
  - dry-run now read-only loads strategy evidence while still not writing DB.
  - near-breakout C-quality non-hard-failure state is kept as tracking / setup wait, not淘汰.

## Verification

- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `484 passed, 8 skipped, 110 subtests passed`
- Official dry-run:
  - 聯電: `等型態｜觀察`
  - `距突破：4.06%｜接近突破`
  - summary: 未持倉 `僅追蹤8`, no 聯電淘汰.

## Current Git State

- branch: `main`
- completion: git completion passed after push.

## Next Action

- Observe next scheduled `run_mode=bot` artifact.
