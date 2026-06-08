# TASK: historical_analogy_library_modules_20260608

## 任務狀態
- task_id: `historical_analogy_library_modules_20260608`
- 任務類型: `normal_patch`
- 狀態: `qa_passed`
- 版本建議: `v20.4.54`
- QA 分級: `L2`

## Owner 問題
Owner 指出 `歷史類比` 不只要顆粒度，還需要更多台灣歷史股災/壓力事件納入；現有 13 件模板不足。
Owner also questioned whether 3231/2337 revenue growth above 100% is accurate, and asked to rename `營收YoY` to `營收`.

## 使用者可見結果
- 台股歷史壓力樣本庫由 13 件擴到 19 件，補入 1987、1998、2001、2006、2007、2021 等台灣市場壓力事件。
- 歷史類比保留多行細節：
  - 最像事件 / 相似度 / 型態 / 壓力級別。
  - 相似點：跌幅、高檔回落、盤中震盪、量能、5日位置。
  - 模組分數：價格、位置、量能、情境。
  - 不相似/限制：說明為何不能直接當崩盤預測。
  - 下一步觀察：隔日低點、量能、高檔回落等具體條件。
  - 資料：TWSE近幾日與樣本庫大小。
- generic historical source 也補 `相似點` / `不相似/限制` / `下一步觀察` 行。
- 關注標的財報改顯示 `營收`；3231/2337 超過 100% 的營收年增以 TWSE 官方月營收 row 做 read-only 查核。

## 非目標
- 不改交易決策、買賣建議、DB schema、DB write、live Telegram delivery。
- 不新增外部歷史資料庫或 DB schema；本輪擴充內建台股壓力事件庫。

## 影響模組與直接消費者
- `core/future_watch.py`: historical analogy library / modular scoring / formatter。
- `core/generator.py`: 使用者可見版本。
- `tests/test_generator_report.py`: future-watch regression。
- TWSE/TPEX OpenAPI: official read-only fundamentals source, no write.

## 輸出契約
- 第 4 則 `歷史類比` section 保持在 `未來30日法說會` 前。
- `歷史類比` 可輸出多行，但不改 message order。
- dry-run only，不觸發 Telegram send。
- 關注標的財報可見文案使用 `營收`，不得再輸出 `營收YoY`。

## 驗收條件
- focused pytest 通過。
- `py_compile` 通過。
- official `generate_report(dry_run=True)`：
- header 為 `v20.4.54`。
- 歷史類比包含 `相似點`、`模組分數`、`不相似/限制`、`下一步觀察`、`資料`。
- 樣本庫顯示 19 件。
- official TWSE read-only spot-check confirms 3231 and 2337 revenue YoY source rows; formatter test rejects `營收YoY`。

## 失敗標本與驗收路由
- Owner 指出 v20.4.52 類比仍不夠精確，歷史股災事件庫/模組不足。
- 驗收路由：official generator `generate_report(dry_run=True)` 最終 message list。

## 禁止事項與阻塞條件
- 禁止 live Telegram delivery。
- 禁止 production DB write / schema change。
- 若 official dry-run 無法產生 message list，結論只能 blocked。
