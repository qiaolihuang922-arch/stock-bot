# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `db_strategy_consumption_phase1_cross_day_state_evidence_weight_20260529`
- task_name: `DB Strategy Consumption Phase 1 - Cross-day State And Evidence Weight`
- task_type: `risk_patch`
- version_level: `minor`
- qa_level: `L3-lite`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `see git log -1`

## Current Result

- Owner 要求：DB 多表已有資料後，先讓 DB 進入策略記憶與證據權重，不要讓多表只停在入庫 / report / audit。
- 本輪完成 Phase 1，不改 DB schema、不 live write、不 live Telegram、不正式 backfill、不改 watchlist、不重設核心 BUY / SELL / RR 門檻。
- 已吸收候選 diff：
  - 新增 `services/cross_day_context.py`，產生 cross-day context：前次狀態、前次行動、連續觀察、修復 / 失效、歷史證據權重、去重 guard、allowed / forbidden effects。
  - `core/generator.py` VERSION 升為 `v20.4.0`，在 render 前注入 cross-day context。
  - DB / local history 只允許影響排序、summary、準備層、歷史追溯、同級停利 / 減碼去重、今日買入 guard。
  - DB history 不得單獨把不可買變可買，不得覆蓋硬風控 / 停損 / REDUCE_50 / STOP_100。
  - 新增 `tests/test_cross_day_context.py`，同步 generator / market evidence / notifier 測試。
- QA 首輪有效阻塞：
  - 發現歷史減碼去重會覆蓋今日硬風控減碼，造成 summary 說硬風控、卡片說減碼後觀察。
  - Tech 補 `cross_day_higher_priority_risk_action()` 與 REDUCE_50 fixture 後，QA 補 STOP_100 反證通過。
- QA 最終通過：
  - `89 passed, 13 warnings`
  - `git diff --check` 通過
  - forbidden diff 掃描無 schema / migration / watchlist / live Telegram / live Supabase write / backfill / SQL diff。
- Post-cycle review：
  - 根因分類：`repeated_pattern` + `high_risk_invariant`；歷史記憶只能去重同級行動，不得壓過更高級風控。
  - QA 攔截有效：抓到測試全綠仍會造成 Owner 手機誤判的跨區塊語意衝突。
  - Owner 追加指出正式流程是 git / runner 啟動產生 TG 報文，本地臨時狀態不能當跨日記憶；已補 `AGENTS.md` 硬規則。
  - Runner gap：Tech runner 在 worktree 以 x86_64 載入 arm64 `pydantic_core`，需統一 `arch -arm64` 或重建 matching venv；auto cycle QA parser / conditional pass handling 仍需補。
  - 下一張產品任務需檢查 `services/cross_day_context.py` 的 local/runtime context 是否只作同 run guard，跨日判斷必須可由 DB fresh run 重建。

## Next Action

- 已 commit / push 本輪 `v20.4.0`；完成後執行 tech worktree cleanup。
- 下一步先開一張 risk_patch 檢查 `cross_day_context` source boundary：DB / persistent source 才能做跨日記憶，local/runtime 只能同 run guard。若通過，再進 Phase 2 真實 schema mapping、`signal_runs / signal_items / signal_outcomes` source precedence、production read-only 驗證；若要建表或 backfill 需先通知 Owner。

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
