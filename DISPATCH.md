# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence_phase_5_readonly_confirmed_evidence_loader`
- task_name: `Evidence Phase 5 Read-only Confirmed Evidence Loader`
- task_type: `normal_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `conditional_pass`
- commit: `fb8aa2d`

## Current Result

- Owner 要求繼續證據鏈；Phase 4 production table schema 已由 Owner 回傳 verification result，hard schema PASS。
- Phase 5 已完成候選開發並吸收：
  - 新增 `services/market_theme_evidence_store.py` read-only loader，讀取 `public.market_theme_confirmed_evidence`。
  - confirmed 條件固定為 `support_level in ('confirmed','supporting')`、`evidence_status='confirmed'`、`freshness='fresh'`。
  - `support_level=strong` 只作負面案例，回 `source-error` / fail closed，不得 accepted。
  - `core/generator.py` 接入 loader；GitHub / fresh runner 缺 DB env、query error、no rows、資料不足時輸出 fail-closed，不用 local/runtime/report-derived fake confirmed。
  - Telegram 使用者可見版本升至 `v20.4.3`。
- QA conditional pass 條件已由 Architect 吸收時滿足：untracked 新檔 `services/market_theme_evidence_store.py` 已一併納入主 repo，不只套 tracked diff。
- 主 repo 驗證：
  - `PYTHONPATH=.qa_tmp:. arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py`
  - 結果：`93 passed, 161 warnings`；warnings 為依賴 deprecation / Python 版本警告，非本輪 contract failure。
  - `git diff --check` 通過。
- 未完成 / 未批准：production read-only role / RLS 實際可讀驗證、writer、backfill、live Telegram、策略門檻調整。
- Post-cycle review：
  - 根因分類：`pm_schema_contract_drift` + `runner_gap`。
  - 首輪 PM 把 `support_level=strong` 寫成合法 fixture，與剛驗過的 production constraint 不符；QA 有效阻塞，第二輪已修正為負面案例。
  - Auto cycle 對 QA `conditional pass` 仍 false fail；已人工讀取 QA 原文並吸收條件，runner parser 待補。
  - 不新增 `AGENTS.md` 硬規則；既有 source-of-truth / fail-closed / schema contract 規則已覆蓋，本輪寫入 `CLEANUP_PLAN.md` 待補 runner / PM guard。

## Next Action

- Phase 5 loader 已 commit / push：`fb8aa2d`.
- push 後清理 agent worktrees。
- 下一步可做 production read-only role / RLS / actual data smoke；若需要建 role/policy 或 writer/backfill，需 Owner 單獨批准。

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
