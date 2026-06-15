# DISPATCH.md

## Active

- task_md_holds: `strong_rebound_not_weak_v21_0_7_20260615`
- status: `complete`
- owner_request:
  - Fix report logic where near-limit-up 旺宏 was still labeled `弱反彈`.
  - Make strategy wording more adaptive without becoming a chase-buy machine.
  - No live Telegram delivery.

## Current Result

- Visible version is now `v21.0.7`.
- `WEAK_REBOUND` with live/day change >= 7% is now `急彈待回測`.
- Strong rebound routes to `等回測`, not `淘汰`.
- Strong rebound card says `卡關主因：急彈未回測`.
- Low-change weak rebound still remains weak/rejected.
- No buy signal is created solely from a sharp rebound.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_trade_state_machine.py tests/test_generator_report.py tests/test_market_theme_evidence.py -q --tb=short
```

Result: `249 passed, 149 warnings, 57 subtests passed`.

Official dry-run:
- `version v21.0.7`
- v21.0.7 messages generated.
- no live Telegram delivery.
- no current `【旺宏 2337】⛔ 淘汰｜弱反彈待確認` in official dry-run output.

## Next Action

- Observe the next Render/GitHub scheduled report if external confirmation is needed.
