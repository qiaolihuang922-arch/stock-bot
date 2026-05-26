# TASK: v20.0.1 Evidence Readiness Message

## 任務狀態

- 日期：2026-05-26
- 版本：`v20.0.1`
- version_level：`patch`
- qa_level：`L2`
- 狀態：已完成並推送
- 對應 commit：`2728a9e fix: hide raw strategy evidence errors`

## 需求摘要

v20.0 盤後報文在 `📊 策略證據 v20.0` 區塊露出 Supabase raw error：

```text
Could not find the table 'public.market_daily_bars' in the schema cache
```

本輪目標是把 raw DB error 轉成 Owner 可理解的 readiness message。

## 使用者可見變化

- schema 未啟用：`策略證據尚未啟用：資料表未建立，主報文不受影響`
- generic DB failure：`證據層暫時略過：資料更新失敗，主報文不受影響`
- 樣本不足：保持 `樣本不足` / `樣本不足，不判讀`

## 禁止項

- 不顯示 `Could not find the table`。
- 不顯示 `schema cache`。
- 不顯示 raw dict，例如 `{'message': ...}`。
- 不顯示 Traceback、URL、token、key、connection detail。
- 不 apply production schema。
- 不正式寫 Supabase。
- 不改 BUY / SELL / `is_tradeable` / `action`。

## 驗收

- schema missing、generic DB failure、insufficient sample 三種情境都有測試。
- 主報文仍正常產生。
- `messages[-1]` summary-last 不回退。
- `reply_markup` last summary 不回退。
- 策略不變性通過。
