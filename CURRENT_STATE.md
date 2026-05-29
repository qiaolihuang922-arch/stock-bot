# CURRENT_STATE.md

本文件由 Architect 維護，作為專案短上下文。新會話應先讀 `AGENTS.md`、`DISPATCH.md`，再按任務讀本文件與必要摘要。

## Project Snapshot

- 專案：台股策略報文機器人。
- 交付形態：排程 / 腳本產生 Telegram 報文並發送給 Owner。
- 股票清單唯一來源：`core/watchlist.py`，預設 12 檔。
- 最新使用者可見 Telegram 版本：`v20.4.0`。
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

- `v20.4.0` DB Strategy Consumption Phase 1 已通過 QA：
  - 新增 `services/cross_day_context.py`，讓既有 DB / local runtime history 進入策略記憶與證據權重。
  - Phase 1 context 包含前次狀態、前次行動、連續觀察天數、修復 / 失效、歷史證據權重、去重 guard、allowed / forbidden effects。
  - `core/generator.py` 在 render 前注入 cross-day context；允許影響排序、summary、準備層、歷史追溯、同級停利 / 減碼去重、今日買入 guard。
  - DB history 不得單獨把不可買變可買，不得進交易執行清單，不得放寬 BUY / SELL / RR / 過熱 / 漲停不追 / 停損停利核心門檻。
  - 歷史停利 / 減碼只可去重同級行動；不得覆蓋硬風控、停損、`REDUCE_50`、`STOP_100` 或風控升級。
  - QA 首輪攔下「歷史減碼覆蓋今日硬風控」跨區塊矛盾；修正後 REDUCE_50 fixture 與 QA STOP_100 probe 均通過。
  - QA / Architect 驗證：`tests/test_cross_day_context.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`，`89 passed, 13 warnings`；`git diff --check` 通過。
- `v20.3.1` Data Authenticity Fail-closed 已通過 QA：
  - DB / 真實來源不可用時，production runtime 不得用 fake/default/synthetic/fallback 補成可買、confirmed、持倉、今日交易、價格或 Telegram 結論。
  - `services/position_store.py` 移除全 watchlist 0 股 fallback；缺 Supabase、positions DB error、positions 0 rows 都回 `{}` 並設 `missing-source / source-error / unavailable` warning。
  - `position_events` DB source-error / missing-source 不再回全 0 event summary；只有 DB query 成功且空資料才代表今日真實無事件。
  - `core/generator.py` 在持倉或今日交易事件 source warning 存在時直接 fail closed，不掃行情、不產生交易建議。
  - `core/market_theme_evidence.py` 將 runtime watchlist breadth fallback 降為非交易診斷，不進 sources、不 confirmed、不再輸出 `weak/runtime`。
  - QA / Architect 驗證：`tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_position_store.py tests/test_notifier.py`，`88 passed, 13 warnings`；full pytest `162 passed, 13 warnings`；`git diff --check` 通過。
- `v20.3.0` Runtime Market Breadth Evidence Fallback 已通過 QA：
  - 注意：此版本的 runtime weak fallback 已被 `v20.3.1` 收斂為非交易診斷；以下只保留歷史背景。
  - 在沒有 DB evidence table/cache 時，可用當次 `results_map` 生成 runtime watchlist breadth fallback evidence。
  - runtime fallback 最高只顯示 `weak/runtime` 或 `absent/missing-source`，缺 `market_index` / `sector_index` 時不得 confirmed。
  - Telegram evidence 文案顯示內部觀察池廣度偏強 / 題材偏支持，但明確標示缺大盤 / 族群指數 evidence，未確認。
  - runtime data 不足時列出缺來源，不再只輸出模糊 absent。
  - 未建表、未新增 migration、未寫 Supabase、未 live Telegram、未 backfill、未改 BUY / SELL / RR / 過熱 / 漲停不追 / 可準備分類。
  - QA 驗證：`tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py tests/test_signal_validator.py tests/test_analysis_engine.py`，`120 passed, 21 warnings`。
- `v20.2.5` Telegram Post-market Noise And Index Wording 已通過 QA：
  - 盤後 summary 將 `今日交易紀錄 / 無新增` 改為 `今日交易 / 新增交易建議：無`，避免與 `已執行（不重複下單）` 並列時被誤讀為今日沒有交易。
  - `僅追蹤 0` 時不再輸出 `等冷卻 0、等回測 0、等RR修復 0、等量能 0` 的零計數拆分。
  - 未持倉詳情索引把 `可準備` 與 `僅追蹤` 分開列，不再用 `未持倉追蹤 8` 混稱可準備 8。
  - QA 驗證：`tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py`，`79 passed, 21 warnings`；策略 smoke `39 passed`。
