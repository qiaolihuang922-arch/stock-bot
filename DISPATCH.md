# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `evidence_phase2_source_mapping_wording_cleanup_20260529`
- task_name: `Evidence Phase 2 Source Mapping And Telegram Wording Cleanup`
- task_type: `normal_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `validated_pending_push`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 要求：針對最新 `v20.4.1` 報文，處理 market/theme evidence 仍顯示 absent/missing-source 與策略證據未啟用造成的手機噪音；若需要擴字段或建表，必須先通知 Owner。
- 本輪完成 `v20.4.2` Evidence Phase 2 wording / source-family gate，不改 DB schema、不新增 table / field、不 live write、不 live Telegram、不正式 backfill、不改 watchlist、不重設核心 BUY / SELL / RR 門檻。
- 已吸收候選 diff：
  - `core/generator.py` VERSION 升為 `v20.4.2`，缺 production source 時 summary 收斂為短句 `證據：production 來源不足，不作確認。`
  - `core/market_theme_evidence.py` 新增 / 收斂 source boundary 欄位與 source-family gate；confirmed / ready 只能由 `production_db` 或 `owner_approved_persistent` 來源成立。
  - `runtime_diagnostic`、runtime、local、cache、worktree、test fixture、report-derived source 可作 detail / limitations trace，但不得 confirmed / ready，不得污染頂層 source_family。
  - market/theme 現有資料不足以 confirmed：需要 production persistent market_index / sector_index / watchlist_breadth 類 source，且具備 freshness、required fields 與 evidence value。
  - `services/strategy_evidence.py` 本輪未改；用既有 read-only tests 驗證未受影響。
- QA 有效阻塞：
  - 首輪抓到 `runtime_diagnostic + watchlist_breadth + market_index` 可被誤判 confirmed / ready。
  - 二輪抓到 production source 已足夠時，report-derived theme text 會污染頂層 `source_family=runtime_diagnostic`。
  - Tech 修正後，QA 反證六種非持久 source family 全部不能 confirmed / ready，production + report-derived 混合時頂層 source_family 保持 `production_db`。
- QA 最終通過：
  - `100 passed, 13 warnings`
  - `git diff --check` 通過
  - forbidden diff 掃描無 schema / migration / SQL / backfill / watchlist / live Supabase write / live Telegram / 策略門檻變更。
- Post-cycle review：
  - 根因分類：`repeated_pattern` / evidence source boundary；不能只排除單一 `runtime_fallback`，必須以 source_family whitelist 控制 confirmed / ready。
  - QA 攔截有效：兩次抓到測試全綠以外的 source-family 污染路徑，避免 fake confirmed 進 Owner 手機 summary。
  - 不新增 `AGENTS.md` 硬規則：現有 source-of-truth / fail-closed / 手機閱讀規則已覆蓋，本輪沉澱為 fixture 與狀態契約。
  - Runner gap：auto cycle 對 QA `阻塞` parser 仍 false fail；Tech runner 第一次未用 `arch -arm64`，但 QA / 主 repo 驗證已用 arm64 命令通過。

## Next Action

- 完成 commit / push 後執行 tech worktree cleanup。
- 後續若 Owner 要 confirmed market/theme evidence，需另開任務定義 production table/view 欄位與 read-only loader；可能需要新增 / 確認 market_index、sector/theme key、watchlist_breadth、freshness、evidence value 等 source，必須先通知 Owner。

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
