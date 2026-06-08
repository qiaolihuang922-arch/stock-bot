# CURRENT_STATE.md

## Current Task

- task_id: `future_fundamentals_and_unheld_status_20260608`
- status: `qa_passed`
- version: `v20.4.51`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- EPS / revenue visibility is per watched stock, not dependent on whether that stock has a MOPS meeting.
- Repetition per stock is acceptable when it carries each stock's decision.
- Production source-of-truth is Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Fixed Markdown files must be rewritten/compressed, not removed.

## Current Changes

- Added `關注標的財報` to future-watch message.
- MOPS meeting section is event-only again.
- Summary all-rejected unheld state now reads `未持倉 7（全部不可行動）`.
- Detail section now reads `未持倉狀態：未持倉 7 檔全部不可行動`.
- Version bumped to `v20.4.51`.

## Verification State

- `py_compile` passed.
- focused pytest + market theme tests passed: 44 tests.
- official `generate_report(dry_run=True)` passed: 4 local preview messages, no live Telegram delivery.

## Known Follow-ups

- CAO TUI automation gap still needs a runner-level fix.
- Historical report suite is not clean; broader baseline cleanup remains separate.
