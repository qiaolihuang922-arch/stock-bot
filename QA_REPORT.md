# QA_REPORT: intraday_report_state_readability_v21_1_20260624

## Test Scope

- Intraday holding card phase wording.
- Low-repair near-ready display.
- Failed-breakout reclaim-zone display.
- Funnel grouping and current Telegram dry-run output.

## Risk Scan

- Strategy risk: medium-low. The patch adds one non-actionable display state and one near-ready display flag; it does not turn near-ready into `可買`.
- DB risk: none.
- Live delivery risk: none.
- User misunderstanding risk reduced:
  - `貼近可買` says exactly that the 5-day MA is still missing.
  - `等站回` says exactly which breakout zone must be reclaimed.
  - Intraday cards no longer say `明日處理`.

## Cross-Block Semantic Consistency

- 光寶科 near-ready card:
  - title: `貼近可買｜低位修復接近成立`
  - condition line: support OK, volume OK, 5-day MA close but not reclaimed.
  - trigger: reclaim 5-day MA before small-position trial.
- 旺宏 reclaim card:
  - title: `等站回｜突破失敗`
  - condition line: exact reclaim zone and price gap.
  - no duplicate trade-state or data line.
- Summary dry-run now includes `等站回1` under tracking, not under actionable buy.

## Failure Specimen Rebuttal

- Owner specimen: 06/24 intraday report showed confusing status changes and noisy non-actionable cards.
- Dry-run rebuttal:
  - `HAS_NEAR_BUY=True`.
  - `HAS_WAIT_RECLAIM=True`.
  - `INTRADAY_TOMORROW_LABEL=False`.
  - Holding cards show `盤中處理`.
  - 光寶科 shows `貼近可買`, not ordinary `等低位修復`.
  - 旺宏 shows `等站回`, not terminal淘汰.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -k "low_repair_near_ma5 or failed_breakout_card or warning_breached_holding"`
  - `3 passed, 223 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -k "low_repair or failed_breakout or warning_breached_holding or holding_next_step or compact"`
  - `11 passed, 215 deselected`.
- Official dry-run via `generator.generate_report(dry_run=True)`
  - `messages=4`.
  - `HAS_NEAR_BUY=True`.
  - `HAS_WAIT_RECLAIM=True`.
  - `INTRADAY_TOMORROW_LABEL=False`.

## Full-Test Finding

- Full `tests/test_generator_report.py` currently reports legacy expectation failures.
- The failures are not new runtime errors; they are stale text expectations around old `淘汰`, `有效買點`, and `明日處理` wording.
- QA does not use the full file as pass/fail for this task until those old specimens are separately updated or retired.

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write.
- DB backfill/prune/dedupe.

## QA Conclusion

通過。

The current Owner-visible 06/24 report issues are fixed on formatter, funnel state, and official dry-run paths. This conclusion does not cover live Telegram delivery or the known legacy full-test cleanup.
