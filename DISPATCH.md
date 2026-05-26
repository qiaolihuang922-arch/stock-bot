# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v19.4-trading-loop`
- task_name: `v19.4 交易閉環升級`
- task_type: `development`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`

## Next Action

- Architect: 已吸收 v19.4 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`，本輪全量 QA 通過。
- PM: 已交付 v19.4 交易閉環升級 `TASK.md`。
- Tech: 已交付 v19.4 交易閉環升級 `CHANGELOG.md`。
- QA: 已完成 v19.4 全量 QA，包含 formatter、策略不變性、snapshot、replay/backfill dry-run、資料入庫路徑檢查與額外風險掃描。
- Owner: 若確認交付，交由 Architect 檢查 diff、重跑必要驗證、commit 並 push。

## Task Brief

v19.3.4 報文已接近穩定，v19.4 需要做出可感知的功能升級，不應只是 formatter 小修或少量文案調整。

PM 需研究：

- v19.4 要達到「顯著升級」的最小範圍，不能只改顯示文字。
- v19.4 是否需要強化策略門檻，而不是只修 formatter。
- 是否要改善買入訊號稀少問題：
  - RR 門檻
  - 過熱但可等待回測
  - R3 市場下的可買 / 排隊 / 冷卻規則
- 是否要改善持倉處理：
  - 核心續抱
  - 新倉風控
  - 洗盤警戒
  - 減碼 / 停利 / 停損升級規則
- 是否要讓回測資訊進一步進入決策，而不是只顯示解釋：
  - 樣本數可信度
  - 3 日勝率
  - 相對表現
  - 是否可作為加權參考
- 是否需要建立「隔日追蹤」或「待確認清單」：
  - 今日不買但明天可重新評估
  - 今日減碼後觀察是否修復
  - 今日新倉浮虧隔日是否降級
- 殘留顯示風險：
  - Owner 最新貼文中旺宏價格行疑似少右括號：`價格：159.75（+4.75%`
  - PM 需判斷這是複製截斷、Telegram split 問題，還是 v19.3.x 仍需補修。

- v19.4 報文應新增哪些使用者可見區塊與文案：
  - `隔日追蹤`
  - `持倉處理優先級`
  - `待確認候選`
  - `回測輔助排序`
  - `明日觸發條件`
- v19.4 是否要把「今天不能買」轉成「明天怎麼看」。
- v19.4 應如何讓使用者感覺版本有明顯進步，而不是只多幾個 label。

不可變更：

- PM 不改代碼。
- 本輪先不直接實作，但 PM 必須定義足夠明確的 v19.4 升級需求。
- 本輪不要求 Tech 實作。
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

## Fixed Startup Commands

Owner 對 Architect：

```text
按 AGENTS.md 和 DISPATCH.md 處理這個需求，分派並更新狀態文件。
```

Owner 對 PM：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 PM 職責處理；根據 RESEARCH.md 的 Architect Conclusion 和 PM Findings，將 TASK.md 改寫為 v19.4 交易閉環升級需求。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；如果 tech_status 是 todo 且 TASK.md 已 ready，就實作 v19.4 交易閉環升級，完成後改寫 CHANGELOG.md。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；如果 qa_status 是 todo 且 CHANGELOG.md 已 ready，就對 v19.4 交易閉環升級做全量 QA，包含 formatter、策略不變性、snapshot、replay/backfill dry-run、資料入庫路徑檢查，以及你認為 Owner 沒想到但可能出問題的地方。完成後更新 QA_REPORT.md。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、RESEARCH.md，整理 Architect Conclusion，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
