# CURRENT_STATE.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保存短上下文與穩定狀態，不重寫啟動清單。

## Stable Context

- 專案：台股策略 Telegram 報文機器人。
- 正式結果以 git / runner 產生報文為準。
- 使用者可見報文版本在 `core/generator.py` 的 `VERSION`，目前已落地為 `v20.4.35`。
- 固定 8 份 Markdown 不刪：`AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`。
- Architect 是總控；產品 / 策略 / 報文 bug 或 feature 預設走 PM -> Tech -> QA。
- 跨日狀態、已執行交易、歷史 evidence 必須來自 production DB 或 Owner 指定持久來源；local/runtime/worktree 不能當跨日記憶。
- 缺資料、source-error、欄位不足或可信度不足時 fail closed。

## Latest Completed Work

- task_id：`risk_patch_20260531_holiday_report_execution_memory_evidence_dates`
- commits：
  - `6367d78 fix holiday execution memory report`
  - `4f19e16 docs mark holiday fix pushed`
- 結論：05/31 假日报文重複第二段停利已修並推送。
- 關鍵行為：
  - production cross-day execution memory 足夠時，英業達 2356 顯示已執行不重複。
  - prior take-profit guard 存在但 execution memory 缺失或 `sold_shares <= 0` 時，顯示 `停利記憶不足`，不輸出賣出股數，不進明日計畫。
  - market/theme evidence 顯示 actual/latest trade date 與 `lookback_range`。
  - strategy sample 0 與 market/theme production evidence 已分層。
- 驗證：QA `通過`；full pytest 264 passed，153 warnings（第三方 deprecation 類）。

## Latest Completed Handoff

- task_id：`research_daily_price_backfill_and_trend_sample_expansion_20260603`
- 狀態：direct production backfill done；QA conditional pass；commit / push / git completion gate 待收口。
- commit：`pending_commit`（上一輪 tooling commit：`5045045 Add daily price backfill research tooling`）。
- 問題：Owner 要直接回填 watchlist 12 檔 daily_price 1-2 年資料，讓 trend continuation 研究不要停在樣本 5；同時研究 artifact 必須固定 12 檔 universe、列每檔命中次數與 total >=30 判斷。
- 修正 / 交付：
  - 新增 `scripts/backfill_daily_price_history.py`。
  - backfill CLI 支援 `--dry-run`、`--write`、`--confirm-write`、`--symbols`、`--start`、`--end`、`--years`、`--skip-existing`、`--read-after-write`、`--no-config`。
  - 未指定 symbols 時使用 `core.watchlist.WATCHLIST_CODES`，目前 12 檔：3231、2421、3035、2303、3481、2344、2376、2408、2356、2324、2301、2337。
  - 寫入只走既有 approved interface：`scripts.backfill_signals.upsert_rows(price_rows, signal_rows=[], client=...)`；為此 `upsert_rows()` 新增向後相容 optional `client=None`。
  - 擴充 `scripts/research_trend_continuation.py` artifact：`universe_symbols / universe_count / date_range / pattern_definition / per_symbol / aggregate`。
  - 新增 `tests/test_backfill_daily_price_history.py`，更新 `tests/test_research_trend_continuation.py`。
- 最新 artifact：
  - `reports/research/trend_continuation_20260603.txt`
  - `reports/research/trend_continuation_20260603.json`
  - production write：12 檔逐檔 approved write / read-after-write，合計新增 `daily_price` 5,218 rows。
  - read-after-write row count：3231=485、2421=485、3035=485、2303=485、3481=478、2344=485、2376=485、2408=470、2356=485、2324=485、2301=464、2337=442；日期範圍皆為 2024-06-03..2026-06-03。
  - universe_count=12；total_hit_count=232；meets_min_sample_count=true。
  - per-symbol hits：2301=16、2303=22、2324=31、2337=23、2344=20、2356=19、2376=16、2408=8、2421=15、3035=16、3231=31、3481=15。
  - pullback continuation：1 日勝率 46.98%、平均 +0.45%；3 日勝率 55.17%、平均 +1.74%；5 日勝率 55.17%、平均 +2.26%；10 日勝率 54.74%、平均 +2.77%；結論 `positive`。
- 驗證：
  - `tests/test_backfill_daily_price_history.py tests/test_research_trend_continuation.py tests/test_backfill_signals.py` 15 passed。
  - `py_compile` passed；`git diff --check` passed。
  - 單檔 dry-run `3231` 回傳 `result=no-write`、`live_write=false`、planned_rows=2。
  - write 缺憑證 probe exit 2 blocked，`live_write=false`。
  - 12 檔逐檔 write-complete，read-after-write `status=ok`。
- QA 狀態：`conditional pass`。原因：approved write path、12 檔 production write、read-after-write、research artifact schema 已驗；但本輪仍未改正式策略，也未取得階段二 Owner 授權。
- 邊界：未改正式策略、Telegram、DB schema、live delivery。階段一研究門檻已達成，可另開階段二 major 策略設計任務；不得把本輪 positive edge 直接視為已開正式買路或追高授權。

## Previous Completed Handoff

- task_id：`research_trend_continuation_phase1`
- 狀態：research done / committed；QA conditional pass；push 與 git completion gate 待收口。
- commit：`3f67e3e Add trend continuation research script`。
- 問題：Owner 要解決「漲兩週的趨勢股永遠不讓買」，但明確要求先做階段一研究，驗證「上升趨勢中縮量回踩 ma5 / ma10 不破後放量站回」是否有正 edge，再決定是否能開 `trend_continuation` 買入路徑。
- 研究交付：
  - 新增只讀腳本 `scripts/research_trend_continuation.py`。
  - 新增 focused tests `tests/test_research_trend_continuation.py`。
  - 產出 artifacts：`reports/research/trend_continuation_20260603.txt`、`reports/research/trend_continuation_20260603.json`。
  - 更新 `RESEARCH.md` 高信號結論。
- 實跑結果：
  - source：production DB read-only `daily_price`，`source_rows=516`。
  - `pullback_continuation`：樣本 5；1 日勝率 40.00%、平均 -1.74%；3 日勝率 0.00%、平均 -7.65%；5 日勝率 20.00%、平均 -3.89%；10 日勝率 80.00%、平均 +9.82%；MFE +16.53%、MAE -9.89%。
  - `extended_spike >=1.08 / 1.15 / 1.22`：樣本 78 / 46 / 30；5 日勝率 65.38% / 65.22% / 63.33%；5 日平均 +6.23% / +7.45% / +6.17%。這只是對照，不授權追高。
- 結論：`pullback_continuation_edge=insufficient-data`。目前定義樣本數低於 min_sample 30，且 5 日勝率與平均收益不符合 Owner 門檻；不得進入階段二實裝，不得放開 `RESEARCH.md` 的「證據不得單獨變 BUY / 不得放寬追高」硬邊界。
- 驗證：
  - `tests/test_research_trend_continuation.py` 4 passed。
  - `py_compile` passed；`git diff --check` passed。
  - mutation scan 無 DB write / schema mutation / live Telegram matches。
- QA 狀態：`conditional pass`。原因：腳本與 production `daily_price` output 已驗，但本輪未消費 `signal_outcomes` / `daily_signal_snapshot` 作三表完整研究。
- 邊界：未改 `services/analysis.py`、`core/condition_engine.py`、`core/generator.py`、DB schema/write、live Telegram。

## Previous Completed Handoff

