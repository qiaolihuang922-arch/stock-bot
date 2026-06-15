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
- Corrected the second mobile issue where every waiting card carried the same broad metric package:
  - `距突破` stays visible on every unheld card;
  - `缺口` / `可買` are scoped by `funnel_state`;
  - `等回測` focuses on retest / breakout-zone confirmation;
  - `等冷卻` focuses on heat;
  - `等風險報酬` focuses on risk-reward;
  - `等型態` focuses on setup / quality;
  - normal waiting/rejected cards suppress noisy `數據：...` rows.
- Follow-up denoise completed:
  - normal waiting/rejected unheld cards suppress repeated `交易狀態` when title + `進場` already explain the state;
  - ordinary repeated-failure `歷史` rows are hidden, while repair / positive-weight / high-signal memory remains eligible.
- Corrected the implementation path:
  - official formatter now consumes `_unheld_entry_contract`;
  - state-specific evidence is selected before formatting;
  - the old post-format parser/crop path is no longer the active rule source.
- Strategy calculations and blockers are unchanged.
- Header/runtime version remains `v21.1`.

## Verification

- Dry-run:
  - `generate_report(dry_run=True)`
  - confirmed unheld cards render short state-scoped `進場` / `缺口` / `可買` lines.
  - latest current-output counts: `trade_state=0`; `history=0`; `data=0`.
- Tests:
  - command: `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `479 passed, 8 skipped, 108 subtests passed`
- No live Telegram delivery.
- No DB schema change/write/backfill.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- latest commit: `git log -1 --oneline`
- HEAD equals upstream: `true after final closeout push`
- worktree/index: `clean after final closeout push`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- After next scheduled `run_mode=bot`, confirm production Telegram artifact keeps the readable unheld-card layout.
