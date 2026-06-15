# CHANGELOG: report_conflict_entry_gate_v21_0_5_20260615

## Changes
- `core/generator.py`
  - Bumped visible version to `v21.0.5`.
  - Separated broad market weakness from individual stock weakness.
  - Prevented `市場：中性觀察 R2` from producing unheld cards that say `等市場｜市場弱`.
  - Added source-context detection so dry-run / owner pasted report paths do not become false `等資料`.
  - Converted unresolved entry quality and RR gates into Chinese visible reasons.
  - Made non-actionable prepare/watch cards fail closed without pretending they are valid buys.
- `core/trade_state_machine.py`
  - Added `WAIT_DATA` mapping for real data failures.
  - Split `MARKET_WEAK` and `STOCK_WEAK` guards.
  - Stopped WATCH cards from becoming data failures solely because source context is absent.
  - Display now shows `個股弱勢` when the blocker is stock-level, not market-wide.
- `presentation/report.py`
  - Treats source status as available when the report has no real source-decision context.
  - Shows `資料不足` only for real `等資料` cards.
  - Keeps data-recovery wording only on real data-state cards.
- Tests updated for `v21.0.5`, stock-level weakness wording, and revised unheld state counts.

## Contract Impact
- Telegram visible version changes to `v21.0.5`.
- User-visible unheld gates now distinguish:
  - market-wide weakness: `市場弱` / `等市場`;
  - individual stock weakness: `個股弱勢` / `等型態` or setup wait;
  - real source failure: `等資料`;
  - RR problem: `等RR修復`.
- No DB schema, RLS, grant, policy, role, index, payload shape, or live Telegram change.

## Verification
- Combined state/report/evidence tests:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `246 passed, 145 warnings, 57 subtests passed`.
- Official dry-run conflict probe:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe -c "from core.generator import generate_report, VERSION; messages,_=generate_report(dry_run=True); text='\n'.join(messages); print('version', VERSION); print('has_R2_market_weak_conflict', ('市場：中性觀察 R2' in text and '等市場｜市場弱' in text)); print('has_nextday_data_conflict', ('隔日確認' in text and '交易狀態：等資料' in text)); print('has_english_quality_noise', 'entry quality low' in text); print('has_buyable', '可買｜' in text or '趨勢延續買入' in text); print('liandian_rr', '【聯電 2303】👀 等RR修復｜觀察' in text and '交易狀態：等RR修復' in text)"
  ```
  Result:
  - `version v21.0.5`
  - `has_R2_market_weak_conflict False`
  - `has_nextday_data_conflict False`
  - `has_english_quality_noise False`
  - `has_buyable False`
  - `liandian_rr True`

## Coverage Layers
- Formatter / visible Telegram report.
- Official generator dry-run.
- State machine transition and guard behavior.
- Market/theme evidence tests.

## Residual Risk
- No live Telegram delivery was performed.
- No production DB write/backfill was performed.
- This remains rule-based decision logic; it does not claim to predict bottoms.