- task_id：`v20.4.35-report-semantics`
- 狀態：code done / committed；QA conditional pass；push 與 git completion gate 待收口。
- commit：`32098c1 Fix v20.4.35 report semantics`。
- 問題：Owner 指出上一輪 v20.4.35 還有四個手機閱讀錯誤：漲停鎖價 / 不可追高標的仍可能取得 evidence boost；低量降級產生 `突破確認｜待確認` 衝突；非加碼持倉數據行把 V 一起拿掉；簡報 `交易執行 N` 與今日新建倉數容易誤讀。
- 修正：
  - `apply_evidence_confidence()` 的 boost blocker 擴到 `trade_state=AVOID`、`price_behavior=LIMIT_LOCK/LIMIT_REBOUND`、以及 `should_show_overheat_rr_blocker(...)`。
  - formatter heat unavailable 文案同步上述 blocker，RR 過熱 / 漲停鎖價 / 不可追高不再顯示 `證據 +`，改 `證據：過熱不適用`。
  - 低量收縮降級使用 `縮量觀察`，避免 `突破確認｜待確認` 同時出現。
  - 非加碼持倉資料行改為 `數據：不適用（既有持倉）｜V {vol}x`，仍不顯示 RR / 綜合 / 技術 / 證據。
  - Summary 首行改 `執行動作 N` 與 `今日新建倉 M` 分開，必要時標注動作類型。
- 驗證：
  - `tests/test_generator_report.py` 157 passed，241 warnings。
  - `py_compile` passed；`git diff --check` passed。
  - official message-list replay 覆蓋不可追高 / 漲停鎖價 evidence blocker、非加碼持倉保留 V、低量文案、簡報計數。
- QA 狀態：`conditional pass`。原因：message-list replay 與 regression tests 覆蓋核心可見錯誤，但未取得正式 runner artifact。
- 邊界：未改 RR 公式、DB schema/write、策略 decision、持倉狀態機、live Telegram。

## Previous Completed Handoff

- task_id：`report-score-evidence-display-20260603`
- 狀態：code done / committed / pushed；QA conditional pass；git completion gate passed。
- commit：`58969a8 Fix report score evidence display`。
- 問題：Owner 指出既有持倉非加碼仍顯示新倉品質分，且 `綜合` 可超過 100；證據不可用全部寫成資料不足；過熱 / 低量 / 低分文案容易誤讀。
- 修正：
  - `core/generator.py` 升 `v20.4.35`，`final_confidence` 封頂 100。
  - heat / extended、FAIL / 弱結構、technical<=0 的 blocked 情境一律 evidence unavailable。
  - 持倉非加碼卡片數據行改 `數據：不適用（既有持倉）`，不顯示 RR / 綜合 / 技術 / 證據 / V；加碼持倉與新倉候選仍顯示分數。
  - evidence unavailable 顯示分流：`過熱不適用`、`風控不適用`、`資料不足`。
  - 盤後低量收縮整理不顯示 `極強`，改 `待確認｜縮量`。
  - technical <10 或 rounded final=technical 時顯示 `微幅`，不顯示 `+X%`。
- 驗證：
  - `tests/test_generator_report.py tests/test_market_theme_evidence.py` 195 passed。
  - `py_compile` passed；`git diff --check` passed。
  - official `formatTelegramMessages` replay 覆蓋非加碼持倉、加碼、新倉封頂、過熱、風控、資料不足、低量、低分。
- QA 狀態：`conditional pass`。原因：message-list replay 與 tests 覆蓋核心可見錯誤，但未取得正式 runner artifact。
- 流程事件：第一次 QA blocked 抓到 `CHANGELOG.md` 錯輪；Architect 重寫本輪 handoff 後於主 repo 重跑測試。
- 邊界：未改 DB schema/write、RR、策略 decision、Render freshness、live Telegram。

## Previous Completed Handoff

- task_id：`render_market_theme_evidence_freshness_20260603`
- 狀態：code done / committed / pushed；QA conditional pass；git completion gate passed。
- commit：`5b9523f Add Render market evidence freshness preflight`。
- 問題：Owner 說實際流程是 Render 每 5 分鐘啟動，不是手動 GitHub Action；寫過的日期不能重寫，缺的日期要自動補，避免 6/1、6/2、6/3 類漏寫後永遠停在 5/29。
- 修正：
  - `app.py` Render route 在 dispatch workflow / already-sent tag 前先跑 market/theme freshness preflight；失敗時不 dispatch、不寫 tag，讓下一次 5 分鐘觸發可重試。
  - `run_phase3_evidence_automation.py --freshness-check-only` 預設檢查最近 5 個 confirmed trading days，safe write time 預設台北 14:00。
  - 已完整日期輸出 `already-complete` 並跳過；未到時間輸出 `skipped-before-safe-write-time`；缺失且過時間走既有 backfill/upsert 並 read-after-write。
  - `market_theme_confirmed_evidence` 完整性要求 9 個官方 TWSE 題材 key，避免只寫一條也被當完整。
  - backfill workflow / CLI 吃 `start_date/end_date + --historical-range`，不再 May-only。
- 驗證：
  - `tests/test_app_render_preflight.py tests/test_phase3_evidence_automation.py tests/test_market_theme_source_backfill.py tests/test_workflow_runtime_config.py` 45 passed。
  - `py_compile` passed；`git diff --check` passed。
  - Architect 已用既有 approved script 回寫 `2026-06-01~2026-06-03`：`market_theme_confirmed_evidence` 27 rows、`market_theme_index_daily_bars` 30 rows，read-after-write passed。
- QA 狀態：`conditional pass`。原因：程式與 runner route 已反證，但尚未取得 Render production 5 分鐘觸發 log；部署後需確認 freshness preflight 真實輸出。
- 邊界：未改 DB schema、RR、策略決策、Telegram 報文格式、live delivery；未手寫 production DML。

## Previous Completed Handoff

- task_id：`20260603_evidence_score_effective_market_freshness_v20_4_34`
- 狀態：code done / committed / pushed；QA conditional pass；git completion gate passed。
- commit：`135bae7 Make evidence scoring use per-stock backtests`。
- 問題：Owner 要讓 evidence 從「顯示但 0 作用」變成真正改變 `綜合` 分，並讓 market confirmed_evidence 每日保鮮。
- 修正：
  - per-stock strategy evidence 改用各股 `backtest_context`；有 sample 但無 source_status 時不再被 global strategy manifest 拉成 unavailable。
  - `reference / reference_level` 支援 `高 / high / reliable / strong` 作為 sample >= 10 的 ready 判斷。
  - avg_return 轉 numeric 後判斷，避免字串欄位比較風險。
  - daily_evidence cron 改為 `0 6 * * 1-5`，對應台北 14:00 收盤後。
  - Phase3 runner 新增 `--require-market-theme-payload`；缺 `MARKET_THEME_APPROVED_PAYLOAD` 時 fail closed / exit 2；payload trade_date mismatch 會在 write CLI 前失敗。
- 驗證：
  - 主 repo `tests/test_generator_report.py tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py` 179 passed，241 warnings。
  - `py_compile` passed；`git diff --check` passed。
  - per-stock replay：global row_count=3 時，緯創 sample 36、華邦 sample 38 仍 ready，兩股 modifier 不同，`final != technical`。
  - weak / failed guard：FAILED_BREAKOUT fixture modifier <= 1.0。
