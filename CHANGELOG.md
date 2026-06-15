# CHANGELOG: summary_brief_mobile_denoise_20260616

## Changes

- Removed `detail_index_text(...)` rendering from `presentation.report.formatTelegramSummary`.
- Added summary extraction filters for generic rows:
  - `原因：...`
  - `風險：...`
  - `持倉：依第一則...`
  - `📎 詳情索引：...`
- Normal source line is removed from the brief when it is only `realtime/yahoo` plumbing.
- Stale `LAST_OHLCV` source warning remains visible because it affects actionability.
- `_brief_holding_line` no longer emits the fixed "依第一則既有卡片處理" line for ordinary holdings; it still emits meaningful exceptions such as no holdings or missing profit-taking memory.
- `rejected_trace_line` now renders `淘汰：N 檔｜主因：...` and no longer appends `詳情見未持倉卡`.
- Updated generator report tests to enforce the compact summary contract and stale-source exception.

## Contract Impact

- Telegram third summary/brief message is shorter and decision-focused.
- Holding cards, unheld cards, strategy calculations, trade-state machine, DB writes, and live delivery are unchanged.
- Runtime report version remains `v21.1`.

## Direct Consumer Sync

- Owner mobile reading should now see:
  - market/action count;
  - new-entry status;
  - today's risk-control plan;
  - holding control checklist;
  - unheld status/funnel;
  - rejected main reason.
- Removed rows are plumbing or navigation, not decisions.

## Verification

- External guideline check:
  - dashboard / executive summary guidance emphasizes decision-specific KPIs and avoiding clutter.
- Local dry-run:
  - `generate_report(dry_run=True)`
  - summary counts: `詳情索引=0`, `📡 資料=0`, `原因=0`, `風險=0`, `持倉：依第一則=0`, `詳情見未持倉卡=0`.
- Test commands:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `203 passed, 44 subtests passed`
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `479 passed, 8 skipped, 108 subtests passed`

## Covered Layers

- Summary formatter.
- Official Telegram generator message list.
- User-visible dry-run replay.

## Residual Risk

- Production scheduled run still needs observation after push.
- `detail_index_text` helper remains for compatibility but is not rendered in the official summary path.
