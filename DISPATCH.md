# DISPATCH.md

## Active

- task_md_holds: `unheld_readability_v21_1_20260615`
- status: `implemented + QA passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- The v21.1 unheld Telegram cards were hard to read because they exposed internal diagnostics as the primary explanation.
- Unheld blocker cards now use a decision-first structure:
  - `不能買：...`
  - `還差：...`
  - `可買條件：...`
- Long strategy evidence is compacted without changing decisions:
  - `RR 1.32→1.5（差0.18）`
  - `品質 D→B以上`
  - `量能偏弱（V10 ... / V20 ...）`
  - `站回突破區 ...`
  - `理論RR ...僅參考`
- Buy/sell logic, thresholds, DB schema, and persistence were not changed.

## Verification

- Formatter/generator regression:
  - `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run:
  - printed the unheld message with `不能買 / 還差 / 可買條件`.
  - no live Telegram delivery.
- Covered paths:
  - RR不足;
  - overheat / limit-up chase;
  - sharp rebound waiting for retest;
  - weak setup / quality D;
  - source/sample errors;
  - post-market prepare.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- closeout uses Windows-equivalent git checks because bash completion gates may fail on this machine without WSL/Hyper-V.

## Next Action

- Observe next scheduled `run_mode=bot` report after push.
