# CHANGELOG: acute_rebound_retest_anchor_v21_0_9_20260615

## Changes
- `core/generator.py`
  - Bumped visible version to `v21.0.9`.
- `presentation/report.py`
  - `急彈待回測` cards now display a compact reason:
    - `急彈追價區，尚未回測`
    - live volume status, entry quality, and RR status when available.
  - `急彈待回測` unlock text now states the buy-condition checklist:
    - `回測前高/突破區不破 + 非漲停追價 + 量能有效 + 品質B以上 + RR>=1.5`.
  - Acute rebound wait cards preserve real RR in the data line when RR exists.
  - Limit-up / locked-overheat cards still keep `RR -（過熱）`.
- `tests/test_generator_report.py`
  - Added regression assertions for the new condition line and RR conflict.
  - Kept negative coverage for limit-up and low-volume limit-up hard blockers.

## Contract Impact
- Telegram unheld card wording changes for acute rebound wait states.
- No DB payload, schema, RLS, grant, policy, role, live delivery, or production write change.
- Trade permission is unchanged: acute rebound remains wait/retest, not buy.

## Verification
- Focused specimens:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v21_0_9_strong_rebound_is_not_labeled_weak_rebound tests/test_generator_report.py::GeneratorReportTest::test_confirmed_evidence_preserves_limit_lock_chase_hard_blocker tests/test_generator_report.py::GeneratorReportTest::test_low_volume_limit_up_prepare_card_and_summary_show_risk -q --tb=short
  ```
  Result: `3 passed`.
- Targeted report/state/evidence suite:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py -q --tb=short
  ```
  Result: `249 passed, 149 warnings, 57 subtests passed`.
- Official dry-run:
  - `VERSION v21.0.9`
  - `messages 4`
  - retest anchor condition line present
  - no live Telegram delivery
  - no current `【旺宏 2337】⛔ 淘汰｜弱反彈待確認`

## Coverage Layers
- Telegram unheld formatter.
- Official generator dry-run message list.
- Strong rebound owner specimen.
- Limit-up / overheat negative specimens.
- Existing report/state/evidence regression suite.

## Residual Risk
- `品質B以上` is an internal composite gate, not an external universal trading term.
- The acute rebound threshold remains rule-based and should be calibrated from DB outcomes in a separate strategy-quality task.



