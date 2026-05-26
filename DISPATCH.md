# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v19.3.4-report-explainability`
- task_name: `v19.3.4 報文解釋力修正`
- task_type: `development`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`

## Next Action

- Architect: 已吸收 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`，本輪可更新狀態。
- PM: 已交付 v19.3.4 `TASK.md`。
- Tech: 已交付 v19.3.4 `CHANGELOG.md`。
- QA: 已交付 v19.3.4 `QA_REPORT.md`，局部 formatter 測試通過。
- Owner: 若要推送本輪修改，要求 Architect 檢查 diff、測試、commit、push。

## Task Brief

本輪仍屬 v19.3.x，不升級 v19.4。目標是提升報文解釋力，不改策略門檻。

PM 需定義：

- 回測欄位如何解釋：
  - `樣本N`
  - `3日勝率`
  - `相對±x%`
  - 增加 `參考度低 / 中 / 高`
  - 增加 `無明顯優勢 / 略優 / 偏弱` 等簡短判讀
- R3 進攻偏熱但不新增倉位時，頂部需要說明原因：
  - 例如強勢股多已過熱、RR 不足、禁止追高。
- 智原這類今日新倉浮虧，不應普通顯示 `續抱觀察`：
  - 需定義為 `新倉風控觀察` 或 `洗盤警戒`。
- 減碼 / 停利 / 停損需補充為什麼是該動作：
  - 例如 `突破失敗但仍有浮盈，所以先減碼25%`。
- 持倉卡片可否增加更明確的 `下一步`：
  - 守警戒價
  - 不加碼
  - 跌破警戒升級風控
  - 隔日未修復降低優先級

不可變更：

- 不升 v19.4。
- 不改 RR 門檻。
- 不改過熱規則。
- 不改加碼 / 減碼 / 停利 / 停損策略門檻。
- 不改 DB / replay / backfill。
- 不改股票池。
- 不做全 repo refactor。

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
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md，按 PM 職責處理；如果 pm_status 是 todo，就根據 DISPATCH.md 的 Task Brief 改寫 TASK.md。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md，按 Tech 職責處理；如果 tech_status 是 todo 且 TASK.md 已 ready，就只做 v19.3.4 報文解釋力修正，完成後更新 CHANGELOG.md。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md，按 QA 職責處理；如果 qa_status 是 todo 且 CHANGELOG.md 已 ready，就驗證 v19.3.4 報文解釋力修正並更新 QA_REPORT.md。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、TASK.md、CHANGELOG.md、QA_REPORT.md，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
