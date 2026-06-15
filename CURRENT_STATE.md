# CURRENT_STATE.md

## Current Task

- task_id: `summary_brief_mobile_denoise_20260616`
- status: `implemented + QA passed, pending commit/push`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid repeated rows.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Third summary/brief message is now decision-focused:
  - no rendered `詳情索引`;
  - no normal `📡 資料：即時價 realtime｜日線 yahoo`;
  - no generic `原因：...` / `風險：...`;
  - no fixed `持倉：依第一則...` line for ordinary holdings;
  - rejected trace is `淘汰：N 檔｜主因：...`.
- Actionable summary content remains:
  - market/action count;
  - new-entry status;
  - risk-control plan;
  - holding control checklist;
  - unheld status/funnel;
  - stale data warning when present.
- Strategy logic is unchanged.
- No DB operation was performed.

## Verification State

- Dry-run `generate_report(dry_run=True)` checked locally; third-message forbidden counts all zero.
- Tests:
  - `203 passed, 44 subtests passed` for `tests/test_generator_report.py`
  - `479 passed, 8 skipped, 108 subtests passed` full suite
- No live Telegram delivery.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact keeps the compact third-message summary.
- Prior DB follow-ups remain:
  - decide whether to enrich or hide `market_theme_index_daily_bars` OHLCV/member placeholder columns;
  - implement or retire `signal_outcomes` max high/drawdown metrics.
