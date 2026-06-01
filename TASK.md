# TASK: cleanup_unused_variables_analysis_py

## 任務狀態

- task_id: tiny_patch_cleanup_unused_variables_analysis_py_20260601
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: 不升使用者可見報文版本
- QA 分級建議: L1

## Owner 問題

services/analysis.py 內有三處已確認 unused / redundant dead code，需要直接刪除，避免靜態檢查噪音與後續誤讀，但不得改變策略邏輯或輸出行為。

本輪只處理這三處：

1. detect_entry_stage() 內 breakout_lv 計算後未被整個函式使用。
2. holding_signal() 內 profile = result.get('entry_profile', 'NONE') 賦值後未在函式內使用。
3. pick_best_stock() 內第一個 entry_quality in ['C','D'] 過濾已被下一行 not in ['A+','A'] 覆蓋，屬冗餘 check。

## 使用者可見結果

使用者可見報文、Telegram message、CLI 輸出、策略建議結果不得改變。
本任務完成後，外部可見結果應只有程式碼更乾淨、靜態檢查不再產生這三處 unused / redundant warning。

## 非目標

- 不重構 services/analysis.py。
- 不調整 detect_entry_stage()、holding_signal()、pick_best_stock() 的策略判斷。
- 不修改 RR、entry quality、持倉建議、買賣 / 加減碼、停損停利邏輯。
- 不改 DB schema、DB write path、production data、Telegram live delivery。
- 不做全 repo dead code cleanup。
- 不順手處理其他 linter warning；若發現旁支問題，只記到交付摘要或後續待辦，不納入本輪。

## 影響模組

- services/analysis.py

## 直接消費者

- 直接函式消費者：
- 呼叫 detect_entry_stage() 的分析流程。
- 呼叫 holding_signal() 的持倉訊號流程。
- 呼叫 pick_best_stock() 的候選股挑選流程。
- 驗收消費者：
- Tech 自檢的 pyflakes 或等價靜態檢查。
- QA L1 針對 scoped diff 與靜態檢查結果做反證。

## 輸出契約

- 函式回傳契約：不變。
- payload / dict key：不變。
- message list / Telegram 報文排序：不變。
- CLI 輸出：不變。
- DB 讀寫契約：不變。
- 版本契約：不升 VERSION，不得修改報文 header 或版本字串。
- 程式碼契約：只刪除三處指定 dead code，不新增替代分支或新 helper。

## 已存在且不得回退的契約

- detect_entry_stage() 的 stage 判斷結果不得因刪除 unused breakout_lv 而改變。
- holding_signal() 的 signal、action、reason、entry profile 相關輸出不得改變。
- pick_best_stock() 仍只能接受 entry_quality 為 A+ 或 A 的候選；C、D 以及其他非 A+ / A 值仍應被排除。
- 使用者可見報文版本與內容不得因本任務變動。

## 驗收條件

1. Scoped diff 只包含 services/analysis.py 中三處指定 dead code 刪除；不得出現策略條件、輸出欄位、版本字串或測試 fixture 的無關改動。
2. 執行 pyflakes 或等價靜態檢查，確認清理後沒有新增 unused variable warning，且這三處不再被回報。
3. 至少執行一個輕量語法或既有測試自檢，例如 py_compile services/analysis.py 或現有 analysis 相關測試；若環境缺依賴，需列出實際錯誤並 blocked，不得宣告通過。

## 範例或 Fixture

- Static check target:
- services/analysis.py
- 驗收案例 1:
- 檢查 detect_entry_stage() 內不再存在 unused breakout_lv 賦值。
- 函式仍可通過語法檢查。
- 驗收案例 2:
- 檢查 pick_best_stock() 仍保留 entry_quality not in ['A+','A'] 或等價排除契約。
- 不允許因刪除前一行冗餘 check 而放行 C、D 或其他非 A+ / A 候選。

## 明確禁止事項

- 禁止改變任何策略決策、排序、分數、RR、entry quality 規則。
- 禁止新增 fallback、try/except、mock data 或 production read/write。
- 禁止改 Telegram、presentation、report、DB、runner、schema、測試大範圍重寫。
- 禁止把本任務擴成全量 lint cleanup。
- 禁止 live Telegram delivery。
- 禁止用「看起來沒影響」替代靜態檢查或可重跑自檢證據。

## 阻塞條件

- 若實際程式碼中三處位置與 Owner 描述不符，Tech 必須 blocked 並列出差異，不得自行改其他邏輯。
- 若刪除任一行會造成函式輸出、測試、策略判斷變更，Tech 必須 blocked。
- 若 pyflakes 或等價工具無法執行，需改用可說明等價性的靜態檢查；若完全無法檢查，blocked。
- 若發現其他 unused warning，不納入本輪；只可列為 follow-up，除非它直接阻塞這三處驗收。

## 本輪停止條件

完成三處指定 dead code 刪除，且 scoped diff、靜態檢查、輕量語法或既有測試自檢通過，即停止。
其他 lint、重構、策略合理性、報文內容、DB 或 Telegram 問題全部不納入本輪，最多記為後續待辦。
