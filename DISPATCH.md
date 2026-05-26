# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v19.5-report-summary-execution`
- task_name: `v19.5 收盤決策壓縮與執行清單升級`
- task_type: `development`
- version_level: `minor`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`

## Next Action

- Architect: 已吸收 v19.5 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`，本輪 L2 QA 通過。
- PM: 已改寫 `TASK.md`，合併 PM / Tech / QA / Owner 約束。
- Tech: 已交付 `CHANGELOG.md`，實作 v19.5 收盤決策壓縮與執行清單升級。
- QA: 已交付 `QA_REPORT.md`，v19.5 L2 驗證通過，包含關聯風險掃描、直接消費者檢查、質疑與反證。
- Owner: 交由 Architect 檢查 diff、重跑必要驗證、commit 並 push。

## Task Brief

Owner 反馈：

- v19.4.1 收盤報文已能把總覽摘要放在最後，但報文仍偏長。
- v19.5 研究已完成，正式進入開發。
- PM 已在 `TASK.md` 定義「今日結論」、「明日執行清單」、「未持倉漏斗」、「詳情索引」。
- Tech 需限定在顯示 / 排序 / summary view model 層實作，避免改策略 action。
- QA 後續需強化質疑：檢查是否會讓使用者漏看風控、誤解等待標的、低優先級不可追溯，或讓 Telegram summary/reply_markup 契約回退。
- Owner 補充：明日執行清單中的持倉項必須保留目前收益百分比，不能為了壓縮刪除盈虧資訊。
- Tech 自檢只需跑與修改直接相關的最小 formatter / contract / 策略不變性 smoke；QA 之後做獨立 L2 驗證與風險掃描，避免把 QA 工作前移到 Tech。

不可變更：

- PM 已完成 `TASK.md`；下一步 Tech 實作。
- 本輪 Architect 只分派與整理，不直接實作。
- 不改策略層、不改買賣判斷、不改 DB、不改 replay/backfill。
- 不做全 repo 分析。
- 不跑全局測試。

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

## Version / QA Levels

- version_level `patch`：bug / 文案 / 顯示一致性，不改策略意圖。
- version_level `minor`：新增使用者可見能力或報文結構。
- version_level `major`：改策略核心、DB schema、交易狀態機、正式寫庫或跨日持久化。
- qa_level `L1`：局部 formatter / snapshot / 指定回歸。
- qa_level `L2`：策略不變性 + formatter + snapshot + 相關模組測試。
- qa_level `L3`：full pytest + replay/backfill dry-run + 入庫 payload 路徑 + 額外風險掃描。
- minor 預設 L3；major 必須 L3 且需 Owner 明確批准。

## Fixed Startup Commands

Owner 對 Architect：

```text
按 AGENTS.md 和 DISPATCH.md 處理這個需求，分派並更新狀態文件。
```

Owner 對 PM：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 PM 職責處理；確認 version_level 與 qa_level，將 TASK.md 改寫為當前任務需求。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；如果 tech_status 是 todo 且 TASK.md 已 ready，就實作 v19.5 收盤決策壓縮與執行清單升級，完成後改寫 CHANGELOG.md。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；如果 qa_status 是 todo 且 CHANGELOG.md 已 ready，就依 DISPATCH.md 的 qa_level 驗證當前任務，並主動做關聯風險掃描、直接消費者檢查、質疑與反證；完成後更新 QA_REPORT.md。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、RESEARCH.md，整理 Architect Conclusion，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
