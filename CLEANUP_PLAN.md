# CLEANUP_PLAN.md

本文件由 Architect 維護，用來記錄清理、收斂與避免重複工作的計畫。未經 Owner 或明確任務確認，不直接執行大範圍清理。

## 目前原則

- 不主動重構核心代碼。
- 不清理未知來源的未提交變更。
- 不刪除固定 8 份 Markdown 工作流文件。
- 不刪除測試或核心文件，除非有明確任務與影響判斷。
- 清理工作必須先有摘要、範圍與驗證方式。
- Architect 不直接修功能代碼；Owner 提出新功能 / 顯示 / bug / 策略需求時，先更新 `DISPATCH.md` 分派。
- QA 不是照單驗收角色；必須主動找問題、跨區塊語意一致性、使用者誤讀風險。
- 每次 Architect 完成 commit / push 後，必須壓縮工作流 Markdown，只保留最新任務與高信號摘要。

## 最新收斂

- v20.0 Strategy Evidence Foundation 已完成並推送。
- v20.0.1 Evidence Readiness Message 已完成並推送。
- push 後已壓縮：
  - `DISPATCH.md`
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`
  - `RESEARCH.md`
  - `CURRENT_STATE.md`
  - `CLEANUP_PLAN.md`
- 本輪不清理核心代碼。

## 待處理項目

- v20.0.1 patch 已完成並推送；工作流文件已壓縮。
- 若 Owner 要正式啟用 v20 evidence DB：
  - 另開 production schema apply 任務。
  - 檢查 Supabase RLS / 權限 / index / rollback。
  - 決定 retention / archive 策略。
- 若 Owner 要 live evidence write：
  - 先做 staging 或 dry-run 對照。
  - 再批准 live Supabase write。
- 若 Owner 要 live Telegram delivery 驗證：
  - 另開明確任務，不混入一般 QA。
- 後續可改善：
  - `load_strategy_evidence_summary()` 增加顯式排序。
  - `漏失` 文案改為更低誤讀版本。
  - 擴充真實外部事件 ingestion，但不得直接接 BUY。

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

- 等待 Owner 下一個需求。
- 若下一步是 v20 production 啟用，不得直接寫庫；必須先分派 PM 定義 rollout / rollback / 驗收條件。
