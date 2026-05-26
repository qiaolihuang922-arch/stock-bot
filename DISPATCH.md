# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v20.0-strategy-evidence-foundation`
- task_name: `v20.0 Strategy Evidence Foundation`
- task_type: `development`
- version_level: `major`
- qa_level: `L3`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `2cc4e8a feat: add v20 strategy evidence foundation`

## Current Result

- v20.0 已完成 PM / Tech / QA 接力並推送到 `origin/main`。
- 本輪新增策略證據資料層、分類績效摘要、Telegram `📊 策略證據 v20.0`、replay/backfill dry-run evidence path 與 schema 草案。
- QA L3 通過：full pytest、synthetic replay/backfill dry-run、DB payload/schema、Telegram contract、策略不變性、未來資料洩漏、證據層失敗降級與外部資料不接 BUY 路徑。
- 本輪未做 production schema apply、live Supabase write、live Telegram delivery、正式 backfill write；這些需 Owner 另開明確批准流程。

## Next Action

- Architect: push 後已壓縮工作流文件；等待 Owner 下一個需求。
- PM: 等待下一輪任務；不得自行改 `TASK.md`。
- Tech: 等待下一輪任務；不得自行改代碼或 `CHANGELOG.md`。
- QA: 等待下一輪任務；不得自行重跑或改 `QA_REPORT.md`。
- Owner: 若要啟用 v20 production schema / live write / live Telegram，需明確下達新任務。

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