- QA 狀態：`conditional pass`。原因：程式與 runner fail-closed path 可吸收，但未讀 production DB、未跑正式 daily_evidence artifact，不能證明 2026-06-03 production confirmed row 已存在。
- 邊界：未改 RR 公式、DB schema/write path、live Telegram、production backfill；未執行 production write。若要把本輪升為 `通過`，需 Owner 配置 `MARKET_THEME_APPROVED_PAYLOAD` 並提供正式 runner artifact，或另開 read-only artifact 任務。

## Previous Completed Handoff

- task_id：`20260603_evidence_sample_gating_v20_4_34`
- 狀態：done / committed；push 與 git completion gate 待收口。
- commit：`b38ae26 Fix evidence sample gating`。
- 問題：Owner 指出 06/03 報文仍顯示 `證據：partial / 不適用（資料不足）`、`綜合=技術`，並已指出三個源頭：market/theme 不該再疊 15 日門檻；strategy_sample 要吃到真實 classification sample count；version filter 若仍在要移除。
- 修正：
  - `core/generator.py` 升 `v20.4.34`。
  - strategy sample count 統一讀 `row_count / sample_rows / evidence_count / sample / sample_count / classification_sample_count`，供 `_strategy_sample_status()`、`_strategy_sample_row_count()`、per-stock strategy payload 共用。
  - `services/strategy_evidence.py` 本輪未改；已核對 loader 目前按近 60 交易日跨版本讀取，沒有 `.eq("version", version)`。
  - official message-list replay 覆蓋 market confirmed + strategy sample 36 的建準等價卡片，顯示非 0 evidence boost 且 `綜合 != 技術`；過熱卡仍維持等冷卻 hard block，但不誤顯 partial。
- 驗證：
  - 主 repo targeted evidence tests 6 passed，13 warnings。
  - 主 repo `tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py` 206 passed，241 warnings。
  - `py_compile` passed；`git diff --check` passed。
- QA 狀態：自動 QA agent runner 遇 Codex usage limit 互動提示，未產生可吸收 agent QA_REPORT；Architect 本地補同層 replay / loader / suite 反證，`QA_REPORT.md` 標 `conditional pass`，不冒稱 agent QA 通過。
- 邊界：未改 RR 公式、DB schema/write path、production backfill、live Telegram；未讀 production source。若 production 真實報文仍不足，下一步應做 read-only artifact 核對真實 evidence payload 欄位。

## Previous Completed Handoff

- task_id：`20260603_same_day_risk_report_replay_regressions`
- 狀態：done / committed / pushed；Git completion gate passed。
- commits：
  - `ea75f15 Fix same-day risk and report replay regressions`
  - `a7ac71d Mark same-day report replay fix closeout`
- 問題：Owner 要修 7 項 06/03 v20.4.32 報文問題，並要求不要再只驗 helper：聯電同日 -3.86% + 突破失敗仍顯示新倉觀察；光寶科可買 / 淘汰同日抖動；技嘉過熱觀察露 RR 0.21；簡報原因逐檔串接；未持倉回測行部分有部分無；盤中 / 盤後降噪漂移；strategy sample version filter 需確認不回退。
- 修正：
  - 同日建倉新增 `SAME_DAY_FAIL_DROP_PCT = 0.03`；今日買入後若 -3% 且突破失敗 / 結構轉弱，持倉主行動顯示 `減碼`；hard_stop 仍優先，僅輕微回落維持新倉風控觀察。
  - 前態淘汰 / failed / weak 的單次 BUY 不直接翻可買；需連續確認且 `breakout_distance <= 1`。被防抖保守降級的卡片顯示 `不買｜前態待確認`，不再出現 `不買｜進場`。
  - 過熱 / 等冷卻 / 過熱觀察未持倉 RR 統一顯示 `-（過熱）`。
  - Summary 原因行單句主線化，不再逐檔串接。
  - 補 06/03 v20.4.32 等價 official message-list replay probe，覆蓋聯電減碼、技嘉 RR、光寶科防抖、原因行、未持倉回測降噪與 `v20.4.33` header。
  - 報文版本升 `v20.4.33`。
- 驗證：QA `通過`；主 repo `tests/test_analysis_engine.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py` 240 passed，241 warnings；06/03 replay single test passed；`py_compile` passed；`git diff --check` passed。
- QA 反證：第一輪 QA blocked 抓到 CHANGELOG 與 diff 不一致；第二輪 QA blocked 抓到 `不買｜進場` 手機誤讀；Tech 補同層 replay 後抓出聯電主行動優先序仍被 `硬風控減碼` 吃掉並修復；最終 QA 額外 probe 確認前態 weak + 連續 2 次但 `breakout_distance=1.2` 仍維持淘汰。
- 邊界：未改 RR 公式、DB schema/write path、production smoke/backfill、live Telegram；`services/strategy_evidence.py` 本輪未改，既有跨版本證據取樣維持。

## Previous Completed Handoff

- task_id：`20260603_strategy_evidence_report_risk_patch`
- 狀態：done / committed / pushed；Git completion gate passed。
- commit：`7ccc808 Fix evidence sampling and same-day risk report`。
- 問題：Owner 要一次性完成 A1+B1-B4+C：strategy evidence 跨版本歷史要真正進樣本；未持倉可買不得混入交易執行；原因 / 風險需拆分；partial +0% 不得誤導；同日建倉 hard_stop / 快速止損不得被剛買入豁免。
- 修正：
  - `load_strategy_evidence_summary(limit=60)` 移除 version filter，改用 `.range()` 分頁，直到資料涵蓋超過 60 個 distinct `trade_date` 後裁切為最近 60 交易日；高 row-density 不再退回 60 rows。
  - 未持倉可買移至 `新倉建議`，標示 `尚未買入｜建議分批`；`今日盤中交易執行` 只列已執行 / 持倉動作。
  - Summary 拆 `原因` / `風險`，按持倉 / 新倉對象呈現；空交易執行不顯示 `無新增下單`。
  - partial evidence modifier = 1.0 顯示 `僅輔助參考`，不顯示 `+0%`。
  - 同日建倉若跌破 hard_stop、入場價 -3%、或入場 K 棒低點，顯示當日減碼；僅破警戒仍為新倉風控觀察。
  - 報文版本升 `v20.4.32`；D1 光寶科同日淘汰 -> 可買翻轉維持 deferred。
- 驗證：QA `通過`；主 repo `tests/test_strategy_evidence.py tests/test_generator_report.py tests/test_market_theme_evidence.py` 201 passed，241 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：前兩輪 QA blocked 抓到 A1 先是 60 rows、後是 `limit * 20` 在 25 檔/日只覆蓋 48 天；最終 pagination 版通過 61 天 x 17 檔跨頁邊界 probe，保留 60 distinct dates / 1020 rows，無 version eq。
- 邊界：未改 RR 公式、DB schema/write、production backfill、live Telegram；未跑 production smoke / full pytest。

## Current Process Correction

- 觸發：Owner 指出「修改一天仍證據不足」，且 06/03 v20.4.32 完整報文仍顯示 strategy evidence partial / market-theme 資料不足，以及聯電同日 -3.86% 未觸發快速止損減碼。
- 根因分類：`evidence_chain` + `mobile_reading` + `QA反證` + `runner_gap`。上一輪 QA 有抓 loader pagination，但沒有把 Owner 完整報文作為 final failure specimen，也沒有驗真實 production/report payload shape。
- 流程補強方向：PM 必須把 Owner 報文濃縮成「失敗標本與驗收路由」；Tech 標明 probe 覆蓋 helper / formatter / official generator / runner artifact 哪一層；QA 若不能在同層 replay Owner 標本，不得給 `通過`。
- 這不是新增死規則；它把每輪驗收從固定 checklist 改成按失敗發生層級選擇最小反證路徑。
- 狀態：流程治理已提交 `32a7a8b Tighten report failure specimen validation flow`。下一輪產品修復不得從 helper fixture 起手；必須先把 Owner 06/03 v20.4.32 報文轉成同層 replay / artifact，再修 evidence partial 與聯電同日快速止損。

