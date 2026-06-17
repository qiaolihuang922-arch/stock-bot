# DISPATCH.md

## Active

- task_md_holds: `db_backed_price_transition_v21_1_20260617`
- status: `implemented + QA pass`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner asked to correct 06/17 intraday cards whose visible strategy state did not match this week's price changes.
- Implemented DB-backed recent price transition:
  - reads `daily_price` recent closes from cross-day context.
  - compares latest DB close to current price.
  - separates yesterday-up/today-down, yesterday-down/today-up, continuous-up, continuous-down.
- Fixed visible conflicts:
  - 旺宏:連漲後當日回落 now routes to `等回測｜反彈修復待回測`, not trend continuation.
  - 群創: V >= 1.1 from report payload no longer displays `量能不足`.
  - 聯電: V < 1.1 near setup now routes to `等量能`, not `不可追高觀察｜等量`.
  - 遠離 20%+ names keep low-repair / approach route; volume does not become the primary blocker there.
- No DB writes, schema changes, backfill, prune, or live Telegram.

## Verification

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `211 passed, 163 warnings, 46 subtests passed`
- `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `494 passed, 8 skipped, 175 warnings, 110 subtests passed`
- Official dry-run:
  - `generate_report(dry_run=True)` returned `4` messages.
  - 聯電 visible as `等量能｜等量`.
  - 旺宏 visible as `等回測｜反彈修復待回測`.
  - 群創 not visible as `等量能｜量能不足`.
  - 緯創 / 技嘉 / 仁寶 remain `等低位修復`.

## Current Git State

- branch: `main`
- latest implementation commit: current `HEAD` for this cycle.
- pushed to upstream: yes.
- git completion gate: passed.

## Next Action

- No active follow-up in this cycle.
