# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v19.3.3-formatter-consistency`
- task_name: `v19.3.3 formatter 一致性修正`
- task_type: `development`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`

## Next Action

- Architect: 已吸收 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`，本輪可更新狀態。
- PM: 已交付 v19.3.3 `TASK.md`。
- Tech: 已交付 v19.3.3 `CHANGELOG.md`。
- QA: 已交付 v19.3.3 `QA_REPORT.md`，局部 formatter 測試通過。
- Owner: 若要進一步處理策略門檻或 live Telegram 驗收，另開新任務。

## Status Values

- `todo`: 等待該角色處理。
- `waiting_pm`: Tech 或 QA 等待 PM 交付。
- `waiting_tech`: QA 等待 Tech 交付。
- `task_ready`: PM 已交付 `TASK.md`。
- `changelog_ready`: Tech 已交付 `CHANGELOG.md`。
- `qa_passed`: QA 驗證通過。
- `qa_failed`: QA 驗證失敗。
- `blocked`: 該角色遇到阻塞，需 Architect 或 Owner 判斷。
- `qa_accepted`: Architect 已吸收 QA 結論並更新狀態。
- `research_dispatched`: Architect 已建立研究任務。
- `research_ready`: 該角色已提交研究摘要。
- `research_accepted`: Architect 已吸收研究摘要並整理結論。

## Fixed Startup Commands

Owner 對 Architect：

```text
按 AGENTS.md 和 DISPATCH.md 處理這個需求，分派並更新狀態文件。
```

Owner 對 PM：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 PM 職責處理；如果 pm_status 是 todo，就只填寫 RESEARCH.md 的 PM Findings。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 Tech 職責處理；如果 tech_status 是 todo，就研究策略層與顯示層一致性，只填寫 RESEARCH.md 的 Tech Findings，不要先改代碼。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 QA 職責處理；等 PM/Tech Findings 完成後，填寫 RESEARCH.md 的 QA Findings。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、RESEARCH.md，整理 Architect Conclusion，並更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