## Previous Completed Handoff

- task_id：`telegram_message_noise_consistency_20260603`
- 狀態：done / committed / pushed；Git completion gate passed。
- 問題：Owner 要把 Telegram 首屏與卡片降噪做徹底：市場/R 值不重複、刪冗餘新倉/背景/持倉行、交易執行短句、僅追蹤與 cross-day 歷史 token 去重、未持倉總數和漏斗一致、淘汰/弱勢不可行動 RR 不露數值、partial +0% 改成僅輔助參考。
- 修正：
  - 首屏市場行改成 compact count：`市場：{mode} {R}｜交易執行 N｜持倉風控 N｜未持倉 N（可買N/僅追蹤N/淘汰N）`；無可買時不印 `可買0`，維持不可推薦語氣。
  - Summary 排除重複 `市場/結論`、`📌 持倉`、`背景`、逐行 `僅追蹤` 等首屏噪音。
  - 交易執行改為短文案，例如 `建準 可買（分批，不追價）`、`旺宏 減碼（續降優先級）`。
  - `cross_day_detail_line()` 去掉與 repair label 重複的 reason token，同一卡片 `修復中 / 連續觀察` 不重複。
  - 未持倉不可行動 RR 顯示為 `RR：-（不可行動）`；可買卡仍保留 raw RR 顯示。
  - partial 且 modifier=1.0 時顯示 `證據：partial｜僅輔助參考`，不顯示 `+0%`。
  - 本輪不升版，仍為 `v20.4.31`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 146 passed，225 warnings；`py_compile` passed；`git diff --check` passed；VERSION scan only `v20.4.31`。
- QA 反證：第一次 QA blocked 抓到 full file 26 failed 與有可買時首屏未列 `可買N` 的誤讀風險；Tech 返工後 QA 自建 `可買1 / 僅追蹤1 / 淘汰1` 盤中 fixture 通過，首屏、交易執行、漏斗、卡片 RR 一致。
- 邊界：未改 strategy decision、RR 公式、DB schema/write、production backfill、live Telegram；未跑 production smoke / full repo pytest。

## Previous Completed Handoff

- task_id：`presentation_noise_reduction_v20_4_31`
- 狀態：done / committed / pushed；Git completion gate passed。
- 問題：Owner 要把 Telegram/report 簡報按手機閱讀降噪：刪重複行、合併市場/結論與原因/風險、移除偽 `追蹤最強`、交易執行短句、卡片不可用歷史/回測不逐卡印、資料依據正常隱藏、B5 漏斗與卡片一致。
- 修正：
  - `format_cross_day_tracking_summary()` 將無有效進場時的 `追蹤最強` 改為 `僅追蹤`。
  - `presentation/report.py` 新增共用降噪/顯示 helper，盤中/盤後共用；市場/結論、原因/風險合併。
  - 正常資料源不顯示資料依據；異常 source-error 盤後顯示單一資料依據短訊。
  - 卡片不可用回測 / 歷史行隱藏，避免逐卡不可用噪音。
  - B5 rendered path 補 `隔日確認 / 等冷卻 / 等回測` Summary、漏斗、card 三方一致。
  - 本輪不升版，仍為 `v20.4.31`。
- 驗證：QA `通過`；主 repo rendered/message tests 8 passed，25 warnings；`py_compile` passed；`git diff --check` passed；VERSION scan only `v20.4.31`。
- QA 反證：盤中 no-valid-entry summary 出現 `僅追蹤`、不出現 `追蹤最強 / 🔥 最強`，`資料依據` count=0；盤後 source-error 只顯示一次策略樣本資料依據；既有 message order / afterhours readability / execution contract 仍通過。
- 邊界：未改 strategy decision、RR 公式、DB schema/write、production backfill、live Telegram。

## Latest Process Review

- 觸發：Owner 指出「在討論流程優化時，Architect 又退回去解釋產品 diff」。
- 根因分類：`runner_gap` + `文件不足` + `post-cycle closeout`。產品修復已 push，但 `DISPATCH.md` / `CURRENT_STATE.md` 仍殘留 `待 push / completion gate`，重開或被追問時容易把焦點帶回上一輪 diff，而不是處理流程失效本身。
- 流程補強：新增 `tools/cao_agent/check_architect_closeout_gate.sh`，在 git completion passed 後掃描 `DISPATCH.md` / `CURRENT_STATE.md` 是否仍有 pending commit / push / completion 語句，並要求 Recently Done 與 Git completion gate 狀態一致。
- 新收口順序：產品或流程任務完成後，先跑 git completion gate，再更新 closeout docs，最後跑 architect closeout gate；任一 gate fail，不得 final 寫完成。
- 這不是新增死規則；它把「不要靠記憶判斷是否已推」改成可重跑檢查。

## Previous Completed Handoff

- task_id：`per_stock_evidence_score_funnel_p0_p3_20260602`
- 狀態：QA passed；commit / push 待 final 收口。
- 問題：Owner 要 evidence 真正成為 per-stock 決策分數，而不是 market/theme 共享背景無差別 +8%；弱勢 / 失敗 / 過熱 / technical=0 不可被正向 boost；B5 漏斗與卡片需一致。
- 修正：
  - `strategy_sample` 以 explicit `reject_family / watch_category / setup_key / setup_category` 對應 `setup_strategy_samples`，成為 per-stock 分量。
  - 缺 explicit setup 時 fail closed，不用 report layer 推導分類補 boost。
  - `compute_evidence_score()` 改成 market 0.4 + strategy 0.6 的加權合成；market/theme 仍為共享背景，strategy/setup 提供逐股差異。
  - `FAIL / FAILED_BREAKOUT / WEAK / DISTRIBUTION / EXTREME / technical<=0` 時 evidence modifier 封頂 1.0，卡片顯示 `證據：不適用`。
  - B5 official rendered path 補 Summary / 漏斗 / card 三方一致回歸。
  - 本輪不升版，仍為 `v20.4.31`。
- 驗證：QA `通過`；主 repo targeted tests 4 passed，13 warnings；`py_compile` passed；`git diff --check` passed；VERSION scan only `v20.4.31`。
- QA 反證：初輪 QA blocked 抓到缺 explicit setup 仍吃推導分類 +7%；Tech 修後缺 setup / WEAK / EXTREME / technical=0 都不顯示 boost；旺宏 / 聯電 explicit setup modifier 不同；B5 三方一致。
- 邊界：未改 RR 公式、DB schema/write、production backfill、live Telegram；未跑 production data quality / setup 欄位覆蓋率。

## Previous Completed Handoff

