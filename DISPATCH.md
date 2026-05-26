# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `cao-runner-process-hardening`
- task_name: `CAO Runner Process Hardening`
- task_type: `workflow_runner_patch`
- version_level: `none`
- qa_level: `process`
- owner_status: `requested`
- architect_status: `completed_local`
- pm_status: `not_required`
- tech_status: `not_required`
- qa_status: `not_required`
- commit: `pending_owner_request`

## Current Result

- 本輪是 Architect 流程 / runner 修復，不改產品策略、報文、DB、watchlist、live Telegram 或 live Supabase。
- 已針對上一輪暴露的 5 個問題補 runner gate：
  - 自動鏈不能因 Tech 自檢通過就放行；QA 缺完整測試環境時必須 blocked。
  - QA runner 維持 read-only，但允許 `.qa_tmp/`、dummy `config.py` 與測試暫存，並用 diff hash / handoff hash 防止 QA 修改候選 diff。
  - Tech / QA 交付抽取改為只吸收最後一個合法 `# CHANGELOG:` / `# QA_REPORT:`，避免 transcript 混入正式文件。
  - Tech worktree 的上下文 Markdown 改為 read-only handoff context，不再作為整包可合併 diff；候選 diff 只看產品 / 測試 / `CHANGELOG.md`。
  - auto cycle 改為 QA 報告結構合格後，才把 `CHANGELOG.md` / `QA_REPORT.md` 寫回主 repo。
- `AGENTS.md` 已新增 Runner hygiene gates，將上述行為固定為後續規則。
- v20.0.6 產品 patch 仍維持：已本地合併、QA L2 `conditional pass`、尚未 commit / push；未做 production 秒數 benchmark。
- Architect final review 驗證已通過：
  - full pytest：`105 passed, 21 warnings`
  - replay synthetic dry-run validate：`VALIDATION OK`
  - backfill synthetic dry-run：`VALIDATION OK`、`DRY RUN ONLY: no database writes`
  - runner shell syntax：`bash -n` 通過

## Next Action

- 若 Owner 要發布到遠端，Architect 需先確認本地 commit，再另行 push。
- 下一次 `run_architect_task.sh auto` 實際任務要觀察新 gate 是否阻止：測試環境缺口、transcript 污染、handoff 文件殘留、QA 偷改 tracked files。
- 若仍覺得 v20.0.6 查詢慢，另開 performance measurement 任務量測 production 真實秒數。

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

Architect 可用 CAO online research：

```text
研究：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh research "<研究問題>"
規劃：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh plan "<技術規劃問題>"
自動開發：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh auto "<Owner 任務>"

底層 run_project_research.sh / run_tech_plan.sh / run_auto_dev_cycle.sh / run_tech_write.sh / run_qa_code.sh 只作為內部工具，不作為 Owner 日常入口。
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
