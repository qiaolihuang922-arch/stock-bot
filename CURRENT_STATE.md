# CURRENT_STATE.md

## Current Task

- task_id: `telegram_denoise_and_deployment_docs_20260608`
- status: `qa_passed`
- version: `v20.4.49`
- no live Telegram delivery.

## Stable Context

- Owner reads Telegram on mobile; Summary must answer decisions, but card details still matter per stock.
- Do not treat repeated per-stock structure as noise by itself.
- Production source-of-truth is Supabase / runner data, not local cache.
- DB schema/RLS/grant/policy/role/index/constraint changes require Owner approval.
- Fixed Markdown files must be rewritten/compressed, not removed.

## Current Changes

- Removed `.cao_agent_context/` stale runtime output.
- Deployment docs rewritten for WSL path:
  - Windows native CAO blocked by Unix `fcntl`.
  - WSL Ubuntu is the supported local path.
  - Codex binary copied to `/root/.local/bin/codex-real`.
  - Codex auth/config copied to `/root/.codex`.
  - Known unresolved gap: CAO/Codex TUI prompt/send automation can hang.
- Report patch implemented:
  - remove `【先看結論】`.
  - afterhours holding cards remove audit-like `條件` / `數據` / history lines.
  - afterhours rejected unheld cards remove diagnostic `盤面` / long reason / data / history lines.

## Verification State

- `py_compile` passed for current changed report files.
- focused pytest passed: 5 tests.
- official `generate_report(dry_run=True)` passed: 4 local preview messages, no live Telegram delivery.

## Known Follow-ups

- CAO TUI automation gap still needs a runner-level fix.
- Historical report suite is not clean; last known broader run had non-task strategy/funnel failures.
