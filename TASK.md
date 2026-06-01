# TASK: presentation_report_structured_noise_flags_tiny_patch_20260601

## 任務狀態

- task_id: presentation_report_structured_noise_flags_tiny_patch_20260601
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: 不升版，維持既有 VERSION，目前上下文顯示為 v20.4.21
- QA 分級建議: L1
- 本輪主 bug: presentation/report.py 顯示層用已渲染字串做反向判斷，導致文案變動或合法字樣可能誤觸發 / 誤過濾

## Owner 問題

presentation/report.py 有兩處顯示層字串匹配脆弱性需要收斂修復：

1. _decision_brief_lines() 目前用 noisy_contains 與硬編碼詞表過濾 summary_message 每行，應改為由上游以結構化欄位傳遞「哪些 summary 噪音內容不應進 brief」，不要從已渲染字串反向判斷。
2. _afterhours_brief_lines() 目前用中文文案 '每日快照未寫入' 偵測寫入警告，應改為由 generator 以結構化參數傳入寫入警告狀態，不依賴報文文案字串。

## 使用者可見結果

手機閱讀盤後 Telegram 報文時：

- 寫入警告仍能在盤後 brief 正確出現。
- summary_message 若含合法的 production 字樣，不會因字串詞表被誤判為噪音而消失。
- 報文既有分組、排序、版本字串、策略結論不因本輪改動改變。

## 非目標

- 不重設報文結構。
- 不改策略 decision、持倉建議、買賣 / 加減碼 / 停損停利邏輯。
- 不改 DB write path、schema、RLS、grant、policy、role、index / constraint。
- 不改 live Telegram delivery。
- 不升 VERSION。
- 不做全檔案清理、命名重構或 presentation 大拆分。
- 不處理 Telegram reply markup 附著最後一則 message 的旁支風險。

## 影響模組

- 主要影響: presentation/report.py
- 可能需要同步的直接上游: core/generator.py 或現有 generator 報文組裝入口，用於傳遞結構化參數
- 測試 / probe: 既有報文測試檔中補最小覆蓋，優先使用現有 generator/report fixture，不新增大型測試框架

## 直接消費者

- Telegram 盤後報文手機閱讀者
- generator 產出的 message list / report formatter 消費者
- QA 用既有 dry-run / fixture probe 驗證 rendered message

## 輸出契約

本輪只收斂一個輸出契約：盤後報文 brief 的顯示內容由結構化狀態控制，不再依賴已渲染文案反向匹配。

- _decision_brief_lines() 不得再靠 summary_message 文字包含 production 或其他硬編碼噪音詞判斷是否過濾合法 summary 行。
- summary 噪音內容應由結構化欄位、明確 flag、或 generator 傳入的排除集合控制；合法 summary 行原文可保留。
- _afterhours_brief_lines() 是否顯示每日快照寫入警告，應由 generator 傳入的結構化寫入警告狀態控制。
- 寫入警告實際顯示文案可沿用既有使用者可見文案；判斷來源不得是比對該文案字串。
- message list 順序、盤後分組、Summary/brief 位置不得因本輪 tiny patch 改變。
- 已存在且不得回退的契約:
- VERSION 不升版，維持目前既有版本。
- 盤後明日語境、短期背景命名、第三則資料依據人話化、未持倉漏斗非執行語意不得回退。
- strategy decision、RR 計算、holding_status、DB write path 不變。
- 無有效進場不得被寫成推薦感文案。

## 手機閱讀路徑與示例輸出形狀

手機閱讀路徑：

1. 打開盤後 Telegram 報文。
2. 先讀第一則 / brief 區塊。
3. 確認 summary 合法內容仍出現。
4. 確認每日快照寫入警告在有結構化警告狀態時出現。

示例形狀，文字可依既有 formatter 為準：

盤後重點
- production 資料來源正常，今日仍無有效進場
- 每日快照未寫入：請檢查寫入來源

反例，不能發生：

盤後重點
- 每日快照未寫入：請檢查寫入來源

若第一行是合法 summary，不能只因含 production 被過濾。

## 驗收條件

1. summary_message 含合法 production 字樣時，盤後 brief 仍保留該行，不被 noisy_contains 類文字詞表誤過濾。
2. generator 傳入「每日快照寫入警告」結構化狀態時，盤後 brief 正確顯示寫入警告；變更警告文案本身不應破壞是否顯示的判斷。
3. 檢查 diff 確認未改 strategy decision、DB write、live Telegram delivery、VERSION。
4. 測試範圍收斂於上述兩個 probe 與必要既有報文測試；不要求 full L3 production 驗證。

## 範例或 Fixture

Tech 應補 1-2 個最小 probe：

- probe A: 建立含合法 summary_message 行的 fixture，例如 production 資料來源正常，今日仍無有效進場，驗 rendered afterhours brief 包含該行。
- probe B: 建立 generator 傳入寫入警告狀態的 fixture，驗 rendered afterhours brief 包含既有每日快照寫入警告文案。

若既有 fixture 已能表達 afterhours report，優先擴充既有 fixture，不新增平行大型 fixtures。

## 明確禁止事項

- 禁止用新增中文 / 英文關鍵字詞表替代現有詞表，形成另一個字串匹配。
- 禁止從 rendered message、summary 文案、warning 文案反推狀態。
- 禁止修改策略輸出以配合顯示層。
- 禁止新增 DB 欄位、寫 production DB、改 schema 或改 live delivery。
- 禁止升 VERSION。
- 禁止把本輪 tiny patch 擴大成 presentation/report.py 全面重構。
- 禁止只改文案不補 probe。

## 阻塞條件

- 若現有 generator 到 presentation 之間完全沒有可傳遞結構化狀態的資料通道，Tech 應 blocked，回報缺少哪個接口，而不是改回字串匹配。
- 若無法判定目前 VERSION 常量位置或值，Tech 不得自行升版；保持不改並在 CHANGELOG 說明。
- 若現有 fixture 無法生成盤後 brief，Tech 可補最小 fixture；若需要 production credential 或 live Telegram 才能驗證，應 blocked，不能用 live delivery 驗收。

## 本輪停止條件

完成以下即停止：

- 移除本輪指定兩處 brittle rendered-string 判斷。
- 補上 1-2 個 probe 覆蓋合法 production summary 不被誤濾、寫入警告由結構化狀態顯示。
- 自檢證明 presentation/report.py 與必要 generator bridge / tests 通過，且 VERSION、策略 decision、DB write path 無 diff。

旁支問題只記待辦，不納入本輪：

- 全報文其他字串匹配盤點。
- Telegram reply markup 落點。
- presentation 分層重構。
- production ledger / source-of-truth 稽核。
