# DISPATCH.md

## Active

- task_md_holds: `strategy_readability_audit_v21_1_20260615`
- status: `implemented + QA passed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.

## Result Summary

- Owner challenged whether the previous patch was only hard text replacement.
- Report wording is now tied to strategy state instead of generic potential-reward wording.
- Summary and unheld cards now render:
  - `等風險報酬`
  - `風險報酬不足`
  - `潛在報酬：好（x倍），但型態/品質未過`
  - `潛在報酬：好（x倍），但尚未回測確認`
  - `潛在報酬：好（x倍），但反彈未轉強`
- Other report noise was normalized:
  - `setup` -> `買點型態`
  - `V10 / V20` -> `10日量 / 20日量`
  - readable spacing for quality and risk/reward thresholds.
- Strategy thresholds, buy/sell decisions, DB schema, and production data were not changed.

## Verification

- Formatter/generator regression:
  - `205 passed, 147 warnings, 44 subtests passed`.
- Official generator dry-run:
  - printed the unheld message and summary with state-aware wording.
  - scan confirmed no visible `setup`, `V10`, `V20`, `理論RR`, `理論風險報酬`, or unspaced `風險報酬>=`.
  - no live Telegram delivery.

## Current Git State

- branch: `main`
- upstream: `origin/main`
- closeout uses Windows-equivalent git checks because bash scripts may fail on this machine without WSL/Hyper-V.

## Next Action

- Commit and push this strategy-aware readability patch, then observe next scheduled `run_mode=bot` report.
