# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v20.0.1-evidence-readiness-message`
- task_name: `v20.0.1 Evidence Readiness Message`
- task_type: `development`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `dispatched`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 貼出 v20.0 盤後報文，策略證據區顯示：
  - `證據層略過：更新失敗 {'message': "Could not find the table 'public.market_daily_bars' in the schema cache", ...}`
- 判斷：
  - evidence layer 降級有效，主報文未被阻斷。
  - production schema 尚未 apply，故 Supabase 找不到 `market_daily_bars` 是符合已知未完成項。
  - 但 Telegram 直接露出 Supabase 原始錯誤，不符合使用者可讀性，需 patch。
- 本輪只處理「未啟用 evidence schema 時的友善提示 / readiness message」，不直接 apply production schema、不正式寫庫。

## Next Action

- Architect: 已吸收 QA `QA_REPORT.md`；本輪 v20.0.1 patch 已通過 L2，下一步做提交前 diff 檢查與必要驗證後提交推送。
- PM: 已完成 `TASK.md`，定義 schema 未啟用、DB 查詢失敗、樣本不足三種 Telegram 文案與驗收條件。
- Tech: 已交付 `CHANGELOG.md`；只改 friendly fallback / readiness message 與必要 tests，未 apply schema、未正式寫庫。
- QA: 已完成 L2 驗證並提交 `QA_REPORT.md`；Telegram 不再露出原始 Supabase dict/error，主報文不阻斷，策略不變。
- Owner: 若要真正啟用 evidence DB，需另開 production schema apply / live write 任務。

## Status Values

- `todo`: 等待該角色處理。
- `waiting_pm`: Tech 或 QA 等待 PM 交付。
- `waiting_tech`: QA 等待 Tech 交付。
- `task_ready`: PM 已交付 `TASK.md`。
- `changelog_ready`: Tech 已交付 `CHANGELOG.md`。
- `qa_passed`: QA 驗證通過。
- `qa_failed`: QA 驗證失敗。
- `blocked`: 該角色遇到阻塞，需 Architect 或 Owner 判斷。
- `completed`: 非開發類任務已由負責角色完成。
- `not_required`: 本輪不需要該角色處理。
- `qa_accepted`: Architect 已吸收 QA 結論並更新狀態。
- `pushed`: Architect 已提交並推送。
- `research_dispatched`: Architect 已建立研究任務。
- `research_ready`: 該角色已提交研究摘要。
- `research_accepted`: Architect 已吸收研究摘要並整理結論。

## Version / QA Levels

- version_level `patch`：bug / 文案 / 顯示一致性，不改策略意圖。
- version_level `minor`：新增使用者可見能力或報文結構。
- version_level `major`：改策略核心、DB schema、交易狀態機、正式寫庫或跨日持久化。
- version_level `none`：純流程 / 文件規則補強。
- qa_level `L1`：局部 formatter / snapshot / 指定回歸。
- qa_level `L2`：策略不變性 + formatter + snapshot + 相關模組測試。
- qa_level `L3`：full pytest + replay/backfill dry-run + 入庫 payload 路徑 + 額外風險掃描。
- qa_level `process`：純流程文件補強。
- qa_level `research`：研究任務，不執行測試。

## Fixed Startup Commands

Owner 對 Architect：

```text
按 AGENTS.md 和 DISPATCH.md 處理這個需求，分派並更新狀態文件。
```

Owner 對 PM：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 PM 職責處理；若 pm_status 是 todo 或 Architect 指定 PM，請撰寫 TASK.md，不修改代碼。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；若 tech_status 是 todo 且 TASK.md 已 ready，就依 TASK.md 實作並改寫 CHANGELOG.md，不修改產品方向。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；若 qa_status 是 todo 且 Tech 已交付 CHANGELOG.md，請執行本輪 qa_level 指定驗證，補直接消費者、跨區塊語意一致性、使用者誤讀風險、負面案例與關聯風險掃描，完成後改寫 QA_REPORT.md。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、TASK.md、CHANGELOG.md、QA_REPORT.md，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
