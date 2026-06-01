# TASK: v20.4.21 盤後簡報清單與資料依據合併

## 任務狀態

- task_id: report_v20_4_21_afterhours_brief_evidence_merge
- 任務類型: normal_patch
- 狀態: qa_passed_pending_git_close
- 版本建議: 不回退，維持 `v20.4.21`
- QA 分級建議: L2

## Owner 問題

Owner 確認盤後第三則仍要保留持倉風控檢查：

- 旺宏 / 光寶科 / 建準：`新倉風控觀察｜明日未修復降級`
- 智原：`續抱觀察｜無法接近買點則降級`

同時，資料依據不能無腦砍成四句空泛說明；需要把市場、持倉 / 價格 / 候選資料、執行記憶、持倉 RR 和數據證據合併呈現，保持人話但保留有用證據。

## 使用者可見結果

- 盤後第三則保留 `持倉風控檢查` 清單。
- 盤後第三則保留 `未持倉漏斗（非執行）` 摘要。
- `資料依據` 顯示可讀的證據摘要：
  - 市場 / 題材短期背景與用途限制。
  - 持倉數、未持倉分類數與使用邊界。
  - 執行記憶對今日買賣 / 停利 / 剩餘股數的處理邊界。
  - 持倉 RR 只用於明確加碼情境，避免誤讀成新買點。
- 不回到 raw table / source / status dump。

## 非目標

- 不改策略邏輯、選股規則、RR 計算公式或進出場決策。
- 不變更 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 DB write、backfill、production DML 或 live Telegram delivery。
- 不處理 `generate()` 預設 dry-run / write 行為；Owner 已說該點是複製錯誤。
- 不修復本輪以外的排序、策略分數或資料完整性問題。

## 影響模組

- `presentation/report.py`
- `core/generator.py`
- `tests/test_generator_report.py`
- 固定 handoff Markdown

## 直接消費者

- Owner 手機閱讀 Telegram 報文。
- Telegram message list / report renderer。
- v20.4.x 報文 fixture / probe。
- QA 驗收流程。

## 輸出契約

- 盤後第三則順序：
  1. `盤後簡報`
  2. `持倉風控檢查`
  3. `未持倉漏斗（非執行）`
  4. `資料依據`
- `資料依據` 必須保留數量與邊界，不輸出 raw DB table / raw source status dump。
- 使用者可見主行動是 `新倉風控觀察` 時，不得顯示具體新倉 RR 數字。
- presentation 顯示層不得 import / call DB writer、strategy evidence writer、schema alter 類入口。

## 驗收條件

- 可重跑手機閱讀 probe 覆蓋盤後第三則含 `持倉風控檢查` 與 `未持倉漏斗（非執行）`。
- 可重跑 probe 覆蓋資料依據含持倉數、未持倉分類數、執行記憶邊界與持倉 RR 邊界。
- 建準同類今日買入 / 底層 ADD 情境仍顯示 `新倉 RR：不適用（既有持倉）`。
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

完成盤後第三則清單恢復、資料依據合併增強、RR 衝突保護與可重跑驗證後停止。
