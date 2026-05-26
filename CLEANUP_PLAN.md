# CLEANUP_PLAN.md

本文件由 Architect 維護，用來記錄清理、收斂與避免重複工作的計畫。未經 Owner 或明確任務確認，不直接執行大範圍清理。

## 目前原則

- 不主動重構核心代碼。
- 不清理未知來源的未提交變更。
- 不刪除固定 8 份 Markdown 工作流文件。
- 不刪除測試或核心文件，除非有明確任務與影響判斷。
- 清理工作必須先有摘要、範圍與驗證方式。

## 待整理項目

- v19.3.3 formatter 一致性修正已完成指定 QA，Architect 已更新狀態。
- v19.3.4 報文解釋力修正已完成指定 QA，Architect 已更新狀態。
- 本輪不清理核心代碼；若要推送，需由 Architect 先檢查 diff 與局部測試結果。
- 若要處理策略門檻、live Telegram 或 full regression，需另開任務。
- 部門交付文件 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 是工作流入口，必須保留；任務結束後只清空或改寫內容，不刪文件。
- 工作區若出現未提交核心檔案修改，Architect 不處理；需由 Tech 或 Owner 確認來源。

## 固定保留清單

- `AGENTS.md`
- `DISPATCH.md`
- `RESEARCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`

## 清理分級

- L0 文件整理：只更新摘要文件，不碰核心代碼。
- L1 局部收斂：只調整單一已確認模組的文件、測試說明或小範圍命名。
- L2 行為相關清理：涉及 formatter、策略、資料來源或 DB 寫入邊界，需 PM 任務與 QA 驗證。
- L3 大範圍清理：跨多模組或影響 replay/backfill/DB，需 Owner 明確批准。

## 下一步

- 收到 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 任一文件後，Architect 只讀該摘要與必要局部上下文。
- 根據摘要更新 `CURRENT_STATE.md`。
- 若發現重複、過期或互相衝突的工作，再更新本文件並交由對應會話處理。
