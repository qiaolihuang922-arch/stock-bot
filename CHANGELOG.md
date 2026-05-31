# CHANGELOG: Holiday Execution Memory Fix

## Summary

- 修復 05/31 假日报文中英業達 2356 重複第二段停利問題。
- 使用 production cross-day execution memory 判斷已執行交易。
- market/theme evidence 顯示 actual/latest trade date 與 lookback_range。
- strategy sample evidence 與 market/theme production evidence 分層。
- 使用者可見版本升到 `v20.4.7`。

## Changed Files

- `core/generator.py`
- `services/cross_day_context.py`
- `core/market_theme_evidence.py`
- `services/market_theme_evidence_store.py`
- `services/strategy_evidence.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## Contract

- 已執行第二段停利不再進明日待賣計畫。
- source ready 但 prior take-profit execution memory 缺股數時 fail closed：`停利記憶不足`。
- 不改 DB schema、write path、買點閾值、live Telegram。

## Verification

- QA：`通過`。
- `PYTHONPATH=. arch -arm64 .venv/bin/python -m pytest -q`：264 passed，153 warnings。
- `git diff --check`：passed。

## Residual

- 下一步才做 evidence chain 策略輔助呈現。
- Runner 待補：QA conclusion parser、Tech worktree hygiene、production-read QA config。
