# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v19.4.1-telegram-order`
- task_name: `Telegram 推送順序調整`
- task_type: `development`
- version_level: `patch`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`

## Next Action

- Architect: 已確認 Tech 補修 `reply_markup` 綁定位置；本輪不再要求 QA 重跑，由 Architect 收口檢查後提交。
- PM: 已交付 `TASK.md`，定義 Telegram 多段推送順序需求與驗收條件。
- Tech: 已補修 Telegram `reply_markup` 綁定位置，並更新 `CHANGELOG.md`。
- QA: 第一輪 L1 已通過；QA 強化規則從下一次任務開始執行。
- Owner: 交由 Architect 檢查 diff、重跑必要驗證、commit 並 push。

## Task Brief

Owner 反馈：

- Telegram 報文是多段疊加推送。
- 使用者打開 Telegram 時，最下面的新訊息最容易直接看到。
- 目前最重要的摘要在第一段，會被後續詳情訊息往上推。
- 需求：調整多段訊息送出順序，讓最重要的總覽摘要最後送出、顯示在最下面。
- 版本由 Architect 判定，本輪定為 `v19.4.1` patch。

PM 需定義：

- 三段預設訊息的目標順序。
- `include_detail=True` 時完整備份是否應排在摘要前，避免摘要被擋住。
- 哪些內容屬於「最重要」並應位於最後一段。
- 是否只改 Telegram 多段訊息排序，不改每段內部排序與策略文案。
- 驗收條件：summary 必須是最後一段；持倉/未持倉詳情仍保留；版本顯示更新策略。
- 收口補充：若 Telegram inline keyboard / reply_markup 存在，需確認它是否應綁定最後的總覽摘要，而不是第一段詳情。

不可變更：

- PM 不改代碼。
- 本輪 Architect 不直接實作。
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
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；如果 tech_status 是 todo 且 TASK.md 已 ready，就實作當前任務，完成後改寫 CHANGELOG.md。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；如果 qa_status 是 todo 且 CHANGELOG.md 已 ready，就依 DISPATCH.md 的 qa_level 驗證當前任務，並主動做關聯風險掃描、直接消費者檢查、質疑與反證；完成後更新 QA_REPORT.md。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、RESEARCH.md，整理 Architect Conclusion，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
