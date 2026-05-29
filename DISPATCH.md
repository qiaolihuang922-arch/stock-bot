# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `urgent_tiny_patch_sql_evidence_phase_4_syntax`
- task_name: `Fix Supabase SQL Artifact End-Of-Input Error`
- task_type: `tiny_patch`
- version_level: `patch`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `validated_pending_push`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `conditional_pass`
- commit: `pending`

## Current Result

- Owner 回報：手動執行 `db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql` 時 Supabase 顯示 `ERROR 42601 syntax error at end of input`。
- PM 已收斂為 tiny patch：只修 SQL artifact 的可複製完整性與 handoff notes，不改 schema intent、不改產品代碼、不連 production、不 backfill。
- Tech 已完成最小修正：
  - SQL header 補明「整段複製執行」，不可只複製中段；漏掉尾端 statement terminator 可能造成 `42601 end of input`。
  - SQL 尾端新增只讀 validation marker：`select 'evidence_phase_4_market_theme_confirmed_evidence.sql complete' as sql_artifact_validation_marker;`
  - 新增 handoff 文件：`docs/handoff/evidence_phase_4_market_theme_confirmed_evidence.md`，說明用途、整段複製方式、不可 production 驗證 / backfill / 加 credentials。
  - 未改 table、欄位、constraint、index、schema intent。
- QA conditional pass：
  - 可吸收範圍限於 `CHANGELOG.md`、SQL artifact、handoff 文件；不得整包吸收 untracked `docs/`。
  - 靜態完整性通過：最後有效字元為 `;`，括號平衡，無 dollar quote 未閉合。
  - 危險詞掃描無 destructive DML、grant、secret、token、connection string。
  - QA 本身未做真正 Postgres parser validation，因無 `psql` / Docker / Podman；仍禁止連 production。
- Architect 額外驗證：
  - 使用臨時 `.qa_tmp/` 安裝 `pglast` 做本地非 production PostgreSQL parser 驗證。
  - 舊 SQL 與修正版 SQL 均可 parse；修正版 `pglast_parse_ok statements=27`。
  - 因此本次 `end of input` 高機率是 Supabase editor 只執行到不完整片段、貼上時漏掉尾段 / 分號，或 selection 沒包含完整 SQL block。
- Post-cycle review：
  - 根因分類：`qa_static_gap` + `operator_copy_risk`。前輪 QA 只有靜態掃描，未做 parser 驗證，也沒有足夠強調整段複製。
  - 已補 artifacts：SQL 尾端 marker、handoff 文件、Architect parser 驗證。
  - 待補流程：後續 SQL artifact 任務需優先嘗試 local parser；若 parser 不可用，需明確標記只做 static review，不得說成可在 Supabase 實際通過。

## Next Action

- commit / push tiny patch。
- Owner 重新打開 `db/sql/evidence_phase_4_market_theme_confirmed_evidence.sql`，整份全選複製到 Supabase SQL editor 執行，不要只選中間建表段。
- 若仍失敗，請回傳 Supabase 顯示的錯誤位置 / line / column；下一輪只修該 SQL syntax，不擴大到 loader / backfill。

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
