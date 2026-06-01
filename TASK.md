# TASK: v20.4.21 持倉 RR 衝突補修

## 任務狀態

- task_id: report_v20_4_21_holding_rr_conflict_followup
- 任務類型: normal_patch
- 狀態: qa_passed_pending_git_close
- 版本建議: 不回退，維持 `v20.4.21`
- QA 分級建議: L2

## Owner 問題

Owner 貼出實際 `generate()` 報文後，建準卡片仍出現跨區塊衝突：

- 卡片主行動：`新倉風控觀察，暫不加碼`
- 同一卡片數據：`RR 2.73`
- 第三則資料依據：既有持倉若不是加碼情境，只顯示新倉 RR 不適用。

此外，Owner 要確認本輪沒有暗中擴建表 / 欄位，沒有把 derived / fixture 當 production 證據。

## 使用者可見結果

- 若最終使用者可見主行動是 `新倉風控觀察`，持倉卡片不得顯示具體新倉 RR 數字，即使底層策略 signal 暫時有 ADD level。
- 建準同類卡片應顯示：`數據：新倉 RR：不適用（既有持倉）｜S ...｜V ...`
- presentation 顯示層不得新增 schema / DB writer / evidence writer 依賴。

## 非目標

- 不改策略邏輯、選股規則、RR 計算公式或進出場決策。
- 不變更 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 DB write、backfill、production DML 或 live Telegram delivery。
- 不處理 `generate()` 預設 dry-run / write 行為；Owner 已說該點是複製錯誤。
- 不修復本輪以外的文案偏好、排序、策略分數或資料完整性問題。

## 影響模組

- `presentation/report.py`
- `tests/test_generator_report.py`
- 固定 handoff Markdown

不得改動策略核心、DB 寫入路徑、交易狀態機或 live delivery runner。

## 直接消費者

- Owner 手機閱讀 Telegram 報文。
- Telegram message list / report renderer。
- v20.4.x 報文 fixture / probe。
- QA 驗收流程。

## 輸出契約

- 使用者可見主行動是 `新倉風控觀察` 時，不得顯示具體新倉 RR 數字。
- RR 顯示以最終報文主行動為準，不能只看底層 strategy ADD level。
- 加碼候選可沿用既有加碼 RR 顯示契約。
- presentation 顯示層不得 import / call DB writer、strategy evidence writer、schema alter 類入口。

## 驗收條件

- 可重跑手機閱讀 probe 覆蓋「今日買入 + 底層 ADD level」仍顯示 `新倉 RR：不適用（既有持倉）`。
- 可用 dry-run 反證建準卡片不再顯示 `RR 2.73`。
- `tests/test_generator_report.py` 通過。
- presentation boundary gate 通過，確認未新增 schema / DB writer / evidence writer 依賴。
- 不做 DB write、live Telegram、DB schema。

## 明確禁止事項

- 禁止 DB write。
- 禁止 live Telegram delivery。
- 禁止 DB schema / RLS / grant / policy / role / index / constraint 變更。
- 禁止改策略核心買賣判斷。
- 禁止只改文件不補可重跑 probe。

## 本輪停止條件

完成建準 RR 衝突補修與可重跑驗證後停止；其他文案偏好、reply markup、2356 ledger 稽核另開任務。
