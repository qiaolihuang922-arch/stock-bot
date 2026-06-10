# CURRENT_STATE.md

## Current Task

- task_id: `report_state_denoise_followup_20260610`
- status: `complete`
- version: `v21.0.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline noise.
- Current direction is v21 read-only trade state machine plus production pipeline hardening.
- Do not expand DB schema unless read-only behavior proves an actual cross-day memory gap.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.

## Current Changes

- Added unheld `等接近` / `WAIT_APPROACH` for far-from-trigger watchlist items.
- Aligned unheld title/state/buy/gap/unlock/summary wording.
- Reworded distance gate to avoid implying all future setups are impossible when distance is far.
- Historical analogy below 60% is now low-confidence reference only.
- Fundamentals block keeps per-stock spacing.

## Verification State

- Generator + state-machine tests: `203 passed, 145 warnings, 44 subtests passed`.
- Analysis/evidence/volume/theme tests: `94 passed, 1 warning, 13 subtests passed`.
- Official dry-run: `messages 4`; key report lines checked; no live Telegram delivery.
- Repo completion is handled by the latest pushed commit and final git gate evidence.

## Known Follow-ups

- None for this report/state denoise task.
