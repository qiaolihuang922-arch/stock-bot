# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `production-evidence-approved-payload-audit`
- task_name: `Production Evidence Source Audit And Approved Payload Gate`
- task_type: `normal_patch`
- version_level: `none`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `ready_to_commit`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 要繼續 production evidence 閉環。read-only smoke 現已可讀 production，但 `market_theme_confirmed_evidence` rows=0；本輪新增 read-only production source audit / approved payload gate，先判斷現有 production DB 資料是否可安全生成 approved payload preview。
- 本輪新增 `scripts/smoke_market_theme_evidence_readonly.py --production-source-audit-json`：
  - 固定 `write_execution=disabled`、`live_write=false`。
  - 讀取 `market_theme_confirmed_evidence`、`daily_signal_snapshot`、`signal_runs`、`signal_items` 的 source availability / row count。
  - 只有 production row 明確具備 `market_index`、`sector_theme_key`、`watchlist_breadth`、`evidence_value`、`support_level`、`lineage` 等既有 contract 欄位，才可輸出 `approved_payload_preview`。
  - 若只有個股策略 snapshot / signal item row count，必須 `can_generate_approved_payload=false`、`status=blocked`。
- 本輪沒有 production live write、formal backfill、DB schema / table / column 變更、RLS / grant / policy / role 變更、live Telegram、策略 decision、Telegram formatter 或 Telegram `VERSION` 變更。
- QA 結論：`conditional pass`，Architect 已用真實 production read-only audit 滿足主要條件。
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q`：34 passed。
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py -q`：21 passed。
  - `git diff --check`：通過。
- Architect 主 repo 驗證：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q`：55 passed，17 warnings。
  - `git diff --check`：通過。
  - 真實 production read-only audit：`market_theme_confirmed_evidence rows=0`、`daily_signal_snapshot rows=48`、`signal_runs rows=1`、`signal_items rows=12`、`can_generate_approved_payload=false`、`status=blocked`。
  - 缺少 semantics：`market_index`、`sector_theme_key`、`watchlist_breadth definition`、`evidence_value meaning`、`support_level rule`、`lineage from production DB columns`。
- Post-cycle review：
  - 根因分類：`production_source_semantics_gap` + `runner_parser_false_fail`。
  - QA 有效覆蓋 dry-run only、fail-closed gate、直接消費者、Owner 誤讀風險。
  - 不新增 `AGENTS.md` 硬規則；既有 source-of-truth、資料寫入邊界、live write 禁令與 Post-cycle Review 已覆蓋。本輪沉澱為 helper/test 與 runner 待補。

## Next Action

- Architect commit / push，清理 CAO worktree。
- 下一步需要 Owner 決策：是否允許把 `daily_signal_snapshot` / `signal_runs/items` 的 production DB row count 與策略欄位定義為 market/theme supporting evidence source；若允許，需明確給出 market_index、sector_theme_key、watchlist_breadth、evidence_value、support_level、lineage 的 mapping 規則。若不允許，需要提供外部市場/族群指數或另一張 production source 表。

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