- task_id：`fix_market_theme_evidence_gate_v20_4_31`
- 狀態：QA passed；commit / push 待 final 收口。
- 問題：Owner 指出 market/theme evidence 仍被三個閘門擋住：8 日 confirmed_trend 又被 `observed_days >= 15` 二次門檻擋；per-stock 缺 market_theme 被誤判 unavailable；strategy 跨版本 history 需回歸確認。
- 修正：
  - `_market_theme_evidence_payload()` 不再用 15 日二次門檻；confirmed + source available + `evidence_trend.status == confirmed_trend` 即 decision eligible。
  - market/theme 作為市場級 evidence，per-stock 缺 market_theme 時 fallback report-level `market_theme_evidence`。
  - `_manifest_status("ready")` 正規化為 available，讓 loader ready payload 可被 score path 消費。
  - strategy summary version filter 維持移除，跨版本 fixture 回歸通過。
  - 本輪不升版，仍為 `v20.4.31`。
- 驗證：QA `通過`；主 repo targeted tests 4 passed，13 warnings；`py_compile` passed；`git diff --check` passed；VERSION scan only `v20.4.31`。
- QA 反證：英業達持倉卡片在 8 日 confirmed report-level evidence + per-stock 缺 market_theme 時，顯示 `證據 +8%（supporting）`，不再顯示 `證據：不適用`。
- 邊界：未改 RR 公式、DB schema/write、production backfill、live Telegram；未改 `services/strategy_evidence.py` 本輪 diff，只做回歸確認。

## Previous Completed Handoff

- task_id：`evidence-wiring-and-funnel-consistency-20260602`
- 狀態：QA passed；commit / push 待 final 收口。
- 問題：Owner 指出前一輪只把 evidence 加權框架搭好，但兩個證據源沒有真正喂入：strategy_sample 被 version filter 切斷，market/theme string summary path 沒傳 trade_date，導致報文仍長期 `不適用 / 資料不足`。
- 修正：
  - `services/strategy_evidence.py load_strategy_evidence_summary()` 移除 `daily_signal_snapshot.version == version` filter，按 trade_date 讀近期跨版本 outcomes。
  - `core/generator.py market_theme_summary_evidence()` 新增 / 消費 `trade_date`，market_summary 是字串時也會呼叫 `load_confirmed_market_theme_evidence(trade_date=...)`。
  - `build_report_context()` 傳入 report trade_date，official `generate_report(dry_run=True)` path 可消費 confirmed evidence trend。
  - D2/B5 rendered message 補 `等冷卻 / 隔日確認` 漏斗與卡片一致 probe。
  - 調試期不再 bump VERSION，本輪仍維持 `v20.4.31`。
- 驗證：QA `通過`；主 repo targeted tests 4 passed，13 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：跨版本 old_version fixture 可產生 `分類：RR不足｜樣本：10 筆`；official generate_report probe 顯示 loader_calls=`['2026-06-02']`，market/theme 不再顯示資料不足；`build_market_theme_production_trend_consumption_check` uses history；智原 / 光寶科 card 分類與漏斗拆分一致。
- 邊界：未改 RR 公式、DB schema / write path、production backfill、live Telegram；未觸碰未追蹤 `scripts/diagnose_evidence_sources.py`。
- 後續：production evidence 實際資料品質、逐股 mapping、長期樣本分布需另開 read-only artifact / source-of-truth 任務。

## Previous Completed Handoff

- task_id：`evidence-per-stock-reliability-funnel-phase3-closeout-20260602`
- 狀態：QA passed；commit / push 待 final 收口。
- 問題：Owner 要一次性修復 per-stock evidence、可靠度門檻、modifier cap、source fail-closed、資料不足文案、card/funnel tracking 一致與 Phase 3 guard 回歸。
- 修正：
  - `compute_evidence_score(report_context, name)` 改為真正逐股取 evidence。
  - `report_context.per_stock_evidence` 已存在時，該股缺 market/theme 或 strategy/setup payload 會 fail closed，不 fallback report-level positive evidence。
  - market/theme source status 在 supporting / weak / mixed 前先 fail closed。
  - confirmed / decision eligible 與資料依據可靠度同口徑；insufficient 不得 confirmed 或 +15%。
  - supporting / partial modifier cap；confirmed 才可到 ceiling。
  - 資料不足文案改為 `短期背景資料不足，僅供觀察`。
  - `隔日確認` 納入 `僅追蹤` aggregate，漏斗拆分加總與 card actual 同口徑。
  - Phase 3 automation 未改碼，但 scheduled / workflow guard 回歸通過。
