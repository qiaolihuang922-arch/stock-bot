# DISPATCH.md

## Active

- task_md_holds: `rr_wording_readability_v21_1_20260615`
- status: `implemented + QA passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- Owner asked what `RR` means and said the wording is hard to understand.
- Report wording now uses `風險報酬` instead of raw `RR`, and replaces unclear theoretical RR wording with a direct potential-reward judgment.
- Summary and unheld cards now render:
  - `等風險報酬`
  - `風險報酬不足`
  - `潛在報酬：好（x倍），買點未成立`
- Strategy thresholds, buy/sell decisions, DB schema, and production data were not changed.

## Verification

- Formatter/generator regression:
  - `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run:
  - printed the unheld message and summary with `風險報酬` wording.
  - no live Telegram delivery.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- Commit and push this wording patch, then observe next scheduled `run_mode=bot` report.
