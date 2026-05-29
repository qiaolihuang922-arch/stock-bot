# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `cross_day_context_source_boundary_hardening_20260529`
- task_name: `Cross-day Context Source Boundary Hardening`
- task_type: `risk_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `validated_pending_push`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 要求：正式 TG 報文由 git / runner 啟動，runner 無狀態；`cross_day_context` 不能把本地 / runtime / 同 run 資料當成跨日記憶。若需要擴字段或建表，必須先通知 Owner。
- 本輪完成 source boundary hardening，不改 DB schema、不新增 table / field、不 live write、不 live Telegram、不正式 backfill、不改 watchlist、不重設核心 BUY / SELL / RR 門檻。
- 已吸收候選 diff：
  - `services/cross_day_context.py` 不再把 `today_position_events` / local runtime 資料提升為 `previous_action`、`previous_action_date`、`dedupe_guard` 或 `source_of_truth`。
  - 同 run 資訊只保留在 `same_run_guard`、`same_run_action`、`same_run_action_date`、`same_run_source`，不得作跨日記憶。
  - `core/generator.py` VERSION 升為 `v20.4.1`，`cross_day_ready()` 只有在 `source_status=ready` 且 `source_of_truth` 全部來自 persistent whitelist 時才生效。
  - 若 `source_of_truth` 混入 `local_position_events` 或其他非持久來源，即使同時有 `position_events`，sorting / summary / detail / prepare / dedupe 全部 fail closed。
  - 新增 DB event、DB missing、source-error、local-only、mixed-source negative 測試，並同步 v20.4.1 header 測試。
- QA 首輪有效阻塞：
  - 發現 Tech 初版用 `any()` 判斷 source whitelist，導致 `["position_events", "local_position_events"]` mixed source 仍可輸出假歷史、連續觀察與權重。
  - Tech 改成所有來源都必須屬於 persistent whitelist 後，QA 額外反證 pure DB 生效、mixed local / missing source fail closed。
- QA 最終通過：
  - `92 passed, 13 warnings`
  - `git diff --check` 通過
  - forbidden diff 掃描無 schema / migration / SQL / backfill / watchlist / live Supabase write / live Telegram 變更；只命中既有測試字串假陽性。
- Post-cycle review：
  - 根因分類：`repeated_pattern` / source boundary；本地同 run guard 與跨日持久記憶在初版實作中仍有混桶風險。
  - QA 攔截有效：不是只重跑測試，而是補 mixed-source 手機誤讀反證，避免 fake history 進 summary / detail。
  - 不新增 `AGENTS.md` 硬規則：現有 `GitHub Runtime / State Source` 硬規則已覆蓋，本輪沉澱為 fixture、狀態契約與 cleanup 待辦，避免文件膨脹。
  - Runner gap 仍存在：auto cycle 初段 Tech runner failed，需後續改善 auto handoff / dirty candidate 續跑；本輪已用 `CLEAN_TECH_WORKTREE=0` 安全返工。

## Next Action

- 完成 commit / push 後執行 tech worktree cleanup。
- 後續 Phase 2 再做真實 schema mapping、`signal_runs / signal_items / signal_outcomes` source precedence、production read-only 驗證；若需要新增 table / field、cache、backfill 或 live write，必須先通知 Owner。

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