- 版本：`core/generator.py` 升為 `v20.4.31`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_phase3_evidence_automation.py tests/test_workflow_runtime_config.py` 191 passed，225 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：逐股缺 market/theme 或 strategy payload 時不吃 report-level confirmed / available；`source-error + supporting-looking payload` unavailable；supporting modifier 不到 ceiling；`隔日確認 1` 不再與 `僅追蹤 0` 分裂。
- 邊界：未改 RR 公式、DB schema / write path、approved write CLI、Phase 3 runner、production backfill、live Telegram。
- 後續：若 production evidence 缺逐股 theme/setup payload，需另開資料品質 / mapping / source-of-truth 任務，不應在 report layer fallback 補缺口。

## Previous Completed Handoff

- task_id：`evidence-score-decision-funnel-phase1-2-2b`
- 狀態：done / committed；push 與 Git completion gate 待 final 收口。
- commit：`c7dd94b Add evidence score decision weighting`。
- 問題：Owner 已拍板 evidence chain 要成為決策分數的一部分，並可影響排序與 funnel 邊界；同時必須保留 fail-closed、透明拆分、不單獨造 BUY、不放寬 chase / overheat / RR hard blockers。
- 修正：
  - 新增 `compute_evidence_score(report_context, name)`、evidence modifier 與 final confidence。
  - 契約公式：`evidence_modifier = clamp(1 + 0.3 * (evidence_score - 0.5), [0.85, 1.15])`；evidence 不足時 modifier = 1.0，final = technical。
  - `pick_best_stock`、watchlist sort 與 execution ordering 使用 final confidence；報文 score line 顯示 `綜合 / 技術 / 證據`。
  - market/theme 只有 `confirmed_trend` 可作 strong boundary evidence；`supporting_trend` 只作 supporting score，`single_day` 不 decision eligible。
  - Phase 2b 只在 existing technical setup near-boundary + strong confirmed evidence 時調整到可準備；不得變可買。
  - RR / overheat / chase / LIMIT_LOCK hard blockers 不被 evidence 放寬。
  - mixed adjusted + ordinary prepare 在 Summary / 漏斗 / card / detail index / manifest 同步拆分；ordinary prepare 主顯示態為 `不可追高觀察`，內部策略態以 `strategy_funnel_state=可準備` 保留。
  - `stock.<name>.risk.value` artifact 同時保留主顯示態、strategy funnel state 與 evidence adjustment reason。
- 版本：`core/generator.py` 升為 `v20.4.30`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 129 passed，225 warnings；focused evidence/mixed tests 24 passed；`py_compile` passed；`git diff --check` passed。
- QA 反證：supporting trend 不升 strong boundary；single_day 不 decision eligible；missing evidence modifier=1.0；no setup 不 BUY / 不可準備；RR / overheat / chase blocker 不放寬；mixed adjusted + ordinary prepare 手機與 manifest 一致；pick/sort 使用 final confidence。
- 邊界：未改 RR 公式、DB schema/RLS/grant/policy、production write/backfill、live Telegram、Phase 3 automation。
- 下一步：若 Owner 要繼續 evidence chain，優先驗 production evidence 資料品質與 per-stock evidence granularity；不要再用單純文案修補替代證據契約。

## Previous Completed Handoff

- task_id：`phase3-evidence-automation-20260602`
- 狀態：done / committed / pushed。
- 問題：Owner 要在 evidence_score / final_confidence major 前，先讓 evidence 常態可用，避免加權空轉。
- 修正：
  - 新增 `scripts/run_phase3_evidence_automation.py`，作為 scheduled evidence runner。
  - GitHub Actions 新增 `daily_evidence` mode 與 weekday 13:25 台北時間 schedule；scheduled path 不要求 Telegram secrets、不跑 live bot delivery。
  - daily_signal_snapshot 透過 `generate_report(return_write_results=True)` 取得寫入結果，並用 `read_daily_signal_snapshot_status()` read-after-write。
  - market/theme confirmed evidence 仍呼叫既有 `scripts/write_market_theme_confirmed_evidence.py --execute` approved write CLI，不繞過 guard。
  - runner 不再用 weekday 當交易日真值；以既有 TWSE official readonly source 確認交易日。無法確認、休市、source-error 或 13:20 前皆 fail closed skip，不寫、不累積 stale。
  - stale/unavailable alert 只按 `trading_day_confirmed=True` 或已確認交易日累積。
- 驗證：QA `通過`；主 repo `tests/test_phase3_evidence_automation.py tests/test_daily_snapshot_store.py tests/test_workflow_runtime_config.py` 29 passed，13 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：daily_evidence schedule 不送 Telegram；13:19 不進 write path；unknown calendar 不累積 stale；approved CLI read-after-write failure nonzero 且輸出 fail_closed。
- 邊界：未改 evidence_score / final_confidence / decision_eligible / funnel modifier、RR、策略 decision、DB schema/RLS/grant/policy、live Telegram；未執行 production write。

## Previous Completed Handoff

- task_id：`phase0-bugs-pre-evidence-score-20260602`
- 狀態：done / committed / pushed。
- 問題：Owner 已拍板 major 方向：證據要進決策分數並影響 funnel 邊界；但落地順序要求先修 Phase 0 顯示門控與 B1-B5 手機閱讀 bug，不提前進入 evidence_score / final_confidence / Phase 3。
- 修正：
  - Phase 0-1：score source status 支援 insufficient / missing alias，缺來源時保守顯示 `S 證據不足`，不出現 `證據不足｜S5/5`。
  - B1：弱勢遠離持倉條件行移除重複 `觀察：` 前綴。
  - B2：score available 但盤面弱勢或遠離突破時，不再顯示 `極強`，改為 `待確認`。
  - B3/B4：保留 v20.4.28 持倉風控完整列出與 card/control/index 同序契約，補回歸。
  - B5：`弱反彈待確認 / 漲停反彈待確認` 進獨立 `隔日確認` bucket，summary / execution checklist / funnel formatter 同步。
- 版本：`core/generator.py` 升為 `v20.4.29`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 119 passed，225 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：message list 同時含六檔持倉與隔日確認未持倉，確認持倉排序一致、`隔日確認 1` 不併入 `等冷卻`；insufficient / missing score 不顯示 S5/5 或極強；弱勢/遠離突破不顯示 `弱勢｜極強`。
- 邊界：未改 RR 公式、DB schema/write、live Telegram；未進入 evidence_score / final_confidence / decision_eligible / funnel evidence modifier major；未做 Phase 3 自動化生產。
- 下一步：依 Owner 指令，先做 Phase 3 自動化證據生產，讓 evidence 常態可用，再開 Phase 1/2/2b major。

## Earlier Completed Handoff

- task_id：`holdings-risk-list-no-truncation-20260602`
- 狀態：done / committed / pushed。
- 問題：Owner 指出第三則 `持倉風控檢查` 不應只列前 5 筆再顯示 `另有 N 項持倉風控見詳情`；持倉有幾檔就要列幾檔。
- 修正：
  - `format_holding_control_checklist()` 預設 `limit=None`，使用者可見路徑完整列出全部持倉。
  - 預設不再輸出 `另有 N 項持倉風控見詳情`；顯式 `limit=5` 仍保留 helper 相容性。
  - `holding_control_items()` 沿用輸入 holding order，讓持倉卡、風控檢查、detail index 同序。
- 版本：`core/generator.py` 升為 `v20.4.28`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 116 passed，225 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：6 檔持倉完整列到第 6 筆，不含 `另有` / `見詳情`；card_order == control_order == index_order；未改 strategy decision、RR、DB、未持倉漏斗。
- 流程復盤：第一次 auto 被 stale Tech worktree 擋下；第一次 QA blocked 是 `CHANGELOG.md` stale 成上一輪任務。已保存 residual patch artifact 並同步正確 CHANGELOG 後 Re-QA 通過。這是既有 `runner_gap`，後續仍需修 Tech answer -> main handoff sync。

## Earlier Completed Handoff

- task_id：`20260602-risk-codex-fixlist-closeout-4-12`
- 狀態：done / committed / pushed。
- 問題：Owner 要「直接全部完成，不要一直拆」，把 Codex 修復清單剩餘可直接修項第 4/5/6/7/9/12 與第 8/10/11 回歸一次收口。
- 修正：
  - strategy_sample 狀態改以結構化 `structured_status` 判定；legacy 中文文字 summary fail closed，不再靠 grep 反推。
  - market/theme 可靠度由 `evidence_trend` 指標派生，不再硬寫「中等」；strategy sample 資料依據去重。
  - cross_day source status 不足時，不用 previous_state / dedupe_guard 做確認結論。
  - `LAST_OHLCV` fallback payload 帶 `stale / data_date / fallback_source`，報文提示非當日資料。
  - Summary 降噪：同義新倉 / 無有效進場壓縮；空執行區塊、`無新增下單`、`交易執行 0`、全 0 未持倉漏斗不顯示。
  - 持倉排序 / 主行動回歸；已突破負百分比改成人話 `已突破，位於突破區上方`。
- 版本：`core/generator.py` 升為 `v20.4.27`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py tests/test_stock_api_history.py` 125 passed，225 warnings；`py_compile` passed；`git diff --check` passed。
- QA 反證：legacy strategy text fail closed、cross_day insufficient 無確認語氣、LAST_OHLCV stale 可見、負突破百分比不出現、全 0 漏斗與 source-missing 空交易區塊不出現。
- 流程復盤：第一輪 QA blocked 是 handoff stale `CHANGELOG.md`；第二、三輪 QA 連續抓到第 10 項殘留（全 0 漏斗、source-missing 空交易區塊）。這是 `runner_gap` + `mobile_reading` + `QA反證`，同類任務必須讓 QA 直接 probe source-missing / 全 0 場景，不能只看一般報文路徑。
- 邊界：未改 strategy decision、RR 公式、DB schema/write path、production DML/backfill、live Telegram；B/C 類仍待研究 / PM 判定。

## Previous Completed Handoff

