# QA_REPORT: report_actionability_readability_v21_1_20260624

## Test Scope

- Low-repair near-ready wording and non-actionable status.
- Low-repair missing-only trigger lines.
- Failed-breakout reclaim-zone routing and display.
- History-line engineering-term suppression.
- Summary zero-count / standalone-backtest noise removal.
- Official dry-run Telegram message list.

## Risk Scan

- Strategy risk: medium. Failed-breakout reclaim watch band widened from 5% to 7%, but only when a real reclaim zone exists and it remains non-actionable `等站回`.
- Buy-action risk: low. `貼近條件` and `準備觀察` are explicitly not `可買`.
- DB risk: none.
- Live delivery risk: none.

## Cross-Block Semantic Consistency

- 光寶科 near-ready now reads `貼近條件｜等站回5日均`; it does not read like a buy signal.
- Low-repair cards now show missing conditions only in the trigger line.
- Failed-breakout cards in the reclaim watch band show `等站回` with the actual zone and gap.
- Summary no longer prints zero-count lines or standalone backtest snippets for non-actionable prepare-only cards.

## Failure Specimen Rebuttal

- Owner specimen: 06/24 intraday report where 光寶科 appeared to oscillate between buy and wait, and reports remained noisy on mobile.
- Official dry-run rebuttal:
  - `HAS_NEAR_BUY=False`.
  - `HAS_NEAR_CONDITION=True`.
  - `HAS_WAIT_RECLAIM=True`.
  - `HAS_ELIMINATED=False`.
  - `HAS_ZERO_ACTION=False`.
  - `INTRADAY_TOMORROW_LABEL=False`.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -k "low_repair_near_ma5 or low_repair_compact_lines or failed_breakout_card or failed_breakout_within_reclaim_buffer or rejected_card_suppresses_positive_repair_history"`
  - `5 passed, 222 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -k "low_repair or failed_breakout or rejected_card_suppresses_positive_repair_history or holding_next_step or compact_market"`
  - `10 passed, 217 deselected`.
- Official dry-run via `generator.generate_report(dry_run=True)`
  - `messages=4`.
  - all readability booleans matched the task acceptance criteria.

## User Misread Check

- `貼近條件` is safer than `貼近可買`; it says the setup is close, not actionable.
- `追價不划算` explains low RR after breakout in reader language.
- `站回觀察` avoids the contradiction of `等站回` plus `遠離突破` near the 7% reclaim band.
- `量能 1x 剛好` is more informative than `OK`.

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write.
- DB backfill/prune/dedupe.
- Full legacy test file as a pass gate; stale wording expectations remain known cleanup debt.

## QA Conclusion

通過。

The current Owner-visible readability and actionability conflicts are fixed on formatter, funnel state, and official dry-run paths. This conclusion does not cover live Telegram delivery or production DB mutation.
