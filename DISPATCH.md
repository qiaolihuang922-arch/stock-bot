# DISPATCH.md

## Active

- task_md_holds: `strategy_axis_split_v21_1_20260615`
- status: `implemented + QA passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- Owner said the system still looks unable to buy: lows, limit-up moves, and multi-day rises can all be blocked in the same way.
- Root cause:
  - one visible grade was carrying too many meanings: stock strength, entry setup, and executable action;
  - replay payloads could also keep stale derived labels after explicit behavior was changed.
- Fix:
  - add three strategy axes: `強弱`, `買點`, `行動`;
  - render them in unheld Telegram cards;
  - make explicit behavior evidence override stale derived labels;
  - preserve conservative action rules for limit-up, overheated, retest, RR, volume, and setup blockers.
- Strategy thresholds, DB schema, production data, and live Telegram were not changed.

## Verification

- Related regression:
  - `258 passed, 149 warnings, 44 subtests passed`.
- Official generator dry-run:
  - generated unheld message with split axis lines.
  - no live Telegram delivery.
- Snapshot probes:
  - confirmed breakout can be `READY` / `BUYABLE`;
  - limit-up is strong but not chaseable;
  - rebound can be strong/improving but still wait for retest.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- Commit and push `strategy_axis_split_v21_1_20260615`, then observe next scheduled `run_mode=bot` report.
