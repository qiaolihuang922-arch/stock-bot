# DISPATCH.md

## Active

- task_md_holds: `db_backed_low_repair_v21_1_20260616`
- status: `implemented + QA pass`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner asked whether DB supports a real judgment for far-from-breakout names, instead of forcing every stock to wait until it returns to the prior high / breakout zone.
- Verified DB support:
  - `daily_price` already provides cross-day OHLCV.
  - Read probe confirmed 仁寶、緯創、技嘉、旺宏、群創 each had 8 DB-backed OHLCV points.
- Implemented DB-backed low-repair route:
  - if cross-day context is ready and includes `daily_price`, far-from-breakout pullback/reclaim names can render as `等低位修復`.
  - if DB daily_price is missing or insufficient, behavior remains fail-closed as `等接近` / other existing wait state.
- User-visible dry-run result:
  - 仁寶、緯創、技嘉 now show `等低位修復｜低位修復觀察`.
  - card shows `近期支撐`, `5日均`, `量能`, and effective buy conditions.
  - card now also shows condition progress: which low-repair requirements are already met and what still blocks entry.
  - `距突破` remains visible.
- Follow-up readability audit:
  - kept useful evidence lines for confirmed / insufficient-evidence prepare cards.
  - hid only the misleading `交易狀態：可準備` helper line from non-buy prepare cards.
  - did not broad-delete data lines after tests showed it would remove useful evidence.

## Verification

- DB read probe:
  - 2324 / 3231 / 2376 / 2337 / 3481 all had `source_of_truth` including `daily_price` and 8 OHLCV points.
- Targeted report/state/cross-day tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_trade_state_machine.py tests\test_cross_day_context.py -q --tb=short`
  - result: `223 passed, 159 warnings, 46 subtests passed`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `491 passed, 8 skipped, 169 warnings, 110 subtests passed`
- Official generator dry-run:
  - result: `4` messages generated, no live Telegram.
  - low-repair cards show `條件：已滿足 ...；還差 ...`.

## Current Git State

- branch: `main`
- implementation commit: `cd3017a Add DB-backed low repair state`
- readability follow-up commit: `cd78bc8 Clarify low repair entry progress`
- pushed to upstream: yes.
- git completion gate: run after closeout doc update.

## Next Action

- Push closeout doc update and run git completion gate.
