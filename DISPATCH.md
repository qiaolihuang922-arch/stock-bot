# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence_chain_approval_payload_template_20260530`
- task_name: `Market Theme Approved Payload Template And Dry-run Sample`
- task_type: `risk_patch`
- version_level: `none`
- qa_level: `L2+`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `conditional_pass`
- commit: `80ae97d pushed`

## Current Result

- Owner 要求開始下一步：建立第一份 market/theme approved payload 模板與可執行 dry-run 樣本，讓 Owner 能用 approval package generator 產生可審核 package。
- 本輪完成 approved payload template / sample workflow：
  - 新增 `docs/examples/market_theme_owner_approved_payload.template.json`：Owner-facing 填寫模板，列出 required fields、allowed / forbidden source family、manual approval boundary。
  - 新增 `docs/examples/market_theme_owner_approved_payload.sample.json`：allowed `owner_approved_persistent` dry-run sample，可產 package JSON / Markdown / review-only SQL。
  - 新增 `docs/examples/market_theme_forbidden_runtime_payload.sample.json`：negative runtime sample，必須 fail closed，不產 deterministic SQL。
  - 更新 handoff docs，固定 sample dry-run 指令、forbidden dry-run 指令、輸出檔案與 no-live-write / review-only / not production confirmed 邊界。
  - 補測試覆蓋 template/sample/docs 契約、allowed sample CLI、forbidden sample CLI、sample-as-production 誤讀防線。
- 本輪沒有 live Supabase write、沒有正式 backfill、沒有 production RLS / grant 變更、沒有 live Telegram、沒有改策略 decision 或使用者可見 Telegram version。
- QA conditional pass，條件已由 Architect 吸收滿足：
  - QA 條件：三份 `docs/examples/*market_theme*` untracked deliverables 必須納入 repo；Architect 已納入。
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q`：39 passed, 17 warnings。
  - allowed sample dry-run exit 0，產出 `approval_package.json`、`approval_package.md`、`market_theme_confirmed_evidence_2026-05-29.sql`。
  - forbidden runtime sample dry-run exit 2，`payload_validation.status=failed`、`deterministic_sql=None`，無 SQL file。
  - `git diff --check` 通過；docs/examples / handoff docs / tests 無 secret / connection string pattern。
- Runner 狀態：CAO auto cycle 對 QA `conditional pass` 再次誤判 failed；Architect 按 QA 報告與主 repo 驗證手動吸收，未整包搬 worktree。
- Post-cycle review：
  - 根因分類：`owner_payload_contract_gap` + `sample_as_production_misread_risk` + `runner_parser_false_fail`。
  - QA 有效攔截 untracked deliverables 風險；Architect 吸收時已納入三份 examples。
  - 不新增 `AGENTS.md` 硬規則；既有 source-of-truth、fake confirmed、live write 禁令已覆蓋。本輪沉澱為 template/sample/docs/tests 與 runner 待補。

## Next Action

- 本輪 diff 已 commit / push：`80ae97d docs: add evidence payload samples`。
- Architect 清理 CAO worktree。
- 下一步若 Owner 要真正進 production：用 template 替換真實 approved persistent evidence reference，產生 package 給 Owner 審核；正式 SQL execution、backfill、RLS / grant、live write、live Telegram 仍需單獨批准。

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
