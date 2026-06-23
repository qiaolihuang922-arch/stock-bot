# QA_REPORT: actionable_report_contract_v21_1_20260623

## Test Scope

- Holding card next-step wording.
- Sharp overheat pullback card contract.
- Low-repair mobile display contract.
- Failed-breakout reclaim-zone card contract.
- Prepare / not-yet-buyable summary label.
- Official dry-run message-list rendering.

## Risk Scan

- Strategy risk: medium. This changes action wording, not buy / sell thresholds or DB state.
- DB risk: none.
- Live delivery risk: none.
- User misunderstanding risk reduced:
  - holdings now show actionable risk prices.
  - overheat / low-repair cards now have one trigger line instead of repeated wait / buy-point / next-day lines.
  - failed breakout says exactly what zone must be reclaimed.
  - `可準備（不可買）` no longer appears on the official route; it is `準備觀察（待確認）`.

## Cross-Block Semantic Consistency

- Holdings: `風控` line and `明日處理` now use the same warning / stop prices.
- Overheat sharp pullback: title, body, and trigger all wait for stop / support confirmation.
- Low repair: card shows support / MA / volume snapshot, then one trigger.
- Failed breakout: title, gap, and trigger all require reclaiming the same breakout zone.
- Summary still says `新倉：無有效進場`; this matches card actionability.

## Failure Specimen Rebuttal

- Owner specimen: 06/23 report asked the reader to infer too much from generic wording.
- Dry-run rebuttal:
  - holding summary includes `跌破警戒 ... 續減，跌破停損 ... 停損`.
  - overheat cards no longer contain `等待：熱度`.
  - low-repair cards have a single `明日觸發`.
  - failed breakout contains `不可買：突破失敗，尚未站回突破區 ...`.
  - summary uses `準備觀察 1（待確認）`.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "overheat_pullback_display_switches_from_cooling_to_retest or overheat_sharp_pullback_display_focuses_on_support or low_repair_compact_lines_show_real_missing_condition_only or failed_breakout_card_does_not_show_attack_volume_as_positive or holding_next_step_uses_risk_prices_not_breakout_zone"`
  - `5 passed, 220 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "overheat or low_repair or failed_breakout or holding_next_step or risk_precedes or direct_actions or prepare"`
  - `27 passed, 198 deselected`.
- Official dry-run via `generator.generate_report(dry_run=True)`
  - `messages=4`, `NO_WAIT_EFFECTIVE_DUP=True`, `LOW_REPAIR_ONE_TRIGGER=True`, `FAILED_BREAKOUT_COMPACT=True`, `SUMMARY_RISK_PRICE=True`.

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write.
- DB backfill/prune/dedupe.

## QA Conclusion

通過.

The requested 06/23 user-visible readability path is fixed by focused tests, the broader related report subset, and official dry-run. This conclusion does not cover live Telegram or DB writes, which were not part of this task.
