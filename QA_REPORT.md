# QA_REPORT: low_repair_ready_state_v21_1_20260622

## Test Scope

- Low-repair state promotion.
- User-visible unheld card wording.
- Summary funnel count consistency.
- Adjacent trade-state/replay tests.
- Official dry-run message list.

## Risk Scan

- DB schema change: not used.
- DB write/backfill/delete: not used.
- Live Telegram: not used.
- Persisted production data: unchanged.
- Strategy risk: limited to low-repair candidate state promotion from waiting to next-session prepare.

## Cross-Block Semantic Checks

- A card that says all low-repair conditions are met no longer remains in `等低位修復`.
- A card missing 5-day MA recovery still remains in `等低位修復`.
- `可準備` remains non-actionable in after-hours wording: confirmation is required before buying.
- Summary bucket counts no longer double-count `隔日確認` as `僅追蹤`.

## Failure Specimen Rebuttal

- Owner specimen `3231 緯創` now renders:
  - `👀 可準備｜低位修復成立`
  - `條件：已滿足 支撐未破、站上5日均、量能有效、風險報酬達標`
  - `可買：明日開盤不追高 + 守支撐/5日均 + 量能不失控`
- Control specimen `2324 仁寶` remains waiting:
  - `還差 站回5日均 37.54`

## Commands And Results

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q -k "low_repair or unheld_funnel or next_day_confirmation or cooling_and_next_day or b5_tracking or postmarket_unheld_gate" --tb=short`
  - result: `12 passed`
- `.\.venv\Scripts\python.exe -m pytest tests\test_unheld_gap_format.py tests\test_trade_state_machine.py tests\test_strategy_buy_path_replay.py tests\test_strategy_rule_outcomes.py -q --tb=short`
  - result: `16 passed`
- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `215 passed`, `1 failed`
- `generate_report(dry_run=True)`
  - result: `top_messages=2`, `flat_messages=5`, no live Telegram.

## Not Tested

- Live Telegram delivery.
- Production DB write/read-after-write, because this cycle had no DB writes.
- Fix for the unrelated future-watch source test.

## QA Conclusion

conditional pass.

The reported low-repair state/display conflict is fixed and covered. Full report suite still has one unrelated live readonly future-watch source failure, so repository-wide completion cannot be claimed until that separate issue is handled.
