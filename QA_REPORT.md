# QA_REPORT: report_state_sync_v21_1_20260617

## Test Scope

- User-visible Telegram card formatting for the Owner-pasted `06/17 收盤｜v21.1` conflict patterns.
- Retest-state wording.
- Holding warning-line breach wording.
- Overheat / limit-up wording separation.
- Wait-volume condition specificity.
- After-hours summary noise removal.

## Risk Scan

- DB schema change: not used.
- DB write/backfill/delete: not used.
- Live Telegram: not used.
- Strategy core rewrite: not used.
- Persisted production data: unchanged.

## Cross-Block Semantic Checks

- A retest basis below/above current price now changes the card wording; it is no longer a fixed phrase.
- Holding card risk reason now overrides stale `未跌破風控` text when price is below warning.
- Overheat cards use limit-up wording only when current behavior/change is limit-like.
- Wait-volume cards show a numeric gap instead of repeating `量能回升後再評估`.
- Summary no longer repeats empty or duplicate sections that do not change the decision.

## Failure Specimen Rebuttal

- `2337 旺宏`: regression test and official dry-run prove `最近反彈收盤 166.5` below-current conflict no longer renders `尚未回測`; it renders `已跌破，等待重新站回或形成新支撐` when price is below the basis.
- `2421 建準`: regression test and official dry-run prove price below warning renders `已跌破警戒，未到停損`.
- `2344/2408`: regression test and official dry-run prove non-limit overheat renders `短線過熱，先等冷卻`; limit wording remains available for true near-limit cards such as `3481 群創`.
- `2303 聯電`: regression test and official dry-run prove `等量能` now includes current volume ratio and target threshold.
- Summary: official dry-run proves `新增交易建議：無`, duplicate `明日計畫`, and duplicate `未持倉僅追蹤...不列入明日計畫` are absent.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "retest_basis or warning_breached or non_limit_overheat or wait_volume_card or db_backed_rebound_pullback" --tb=short`
  - result: `5 passed`
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `215 passed`, `46 subtests passed`
- `.\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_trade_state_machine.py tests\test_strategy_buy_path_replay.py tests\test_strategy_rule_outcomes.py -q --tb=short`
  - result: `16 passed`
- `generate_report(dry_run=True)`
  - result: `4` messages, no live Telegram.

## Not Tested

- Live Telegram delivery.
- Render/GitHub scheduled production run.
- DB write/read-after-write, because this cycle had no DB writes.

## QA Conclusion

通過.

The report-state conflicts identified by Owner are covered by regression tests and official dry-run output.
