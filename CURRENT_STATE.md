# CURRENT_STATE.md

## Current Task

- task_id: `holding_card_contract_v21_1_20260616`
- status: `implemented + QA passed + pushed`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid repeated rows.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, or agent memory.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Holding card contract:
  - visible: `倉位 / 風控 / 盤面 / 距突破 / 決策 / 缺口 / 可續抱或可恢復或再進場 / 下一步 / 價格`;
  - hidden from holding cards: `交易狀態 / 數據 / 回測 / 歷史`;
  - stop-loss and take-profit execution-memory fail-closed wording remains visible when needed.
- No DB operation was performed.

## Verification State

- Targeted tests: `203 passed, 44 subtests passed`.
- Full tests: `479 passed, 8 skipped, 108 subtests passed`.
- Dry-run official generator checked locally.

## Known Follow-ups

- Observe next scheduled `run_mode=bot` report and confirm production Telegram artifact matches dry-run wording.
- If production still shows old holding-card rows, inspect runner commit/deployment path first.
