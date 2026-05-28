# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `telegram-breakout-distance-always-visible-v20.2.1`
- task_name: `Telegram Breakout Distance Always Visible`
- task_type: `display_bugfix`
- version_level: `patch`
- qa_level: `L1`
- owner_status: `requested`
- architect_status: `pushed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pushed`

## Current Result

- Owner 要求小改動：不管距離突破點多少，只要有距離資料，Telegram / 報文卡片都要顯示突破距離。
- 本輪範圍限定為 tiny_patch / L1：
  - 只改持倉與未持倉卡片的盤面行顯示。
  - 不改策略 decision、突破門檻、買賣 / 加減碼、DB、watchlist、live Telegram、replay/backfill。
  - 使用者可見版本升為 `v20.2.1`。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，Architect 已檢查：
  - `# TASK:` 標題存在。
  - 已列手機閱讀路徑、直接消費者、輸出契約、版本契約與禁止事項。
- Tech 已交付 `CHANGELOG.md` 與候選 diff：
  - `core/generator.py` VERSION 升為 `v20.2.1`。
  - 卡片距離讀取支援 `data.breakout_distance` 缺失時 fallback 到 `result.breakout_distance`。
  - 持倉與未持倉卡片共用同一距離顯示規則。
  - 測試同步 formatter、notifier direct consumer、market evidence header。
- QA 最終驗證通過：
  - 有距離資料時，`已突破 / 臨界突破 / 接近突破 / 遠離突破` 都保留括號距離。
  - 缺資料時不輸出 `0%`、`None%`、空括號或假距離。
  - message list / notifier payload shape 未破壞。
  - 無策略、DB、watchlist、live Telegram、replay/backfill diff。
- 主 repo 驗證：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py`
  - 結果：`72 passed, 21 warnings`
  - `git diff --check` 通過。
- Post-cycle review：
  - 根因分類：正常 tiny_patch，外加一次 runner / worktree 交付摘要不一致被 QA 攔下。
  - QA 有效攔截：版本 / CHANGELOG 與實際 diff 不一致時 blocked，修正後通過。
  - 不新增硬規則；此屬 runner handoff 風險，已按既有 Post-cycle Review Gate 記錄到 `CLEANUP_PLAN.md`。
- Owner 追問本輪耗時過長後，Architect 已補 runner guard：
  - `run_tech_write.sh` 遇到 dirty tech worktree 時預設拒絕 reset。
  - 修交付摘要需顯式 `CLEAN_TECH_WORKTREE=0`，刻意丟棄候選 diff 需顯式 `ALLOW_DISCARD_TECH_WORKTREE=1`。
  - 目的：避免小修正因 worktree diff 被沖掉而重跑整輪。

## Next Action

- 等待 Owner 下一個需求；若是產品 / 顯示 / 策略 bug，仍先分派 PM。

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
