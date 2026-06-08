# QA_REPORT: render_git_tg_db_pipeline_check_20260609

## Scope
- Render dispatch target.
- GitHub workflow daily evidence and bot separation.
- Telegram sender failure guard.
- Official generator dry-run.
- Daily DB tables and market-theme evidence freshness.

## Risk Scan
- Render may call a missing workflow file and never trigger GitHub Actions.
- Daily evidence may fail before writing DB if a payload secret is absent.
- Bot mode must not run during daily evidence mode.
- Dry-run must not write DB.
- Telegram failure must not mark a message as sent.

## Semantic Consistency
- Render now dispatches `stock-bot-clean.yml`, matching the actual workflow file.
- Workflow still supports `MARKET_THEME_APPROVED_PAYLOAD`, but no longer requires it for official TWSE payload generation.
- `generate_report(dry_run=True, return_write_results=True)` returns `write_results {}`.
- DB read-after-write confirms daily rows exist after backfill.

## Failure Specimen Countercheck
- Render mismatch: fixed and covered by `test_render_dispatch_targets_existing_workflow_file`.
- Market-theme gap: before backfill, recent rows stopped at 2026-06-03; after approved freshness script, 2026-06-04, 2026-06-05, and 2026-06-08 are present and verified.

## Additional Challenge
- Ran Telegram guard tests to ensure no false success on failed delivery.
- Ran daily/evidence/cross-day tests to ensure DB source-of-truth paths still fail closed.

## Not Tested
- Live Telegram delivery was not run.
- Live Render HTTP dispatch to GitHub was not run.
- GitHub Actions UI status was not queried with authenticated `gh`.

## QA Conclusion
通過
