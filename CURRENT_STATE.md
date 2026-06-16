# CURRENT_STATE.md

## Current Task

- task_id: `rebound_retest_source_gate_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed + pushed`
- version: `v21.1`
- no live Telegram delivery.
- no DB schema/write/backfill/prune.

## Stable Context

- Owner reads Telegram on mobile; report wording must be decision-first and avoid repeated rows.
- Production dispatch model: Render web service is called every five minutes, then GitHub workflow dispatch runs `run_mode=bot`.
- Production source-of-truth is Supabase / runner data, not local cache, worktree state, runtime dict, or agent memory.
- Cross-day memory must be DB backed. Same-run Yahoo/TWSE loader payload can support current indicators, not cross-day memory claims.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval unless explicitly authorized.
- Non-schema DB writes/backfills must use approved repo scripts or service APIs; direct hand-written production DML is forbidden.

## Current Implementation State

- Runtime report remains `v21.1`.
- Distance contract:
  - `<0`: 已突破
  - `<1`: 臨界突破
  - `<=5`: 接近突破
  - `>5`: 遠離突破
- `can_buy` now rejects distance only when `>5%`.
- Multi-day rebound repair:
  - uses DB-backed `cross_day_context.recent_daily_price_points`;
  - waits for recent repair support retest;
  - remains non-actionable until回測不破 + 非追高 + 量能有效.
- Source-only failures:
  - display as `等資料` / `不可行動`;
  - no longer become strategy淘汰 unless there is a real structural reject;
  - no longer show actionable RR as buying evidence.

## Verification State

- Focused report / strategy: `268 passed, 46 subtests passed`.
- Full pytest: `484 passed, 8 skipped, 110 subtests passed`.
- Official dry-run:
  - 聯電: `等資料｜策略樣本證據不足`
  - 群創: `等回測｜反彈修復待回測`
  - 旺宏: `等回測｜反彈修復待回測`

## Known Follow-ups

- Observe next production `run_mode=bot` artifact to confirm Render/GitHub runner uses this commit.
