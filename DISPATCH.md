# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `git-runner-may-backfill-entrypoint`
- task_name: `Git Runner May Backfill Entrypoint`
- task_type: `normal_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `verified_ready_to_commit`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 要先做「market/theme evidence 歷史趨勢消費」，讓舊資料不只是保存，而是被策略證據層使用。
- 已完成 `market_theme_confirmed_evidence` history trend 消費：
  - loader 仍先找 requested date / 上一交易日最新 confirmed row。
  - 額外讀取 `trade_date <= requested_trade_date` 的最近 evidence rows，產出 `evidence_trend`。
  - `evidence_trend` 包含 observed_days、recent_supporting_days、support_streak_days、days、allowed_effects、forbidden_effects。
  - 趨勢只允許 wording / 排序提示 / detail trace；不得放寬買點、不得覆蓋風控、不得單獨變 BUY。
  - Telegram evidence summary 在 confirmed 時新增短行：`趨勢：...`，讓 Owner 看出不是只看單日證據。
- 本輪新增 GitHub workflow backfill 入口：
  - `workflow_dispatch.run_mode`: `bot`、`backfill_may`、`backfill_and_bot`。
  - `start_date` / `end_date` / `backfill_version` 可由 workflow input 指定，預設 `2026-05-01` 到 `2026-05-29`、`v20.4.5`。
  - `backfill_may` 會從 GitHub runner 執行 `scripts/backfill_signals.py --source twse --allow-partial --write --confirm-write`，回寫 `daily_price`、`daily_signal_snapshot`。
  - `--allow-partial` 只寫 source 實際可取得的真實 rows，並輸出缺資料 warnings；不得為了通過 validation 補假 3035 或假 05/01 snapshot。
  - 舊 `market_daily_bars` / `strategy_feature_snapshots` / `strategy_outcome_metrics` / `strategy_classification_audit` production 表已不在目前 schema；backfill script 只計算衍生 rows 供 log 診斷，不寫入已刪除或語義不符的表。
  - `backfill_and_bot` 會先回填，再跑正式 bot。
  - 非 schema 寫入不需要 Owner 手動 SQL；正式結果以 GitHub runner 為準。
- 邊界：`scripts/backfill_market_theme_sources.py` 目前的 TWSE OpenAPI source 是 latest source，不是整月 historical source；它會補最新 official market/theme evidence。history trend 只消費 production 已有 confirmed rows，不會偽造五月 market/theme history。
- 同步使用者可見 Telegram header 版本：`v20.4.5`。
- 本輪沒有 production live write、formal backfill、DB schema / table / column 變更、RLS / grant / policy / role 變更、live Telegram、策略 decision、watchlist 或交易門檻變更。
- Architect 驗證：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py tests/test_market_theme_source_backfill.py tests/test_workflow_runtime_config.py tests/test_generator_report.py tests/test_notifier.py -q`：140 passed，157 warnings。
  - `arch -arm64 .venv/bin/python -m pytest tests/test_workflow_runtime_config.py tests/test_backfill_signals.py tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py tests/test_market_theme_source_backfill.py tests/test_generator_report.py tests/test_notifier.py -q`：144 passed，153 warnings。
  - `git diff --check`：通過。
- Post-cycle review：
  - 根因分類：`history_evidence_consumption_gap` + `git_runner_backfill_entrypoint_gap`。
  - 既有 GitHub runtime / source-of-truth 規則已覆蓋，不新增 `AGENTS.md` 硬規則。
  - 補測歷史趨勢、summary 趨勢文案、write CLI read-after-write smoke 兼容歷史查詢、workflow dispatch backfill inputs、版本 header 同步。

## Next Action

- Architect commit / push。
- 推送後用 GitHub workflow dispatch 跑 `run_mode=backfill_may`，日期 `2026-05-01` 到 `2026-05-29`。
- 回填完成後再跑一次 read-only / workflow result 檢查，才能繼續下一段證據鏈開發。
- 注意：報文底部 `📊 策略證據 v20.0｜資料表未建立` 屬於 `services/strategy_evidence.py` 的另一組 strategy evidence tables，不是本輪 `market_theme_confirmed_evidence` 假日讀取問題。

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
