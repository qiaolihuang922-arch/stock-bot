# DISPATCH.md

## Active

- task_md_holds: `future_watch_remove_history_events_20260626`
- status: `implemented + QA passed + pushed`
- current_version: `v21.1`
- live Telegram delivery: `not run`
- DB schema/write/backfill/delete: `none`

## Current Board

- 06/26 Owner failure specimen shows future-watch noise: `歷史類比` and `未來30日台股影響事件`.
- Code now removes both blocks from future-watch output.
- Default live future-watch source no longer queries historical TWSE analogy or global event source.
- Future-watch still keeps `未來30日法說會` and `關注標的財報`.
- QA passed; implementation pushed to `origin/main`.

## Recently Done

- `future_watch_remove_history_events_20260626`: removed future-watch `歷史類比` and `未來30日台股影響事件` from output and default live queries; QA passed; Git completion gate passed.
- `docs_local_env_cleanup_20260626`: root Markdown compressed, D-drive deployment runbook optimized, local bootstrap verified, and Git completion gate passed after commit/push.
- `local_d_drive_env_bootstrap_20260626`: installed D-drive portable Git/Bash, added local bootstrap scripts, verified pytest and `generate_report(dry_run=True)`, pushed to `origin/main`, and passed git/closeout gates.
- `report_actionability_consistency_v21_1_20260624`: v21.1 Telegram readability fixes were implemented, QA passed, and pushed. No live Telegram or DB writes.

## Next Action

- None for this task.
