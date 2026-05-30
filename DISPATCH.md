# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence_chain_write_interface_20260530`
- task_name: `Market Theme Confirmed Evidence Repo-side Write CLI`
- task_type: `risk_patch`
- version_level: `none`
- qa_level: `L2+`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `conditional_pass`
- commit: `c0491ae pushed`

## Current Result

- Owner 最新規則：只有新增表 / 擴字段 / schema / RLS / grant / policy / role 變更才找 Owner；非 schema 的 evidence rows 新增 / 回寫 / backfill 應走既有接口 / repo script / approved service API，不再交普通 DML 給 Owner 手動跑。
- 本輪完成 repo-side write CLI：
  - 新增 `scripts/write_market_theme_confirmed_evidence.py`。
  - 預設 dry-run / validate，不寫 DB；輸出 target table、validation status、row count、conflict target、sanitized preview。
  - `--execute` 只有在 payload validation passed、source family allowed、`SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` 存在時才進入 upsert。
  - 缺 env、forbidden source、missing source、mixed allowed+forbidden source 全部 fail closed。
  - 更新 `services/market_theme_evidence_store.py`，新增 write plan、write env validation、client builder、upsert helper；未改 read-only loader confirmed 判斷。
  - 更新 handoff docs 與 examples，說明非 schema evidence rows 走 repo script / approved API；schema/RLS/grant/table/column 才找 Owner。
- 本輪沒有 production live write、沒有正式 backfill、沒有 DB schema / table / column 變更、沒有 RLS / grant / policy / role 變更、沒有 live Telegram、沒有改策略 decision 或 Telegram version。
- QA conditional pass，條件已由 Architect 吸收滿足：
  - QA 條件：untracked `scripts/write_market_theme_confirmed_evidence.py` 必須納入 repo；Architect 已納入。
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q`：43 passed, 17 warnings。
  - allowed sample dry-run exit 0，`write_execution=disabled`，`rows_to_upsert=1`。
  - forbidden runtime sample dry-run exit 2，`payload_validation.status=failed`。
  - `--execute` 缺 env exit 2，`write_execution=blocked`，列出 missing env names，`rows_written=0`。
  - `py_compile`、`git diff --check` 通過。
- Runner 狀態：CAO auto cycle 對 QA `conditional pass` 再次誤判 failed；Architect 按 QA 報告與主 repo 驗證手動吸收，未整包搬 worktree。
- Post-cycle review：
  - 根因分類：`write_interface_gap` + `approval_boundary_overbroad` + `runner_parser_false_fail`。
  - QA 有效攔截 untracked CLI 風險；Architect 吸收時已納入 write script。
  - 不新增 `AGENTS.md` 硬規則；Owner 最新資料寫入邊界已在上一輪寫入。本輪沉澱為 write CLI、tests、handoff docs 與 runner 待補。

## Next Action

- 本輪 diff 已 commit / push：`c0491ae feat: add evidence write cli`。
- Architect 清理 CAO worktree。
- 下一步若要真正寫入 production：準備真實 approved persistent payload，先跑 write CLI dry-run；若 env / permissions 具備，可用 `--execute` 走接口 upsert，再跑 read-only smoke。只有 schema/RLS/grant/table/column 或 live Telegram 才再找 Owner。

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
