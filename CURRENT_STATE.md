# CURRENT_STATE.md

## Current Task

- task_id: `future_watch_source_and_card_denoise_20260610`
- status: `complete`
- version: `v21.0.2`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline noise.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- TWSE historical source has same-run retry and clearer fail-closed source-error wording.
- TWSE listed revenue OpenAPI is included in fundamentals loading.
- Compact non-actionable wait cards reduce repeated low-signal rows.
- Visible report version is `v21.0.2`; state-machine schema remains `v21.0.1`.

## Verification State

- Generator + state-machine tests: `206 passed, 145 warnings, 44 subtests passed`.
- Market/theme/analysis/strategy/volume tests: `94 passed, 1 warning, 13 subtests passed`.
- Official dry-run: `messages 4`; v21.0.2 output checked; no live Telegram delivery.

## Known Follow-ups

- MOPS法說會 parsing still fail-closes when official source is not parseable.
