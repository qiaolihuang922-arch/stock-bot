# CURRENT_STATE.md

## Current Task

- task_id: `strategy_soft_gate_patch_v21_1_20260616`
- status: `implemented + QA pass`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.

## Stable Context

- Owner reads Telegram on mobile; card wording must show the current actionable state, not repeat the same condition under several labels.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Strategy soft-gate patch remains in place:
  - `LIMIT_LOCK`, `EXTREME`, `AVOID`, failed breakout, and `RR < 1.0` are hard gates.
  - HOT / EXTENDED / LIMIT_REBOUND / low-RR-near-setup are soft gates when evidence supports preparation.
  - Soft gates can become `可準備`, not direct `可買`.
- Telegram card display is now state-specific:
  - holdings: `決策` plus `明日處理`.
  - `等冷卻`: `狀態` plus `等待`.
  - `等回測`: `狀態` plus concrete `回測` anchor plus `有效買點`.
  - rebound-close `等回測`: `回測基準 ...；尚未回測`, not completed retest wording.
  - `等型態`: `狀態` plus `等待` plus `有效買點`.
  - `等接近`: `進場` plus `等待`, with only one breakout zone reference.

## Verification State

- Full pytest passed:
  - `489 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Targeted report/state tests passed:
  - `215 passed, 155 warnings, 46 subtests passed`
- Official generator dry-run generated `4` messages and showed the updated mobile card contract.

## Known Findings

- `.pytest_cache` cannot be written on this machine because of local `WinError 5`; tests still execute and pass.
- Rule outcome audit from the earlier soft-gate cycle still has future calibration work, but this display cycle did not alter strategy thresholds.

## Next Action

- Watch the next official runner artifact / Telegram dry-run for mobile readability regressions.
