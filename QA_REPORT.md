# QA_REPORT: historical_analogy_library_modules_20260608

## 測試範圍
- TWSE historical analogy helper tests。
- future-watch formatter test。
- notifier tests。
- market theme evidence tests。
- market theme evidence tests。
- official `generate_report(dry_run=True)` replay。

## 關聯風險掃描
- 多行 historical analogy 不改 message order。
- 類比仍明確包含限制，不升格成預測。
- 缺量能時顯示為限制，不假裝有量能證據。

## 跨區塊語意一致性
- `歷史類比` section 在 `未來30日法說會` 前。
- section 內包含：
  - 主類比事件。
  - `相似點`。
  - `模組分數`。
  - `不相似/限制`。
  - `下一步觀察`。
  - `資料`。

## 使用者誤讀風險
- `不相似/限制` 保留，避免把歷史類比讀成崩盤預測。
- `壓力級別` 使用壓力/急跌語言，不直接下交易命令。

## 失敗標本反證
- Owner 指出 v20.4.52 歷史事件庫/模組仍不足。
- v20.4.54 official dry-run 顯示 19 件樣本庫與價格/位置/量能/情境模組分數。
- Owner questioned 3231/2337 revenue growth above 100%; TWSE read-only official rows confirmed 3231 `111.98927364274991%` and 2337 `153.71283899759698%`.
- Future-watch formatter regression confirms user-visible label is `營收`, not `營收YoY`.

## 未測項目
- live Telegram delivery 未測且禁止。
- 未新增外部 historical DB；本輪是內建台股事件庫擴充。

## QA 結論
通過
