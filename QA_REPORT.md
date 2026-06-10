# QA_REPORT: future_watch_source_and_card_denoise_20260610

## Scope
- Official v21.0.2 report route.
- TWSE historical source fallback behavior.
- TWSE/TPEX fundamentals revenue source coverage.
- Compact unheld wait-card readability.

## Risk Scan
- Retrying TWSE could mask persistent source failures.
- New TWSE revenue endpoint could overwrite EPS or TPEX revenue incorrectly.
- Compact cards could hide action-critical fields.
- Version bump could desync tests and visible headers.

## Semantic Consistency
- Source failures still fail closed and do not invent analogy data.
- Compact cards still show non-actionable state, blocker, gap, unlock, trigger, and price.
- Listed-stock revenue fills from TWSE OpenAPI before relying on MOPS refresh.
- State-machine schema remains `v21.0.1`; report header is `v21.0.2`.

## Failure Specimen Countercheck
- Owner specimen showed:
  - `歷史類比... source-error`
  - EPS-only rows for some stocks.
  - Long repeated `等接近` cards.
- Official dry-run now shows:
  - `【06/10 盤後｜v21.0.2】`
  - compact `等接近` card without low-signal RR/data rows.
  - 2303 and 2301 with `營收 2026/05`.
  - historical source available in this run; source-error path has a tested human-readable fail-closed line.

## Additional Challenge
- Tested source helper behavior separately from final generator.
- Ran official dry-run after tests to inspect user-visible text.

## Not Tested
- Live Telegram delivery.
- Production DB writes/backfill.
- GitHub Actions live run.

## QA Conclusion
通過
