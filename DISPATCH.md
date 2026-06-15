# DISPATCH.md

## Active

- task_md_holds: `entry_quality_d_semantics_v21_1_20260615`
- status: `implemented + QA passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- Owner challenged why many cards show `D`, including limit-up or multi-day rising stocks.
- Root cause:
  - `market_grade` is per-stock technical state, not broad market state.
  - `entry_quality` is current entry setup quality, not a general stock score.
  - Report wording mixed these concepts, so limit-up / rebound could look like generic `D` weakness.
- Fix:
  - rebound/retest cards now say `買點品質：回測 / 轉強後重評`;
  - true setup cards say `買點品質未過（目前 D，需 B 以上）`;
  - unlocks say `買點品質 B 以上`;
  - recognized limit/rebound price behaviors are not overwritten to `等型態` only because entry quality is below B;
  - snapshot D reason now says `個股弱勢`, not `市場弱`.
- Strategy thresholds, DB schema, production data, and live Telegram were not changed.

## Verification

- Related regression:
  - `257 passed, 149 warnings, 44 subtests passed`.
- Official generator dry-run:
  - generated full message list with the new D semantics.
  - no live Telegram delivery.
- Snapshot probe:
  - limit-up sample: `market_grade=A+`, `entry_quality=D`, non-actionable due to chase / heat / RR.
  - multi-day rise sample: `market_grade=A+`, `entry_quality=C`, observation due to low RR.
  - weak rebound sample remains D.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- Commit and push `entry_quality_d_semantics_v21_1_20260615`, then observe next scheduled `run_mode=bot` report.
