# DISPATCH.md

## Active

- task_md_holds: `strategy_feature_persistence_v21_1_20260615`
- status: `complete`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- v21.1 strategy features are persisted through repo-supported paths:
  - SQL artifact: `db/sql/v21_1_strategy_feature_snapshot_columns.sql`.
  - Writers/backfill carry V10/V20, 20D/60D resistance, breakout distances, retest zone, and compact `raw_result`.
  - Writer paths have schema-missing fallback so runner does not crash before migration.
- Normal `run_mode=bot` now also runs market/theme evidence freshness after the bot step; `daily_evidence` stays as manual recovery.
- Approved backfill/cleanup completed through repo scripts:
  - two-year v21.1 strategy snapshot backfill with 120-day warmup;
  - market/theme evidence gaps for 2026-06-11, 2026-06-12, 2026-06-15 filled;
  - `daily_signal_snapshot` cleaned to only `v21.1`, with old-overlap duplicates removed.
- Telegram report readability fixed:
  - non-actionable unheld cards share compact setup evidence instead of only `急彈待回測` showing rich details;
  - redundant after-hours internal lines are suppressed when `量化差距` already carries the decision evidence;
  - `距突破：x%｜狀態` is a standalone line for holding and unheld cards whenever data exists;
  - `盤面` no longer embeds `遠離突破（x%）` / `接近突破（x%）`.
- Strategy-granular report wording added:
  - `等冷卻` shows heat/cooling blockers and hides internal `RR -（過熱）` / `風控不適用` data noise;
  - `等型態`, `等回測`, and `等RR修復` use `補充：...但...未過/未確認/未達標` instead of presenting positive evidence as a buy reason;
  - strong rebound holding watch uses rebound-continuation wording instead of weak-template downgrade wording.

## Verification

- Persistence/backfill/calibration focused tests: `19 passed`.
- Targeted strategy/report/backfill suite: `334 passed, 149 warnings, 57 subtests passed`.
- Report formatter/generator regression: `205 passed, 147 warnings, 44 subtests passed`.
- Evidence automation tests: `71 passed, 13 subtests passed`.
- Official generator dry-run: `VERSION v21.1`, `messages 4`, `write_results None`, no live delivery.
- Dry-run report confirmed standalone `距突破` lines in holding and unheld sections.
- Dry-run report confirmed strategy-granular wording in cooling, setup, RR-repair, retest, and strong-rebound holding cards.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- HEAD/upstream checked at closeout; final response reports the exact commit.
- worktree expected clean except local `.pytest_cache` permission warning.
- bash completion gate cannot run on this machine because WSL/Hyper-V is unavailable; Windows-equivalent git checks have been used.

## Next Action

- Monitor the next normal `run_mode=bot` after the after-close safe-write window to confirm market/theme evidence freshness continues automatically.
- Optional DB cleanup remains separate: Owner said abandoned `trades` table may be deleted manually; no latest code scan found `.table("trades")` / `.from("trades")` consumers.
