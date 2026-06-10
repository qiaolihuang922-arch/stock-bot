# QA_REPORT: render_dispatch_writeback_logic_20260610

## Scope
- Render five-minute dispatch logic.
- Close-window writeback/preflight timing.
- GitHub workflow dispatch-only contract.
- Regression that Phase3 evidence path remains intact.

## Risk Scan
- Native GitHub cron could bypass Render's sent-tag and close-stop logic.
- Close preflight before `14:00` could skip market/theme writes forever because Render would stop dispatching afterward.
- Ten-minute intraday buckets conflict with the intended five-minute Render cadence.
- Dispatch without explicit run mode could become ambiguous later.

## Semantic Consistency
- Render is the scheduler.
- GitHub workflow is an execution target.
- Market/theme freshness preflight runs before workflow dispatch.
- Close dispatch now starts at the safe-write window instead of before it.
- No live Telegram delivery was executed.

## Failure Specimen Countercheck
- Before correction:
  - MD and workflow claimed GitHub schedule was the main timing fix.
  - `app.py` close dispatch started at `13:20`, before the default `14:00` freshness safe-write time.
  - Intraday bucket was `minute // 10`.
- After correction:
  - GitHub workflow has no `schedule:` or `github.event.schedule` mapping.
  - `13:25` returns skip in the Render route.
  - `14:05` runs freshness, checks sent tag, dispatches GitHub, then marks sent.
  - Intraday buckets are five-minute buckets.

## Additional Challenge
- Verified dispatch payload includes `inputs.run_mode=bot`, making Render intent explicit.
- Re-ran Phase3 evidence tests to ensure previous freshness/backfill helper logic remains intact.

## Not Tested
- Live Telegram delivery.
- Live Render external ping service.
- Live GitHub Actions run after this correction push.

## QA Conclusion
conditional pass

Reason: local route and workflow contract tests pass; live Render/GitHub execution can only be proven after push and next external ping.
