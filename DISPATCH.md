# DISPATCH.md

## Active

- task_md_holds: `strategy_soft_gate_patch_v21_1_20260616`
- status: `implemented + QA pass + git closeout ready`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner asked to stop strategy deadlocks after DB replay showed hot / limit-up / low-RR / broad quality-D gates could be too strict.
- Implemented soft-gate strategy split:
  - `LIMIT_LOCK`, `EXTREME`, `AVOID`, `RR < 1.0`, failed breakout remain hard blocks.
  - `HOT`, `EXTENDED`, `LIMIT_REBOUND`, and low-RR near setup become soft blocks only when evidence/shape supports preparation.
  - Limit-up rebound no longer becomes fake `等資料`; it is `隔日確認`.
  - Confirmed/supporting evidence can promote soft-gated names to `可準備`, not `可買`.
- Mobile report wording is unchanged in version header but no longer marks HOT / LIMIT_REBOUND evidence as unavailable by default.
- `等接近` mobile card was de-duplicated:
  - keeps breakout distance and one breakout zone reference.
  - replaces repeated `進場 / 缺口 / 可買 / 明日觸發` wording with `進場 / 等待 / 觸發`.
  - no DB or strategy threshold change.

## Verification

- Generator report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `206 passed, 153 warnings, 46 subtests passed`
- Full tests:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Dry-run official generator:
  - result: `4` messages generated, no live Telegram.
- DB replay after patch:
  - `reports/audit/strategy_buy_path_replay_v21_1_soft_gates_20260616.json`
  - `deadlock_suspected=false`
  - `has_real_buyable_path=true`
  - `has_prepare_path=true`
  - `funnel_blocks_snapshot_tradeable=false`
  - `可買 700`, `可準備 364`
- Rule outcome audit after patch:
  - `reports/audit/strategy_rule_outcomes_v21_1_soft_gates_20260616.json`
  - still flags 7 categories for future sub-classification, but current hard-gate deadlock is reduced.

## Current Git State

- branch: `main`
- implementation commit: `622cf6d`
- completion: ready for push / git completion gate.

## Next Action

- Push, then run git completion and closeout gates.