- task_id：`risk_patch_unheld_funnel_overheat_prepare_fix`
- 狀態：done / committed / pushed。
- commit：`d432545 exclude overheated stocks from prepare funnel`。
- 問題：Owner 清單第 3 項指出過熱 / RR blocker / `過熱降溫` 未持倉仍被漏斗算進 `可準備 / 不可追高觀察 N（不可買）`，卡片、漏斗、summary 容易自相矛盾。
- 修正：`unheld_funnel_state()` 在 `should_show_overheat_rr_blocker(result, holding=False)`、`heat_state HOT/EXTREME` 或 `strong_prepare_bucket == 過熱降溫` 時，不再回傳 `可準備`；改入既有 `等冷卻 / 等回測` 僅追蹤。普通非過熱突破回測仍保留 `可準備`。
- 版本：`core/generator.py` 升為 `v20.4.26`。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 112 passed，221 warnings；`py_compile core/generator.py tests/test_generator_report.py` passed；`git diff --check` passed。QA 補同份報文手機閱讀反證：summary / 漏斗 count / 卡片標題 / 強勢準備同源。
- 邊界：未改 strategy decision、RR 公式 / blocker 定義、DB schema/write、production DML/backfill、live Telegram。

## Earlier Completed Handoff

- task_id：`risk_patch_score_source_status_display_gate_20260602`
- 狀態：done / committed / pushed。
- commit：`ffbaf70 gate score display by evidence status`。
- 問題：Owner 清單第 1 項指出，卡片在 `stock.<name>.score.source_status` 非 available / derived 時仍可能顯示 `S 5/5`、`極強`、`突破確認` 等高置信文字。
- 修正：`presentation/report.py` 新增 score source gate；持倉 / 未持倉卡顯示 S 分數或依賴 score/strength 的高置信盤面文字前讀 `stock.<name>.score.source_status`。score 不足時顯示 `S 證據不足` 或 `S 不可用`，盤面降級為 `強弱證據不足｜待確認`；price / RR / volume 可用時不被誤藏。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 111 passed，221 warnings；`py_compile presentation/report.py tests/test_generator_report.py` passed；`git diff --check` passed。QA 額外反證缺 `stock.TEST.score` manifest 時 fail closed 且不誤傷 price/RR。
- 邊界：未改 strategy decision、RR 公式、DB schema/write、production DML/backfill、live Telegram。

## Older Completed Handoff

- task_id：`evidence_gate_p1_p2_p4_20260602`
- 狀態：done / committed / pushed。
- commit：`9b1e084 fix evidence gate report conflicts`。
- 問題：Owner 指出 evidence_manifest / 資料依據已宣告 strategy_sample、ledger、market/theme 等證據不足或只作背景，但卡片仍顯示 S 5/5、極強、突破確認、精確今日買賣 / 股數 / 均價與可行動 funnel，形成「滿分結論 vs 不足證據」。
- 修正範圍：只處理 P1/P2/P4。
  - P1：strategy_sample missing / insufficient / source-error / unresolved-conflict 時，未持倉高置信行動標籤 fail closed；不再顯示可買、S 5/5、突破確認或進場觸發。
  - P2：持倉卡片 execution 行同時檢查 positions 與 ledger / execution_memory status；任一不足或衝突時，隱藏精確股數、均價、今日買賣，改顯示執行記憶不足。
  - P4：未持倉 funnel source status 納入 strategy_sample；RR 不可用、過熱或證據不足時不得進可買 / 可準備 / 進場觸發。
- 重要反證：strategy_sample source-error 但 price/OHLCV/RR available 時，只阻斷高置信策略樣本依賴結論，不把原因誤寫成 price/OHLCV/RR source failure，也不隱藏可用價格。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 108 passed，221 warnings；`py_compile core/generator.py presentation/report.py tests/test_generator_report.py` passed；`git diff --check` passed。
- 邊界：未改 `services/analysis.py`、strategy decision、RR 公式、DB schema/write、production DML/backfill、live Telegram；P3/P5/P6/P7/P8 未處理。
- 流程復盤：第一輪 QA blocked 是有效攔截，抓到 strategy_sample source-error 被誤歸因為 price/OHLCV/RR failure 且價格被藏掉；第二輪 Tech 先漏 P2，Architect 未送 QA，改用 `CLEAN_TECH_WORKTREE=0` 在候選上補 P2。這是 `QA反證` + `Tech同步` + `runner_gap`，後續同類任務要把 P1/P2/P4 三條 probe 都列為 stop condition，不讓局部通過冒充整輪完成。

## Older Completed Handoff

- task_id：`20260602_intraday_v20_4_24_a1_a2_a3_hard_conflicts`
- 狀態：done / committed / pushed；Git completion gate passed。
- commit：`dab598e fix intraday report hard conflicts`。
- 問題：06/02 盤中 `v20.4.24` 報文有三個手機閱讀硬衝突：未持倉不可買 / 不可追高仍以推薦感 `可準備` 主標籤呈現；同一持倉主行動在卡片 / 決策 / 風控檢查混用；持倉排序在卡片 / 風控檢查 / 詳情索引不一致。
- 修正：報文版本升 `v20.4.25`；不可買未持倉顯示為 `不可追高觀察` / `過熱待回測` / `待回測`；一般續抱持倉可見主行動收斂為 `續抱觀察`；詳情索引的持倉欄位改列 ordered holding names，與持倉卡片和風控檢查同序。
- 驗證：QA `通過`；主 repo `tests/test_generator_report.py` 106 passed，217 warnings；`py_compile` / `git diff --check` passed；QA 額外 rendered-message probe 確認 3 則 message、未持倉 title 無 `可準備 / 可買 / 推薦`、持倉 card/control/index order 一致、同一持倉主行動三處一致。
- 邊界：未改 `services/analysis.py`、strategy decision、RR 計算、holding_status、DB schema/write、live Telegram；降噪第二批未處理，另開。
- 流程復盤：auto runner 第一次被 Tech worktree stale diff 阻塞，已保存 residual patch artifact；Tech agent 前兩次長時間停在分析階段，第三次以「先補紅測再最小實作」指令完成。這是 `runner_gap`，後續需強化 Tech runner 的進度/超時與 worktree hygiene。

## Archived Completed Handoff

- task_id：`fix-bot-workflow-may-backfill-guard-20260602`
- 狀態：done / committed / pushed；Git completion gate passed。
- commit：`c6da0bf skip may backfill in bot workflow`。
- 問題：GitHub Actions `Stock Bot Pro / run-bot` 在 default `run_mode=bot` 時仍跑 May market/theme evidence write，2026-06-02 觸發 `source date outside requested May range` guard 後 exit 1。
- 修正：`.github/workflows/stock-bot.yml` 的 May market/theme evidence backfill step 只在 `backfill_may` / `backfill_and_bot` 執行；default `bot` 明確 skip，不呼叫 `--write --confirm-write`。
- 驗證：QA `通過`；`tests/test_workflow_runtime_config.py tests/test_market_theme_source_backfill.py` 21 passed；QA 補 fake python success path，確認 backfill modes 仍執行且 guard failure 不被吞。
- 邊界：未改 `scripts/backfill_market_theme_sources.py` production guard、DB schema/write、Telegram 報文、live delivery；Node.js 20 deprecation warning 非本輪目標。

## Legacy Completed Handoff

