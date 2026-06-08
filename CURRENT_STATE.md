# CURRENT_STATE.md

## Current Task

- task_id: `unheld_volume_tracking_reclassification_20260608`
- status: `qa_passed`
- version: `v20.4.55`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; visible wording must be decision-first and avoid internal pipeline terms.
- 未持倉標的要分清：現在可買、可準備、僅追蹤、淘汰。
- `量能不足` 或遠離突破不等於永久淘汰；若結構沒壞，應列追蹤並等待確認。
- EPS / revenue visibility is per watched stock, not dependent on whether that stock has a MOPS meeting.
- Revenue label is user-facing `營收`; internal source field remains monthly revenue YoY from TWSE/TPEX.
- Historical analogy is context, not prediction or trade instruction.
- Production source-of-truth is Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Fixed Markdown files must be rewritten/compressed, not removed.

## Current Changes

- Version bumped to `v20.4.55`.
- `量能不足` unheld candidates now stay in `僅追蹤/等量能` unless structurally broken.
- If volume is weak and the stock is still far from breakout, trigger requires both volume recovery and re-approach to buy area.
- Unheld reject reason fallback now keeps true reject reason instead of showing RR noise.

## Verification State

- focused pytest passed: 3 tests.
- broader focused pytest passed: 9 tests.
- `py_compile` passed.
- market theme tests passed: 38 tests, 13 subtests.
- official `generate_report(dry_run=True)` passed: 4 local preview messages, no live Telegram delivery.
- official dry-run unheld summary: `未持倉 7｜僅追蹤 7（等回測1/等量能6）`.

## Known Follow-ups

- CAO TUI automation gap still needs a runner-level fix.
- Historical sample library is now 19 internal Taiwan crash/stress templates; full research-grade historical DB remains a separate task.
