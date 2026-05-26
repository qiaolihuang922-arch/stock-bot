# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v19.5.1-summary-semantic-consistency`
- task_name: `v19.5.1 摘要語意一致性修復`
- task_type: `development`
- version_level: `patch`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`

## Next Action

- Architect: 已吸收 QA 重測結論，v19.5.1 L1 驗證通過；下一步檢查 diff、提交並推送。
- PM: 已改寫 `TASK.md`，定義「執行項 vs 僅追蹤候選」文案規則與驗收條件。
- Tech: 已補修 QA blocker，修復 `0 檔僅追蹤` 文案分支並補 formatter unit test，`CHANGELOG.md` 已更新。
- QA: 已交付 `QA_REPORT.md` 重測結果，v19.5.1 QA blocker 已解除，結論通過。
- Owner: 交由 Architect 提交並推送本輪變更。

## Task Brief

Owner 反馈：

- v19.5 完整走過 PM / Tech / QA 後，實際報文仍出現摘要語意衝突。
- 現象：
  - 今日結論寫 `明日只追 6 檔`。
  - 明日執行清單 5 項全是持倉。
  - 6 檔未持倉只在 `另有 6 檔追蹤見詳情` 與漏斗中出現。
- 問題：使用者會混淆「明日執行項」與「僅追蹤候選」，也會誤解摘要中的 `追 N 檔`。
- 目標：修正 summary 文案與 overflow 語意，使今日結論、明日執行清單、未持倉漏斗、詳情索引互相一致。
- 本輪定位為 patch：只修顯示語意與測試，不改策略、不改買賣判斷、不改 DB。
- QA 第一輪阻塞：指定測試通過，但 QA 補充 smoke 發現「有持倉 + 有合格 BUY + 沒有不可買追蹤候選」時，今日結論仍輸出 `未持倉 0 檔僅追蹤`；這違反 `TASK.md` Edge Case，需回交 Tech 修復。

不可變更：

- 本輪 Architect 只分派與收口，不直接實作。
- 不改策略層、不改買賣判斷、不改 DB、不改 replay/backfill。
- 不改 v19.5 的 Telegram summary-last contract。
- 不移除持倉盈虧百分比。
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
- `completed`: 非開發類任務已由負責角色完成。
- `not_required`: 本輪不需要該角色處理。
- `qa_accepted`: Architect 已吸收 QA 結論並更新狀態。
- `research_dispatched`: Architect 已建立研究任務。
- `research_ready`: 該角色已提交研究摘要。
- `research_accepted`: Architect 已吸收研究摘要並整理結論。

## Version / QA Levels

- version_level `patch`：bug / 文案 / 顯示一致性，不改策略意圖。
- version_level `minor`：新增使用者可見能力或報文結構。
- version_level `major`：改策略核心、DB schema、交易狀態機、正式寫庫或跨日持久化。
- version_level `none`：純流程 / 文件規則補強，不對應產品版本。
- qa_level `L1`：局部 formatter / snapshot / 指定回歸。
- qa_level `L2`：策略不變性 + formatter + snapshot + 相關模組測試。
- qa_level `L3`：full pytest + replay/backfill dry-run + 入庫 payload 路徑 + 額外風險掃描。
- qa_level `process`：純流程文件補強，不要求測試部門驗證。
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
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；如果 tech_status 是 todo 且 TASK.md 已 ready，就實作 v19.5.1 摘要語意一致性修復，限定 formatter / summary view model 與必要局部測試，完成後改寫 CHANGELOG.md。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；如果 qa_status 是 todo 且 CHANGELOG.md 已 ready，就依 DISPATCH.md 的 qa_level 驗證當前任務。QA 不只照指定清單驗收，必須主動找 PM / Tech 未想到的風險，包含跨區塊語意一致性、使用者誤讀、壓縮失真、數字與明細矛盾、直接消費者契約；完成後更新 QA_REPORT.md。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、RESEARCH.md，整理 Architect Conclusion，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