- task_id：`holding-weak-observation-clock-20260601`
- 狀態：done / committed / pushed；Git completion gate passed。當前沒有 Active Tech/QA 任務，實際看板以 `DISPATCH.md` 為準。
- commit：任務二 blocked 文件已在 `9120672 mark support stop task blocked` 推送到 `origin/main`。
- 已完成前置任務：光寶科今日買入盤後不可續買說明已在 `2bd0a48 explain today buy non-current entry` 推送；技嘉過熱 RR 顯示已在 `2036415 show overheat blocker for zero rr` 推送。
- 問題：智原類弱勢遠離持倉只顯示 `續抱觀察 / 降低優先級`，缺觀察第幾天或來源未確認狀態。
- 修正：報文版本升 `v20.4.24`；弱勢遠離且續抱觀察持倉在條件行顯示可信 `弱勢觀察第 N 天`，或缺來源時 fail-closed 顯示 `觀察天數未確認`；`position_events` 非 dict 時不 crash，視為無可信事件。
- 驗證：最終 Re-QA output `.cao_agent_context/outputs/20260601_223651_26823_stock_qa_code_readonly.answer.txt`，結論 `通過`；主 repo related tests passed，Git completion gate passed。
- 邊界：未改 strategy decision、RR 計算、DB write、live Telegram、持倉狀態機。
- 後續：若 Owner 要真正補齊長期第 N 天，需要另開 production source / observation start 資料治理；本輪不 backfill、不新增 schema。
- 上一輪 v20.4.21 行為摘要保留如下，供重開對話辨識已落地內容：
- 關鍵行為：
  - 不升 VERSION，仍為 `v20.4.21`。
  - 三日資料改稱短期背景 / 短期背景資料，不再使用交易證據日語感。
  - 盤後下一步改為明日語境。
  - 盤後未持倉卡片移除逐檔長資料來源句。
  - 第三則資料依據改成人話：持倉與價格支持風控；未持倉只支持分類觀察，不支持直接進場。
  - 非加碼持倉不顯示新倉 RR 數字；新倉候選 RR 保留。
  - 今日買入且主行動為 `新倉風控觀察` 時，即使底層 signal 是 `ADD_10 / allow_add=True`，也不顯示具體新倉 RR 數字。
  - 盤後第三則恢復 `持倉風控檢查` 與 `未持倉漏斗（非執行）`。
  - 資料依據改為合併證據摘要：市場短期背景、持倉數、未持倉分類數、執行記憶邊界、持倉 RR 邊界。
  - 不改 strategy decision、RR 計算、holding_status、DB schema/write、live Telegram。
- 驗證：
  - Re-QA output：`.cao_agent_context/outputs/20260601_181248_1516_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - Follow-up Re-QA output：`.cao_agent_context/outputs/20260601_183214_25279_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - Afterhours brief/evidence Re-QA output：`.cao_agent_context/outputs/20260601_185800_22905_stock_qa_code_readonly.answer.txt`，結論 `通過`。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：128 passed，181 warnings。
  - Follow-up `tests/test_generator_report.py`：92 passed，181 warnings。
  - `.qa_tmp/v20_4_21_holding_rr_dry_run_card.json`：`credential_values_included=false`、`schema_change=false`、`data_write=false`、`live_telegram=false`，card 含 `新倉 RR：不適用（既有持倉）`，不含 `數據：RR 2.73`。
  - QA source-error phone-order probe：passed。
  - `git diff --check`：passed。
  - QA 額外反證：按手機閱讀順序掃描三則訊息，禁止詞不出現在 rendered output，資料邊界集中在第三則。
  - 先前 production read-only strategy evidence artifact 仍顯示缺 `classification backtest source-of-truth`，報文正確 fail closed，不回到舊式 `樣本 0｜樣本不足，不判讀`。
- 2356 production read-only artifact：
  - path：`.qa_tmp/production_readonly_2356_positions_events.json`。
  - 安全契約：`credential_values_included=false`、`schema_change=false`、`data_write=false`、`live_telegram=false`。
  - `positions` 摘要：2356 英業達 `shares=0`、`status=CLOSED`、`realized_profit_taken_ratio=0.5`、`last_realized_profit_date=2026-05-25`。
  - `position_events` 摘要：4 筆 sell summary，labels 皆為「賣出」，`second_stage_like_labels=[]`、`has_confirmed_second_stage_label=false`。
  - 解讀：production ledger 目前不是「仍持倉 225」；但也沒有可被報文稱為「已確認第二段停利」的 label。若 Owner 認定實際未賣，需另開 source-of-truth/ledger 稽核任務。
- Runner / 流程修正：
  - `tools/cao_agent/run_qa_code.sh` 已補 QA 啟動前同步主 repo handoff files 到 tech worktree，避免 QA 驗到 stale `CHANGELOG.md`。

## Data / Evidence Status

- production 2026-05 market/theme 資料已回填並通過 read-only audit：
  - `market_theme_confirmed_evidence`：180 rows，20 trade dates，`2026-05-04` 到 `2026-05-29`，duplicate groups 0。
  - `market_theme_index_daily_bars`：200 rows，20 trade dates，`2026-05-04` 到 `2026-05-29`，duplicate groups 0。
  - `sector_theme_members`：12 active mapping rows，只是 mapping，不是 daily history。
  - `daily_signal_snapshot`：每日當時版本留存，不要求舊五月回填為 current version。
- generator 已消費 production `market_theme_confirmed_evidence` history；不是 runtime/local 假資料。

## Next Development

- 重開對話後先以 `git status --branch --short` 與 `tools/cao_agent/check_git_completion_gate.sh` 確認 commit/push 狀態，不再依賴對話記憶。
- 只把 `CHANGELOG.md` 所列 scoped diff 當成本輪驗收範圍；工作樹其他旁支 dirty files 不能因本輪 QA 通過而整包吸收。
- 已處理 Owner 指出的「是 72/100 那個 maturity 到 100%」：目前五維 maturity report 可重跑為 100。
- 已處理本輪「先解合理度跟衝突」的第一層：使用者可見報文不再把無有效進場和推薦感最強同時輸出；raw evidence slot 改成人話，衝突/缺資料保守揭露。
- 已處理 Owner 指出的 v20.4.21 剩餘手機閱讀問題：三日短期背景命名、非加碼 RR、盤後明日語境、卡片資料降噪、第三則資料依據人話化。
- 流程強化不是新增死規則：已新增 `tests/test_generator_report.py` probe，讓同類錯誤可重跑失敗。
- import boundary gate 仍保護後續拆分：presentation 不能反向依賴 writer/DB，core/services 不能依賴 presentation，`core/generator.py` bridge 只是 transitional。
- 另開旁支：若 Owner 認定 2356 英業達實際未賣，查 production positions / position_events 為何目前 artifact 顯示 CLOSED / shares 0。
- 另開旁支：盤點全報文 `追高 / 追蹤` 相關文案。
- 另開旁支：Telegram reply markup 附著最後一則 message 的 delivery consumer 風險。

## Runner Gaps To Fix Later

- CAO auto wrapper QA conclusion parser 已在工作樹修正，待 commit。
- Tech worktree 曾殘留舊 candidate diff；新任務前應自動清理或阻塞並明確提示。
- QA production-read 任務已可用 `CAO_QA_USE_REPO_CONFIG=1` 避免 dummy config；QA sandbox DNS 仍可能失敗，可用 `scripts/smoke_market_theme_evidence_readonly.py --auxiliary-render-artifact-json` 生成 safe read-only artifact。
- QA worktree handoff sync 已補：每次 QA runner 啟動前從主 repo 同步固定 handoff Markdown，避免 stale TASK/CHANGELOG/QA_REPORT 造成反覆 conditional。
- 流程強化：完整報文任務的 QA probe 必須覆蓋 Summary 首屏、卡片、漏斗、交易執行 / 明日計畫，不只驗單一 formatter 或 manifest。
- Git completion gate 已補：repo 落地任務 final 前必須確認 worktree clean、branch 有 upstream、local HEAD 等於 upstream HEAD；標準命令為 `tools/cao_agent/check_git_completion_gate.sh`。
