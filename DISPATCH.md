# DISPATCH.md

## Active

- task_md_holds: `unheld_card_mobile_denoise_20260616`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- Owner requested smarter denoise for unheld cards, specifically:
  - merge `拆解` / `盤面`-like state;
  - merge `買點` / `不能買` / `還差` / `可買條件`.
- Corrected presentation-only denoise after Owner screenshot showed the previous hard-concat was unreadable:
  - no standalone `拆解` row;
  - no wall-like `狀態` / `進場檢查` row;
  - non-actionable cards use `進場` / `缺口` / `可買`.
- Strategy calculations and blockers are unchanged.
- Header/runtime version remains `v21.1`.

## Verification

- Dry-run:
  - `generate_report(dry_run=True)`
  - confirmed unheld cards render short `進場` / `缺口` / `可買` lines.
- Tests:
  - command: `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_unheld_gap_format.py -q --tb=short`
  - result: `205 passed, 44 subtests passed`
- No live Telegram delivery.
- No DB schema change/write/backfill.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- latest commit: `see git log -1 after push`
- HEAD equals upstream: `true after closeout push`
- worktree/index: `clean`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- After next scheduled `run_mode=bot`, confirm production Telegram artifact keeps the readable unheld-card layout.
