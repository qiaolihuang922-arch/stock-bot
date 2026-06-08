# CURRENT_STATE.md

## Current Task

- task_id: `report_conflict_future_watch_format_20260608`
- status: `qa_passed`
- version: `v20.4.50`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must avoid implying a current buy when only ledger/manual buy records exist.
- Repetition per stock is acceptable when it carries each stock's decision; conflict/noise is the target, not blind dedupe.
- Production source-of-truth is Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Fixed Markdown files must be rewritten/compressed, not removed.

## Current Changes

- Summary uses `今日買入紀錄` instead of `今日已買`.
- Unheld rejected cards align title blocker and `卡關主因`.
- Future 30-day MOPS meetings split finance data into an indented `財報：...` line under each filtered meeting.
- Version bumped to `v20.4.50`.

## Verification State

- `py_compile` passed.
- focused pytest passed.
- official `generate_report(dry_run=True)` passed: 4 local preview messages, no live Telegram delivery.

## Known Follow-ups

- CAO TUI automation gap still needs a runner-level fix.
- Historical report suite is not clean; broader baseline cleanup remains separate.
