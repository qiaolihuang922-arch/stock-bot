# DISPATCH.md

## Active

- task_md_holds: `strategy_soft_gate_patch_v21_1_20260616`
- status: `implemented + QA pass`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner pointed out that the mobile report still read like repeated mechanical gates:
  - holdings repeated `缺口 / 可恢復 / 下一步`.
  - `等冷卻`, `等回測`, `等型態`, `等接近` reused similar `進場 / 缺口 / 可買 / 觸發` lines even when the strategy state was different.
- Implemented state-specific Telegram card templates:
  - holdings now use one decision line plus one `明日處理` line.
  - `等冷卻` now shows `狀態` and `等待` with the effective cooling trigger.
  - `等回測` now shows `狀態`, concrete `回測` anchor, and `有效買點`.
  - `等回測` rebound anchors that come from the latest rebound close now show `回測基準 ...；尚未回測`, so current close is not misread as a completed pullback.
  - `等型態` now shows `狀態`, `等待`, and `有效買點`.
  - `等接近` keeps breakout distance and one explicit breakout zone reference only.
- Strategy thresholds, DB data, replay data, Render/GitHub dispatch, and Telegram sender were not changed.

## Verification

- Targeted report/state tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_trade_state_machine.py -q --tb=short`
  - result: `215 passed, 155 warnings, 46 subtests passed`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Official generator dry-run:
  - result: `4` messages generated, no live Telegram.
  - verified unheld cards now use state-specific lines for cold / setup / near-trigger / retest cases.

## Current Git State

- branch: `main`
- implementation commit: recorded in git after final commit.
- git completion gate: passed after push.

## Next Action

- Watch the next official runner artifact / Telegram dry-run for mobile readability regressions.
