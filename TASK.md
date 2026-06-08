# TASK: future_fundamentals_and_unheld_status_20260608

## 任務狀態
- task_id: `future_fundamentals_and_unheld_status_20260608`
- 任務類型: `normal_patch`
- 狀態: `qa_passed`
- 版本建議: `v20.4.51`
- QA 分級: `L2`

## Owner 問題
Owner 貼出 v20.4.50 dry-run 報文並指出：
1. EPS / 營收不能綁在法說會底下，否則沒有法說會的股票就不出現。
2. 再掃描報文還有什麼衝突。
3. `未持倉漏斗（非執行）：未持倉 7｜淘汰 7` 很怪，需要改成可讀決策語句。

## 使用者可見結果
- 未來 30 日法說會維持原本過濾結果，只列有法說會的事件。
- 新增 `關注標的財報` 區塊，對同一批關注標的逐檔列 EPS / 營收YoY，不依賴是否有法說會。
- Summary 首行移除 0-count：`未持倉 7（全部不可行動）`。
- Summary 詳情區改為 `未持倉狀態：未持倉 7 檔全部不可行動`，不再露出內部漏斗詞。

## 非目標
- 不改法說會來源/過濾條件。
- 不改策略決策、漏斗分類、DB schema、DB write、live Telegram delivery。
- 不補沒有來源的年度營收欄位；目前使用既有官方 fundamentals source 的 EPS 與營收YoY。

## 影響模組與直接消費者
- `core/future_watch.py`: 關注標的財報收集與 formatter。
- `presentation/report.py`: Summary 未持倉狀態文案。
- `core/generator.py`: 版本與 QA visible refs。
- `tests/test_generator_report.py`, `tests/test_market_theme_evidence.py`: 回歸測試。

## 輸出契約
- message order 不變。
- 第 3 則 Summary 不顯示 `未持倉漏斗（非執行）`。
- 第 4 則包含：
  - `未來30日法說會`
  - `關注標的財報`
  - `未來30日台股影響事件`
- `關注標的財報` 使用 watch/holding target filtering，不用法說會 event filtering。
- dry-run only，不觸發 Telegram send。

## 驗收條件
- focused pytest 通過。
- market theme report tests 通過。
- `py_compile` 通過。
- official `generate_report(dry_run=True)`：
  - header 為 `v20.4.51`。
  - Summary 顯示 `未持倉 7（全部不可行動）`。
  - 詳情顯示 `未持倉狀態：未持倉 7 檔全部不可行動`。
  - 第 4 則 `關注標的財報` 包含有法說會與沒有法說會的關注股。

## 失敗標本與驗收路由
- Owner 樣本：2026-06-08 v20.4.50 完整 dry-run 報文。
- 驗收路由：official generator `generate_report(dry_run=True)` 最終 message list。

## 禁止事項與阻塞條件
- 禁止 live Telegram delivery。
- 禁止 production DB write / schema change。
- 若 official dry-run 無法產生 message list，結論只能 blocked。
