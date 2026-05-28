# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `market-theme-evidence-production-pm-20260528`
- task_name: `Market Theme Evidence Production PM Definition`
- task_type: `feature`
- version_level: `minor`
- qa_level: `L3`
- owner_status: `requested`
- architect_status: `qa_passed_absorbed`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pushed`

## Current Result

- Owner 要求開始證據鏈下一步。
- 當前只進入 PM 定義階段，不直接改產品代碼、不建表、不做 live Supabase write、不做正式 backfill、不做 live Telegram。
- PM 必須定義：
  - production confirmed 需要哪些 runtime sources。
  - source freshness、cache / schema 邊界、payload contract。
  - 什麼情況需要先通知 Owner 才能建表 / cache / external provider。
  - evidence 如何進 Telegram 報文，但不得改策略 decision 或放寬買點。
  - 驗收條件與 QA L3 範圍。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，Architect 已檢查：
  - `# TASK:` 標題存在。
  - 已列直接消費者、輸出契約、版本契約、approval gates、阻塞條件。
  - 明確禁止本輪建表、live write、正式 backfill、live Telegram。
- Tech runner 狀態：
  - 第一輪 Tech 在隔離 worktree 產生候選 diff，局部測試一度通過，但在重寫 `CHANGELOG.md` 時超時退出。
  - 第二輪收口仍未產生有效輸出，`CHANGELOG.md` 仍是舊任務內容。
  - Architect 拒收本輪 Tech 交付：不進 QA、不合併產品 diff、不推送產品變更。
  - 主 repo 只保留 PM 任務卡與阻塞紀錄；隔離 worktree 已清理。
- Owner 確認這是正常流程保護後，Architect 重新分派 Tech 從乾淨 worktree 實作。
- Tech 重跑已交付合格 `CHANGELOG.md` 與候選 diff；runner 已修正為由 Tech final answer 生成 `CHANGELOG.md`，避免再次卡在檔案編輯收口。
- QA 已阻塞候選 diff：
  - 一般五類 fixture 與 notifier / strategy invariance 測試通過。
  - QA 自訂反證發現：若 required source 同時有 `freshness=stale/unavailable` 與 `freshness_reason=same_trade_date`，候選仍可能輸出 `confirmed`。
  - 這違反 TASK「任一 required source stale / unavailable 時，不得輸出 confirmed」。
- Tech 已完成 QA block 修正：
  - `freshness=stale/unavailable/missing` 現在優先於 allowed `freshness_reason`。
  - 已補負面測試並重新跑相關 evidence / formatter / notifier / strategy invariance 測試。
- QA 重新驗證結果：
  - freshness precedence 阻塞點已解除。
  - 相關測試與 Telegram direct-consumer smoke 通過。
  - 但 `CHANGELOG.md` 只描述最後的 freshness fix，未覆蓋整個 worktree 的 v20.2.0 feature diff，因此不能整包吸收。
- Tech 已補完整 `CHANGELOG.md`，覆蓋 `core/market_theme_evidence.py`、`core/generator.py`、formatter/notifier tests、版本同步與 no-live-write 邊界。
- QA 最終一致性複核通過：
  - `CHANGELOG.md` 與 worktree diff 一致。
  - freshness precedence、v20.2.0 header、no DB/schema/cache/live/backfill、message list/notifier payload shape 均通過。
  - Architect 已只吸收 QA 明確列出的 6 個檔案，不整包合併 worktree。
- 主 repo 驗證：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py tests/test_analysis_engine.py tests/test_strategy_evidence.py`
  - 結果：`113 passed, 21 warnings`
  - `git diff --check` 通過。

## Next Action

- commit / push 後清理 tech worktree。

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
