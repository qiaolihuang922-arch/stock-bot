# TASK: report_conflict_future_watch_format_20260608

## 任務狀態
- task_id: `report_conflict_future_watch_format_20260608`
- 任務類型: `normal_patch`
- 狀態: `qa_passed`
- 版本建議: `v20.4.50`
- QA 分級: `L2`

## Owner 問題
Owner 貼出 v20.4.49 dry-run 報文並要求：
1. 分析衝突點並修正。
2. 未來 30 日法說會維持目前過濾結果，但 EPS / 營收要拆成每檔法說會底下的單獨點。

## 衝突點
- Summary 的 `今日已買` 容易被讀成策略新買點，但同區塊又說 `新增有效進場：無`。
- 未持倉卡片 title 顯示 `量能不足` / `市場弱`，內文卻先顯示 `卡關主因：樣本不足`，主因不一致。
- 法說會單行塞入 EPS / 營收 / 關注原因，手機閱讀過長；但財報資料仍必須跟著被過濾後的法說會，不可變成獨立全市場清單。

## 使用者可見結果
- 盤後 Summary 改用 `今日買入紀錄`，區分已發生交易與新增有效進場。
- 未持倉卡片的 `卡關主因` 優先對齊 title：量能不足卡主因就是量能不足，市場弱卡主因就是市場弱。
- 策略樣本 / 資料不足退為補充 gap，不再搶主因。
- 未來 30 日法說會主行保留日期、代號、名稱、會議、關注原因。
- EPS / 營收YoY 拆成下一行 `財報：...`，只跟著該檔法說會出現。

## 非目標
- 不改策略分數、買賣判斷、漏斗分類、DB schema、DB write、live Telegram delivery。
- 不改未來 30 日法說會的過濾來源與股票範圍。

## 影響模組與直接消費者
- `presentation/report.py`: Summary 與未持倉 blocker 顯示。
- `core/future_watch.py`: 未來 30 日法說會格式。
- `core/generator.py`: 使用者可見版本。
- `tests/test_generator_report.py`: 回歸測試。

## 輸出契約
- message order 不變：持倉 -> 未持倉 -> 簡報 -> 未來30日。
- 第 3 則 Summary 使用 `今日買入紀錄`。
- 第 4 則法說會每個 item 最多兩行：主行 + optional `財報：...`。
- dry-run only，不觸發 Telegram send。

## 驗收條件
- focused pytest 通過。
- `py_compile` 通過。
- official `generate_report(dry_run=True)`：
  - header 為 `v20.4.50`。
  - Summary 出現 `今日買入紀錄` 與 `新增有效進場：無`。
  - 未持倉量能不足卡的 `卡關主因` 為 `量能不足`。
  - 法說會財報拆成 `財報：EPS...｜營收YoY...` 子行。

## 失敗標本與驗收路由
- Owner 樣本：2026-06-08 v20.4.49 完整 dry-run 報文。
- 驗收路由：official generator `generate_report(dry_run=True)` 最終 message list。

## 禁止事項與阻塞條件
- 禁止 live Telegram delivery。
- 禁止 production DB write / schema change。
- 若 official dry-run 無法產生 message list，結論只能 blocked。
