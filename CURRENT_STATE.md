# CURRENT_STATE.md

## Current Task

- task_id: `strategy_feature_persistence_v21_1_20260615`
- status: `complete`
- version: `v21.1`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- v21.1 strategy evidence is durable, not report-only:
  - typed strategy fields exist for `daily_signal_snapshot` and `signal_items` after Owner-applied migration;
  - daily snapshot, signal item, and backfill paths write V10/V20, 20D/60D resistance, breakout distances, retest zone, and compact `raw_result`;
  - schema fallback remains for pre-migration safety.
- `run_mode=bot` now includes market/theme evidence freshness after the bot step; `daily_evidence` is manual recovery.
- Two-year v21.1 strategy snapshot backfill completed for the 12 tracked stocks; latest tracked rows reach `2026-06-15`.
- `daily_signal_snapshot` cleanup completed: only `v21.1` rows remain, no old-version overlap remains.
- Report display state:
  - unheld waiting/rejected cards expose compact setup evidence consistently;
  - `距突破：x%｜狀態` is shown as its own line on holding and unheld stock cards when available;
  - `盤面` no longer includes breakout distance text;
  - non-actionable positive evidence is shown as state-aware `補充` with a blocker-specific caveat, not as a buy reason;
  - `等冷卻` cards suppress internal `RR -（過熱）` / `風控不適用` data noise;
  - limit-lock /急彈追價 overheat keeps `等回測`; pure overheat keeps `等冷卻`;
  - after-hours brief can show short unheld state groups by names, but falls back when the list would become noisy;
  - unmet RR is shown once as the primary blocker and not repeated again in setup context;
  - strong rebound holdings use rebound-continuation next-step wording;
  - this is display-only and does not change buy/sell thresholds.

## Verification State

- Focused persistence/backfill/calibration: `19 passed`.
- Targeted strategy/report/backfill suite: `334 passed, 149 warnings, 57 subtests passed`.
- Report formatter/generator regression: `205 passed, 147 warnings, 44 subtests passed`.
- Evidence automation tests: `71 passed, 13 subtests passed`.
- Official generator dry-run: `v21.1`, `messages 4`, `write_results None`, no live Telegram delivery.
- Dry-run report confirmed standalone `距突破` in holding and unheld sections.
- Dry-run report confirmed state-aware wording for `等冷卻`, `等型態`, `等RR修復`, `等回測`, and strong-rebound holding cards.
- Dry-run report confirmed limit-up/overheat breakout context and bounded unheld group names in the after-hours brief.

## Known Follow-ups

- Confirm the next scheduled `run_mode=bot` writes market/theme evidence after the after-close safe-write window.
- Add a PowerShell-equivalent git completion gate because bash gates fail locally without WSL/Hyper-V.
- Optional dedicated cleanup task: Owner may delete abandoned `trades` table; current code scan found no consumers.
