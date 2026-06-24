# QA_REPORT: compact_actionable_buy_card_v21_1_20260624

## Test Scope

- Low-repair actionable buy-card rendering.
- Summary backtest noise filtering.
- Adjacent report readability paths: overheat, low repair, failed breakout, holding next step, direct actions, prepare.
- Official dry-run message-list rendering.

## Risk Scan

- Strategy risk: low. The patch changes display only; it does not change `low_repair_intraday_buy_ready` or buy/sell thresholds.
- DB risk: none.
- Live delivery risk: none.
- User misunderstanding risk reduced: a buyable card now starts with the trade instruction and shows one condition snapshot.

## Cross-Block Semantic Consistency

- Card title says `可買｜小倉｜低位修復成立`.
- Body says `小倉：可試單｜守支撐/5日均｜不追價`.
- Snapshot shows the same support / 5-day MA / volume status used by the low-repair logic.
- Trigger line no longer repeats separate buy-point or reason wording.
- Summary still lists the candidate under `新倉建議`.

## Failure Specimen Rebuttal

- Owner specimen: 06/24 光寶科 card was actionable but cluttered.
- Dry-run rebuttal:
  - contains `小倉：可試單｜守支撐/5日均｜不追價`.
  - contains one `低位修復：...` snapshot.
  - does not contain the old duplicate trade-state / buy-point / reason / data lines.
  - summary no longer shows the no-edge 光寶科 backtest line.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "low_repair"`
  - `5 passed, 220 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "low_repair or backtest_groups or direct_actions or prepare"`
  - `21 passed, 204 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "overheat or low_repair or failed_breakout or holding_next_step or risk_precedes or direct_actions or prepare"`
  - `27 passed, 198 deselected`.
- Official dry-run via `generator.generate_report(dry_run=True)`
  - `messages=4`.
  - `LOW_BUY_OLD_NOISE_ABSENT=True`.
  - `LOW_BUY_COMPACT_PRESENT=True`.
  - `NO_NO_EDGE_BACKTEST_SUMMARY=True`.

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write.
- DB backfill/prune/dedupe.

## QA Conclusion

通過。

The 06/24 user-visible buy-card readability issue is fixed on the formatter path and official dry-run path. This conclusion does not cover live Telegram delivery or DB writes, which were not part of this task.
