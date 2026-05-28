# CURRENT_STATE.md

本文件由 Architect 維護，作為專案短上下文。新會話應先讀 `AGENTS.md`、`DISPATCH.md`，再按任務讀本文件與必要摘要。

## Project Snapshot

- 專案：台股策略報文機器人。
- 交付形態：排程 / 腳本產生 Telegram 報文並發送給 Owner。
- 股票清單唯一來源：`core/watchlist.py`，預設 12 檔。
- 最新使用者可見 Telegram 版本：`v20.2.1`。
- 最新 pushed commit 以 `git log -1` 為準。
- 固定 8 份 Markdown 不刪除，只改寫內容：`AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`。

## Current Process State

- Architect 是唯一總控入口；Owner 日常只對 Architect 下任務。
- 新對話或上下文壓縮後，Architect 第一個動作必須讀 `AGENTS.md` 與 `DISPATCH.md`，確認自己不是 PM / Tech / QA。
- 產品 bug / 顯示 bug / 策略 bug / feature request 預設先分派 PM，不直接定位代碼、不手寫 `TASK.md`、不改產品代碼。
- 純流程 / 規則 / 文件壓縮可由 Architect 直接改總控文件，但不得順手建立產品任務卡或修產品代碼。
- 每輪完成、阻塞、QA conditional / blocked、runner 失敗、commit / push 後都要跑 Post-cycle Review Gate。
- 規則治理原則：先分類根因，再決定是否升級為硬規則；一次性事故只進狀態或清理計畫，不直接塞進 `AGENTS.md`。

## CAO Availability

- CAO API：`http://127.0.0.1:9889/`
- CAO 中文前端：`http://127.0.0.1:5173/`
- 中文前端預設目錄：`$HOME/.local/share/cao-web-zh/web`，可用 `CAO_WEB_DIR` 覆蓋。
- 服務確認 / 啟動腳本：`tools/cao_agent/ensure_cao_services.sh`
- 本機部署文件：`tools/cao_agent/DEPLOYMENT.md`
- 本機 bootstrap：`tools/cao_agent/bootstrap_local.sh`
- CAO stock agent profile 模板：`tools/cao_agent/profiles/stock_*.md.template`
- Architect 只要分配、啟動或回覆 CAO 前端地址，必須先確認 `9889` API 與 `5173` 前端正在 listen；未啟動則先跑服務確認腳本。

## Recent High-Signal Milestones

- `v20.2.1` Telegram Breakout Distance Always Visible 已通過 QA：
  - 持倉與未持倉卡片只要有突破距離資料，`已突破 / 臨界突破 / 接近突破 / 遠離突破` 都顯示括號距離。
  - `data.breakout_distance` 缺失時 fallback 到 `result.breakout_distance`。
  - 缺距離資料時不輸出 `0%`、`None%`、空括號或假距離。
  - QA 驗證：`tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py`，`72 passed, 21 warnings`。
- `v20.2.0` Market Theme Evidence Production Contract 已推送：
  - confirmed 必須同時有 fresh supportive `watchlist_breadth` 與 `market_index` / `sector_index`。
  - `stale` / `unavailable` / `missing` freshness 優先於 allowed `freshness_reason`，不得 confirmed。
  - Telegram evidence 區塊顯示 confirmed / weak / mixed / stale / absent 與限制句。
  - 未新增 DB schema / cache / external provider / live write / backfill / live Telegram。
- `v20.1.3` Telegram Holding Risk Tomorrow Plan Dedupe 已推送：
  - 移除重複 `隔日計畫`。
  - 持倉未修復 / 降級檢查只留在 `持倉風控檢查`。
  - 無非重複明日事項時，不輸出 `明日計畫 0`、`無新增下單` 或空區塊。
  - QA 驗證：`tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`，`64 passed, 21 warnings`。
- Post-cycle Review Gate 已推送：
  - 每輪收口後必須總結根因、QA 攔截、是否回退既有契約、是否需要補 agent / runner / 流程。
  - 不得只說「下次注意」。
- `v20.1.2` Market Theme Evidence Structured Provider 已推送：
  - `build_market_theme_evidence_provider()` 接入 formatter path。
  - structured evidence 會重新驗證 source families / required fields / freshness。
  - 未新增 DB schema / cache / external provider / live write / backfill。
- `v20.1.1` Telegram Mobile Noise Reduction 已推送：
  - 收斂手機閱讀、盤後語意、待觸發加碼文案與淘汰卡產業句。
- `v20.1.0` Market Theme Evidence Dry-run 已推送：
  - 建立 `market_theme_evidence` dry-run helper 與測試。
  - report-derived only 只能 weak / track only，不可 confirmed。
- 早期 v20.0.x 舊細節已壓縮：完整流水不再保留在本文件，必要時查 git history。
## Stable Product Contracts

