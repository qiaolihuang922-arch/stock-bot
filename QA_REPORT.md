# QA_REPORT: summary_brief_mobile_denoise_20260616

## Test Scope

- Telegram third summary/brief message.
- Owner 06/16 pre-market failure specimen.
- Stale source warning exception.
- Existing generator message list regressions.

## Risk Scan

- Removing summary lines could hide an actionable warning.
- Removing normal source line must not hide stale `LAST_OHLCV`.
- Removing detail index must not affect holding order or card content.
- Removing generic reason/risk must not change strategy decisions.

## Cross-Block Semantic Consistency

- First message still carries holding details.
- Second message still carries unheld cards.
- Third message now carries only decision summary and action checklist.
- `詳情索引` is absent from the summary.
- Normal source plumbing is absent; stale source warnings remain covered by tests.
- Rejected main reason remains visible as `淘汰：N 檔｜主因：...`.
- No live Telegram delivery was performed.

## User Misread Risk

- Reduced: no more "details index" navigation line on mobile.
- Reduced: no generic source/reason/risk rows that read like system explanation instead of decision.
- Preserved: user still sees what to do today and which bucket unheld stocks are in.

## Failure Specimen Countercheck

- Owner sample asked to delete `詳情索引` and keep only useful decision info.
- Dry-run third message now contains:
  - market/action count;
  - `新倉：無有效進場`;
  - risk-control plan;
  - holding control checklist;
  - unheld status;
  - rejected main reason.
- Dry-run third message no longer contains:
  - `詳情索引`;
  - normal `📡 資料`;
  - `原因：`;
  - `風險：`;
  - `持倉：依第一則`;
  - `詳情見未持倉卡`.

## Evidence

- Focused test:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `203 passed, 44 subtests passed`
- Full test:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `479 passed, 8 skipped, 108 subtests passed`
- Dry-run:
  - `generate_report(dry_run=True)`
  - third-message forbidden counts all `0`.

## Not Tested

- Live Telegram delivery.
- Next production scheduled run after push.

## QA Conclusion

通過

Reason: official dry-run and regression tests confirm the summary is shorter while preserving actionable risk-control and stale-source safeguards.