- `v20.2.4` R3 Hot Market Evidence Wording And Prepare Layer 已通過 QA：
  - `evidence absent` 改為描述內部結構化市場 / 題材證據未啟用或不足，不再像是否定外部市場強勢。
  - R3 進攻偏熱時，未持倉強勢但不可追標的新增 `強勢準備` / `可準備` 層：漲停鎖價、過熱降溫、突破回測都明確標示不可買 / 不追高 / 待觸發。
  - 可買門檻未放寬，準備層不進交易執行清單。
  - QA 首輪攔下 summary overflow 混桶；修正後 hidden items 同狀態才寫 `同狀態`，跨狀態改顯示分類數量，例如 `過熱降溫 1、突破回測 2`。
  - QA 驗證：`tests/test_generator_report.py -k v20_2_4_r3_hot`，`tests/test_generator_report.py -k v20_2_4 tests/test_market_theme_evidence.py tests/test_notifier.py`，策略 smoke `tests/test_signal_validator.py tests/test_analysis_engine.py`。
- `v20.2.3` Second Take-profit Execution Dedupe 已通過 QA：
  - 報文優先使用既有 DB execution / local execution，再 fallback 到 `position_events` 判斷今日已賣。
  - 第二段停利 completed：顯示 `第二段停利後觀察`、今日已賣、剩餘股數、第二段已執行，不再顯示完整可執行建議。
  - 第二段停利 partial：只顯示剩餘建議股數，不回吐完整原建議。
  - 第二段停利 unexecuted：仍保留 `第二段停利 / 本次建議 / 剩餘`，避免合法第二段被藏掉。
  - 持倉卡 `今日 ...` 欄與 summary / 風控檢查共用 execution state，不再出現 `今日 無` 與 `今日已賣 N 股` 同卡矛盾。
  - QA 驗證：`tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py`，`76 passed, 21 warnings`；策略 smoke `8 passed`。
- `v20.2.2` Post-profit State Consistency 已通過 QA：
  - 同日已執行同級停利後，報文主行動轉為 `停利後觀察`，不再讓 Owner 誤讀為再次同級停利。
  - 若同日已賣後仍有更高級 / 第二段停利建議，報文顯示 `第二段停利`，並同行列出今日已賣、剩餘股數、本次建議股數。
  - QA 驗證：`tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py tests/test_analysis_engine.py`，`108 passed, 21 warnings`。
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
- `僅追蹤 0` 時不得輸出零計數拆分；summary / index 也不得把 `可準備` 全部混稱為 `未持倉追蹤`。
- R3 強勢偏熱時，`可準備` 是不可買的準備層；必須清楚標示不可追高、不可買或待觸發，不得進交易執行清單。
- 強勢準備 summary 超過 3 檔時，不得把不同狀態混成 `另 N 檔同狀態`；跨狀態需顯示分類數量或等價不誤導文案。
- 同一檔持倉同一份報文只能有一個主行動；持倉風控優先於高分、最強、待觸發加碼。
- 今日買入後預設是 `新倉風控觀察`；若要賣 / 減碼 / 停損，必須說明明確觸發條件。
- 今日已減碼 / 停利達同級建議時，預設轉為觀察；只有更高級風控或硬停損可覆蓋。
- DB / cross-day history 只能壓制同級重複行動；不得覆蓋硬風控、停損、`REDUCE_50`、`STOP_100` 或風控升級。
- DB / cross-day history 可提升排序、追蹤優先級或可準備呈現，但不得單獨把不可買改成可買或放入交易執行清單。
- 同日第二段 / 額外停利必須尊重 execution 資料：completed 轉觀察、partial 只顯示剩餘、unexecuted 才顯示完整第二段建議。
- 持倉卡、summary、風控檢查的今日已賣、剩餘、建議股數必須使用一致來源；不得同卡出現 `今日 無` 與 `今日已賣 N 股`。
- 空區塊、0 計數、無行動占位都是手機噪音；未定義必要性時不顯示。
- 市場 / 題材 evidence 不得放寬個股買點；confirmed theme 也不能自動產生 BUY。
- `evidence absent` 只代表內部結構化證據未啟用 / 不足 / missing，不代表外部市場不強。
- Runtime watchlist breadth fallback 只能作為非交易診斷或 missing-source 說明；不得稱市場證據、不得輸出 weak/runtime、不得 confirmed、不得改交易決策。
- positions / position_events 來源錯誤不可補假值：positions 不可回全 watchlist 0 股，position_events source-error 不可回全 0 event summary 或讓報文誤讀為今日無交易。

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
- 跨日策略記憶 / 歷史證據權重：`services/cross_day_context.py`
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

- 2026-05-29 報文研究結論：
  - 英業達今日已停利後主決策仍顯示 `停利` 的高風險誤讀已由 `v20.2.2` 修正。
  - 英業達第二段已執行後仍重複建議第二段停利的高風險誤讀已由 `v20.2.3` 修正。
  - 本週台股 / AI / 電子偏強有公開資料支持，但零 BUY 不必然是錯；`v20.2.4` 已補「強勢市場但不可追」的準備層 / 手機文案，未放寬買點。
- 證據鏈 v20.3.1 已將 runtime breadth fallback 收斂為非交易診斷；若要自動取得 market_index / sector_index、建表、cache、external provider 或持久化 evidence，先通知 Owner。
- 若 Owner 仍覺得查詢慢，另開 performance measurement 任務，量測 production 實際秒數。
- 後續可改善 `load_strategy_evidence_summary()` 顯式排序與 `漏失` 文案，但需另開任務。