- Telegram 報文以手機閱讀為第一視角。
- 使用者可見報文變更需同步 `core/generator.py` 的 `VERSION` 或等價 header 常量，除非 PM 明確定義不升版理由。
- 持倉與未持倉卡片只要有突破距離資料，盤面行必須顯示括號距離；缺資料不得輸出假距離。
- 未持倉漏斗母集合固定為：`可買 / 可準備 / 僅追蹤 / 淘汰`；`僅追蹤` 再拆 `等冷卻 / 等回測 / 等RR修復 / 等量能`。
- 同一檔持倉同一份報文只能有一個主行動；持倉風控優先於高分、最強、待觸發加碼。
- 今日買入後預設是 `新倉風控觀察`；若要賣 / 減碼 / 停損，必須說明明確觸發條件。
- 今日已減碼 / 停利達同級建議時，預設轉為觀察；只有更高級風控或硬停損可覆蓋。
- 空區塊、0 計數、無行動占位都是手機噪音；未定義必要性時不顯示。
- 市場 / 題材 evidence 不得放寬個股買點；confirmed theme 也不能自動產生 BUY。

## Module Map

- 策略判斷：`services/analysis.py`
- 報文與 Telegram formatter：`core/generator.py`
- 市場 / 題材證據 dry-run 與 provider：`core/market_theme_evidence.py`
- 條件映射：`core/condition_engine.py`
- 行情來源：`services/stock_api.py`
- 股票清單：`core/watchlist.py`
- 持倉讀取：`services/position_store.py`
- 原始信號寫入：`services/signal_store.py`
- 每日 snapshot 寫入：`services/daily_snapshot_store.py`
- snapshot 組裝 / 驗證：`core/signal_snapshot.py`、`core/signal_validator.py`
- 策略證據資料層：`services/strategy_evidence.py`
- replay / backfill：`scripts/dry_run_replay.py`、`scripts/backfill_signals.py`
- Telegram 持倉命令：`supabase/functions/telegram-execution/index.ts`

## Known Boundaries

- 未完成 production schema apply。
- 未做 live Supabase write。
- 未做 live Telegram delivery。
- 未做 TWSE live replay / live backfill。
- 未做正式 backfill write。
- 未接真實外部新聞 / 題材 ingestion。
- 未驗證 Supabase RLS / 權限 / index / rollback。
- 若下一步需要建表、cache、正式外部 provider、live write 或 backfill，必須先通知 Owner。

## Workflow Health

- CAO 入口收斂為：
  - `tools/cao_agent/run_architect_task.sh research "<研究問題>"`
  - `tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"`
  - `tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"`
- Tech write 只在隔離 worktree 產生候選 diff；預設位置為 repo 同級 `stock-bot-agent-worktrees/tech_write`。
- Tech runner 不得默默丟棄 dirty worktree candidate diff；`run_tech_write.sh` 預設會拒絕 reset，除非顯式 `ALLOW_DISCARD_TECH_WORKTREE=1`。只修 handoff 摘要時用 `CLEAN_TECH_WORKTREE=0`。
- QA code runner read-only，只允許 `.qa_tmp/` 測試暫存，hash gate 防止改 tracked files。
- CAO runner prompt 已補效率 guard：
  - PM 先判斷任務尺寸與停止條件，避免小 bug 膨脹。
  - Tech 先定義最小改動策略，避免順手重構、過擬合測試或回退既有契約。
  - QA 先定義 1-3 個風險預算與停止條件，避免 tiny patch 被驗成大任務。
  - Tech plan 先輸出任務尺寸、最小影響面與不應觸碰模組。
  - 實際腳本已納入 repo：`tools/cao_agent/run_auto_dev_cycle.sh`、`run_tech_write.sh`、`run_qa_code.sh`、`run_tech_plan.sh`。
- CAO 本機可重建資產已納入 repo：
  - runner 腳本、sandbox wrapper、profile 模板、profile 安裝腳本、bootstrap 腳本與部署文件。
  - 可下載依賴記錄在 `tools/cao_agent/DEPLOYMENT.md`；手寫 agent role cards 以模板保存在 `tools/cao_agent/profiles/`。
  - 中文 CAO UI 目前仍是外部 checkout，不直接放入主 repo；若要長期固定中文化，需另開任務抽 patch 或 fork。
- commit / push 後需執行 `tools/cao_agent/cleanup_agent_worktrees.sh`，讓隔離 worktree 對齊主 repo。
- 清理任務若涉及產品代碼、測試或 runtime 文件，必須有 PM 任務、Tech 證據表與 QA 反證；流程文件壓縮可由 Architect 直接處理。

## Open Follow-Ups

- 證據鏈 v20.2.0 只建立 production contract 與 runtime source gate；若要自動取得 market_index / sector_index、建表、cache、external provider 或持久化 evidence，先通知 Owner。
- 若 Owner 仍覺得查詢慢，另開 performance measurement 任務，量測 production 實際秒數。
- 後續可改善 `load_strategy_evidence_summary()` 顯式排序與 `漏失` 文案，但需另開任務。
