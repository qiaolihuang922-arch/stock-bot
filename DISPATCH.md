# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `workflow_supabase_service_role_runtime_config_20260530`
- task_name: `GitHub Workflow Supabase Service-role Runtime Config Wiring`
- task_type: `tiny_patch`
- version_level: `none`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `qa_condition_satisfied_pending_commit`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `conditional_pass_satisfied`
- commit: `pending`

## Current Result

- Owner 要「多多檢查」Supabase evidence write path。Architect 發現 GitHub workflow `Create runtime config` 只寫入 `SUPABASE_URL / SUPABASE_KEY`，沒有把 `SUPABASE_SERVICE_ROLE_KEY` 或 `SERVICE_ROLE_KEY` alias 寫進 fresh runner `config.py`。
- 本輪修正 GitHub workflow runtime config wiring：
  - split-secret path 新增 `SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}`。
  - runtime `config.py` 同時保留 `SUPABASE_KEY`，並新增 `SUPABASE_SERVICE_ROLE_KEY` 與 `SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY`。
  - legacy `STOCK_CONFIG` path 保留；若新 secret 存在，只追加 service-role aliases，不覆蓋既有 `SUPABASE_KEY`。
  - workflow validation log 只輸出 present / missing，不輸出 URL、read key、service-role key、截斷值或 hash。
- 本輪沒有 production live write、沒有正式 backfill、沒有 DB schema / table / column 變更、沒有 RLS / grant / policy / role 變更、沒有 live Telegram、沒有改策略 decision 或 Telegram version。
- QA conditional pass，Architect 已滿足條件：
  - QA 條件：untracked `tests/test_workflow_runtime_config.py` 必須納入 repo，且修正 `CHANGELOG.md` 自述矛盾。
  - Architect 已納入測試並修正 `CHANGELOG.md`。
  - 主 repo 驗證：`.venv/bin/python -m pytest tests/test_workflow_runtime_config.py tests/test_market_theme_evidence_handoff.py -q`：29 passed。
  - `git diff --check` 通過。
- Runner 狀態：CAO auto cycle 對 QA `conditional pass` 再次誤判 failed；Architect 按 QA 報告條件與主 repo 驗證手動吸收，未整包搬 worktree。
- Post-cycle review：
  - 根因分類：`github_runner_secret_mapping_gap` + `runner_parser_false_fail`。
  - QA 有效覆蓋 workflow-generated config、legacy STOCK_CONFIG、secret redaction、direct write CLI fake consumer。
  - 不新增 `AGENTS.md` 硬規則；既有 GitHub Runtime / State Source 與資料寫入邊界已覆蓋。本輪用 workflow test 與 CLEANUP_PLAN runner 待補沉澱。

## Next Action

- Architect 進行 commit / push，然後清理 CAO worktree。
- 下一步若要真正寫入 production：準備真實 approved persistent payload，先跑 write CLI dry-run；GitHub runner 會由 workflow runtime config 提供 service-role aliases，本機可 fallback `config.py`。`--execute` 走接口 upsert，再跑 read-only smoke。只有 schema/RLS/grant/table/column 或 live Telegram 才再找 Owner。

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
