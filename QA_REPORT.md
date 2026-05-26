# QA_REPORT.md

## 任務狀態

- 對應任務：`v20.0.1-evidence-readiness-message`
- 版本：`v20.0.1`
- QA 等級：`L2`
- 提交日期：2026-05-26
- 結論：通過

## 測試範圍

- formatter / evidence fallback。
- Telegram summary-last / reply_markup-last contract。
- 策略不變性。
- 直接消費者：`generate_report()`、`formatTelegramMessages()`、`main.py -> send_many()`、`services.notifier.send_many()`。
- 負面案例：schema missing、generic DB failure、raw URL/token/Traceback、樣本不足。
- 跨區塊語意一致性與使用者誤讀風險。

## 執行命令

```bash
.venv/bin/python -m pytest tests/test_strategy_evidence.py tests/test_generator_report.py tests/test_notifier.py
```

結果：`44 passed, 21 warnings`

```bash
.venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py
```

結果：`33 passed`

## 驗證結論

- schema missing raw error 已轉為：`策略證據尚未啟用：資料表未建立，主報文不受影響`
- generic DB failure 已轉為：`證據層暫時略過：資料更新失敗，主報文不受影響`
- 樣本不足仍顯示 `樣本不足，不判讀`，不誤報為更新失敗。
- Telegram summary-last 與 reply_markup-last contract 未回退。
- 策略不變性通過。
- 本輪未 apply production schema、未正式寫庫、未改 replay/backfill。

## 使用者誤讀風險

- 已降低：不再把 Supabase raw dict / schema cache / table name dump 到 Telegram。
- 文案明確說明 `主報文不受影響`。
- 殘留：`📊 策略證據 v20.0` 區塊名稱仍是 evidence foundation 名稱，而主報文版本是 `v20.0.1`；QA 判斷不阻塞。

## 未測項目

- full pytest。
- replay / backfill dry-run。
- production schema apply。
- live Supabase write。
- live Telegram delivery。
- TWSE live replay / live backfill。

## QA 結論

通過。production schema apply、live Supabase write、live Telegram delivery 仍需另開明確批准流程。
