# CHANGELOG: strong_rebound_not_weak_v21_0_7_20260615

## Changes
- `core/generator.py`
  - Bumped visible version to `v21.0.7`.
  - Added `is_strong_intraday_rebound()` based on `WEAK_REBOUND` plus live/day change >= 7%.
  - Replaced visible `弱反彈待確認` with `急彈待回測` for strong intraday rebounds.
  - Strong rebounds route to `等回測`, not `淘汰`.
  - Rejected reason / wait text / summary cause now use acute rebound semantics.
- `core/trade_state_machine.py`
  - Added matching strong-rebound guard.
  - Visible state line can now show `主因：急彈待回測`.
  - Strong rebound guard maps to pullback confirmation, not stock-weak setup failure.
- `presentation/report.py`
  - `急彈待回測` cards now show `卡關主因：急彈未回測`.
  - Gap text says the move is already extended and needs retest confirmation.
- Tests updated to `v21.0.7`.

## Contract Impact
- New visible blocker: `急彈待回測`.
- New visible card reason: `急彈未回測`.
- No DB payload, schema, RLS, grant, policy, role, live delivery, or production write change.

## Verification
- Focused regression:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_rejected_weak_rr_uses_true_reject_reason_not_rr tests/test_generator_report.py::GeneratorReportTest::test_v21_0_7_strong_rebound_is_not_labeled_weak_rebound -q --tb=short
  ```
  Result: `2 passed`.
- Targeted report/state/evidence suite:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `249 passed, 149 warnings, 57 subtests passed`.
- Official dry-run:
  - `version v21.0.7`
  - generated v21.0.7 messages
  - no live Telegram delivery
  - no current `【旺宏 2337】⛔ 淘汰｜弱反彈待確認` in official dry-run output

## Coverage Layers
- Blocker helper.
- Unheld funnel.
- Trade state machine.
- Telegram unheld formatter.
- Official generator dry-run.

## Residual Risk
- The threshold is rule-based (`>=7%`) and not a learned optimizer.
- Near-limit-up is still not a buy signal by itself; it waits for retest / non-chase confirmation.
