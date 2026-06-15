# DISPATCH.md

## Active

- task_md_holds: `acute_rebound_retest_anchor_v21_0_9_20260615`
- status: `complete`
- owner_request:
  - Verify whether acute rebound buy gates are reasonable against public trading references.
  - Make the Telegram card explain why 旺宏 is not buyable now and what must happen before it can become buyable.
  - Reduce visible contradiction and noise without loosening strategy.
  - No live Telegram delivery.

## Current Result

- Visible version is now `v21.0.9`.
- `急彈待回測` card now shows:
  - `量化差距：急彈追價區，尚未回測｜V ...x偏弱｜品質 D 未達B｜RR ...達標`
  - `解鎖：回測前高/突破區不破 + 非漲停追價 + 量能有效 + 品質B以上 + RR>=1.5`
- Acute rebound remains `等回測`, not buy.
- Real RR can be shown on acute rebound wait cards to avoid `RR達標` vs `RR -` contradiction.
- Limit-up / locked-overheat cards still keep overheat no-chase behavior.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v21_0_9_strong_rebound_is_not_labeled_weak_rebound tests/test_generator_report.py::GeneratorReportTest::test_confirmed_evidence_preserves_limit_lock_chase_hard_blocker tests/test_generator_report.py::GeneratorReportTest::test_low_volume_limit_up_prepare_card_and_summary_show_risk -q --tb=short
```

Result: `3 passed`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `249 passed, 149 warnings, 57 subtests passed`.

Official dry-run:
- `VERSION v21.0.9`
- `messages 4`
- retest anchor condition line present.
- no live Telegram delivery.
- no current `【旺宏 2337】⛔ 淘汰｜弱反彈待確認`.

## Next Action

- Observe the next Render/GitHub scheduled report if external confirmation is needed.



