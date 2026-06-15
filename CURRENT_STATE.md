# CURRENT_STATE.md

## Current Task

- task_id: `strategy_feature_persistence_v21_1_20260615`
- status: `complete`
- version: `v21.1`
- no live Telegram delivery.
- production DB backfill was executed through approved repo scripts only.

## Stable Context

- Owner reads Telegram on mobile; wording must be decision-first and avoid internal pipeline noise.
- Production dispatch model is Render web service called every five minutes, then GitHub workflow dispatch.
- Production source-of-truth remains Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes normally require Owner approval; Owner authorized adding fields / more recording for this task.
- Non-schema DB write/backfill must use existing approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Changes

- v21.1 strategy features are no longer report-only.
- Market/theme evidence stale-row root cause:
  - normal bot path writes `daily_price` / `daily_signal_snapshot`;
  - market/theme evidence writes live under `run_mode=daily_evidence`;
  - workflow previously had no schedule, only manual dispatch.
- `.github/workflows/stock-bot-clean.yml` now runs market/theme freshness inside normal `run_mode=bot` after the bot step.
- `daily_evidence` remains available only as a manual recovery mode.
- New SQL artifact adds typed strategy-feature columns to:
  - `daily_signal_snapshot`
  - `signal_items`
- Daily snapshot, report item persistence, and backfill rows now carry:
  - V10/V20 volume;
  - 20D/60D resistance;
  - 20D/60D breakout prices and distances;
  - retest zone;
  - compact raw_result where applicable.
- Schema-missing fallback keeps runner/backfill from crashing before migration is applied.
- `backfill_signals.py` now supports `--lookback-days`.
- Owner applied the SQL migration; schema was verified read-only before backfill.
- v21.1 strategy-feature backfill has been executed for the 12 tracked stocks.
- market/theme evidence gaps for `2026-06-11`, `2026-06-12`, and `2026-06-15` have been filled.
- `daily_signal_snapshot` old-version overlap cleanup has been executed through approved repo script.
- Residual old-version rows were traced to TWSE historical source gaps for `2303` 2026/04 and `2301` 2026/05; both months existed in `daily_price`.

## Backfill Decision

- Completed strategy-feature backfill: `730` calendar days.
- Reason:
  - 60D resistance needs enough warmup;
  - outcome calibration needs repeated 1/3/5/10-day forward samples across regimes;
  - Owner said two years of DB data should exist.
- Script warmup: `120` calendar days before requested start.
- Result:
  - `daily_signal_snapshot` v21.1 total rows: `5112`.
  - All 12 tracked stocks have v21.1 snapshots through `2026-06-15`.
  - v21.1 feature columns are non-null on all `5112` v21.1 rows.
  - No live Telegram delivery.
- Cleanup result:
  - Added `scripts/prune_daily_signal_snapshot_versions.py`.
  - Added `scripts/backfill_snapshots_from_daily_price.py`.
  - Deleted `1670` old-version rows only where the same `stock_id` / `trade_date` had `v21.1`.
  - Rebuilt missing v21.1 snapshots from existing `daily_price`:
    - `2303` 2026/04: 20 rows.
    - `2301` 2026/05: 20 rows.
- Deleted the remaining `118` old-version rows after v21.1 replacements existed.
- Post-cleanup total rows: `5152`; v21.1 rows: `5152`; old versions: `0`; overlap old-with-v21.1: `0`.

## Report Readability Follow-up

- Root cause of Owner's v21.1 report issue:
  - `旺宏` used the dedicated `急彈待回測` formatter branch, so it showed retest zone, V10/V20 volume, quality, and RR details.
  - other waiting states such as `等型態` / `等RR修復` fell back to generic gap text, so cards looked inconsistent and hid the same class of decision evidence.
- `presentation/report.py` now shares compact setup context for non-actionable unheld cards:
  - retest / breakout zone where available;
  - breakout distance;
  - V10/V20 volume status;
  - RR status.
- After-hours waiting / rejected tracking cards suppress redundant `盤面：證據不足｜待確認` and `數據：...風控不適用` lines when `量化差距` already carries the decision evidence.
- Strategy logic was not changed in this follow-up; this is report presentation / noise reduction only.
- Breakout distance display follow-up:
  - holding and unheld cards now show `距突破：x%｜狀態` as a standalone line when breakout distance exists;
  - `盤面` line no longer carries the distance segment;
  - the standalone line is display-only and does not depend on whether the strategy is using breakout, retest, trend continuation, RR repair, cooling, or rejection.

## Verification State

- Focused persistence/backfill/calibration:
  - `19 passed`.
- Targeted strategy/report/backfill suite:
  - `334 passed, 149 warnings, 57 subtests passed`.
- Official generator dry-run:
  - `v21.1`;
  - `messages 4`;
  - `write_results None`.
- TWSE v21.1 strategy backfill:
  - approved script used: `scripts/backfill_signals.py`;
  - version: `v21.1`;
  - source: `twse`;
  - `schema_fallback=False` on completed single-stock writes.
- Market/theme freshness / backfill check:
  - `2026-06-10` complete;
  - `2026-06-11` complete after backfill;
  - `2026-06-12` complete after backfill;
  - `2026-06-13`, `2026-06-14` weekend / no rows expected;
  - `2026-06-15` complete after backfill.
- Evidence automation tests:
  - `71 passed, 13 subtests passed`.
- Cleanup script tests:
  - `tests/test_prune_daily_signal_snapshot_versions.py`: `2 passed`.
- Report readability tests:
  - `tests/test_unheld_gap_format.py tests/test_generator_report.py`: `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run confirmed standalone `距突破` lines in both holding and unheld report sections, with no live Telegram delivery.

## Git State

- branch: `main`
- upstream: `origin/main`
- HEAD equals upstream: `yes`
- worktree: clean except local `.pytest_cache` permission warning.
- bash completion gate could not run because WSL/Hyper-V is unavailable; Windows-equivalent git checks passed.

## Known Follow-ups

- Market/theme evidence should resume through the normal bot workflow after the after-close safe-write window.
- Owner said `trades` is abandoned and will delete it directly; no repo code depends on `.table("trades")` / `.from("trades")` from the latest scan.
