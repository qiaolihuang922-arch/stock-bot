# CHANGELOG

## 2026-05-26 - v20.0.1 Evidence Readiness Message

狀態：已完成並推送。  
Commit：`2728a9e fix: hide raw strategy evidence errors`

## 修改內容

- `core/generator.py`
  - 報文版本升至 `v20.0.1`。
  - evidence summary 查詢 / 更新失敗時，不再把 raw exception 直接塞入 Telegram。
- `services/strategy_evidence.py`
  - 新增 `strategy_evidence_error_kind()`。
  - 新增 `format_strategy_evidence_error()`。
  - schema / table missing 顯示 readiness message。
  - generic DB / network / timeout 顯示 sanitized fallback message。
- `tests/test_strategy_evidence.py`
  - 覆蓋 schema missing raw error 清洗。
  - 覆蓋 generic DB error 清洗。
- `tests/test_generator_report.py`
  - 更新主報文版本 contract 為 `v20.0.1`。

## 未影響模組

- `services/analysis.py`
- `core/signal_snapshot.py`
- `core/signal_validator.py`
- `services/daily_snapshot_store.py`
- `services/signal_store.py`
- `services/position_store.py`
- `services/notifier.py`
- `services/stock_api.py`
- `scripts/dry_run_replay.py`
- `scripts/backfill_signals.py`
- `docs/v20_strategy_evidence_schema.sql`
- production schema / DB migration
- live Supabase write
- live Telegram delivery
- BUY / SELL / WAIT 決策門檻

## 驗證

- `.venv/bin/python -m pytest tests/test_strategy_evidence.py tests/test_generator_report.py tests/test_notifier.py`
  - `44 passed, 21 warnings`
- `.venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py`
  - `33 passed`
- schema missing smoke：
  - 顯示 `策略證據尚未啟用：資料表未建立，主報文不受影響`
  - 不露 `schema cache` / `market_daily_bars` / raw dict。

## 未執行

- full pytest。
- replay / backfill dry-run。
- production schema apply。
- live Supabase write。
- live Telegram delivery。

原因：本輪為 L2 patch，只修 Telegram readiness / fallback 文案；production 啟用需另開任務。
