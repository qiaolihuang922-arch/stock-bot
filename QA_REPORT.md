# QA_REPORT: actionable_report_contract_v21_1_20260623

## Test Scope

- Holding card next-step wording.
- Sharp overheat pullback card contract.
- Failed-breakout reclaim-zone card contract.
- Official dry-run message-list rendering.

## Risk Scan

- Strategy risk: medium. This changes action wording, not buy / sell thresholds or DB state.
- DB risk: none.
- Live delivery risk: none.
- User misunderstanding risk reduced:
  - holdings now show actionable risk prices.
  - sharp pullback no longer reads as generic "do not chase".
  - failed breakout says exactly what zone must be reclaimed.

## Cross-Block Semantic Consistency

- Holdings: `風控` line and `明日處理` now use the same warning / stop prices.
- Overheat sharp pullback: title, body, effective buy point, and trigger all wait for stop / support confirmation.
- Failed breakout: title, gap, and buy condition all require reclaiming the same breakout zone.
- Summary still says `新倉：無有效進場`; this matches card actionability.

## Failure Specimen Rebuttal

- Owner specimen: 06/23 report asked the reader to infer too much from generic wording.
- Dry-run rebuttal:
  - holding cards include `跌破警戒 ... 續減，跌破停損 ... 停損`.
  - 南亞科 includes `急殺回測，先不接刀`.
  - 旺宏 includes `尚未站回突破區 175.5~176.38（現價 172，差 3.5）`.
  - summary includes `新倉：無有效進場`.

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "overheat_pullback_display_switches_from_cooling_to_retest or overheat_sharp_pullback_display_focuses_on_support or low_repair_compact_lines_show_real_missing_condition_only or failed_breakout_card_does_not_show_attack_volume_as_positive or holding_next_step_uses_risk_prices_not_breakout_zone or v19_3_3_profit_reduce_stop_detail_lines_are_direct_actions"`
  - `6 passed, 219 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "holding_next_step or direct_actions or holding_risk_precedes or today_buy"`
  - `8 passed, 217 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "overheat or low_repair or failed_breakout or holding_next_step or risk_precedes or direct_actions"`
  - `14 passed, 211 deselected`.
- Official dry-run via `generator.generate_report(dry_run=True)`
  - `messages=4`, `live_telegram=False`, key checks true.
- Full `tests/test_generator_report.py`
  - `206 passed, 22 failed`.

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write.
- DB backfill/prune/dedupe.

## QA Conclusion

conditional pass.

The requested 06/23 user-visible path is fixed by focused tests and official dry-run. Conditional because the full legacy report test file still has unrelated and stale expectation failures.
