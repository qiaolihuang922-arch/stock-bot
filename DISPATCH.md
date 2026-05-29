# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `postmarket-noise-index-wording-v20.2.5`
- task_name: `Post-market Noise And Index Wording`
- task_type: `normal_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `qa_passed_absorbed_pending_push`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 檢查 `v20.2.4` 盤後報文後，策略方向可接受，但指出仍需先處理手機噪音與語意衝突，再繼續證據鏈。
- 本輪只修 Telegram 盤後 summary / funnel / index 文案：不改策略門檻、不改 `可準備` 分類、不改 evidence provider、不改 DB schema，不 live、不 backfill。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，定義：
  - `今日交易紀錄 / 無新增` 與 `已執行（不重複下單）` 並存時易誤讀，應改為 `今日交易 / 新增交易建議：無`。
  - `僅追蹤 0` 時不得輸出 `等冷卻 0、等回測 0、等RR修復 0、等量能 0`。
  - `非執行追蹤合計 8（可準備 + 僅追蹤）` 在僅追蹤 0 時要改成更清楚的可準備語意。
  - 詳情索引不得把可準備 8 混稱為 `未持倉追蹤 8`。
- Tech 已交付候選 diff：
  - `core/generator.py` VERSION 升為 `v20.2.5`。
  - `format_unheld_funnel()` 僅在有非零僅追蹤分類時輸出拆分行，且只列非零分類。
  - `detail_index_text()` 分開列 `可準備 N`、`僅追蹤 N`、`淘汰 N`。
  - 盤後 summary 今日交易區塊改為 `今日交易 / 新增交易建議：無`。
  - 新增 05/29 盤後 fixture：可買 0、可準備 8、僅追蹤 0、淘汰 2、英業達今日已賣 187 股。
- QA 最終驗證通過：
  - 05/29 盤後類似 fixture 驗證 `今日交易 / 新增交易建議：無` 與 `已執行（不重複下單）` 可清楚區分。
  - `僅追蹤 0` 不輸出零拆分，不出現 `等冷卻 0 / 等回測 0 / 等RR修復 0 / 等量能 0`。
  - 漏斗與索引一致：`可買 0｜可準備 8（不可買）｜僅追蹤 0｜淘汰 2`，索引顯示 `可準備 8｜淘汰 2`。
  - 無策略門檻、DB schema、watchlist、live Telegram、Supabase write、replay/backfill diff。
  - 主 repo 驗證：`79 passed, 21 warnings`；策略 smoke `39 passed`；`git diff --check` 通過。
- Post-cycle review：
  - 根因分類：`repeated_pattern` / 空狀態與聚合名稱造成手機誤讀；既有手機閱讀與 0-count 噪音規則已覆蓋。
  - Runner gap：auto cycle 對 QA `通過` 產生 false fail，已記入 `CLEANUP_PLAN.md`，本輪手動吸收 QA 明確通過報告。
  - 不新增 `AGENTS.md` 硬規則，改沉澱到 fixture / QA 反證與 runner 待補。

## Next Action

- commit / push 後清理 tech worktree。
- 報文確認後再開證據鏈下一步；若涉及 DB table / cache / external provider，先通知 Owner。

## Status Values

- `todo`: 等待該角色處理。
- `waiting_pm`: Tech 或 QA 等待 PM 交付。
- `waiting_tech`: QA 等待 Tech 交付。
- `task_ready`: PM 已交付 `TASK.md`。
- `changelog_ready`: Tech 已交付 `CHANGELOG.md`。
- `qa_passed`: QA 驗證通過。
- `qa_failed`: QA 驗證失敗。
- `conditional_pass`: QA 有條件通過，仍有合併前必要驗證或 Owner 決策。
- `conditional_acceptance`: Architect 有條件吸收結果，不代表可 commit / push。
- `blocked`: 該角色遇到阻塞，需 Architect 或 Owner 判斷。
- `completed`: 非開發類任務已由負責角色完成。
- `not_required`: 本輪不需要該角色處理。
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
你是 Architect / 總控，不是 PM、Tech、QA。先讀 AGENTS.md 和 DISPATCH.md；若是產品 bug / 顯示 bug / feature request，只能先更新 DISPATCH.md 分派 PM，不得直接寫 TASK.md、不得搜尋或修改產品代碼，除非 Owner 明確說你直接代該角色。
```

Architect 可用 CAO：

```text
研究：tools/cao_agent/run_architect_task.sh research "<研究問題>"
規劃：tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
自動開發：tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"

CAO 服務確認：tools/cao_agent/ensure_cao_services.sh
分配或啟動 CAO agents 後，Architect 必須先確認服務已啟動，再回覆 Owner 前端地址：http://127.0.0.1:5173/
```

Owner 對 PM：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 PM 職責處理；若 pm_status 是 todo 或 Architect 指定 PM，請撰寫 TASK.md，不修改代碼。TASK.md 必須從 # TASK: 開始，並符合 AGENTS.md 的 PM 任務卡固定欄位；若需求不足，請輸出 blocked TASK.md。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；若 tech_status 是 todo 且 TASK.md 已 ready，就依 TASK.md 實作並改寫 CHANGELOG.md，不修改產品方向。CHANGELOG.md 必須從 # CHANGELOG: 開始，並符合 AGENTS.md 的 Tech 實作卡固定欄位；若 TASK.md 缺直接消費者、驗收條件或輸出契約，請 blocked。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；若 qa_status 是 todo 且 Tech 已交付 CHANGELOG.md，請執行本輪 qa_level 指定驗證，補直接消費者、跨區塊語意一致性、使用者誤讀風險、負面案例與關聯風險掃描，完成後改寫 QA_REPORT.md。QA_REPORT.md 必須從 # QA_REPORT: 開始；若只重跑 Tech 測試或沒有主動質疑，不能判定通過。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、TASK.md、CHANGELOG.md、QA_REPORT.md，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
