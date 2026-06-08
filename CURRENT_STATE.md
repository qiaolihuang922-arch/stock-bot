# CURRENT_STATE.md

## Current Task

- task_id: `historical_analogy_granularity_20260608`
- status: `qa_passed`
- version: `v20.4.52`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- EPS / revenue visibility is per watched stock, not dependent on whether that stock has a MOPS meeting.
- Historical analogy is context, not prediction or trade instruction.
- Production source-of-truth is Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Fixed Markdown files must be rewritten/compressed, not removed.

## Current Changes

- Historical analogy has higher granularity:
  - pattern / pressure level.
  - similar points.
  - dissimilar limits.
  - next observations.
  - data/source line.
- Version bumped to `v20.4.52`.

## Verification State

- `py_compile` passed.
- focused pytest passed: 7 tests; market theme tests passed: 38 tests.
- official `generate_report(dry_run=True)` passed: 4 local preview messages, no live Telegram delivery.

## Known Follow-ups

- CAO TUI automation gap still needs a runner-level fix.
- Historical sample library still uses 13 internal Taiwan crash templates; broader research/database expansion is a separate task.
