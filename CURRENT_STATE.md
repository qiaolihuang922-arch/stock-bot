# CURRENT_STATE.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保存短上下文與穩定狀態，不重寫啟動清單。

## Stable Context

- 專案：台股策略 Telegram 報文機器人。
- 正式結果以 git / runner 產生報文為準。
- 使用者可見報文版本在 `core/generator.py` 的 `VERSION`，目前已落地為 `v20.4.47`。
- 固定 8 份 Markdown 不刪：`AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`。
- Architect 是總控；產品 / 策略 / 報文 bug 或 feature 預設走 PM -> Tech -> QA。
- 跨日狀態、已執行交易、歷史 evidence 必須來自 production DB 或 Owner 指定持久來源；local/runtime/worktree 不能當跨日記憶。
- 缺資料、source-error、欄位不足或可信度不足時 fail closed。

## Latest Completed Work

- task_id：`future_watch_mops_fundamentals_context_20260604`
- 狀態：code done / QA 通過；報文版本維持 `v20.4.47`。
- 問題：Owner 要在法說會段增加股票 EPS 與營收年增；營收用當月，當月沒有用上一個官方公告月；同時法說會要顯示 conference 名稱，避免同公司多場看起來像重複。
- 關鍵行為：
  - 新增 TWSE/TPEX 官方 OpenAPI 月營收與 EPS source。
  - `build_live_stock_fundamentals_source()` 合併上市 / 上櫃最新月營收與最新季 EPS snapshot。
  - `collect_mops_events()` 將 fundamentals attach 到 MOPS 法說會 event。
  - 法說會行改成 `日期 代號 名稱｜conference｜EPS ...｜營收YoY ...｜關注原因：...`，不再顯示 `source=MOPS`。
  - MOPS summary 會清理 `本公司受邀參加...說明...` 這類模板字；有引號的 conference 名稱優先取引號內容。
- 驗證：
  - Focused future-watch tests：11 passed。
  - py_compile：passed。
  - `git diff --check`：passed。
  - Official `generate()` read-only smoke：光寶科 / 聯電 / 英業達等法說會顯示 conference、`EPS 2026Q1`、`營收YoY 2026/04`。
- 邊界：未改策略、RR、持倉風控、DB schema/write/backfill、live Telegram；EPS 是最新季，不是月資料；營收是官方最新月 snapshot。

## Previous Completed Work

- task_id：`future_watch_event_impact_explanation_20260604`
- 狀態：code done / QA 通過；報文版本維持 `v20.4.47`。
- 問題：Owner 問歷史類比目前怎麼查數據，並要求第三段相關事件去除來源、增加為什麼影響台股的說明。
- 關鍵行為：
  - `未來30日台股影響事件` 行由 `來源：...` 改為 `說明：...`。
  - 新增 `_taiwan_market_impact_note()`：利率/匯率 -> 外資風險偏好、台股估值、美元/台幣與外資流向；通膨 -> Fed 路徑與科技股估值；政治風險 -> 避險情緒與供應鏈不確定性。
  - `collect_global_events()` 保留內部 source/source_label，但 formatter 不顯示來源。
  - 歷史類比算法未改：目前讀 TWSE 即時大盤與近月 OHLC，計算單日跌幅、高檔回落、盤中震盪、TWSE樣本天數，再套固定壓力情境模板；不是多年歷史資料庫相似度模型。
- 驗證：
  - Focused future-watch tests：11 passed。
  - py_compile：passed。
  - `git diff --check`：passed。
  - Official `generate()` read-only smoke：第三段無 `來源：`，每筆有 `說明：...`。
- 邊界：未改資料查詢邏輯、策略、RR、持倉風控、DB schema/write/backfill、live Telegram。

## Previous Completed Work

- task_id：`future_watch_mops_breadth_query_fix_20260604`
- 狀態：code done / QA 通過；報文版本維持 `v20.4.47`。
- 問題：Owner 貼出的第 4 則 `未來30日法說會` 只剩 `06/05 2303 聯電` 一筆；改版前查詢資料是對的。
- 根因：MOPS 查詢優化後採單檔深度優先，前面標的會先掃完所有 TYPEK / 月份，在 query budget 下後排標的被漏查。
- 關鍵行為：
  - MOPS 查詢改為廣度優先：所有標的先查第一優先 TYPEK，再進 fallback。
  - `MOPS_DEFAULT_MAX_TARGETS` 8 -> 12，`MOPS_DEFAULT_MAX_QUERIES` 24 -> 32。
  - 法說會顯示上限 5 -> 10，避免查到的後段事件被截掉。
- 驗證：
  - Focused future-watch tests：11 passed。
  - py_compile：passed。
  - `git diff --check`：passed。
  - Official `generate()` read-only smoke：未來30日法說會恢復多檔，包含 06/04 緯創 / 群創、06/05 光寶科 / 聯電 / 仁寶 / 英業達、06/08 英業達、06/09 仁寶、06/22 光寶科。
- 邊界：未改策略、RR、持倉風控、DB schema/write/backfill、live Telegram。

## Previous Completed Work

- task_id：`future_watch_30d_section_semantics_20260604`
- 狀態：code done / QA 通過；報文版本維持 `v20.4.47`。
- 問題：Owner 指出除了歷史類比外，其他兩個大項都只是未來 30 天；第三點應改為會影響台灣股市的事件，不要泛稱全球事件。
- 關鍵行為：
  - 第 4 則段落維持三段，但標題改為 `歷史類比`、`未來30日法說會`、`未來30日台股影響事件`。
  - MOPS source-error 文案改為 `未來30日法說會：MOPS 官方來源暫時不可解析，本次不列未確認事件`。
  - 台股影響事件 source-error / empty 文案同步使用 `未來30日台股影響事件`。
  - 舊段落標題 `法說會提醒` / `全球事件` 不再出現在第 4 則。
- 驗證：
  - Focused future-watch tests：10 passed。
  - py_compile：passed。
  - `git diff --check`：passed。
  - Read-only live smoke with 2301：第 4 則顯示新標題，仍列 MOPS 06/05 / 06/22 光寶科法說會。
- 邊界：未改資料查詢邏輯、策略、RR、持倉風控、DB schema/write/backfill、live Telegram。

## Previous Completed Work

- task_id：`future_watch_query_interface_optimization_20260604`
- 狀態：code done / QA 通過；報文版本維持 `v20.4.47`。
- 問題：Owner 擔心未來 30 日關注的即時接口查詢會久，需要多增加查詢參數與範圍控制，不走 DB/cache 方向。
- 關鍵行為：
  - MOPS `collect_mops_events()` 新增 `max_targets`、`max_queries`、`max_seconds`。
  - 回傳 diagnostics：`query_count`、`target_count`、`budget_exhausted`、`source_error_count`。
  - MOPS POST 參數包含 `encodeURIComponent=1`、`step=1`、`firstin=1`、`off=1`、`TYPEK`、`year`、`month`、`co_id`。
  - 市場別正規化：上市/TWSE -> `sii`，上櫃/TPEX/OTC -> `otc`，興櫃 -> `rotc`，公開發行 -> `pub`。
  - 持倉 / 可買準備候選優先查；淘汰 / blocked 後置。
  - 已知市場別時每月查對應 TYPEK 後停止，不再盲掃四種市場。
- 驗證：
  - Focused future-watch tests：10 passed。
  - py_compile：passed。
  - `git diff --check`：passed。
  - Read-only live smoke with 2301：`mops_query_count=2`、`mops_target_count=1`、`budget_exhausted=False`，仍列 MOPS 06/05 / 06/22 光寶科法說會。
- 邊界：未改策略、RR、持倉風控、DB schema/write/backfill、live Telegram；第 4 則可見格式不變。

## Previous Completed Work

- task_id：`future_watch_complete_v20_4_47`
- 狀態：code done / QA conditional pass；報文版本升 `v20.4.47`。
- 問題：Owner 認為 v20.4.46 第 4 則仍只是保守試行，不是完成版：歷史類比空泛、MOPS source-error、全球事件 raw/英文。
- 關鍵行為：
  - TWSE 歷史類比改為壓力情境線，顯示相似情境、相似度、相似點、差異、關注條件與 `source=TWSE`。
  - MOPS adapter 補 `step=1` / `firstin=1`，可解析官方 `t100sb02_1` 表格；資料列不必重複出現 `法人說明會`，欄位標題可信即可。
  - MOPS 多市場查詢不再讓單一 TYPEK source-error 覆蓋已查到事件。
  - 全球事件中文化，來源改為 `來源：...官方/備援`。
- 驗證：
  - Focused future-watch tests：9 passed。
  - py_compile：passed。
  - `git diff --check`：passed。
  - Read-only live smoke with 2301：TWSE 壓力情境、MOPS 06/05 / 06/22 光寶科法說會、中文全球事件。
- 殘留風險：full `tests/test_generator_report.py -q` 仍有 30 個既有未持倉漏斗 / legacy snapshot failures；全球事件 smoke 走備援 source；TWSE 歷史類比是壓力情境 template，不是多年統計模型。
- 邊界：未改策略、RR、持倉風控、DB schema/write/backfill、live Telegram。

## Previous Completed Work

- task_id：`github_actions_manual_workflow_clean_inputs_20260604`
- 狀態：code done / QA 通過；不升 Telegram 報文版本。
- 問題：Owner 手動執行 GitHub Actions 時，手機畫面仍顯示舊 `start_date` / `end_date` / `backfill_version` 欄位，送出後 GitHub 回 `Unexpected inputs provided`。
- 關鍵行為：
  - 刪除舊 `.github/workflows/stock-bot.yml`。
  - 新增 `.github/workflows/stock-bot-clean.yml`。
  - workflow 名稱改為 `Stock Bot`，避免手機端沿用舊 `Stock Bot Pro` / old path dispatch form cache。
  - manual workflow inputs 只保留 `run_mode`，choices 只保留 `bot` / `daily_evidence`。
  - `tests/test_workflow_runtime_config.py` 改讀新 workflow，並反證舊 workflow file / 舊 backfill inputs 不存在。
- 驗證：
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/workflow_clean_inputs_pytest arch -arm64 ./.venv/bin/python -m pytest tests/test_workflow_runtime_config.py -q` -> 9 passed。
  - `git diff --check` -> passed。
  - `.github/workflows` 只剩 `.github/workflows/stock-bot-clean.yml`。
- 殘留風險：未直接操作 GitHub mobile app；push 後需從 Actions list 選新的 `Stock Bot` workflow。若仍看到舊 `Stock Bot Pro`，關閉重開 app 或刷新 workflow list。
- 邊界：未改 Telegram 報文版本、策略、RR、DB schema/write/backfill、live Telegram。

## Previous Completed Work

- task_id：`future_30d_watch_live_readonly_sources_v20_4_46`
- 狀態：code done / QA conditional pass with closeout fixed；報文版本升 `v20.4.46`。
- 問題：Owner 要未來 30 日關注功能先走即時資料試行，不做資料庫方向；需要查 TWSE / MOPS / 全球官方頁，且 source 不可靠時必須 fail closed，不能假造法說會、崩盤類比或交易建議。
- 關鍵行為：
  - `default_future_watch_sources(now)` 每次 `generate_report()` 建立 live readonly sources，不讀寫 DB。
  - TWSE OpenAPI 今日 / 近月 TAIEX source 可讀時仍保守顯示 `歷史類比：無高相似崩盤樣本｜依據不足/相似度低｜source=TWSE`，不硬套崩盤時間線。
  - MOPS official POST adapter 只有解析出日期 / 公司 / 法說會欄位才列事件；SPA shell、無 table、欄位不可辨識或空 rows 都回 `source-error`，第 4 則顯示 `法說會提醒：source-error（MOPS），本次不列事件`。
  - 全球事件嘗試讀 Fed / BLS / BOJ / BEA / ECB 官方頁；全部解析失敗時保留 seed fallback，仍只在第 4 則顯示。
  - 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報三則之後，前三則不混入未來關注內容。
- 驗證：
  - Focused tests：`PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_46_live_future_watch arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_46_future or v20_4_46_live or v20_4_46_generate_report_appends_live' -q` -> 9 passed, 173 deselected。
  - `py_compile core/future_watch.py core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
  - QA 補 official message-list probe：`qa_probe_pass message_count=4 malformed_mops=source-error first_three_clean=true no_db_client_requested=true`；QA 結論 `conditional pass`，條件為收口文件仍停 v20.4.45，本文件與 `DISPATCH.md` 已更新。
- 殘留風險：未跑 full pytest / production runner artifact / live Telegram；未驗真實 MOPS live 長期可解析；全球 official HTML 改版仍可能 fallback seed；TWSE 歷史類比尚未做多年 deterministic similarity。
- 邊界：未改交易策略、RR、持倉風控、DB schema/write/backfill、production source-of-truth、live Telegram。

## Previous Completed Work

- task_id：`evidence_chain_decision_layers_v20_4_43`
- 狀態：code done / QA conditional pass；報文版本升 `v20.4.43`。
- 問題：Owner 要保留目前顯示方式，但把 evidence-chain 接入所有主判斷；證據達標要有不同展示方式，hard gate 未解時不能只靠文字說明，summary / funnel / card 仍誤顯可買。
- 關鍵行為：
  - 新增每檔 `decision_judgment` 聚合，寫入 `stock.*.decision_judgment` 與 `report_context["stock_judgments"]`。
  - judgment 包含 `eligibility_state`、`primary_action`、`evidence_status`、`evidence_refs`、`blocking_reasons`、`progress_reasons`。
  - Telegram 既有 reason slot 追加 `決策證據：...`，不重設卡片版型。
  - RR不足、過熱 / EXTREME、突破失敗、source missing/error/conflict、量能、追高/漲停、持倉 hard stop 等 hard gates 會讓 judgment / summary / funnel / card 同步 fail closed。
  - 低 RR `trend_continuation` 不再顯示綠卡 / 小倉買點 / 新倉建議，改為 `等RR修復` 並保留 `卡關主因` / `量化差距`。
  - DB/live non-bypass restriction 只留在 context / manifest blocking reasons，不顯示成可見買入授權。
- 驗證：
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_43_main_focused arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_43 or v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics or v20_4_18_structural_artifacts_cover_three_fail_closed_cases or v20_4_20_maturity_report or v20_4_25_strategy_sample_source_error_blocks_action_without_hiding_available_price or v20_4_16_unheld_card_fails_closed_when_ohlcv_missing or trend_continuation_official_report_has_separate_small_buy_bucket' -q` -> 14 passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_43_main_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
  - 補充 mixed official probe：一檔真正 BUY + 一檔低 RR trend_continuation 時，summary 只列真正 BUY；低 RR 標的為 `等RR修復`，含 `決策證據` 且不含小倉買點 -> passed。
- QA 狀態：`conditional pass`。正式 `run_qa_code.sh` 與直接 `codex exec --model gpt-5.4-mini` 均遇 Codex usage limit；本地 official replay / direct consumer probe 已反證主要風險，但未取得正式 QA agent pass。
- 殘留風險：未跑 full pytest、production runner artifact、production DB source artifact、DB read/write、live Telegram。
- 邊界：未改 RR、strategy threshold、can_buy/is_valid_entry 核心、持倉狀態機、DB schema/write、live Telegram。

## Previous Completed Work

- task_id：`pm-20260604-v20.4.42-unheld-attribution-readable-gap`
- 狀態：code done / QA 通過；報文版本升 `v20.4.42`。
- 問題：v20.4.41 修掉假差距後，未持倉非可買卡片只剩單行主因，Owner 仍看不出「差多少」或下一步要等什麼。
- 關鍵行為：
  - 非可買未持倉卡片 attribution 由 `到達可買差距：...` 改成固定兩行：`卡關主因：...`、`量化差距：...`。
  - RR不足顯示 RR 現值、門檻與差值，例如 `RR 0.98｜需>=1.5｜差0.52`；距突破 >4% 才追加 `距突破 ...｜差...%`，距突破 <=4% 不列。
  - EXTREME / HOT 顯示熱度主因與降溫條件，不列 RR / entry quality 次因。
  - post-market ordinary prepare 顯示盤後待確認與開盤後確認要求，不寫成資料不足。
  - FAILED_BREAKOUT 顯示突破失敗與需重新站回突破區，不顯示 RR 0 / RR 門檻。
  - source missing、strategy sample、limit lock、weak rebound 人話化；真正可買與 `trend_continuation` 小倉 BUY 不顯示卡關兩行。
  - `tests/test_generator_report.py` current-version `v20.4.41` 硬編碼已清空並同步 v20.4.42。
- 驗證：
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_42_pytest_main3 arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'test_0604_v20_4_37_generate_mobile_consistency_message_list_replay or test_v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay or test_v20_4_10_mixed_valid_and_source_ineligible_buy_like_stays_consistent or test_v20_4_25_strategy_sample_source_error_blocks_action_without_hiding_available_price or test_confirmed_evidence_preserves_limit_lock_chase_hard_blocker or v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics or market_theme_source_error_supporting_payload_fails_closed_before_supporting or post_market_add_plan_is_not_labeled_as_risk_control or afterhours_brief_counts_today_buy_holdings_as_executed_new_positions or v20_4_10_summary_hides_strongest_when_candidate_source_missing or v20_4_16_unheld_card_fails_closed_when_ohlcv_missing' -q` -> 12 passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_42_pycache_main3 arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `rg 'v20\\.4\\.41' tests/test_generator_report.py` -> no matches；`git diff --check` -> passed。
  - QA 補 source-missing direct consumer 與 official replay 反證；QA 結論 `通過`。
- 殘留風險：未跑 full pytest、production runner artifact、production source artifact、DB read/write、live Telegram。
- 邊界：未改策略、RR、can_buy/is_valid_entry、持倉、DB schema/write、live Telegram。

## Previous Completed Work

- task_id：`v20.4.41-post-market-unheld-gate-attribution-readability`
- 狀態：code done / QA 通過；報文版本升 `v20.4.41`。
- 問題：v20.4.40 盤後未持倉 gate attribution 仍有手機閱讀誤讀：真正可買 / trend_continuation 小倉 BUY 也顯示 `到達可買差距`；FAILED_BREAKOUT 顯示假 RR 0；盤後 prepare 像資料不足；過熱卡列太多次因；raw enum 外露。
- 關鍵行為：
  - 真正 `可買` 與 `trend_continuation` 小倉 BUY 卡不顯示 `到達可買差距`。
  - 未達可買條件卡仍保留可信 gap；RR不足且距突破未達標如 6% 才顯示 `距突破 6%/需<=4%`。
  - QA 抓到 `距突破 2%/需<=4%` 已達標卻列入 gap 的 blocker，已修為距離 >4 才列入差距。
  - FAILED_BREAKOUT 顯示 `突破失敗/需重新轉強`，不顯示 RR 0 / `需>=1.5` 作主因。
  - post-market ordinary prepare 顯示 `盤後訊號｜需開盤後重新確認`，數據行顯示 `盤後待確認，需開盤後重新確認`，不再顯示 `證據：資料不足`。
  - EXTREME / HOT 冷卻前只顯示 `極熱/需降溫` 或 `過熱/需降溫`；LIMIT_LOCK / LIMIT_REBOUND / WEAK_REBOUND 人話化。
- 驗證：
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_41_pytest_pycache_main2 arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_41_postmarket_unheld_gate_attribution_readability_message_list_replay or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics' -q` -> 4 passed。
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_41_pycache_main2 arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
  - QA 補 official replay smoke 與 source missing / distance=2 反證；QA 結論 `通過`。
- 殘留風險：未跑 full pytest、production runner artifact、live Telegram、DB read/write；若未來新增 source blocked 但仍保留有效 distance 的新路徑，需補 focused test。
- 邊界：未改策略、RR、can_buy/is_valid_entry、DB schema/write、live Telegram。

## Previous Completed Work

- task_id：`telegram-unheld-gate-attribution-v20.4.40`
- 狀態：code done / QA 通過；報文版本升 `v20.4.40`。
- 問題：Owner 看不到「哪種情況真的會變可買」，只看到 `等冷卻 / 等RR修復 / 可準備` 等狀態；需要先試行未持倉卡片 gate attribution，顯示距離可買還差哪幾條。
- 關鍵行為：
  - 未持倉非可買卡片新增 `到達可買差距：...`。
  - 最多顯示 1-3 個可信 gate：RR、heat、source、突破距離、entry quality、LIMIT_LOCK / 不可追高、突破失敗等。
  - 真正 `可買` 卡與 `trend_continuation` 小倉 BUY 卡不顯示差距行，避免可買卡噪音。
  - `LIMIT_LOCK / LIMIT_REBOUND / 不可追高` 優先顯示開板回測方向；`trade_state=AVOID/EXTENDED` 但 `heat_state=NORMAL` 不再誤顯 `heat NORMAL/需降溫`。
- 驗證：
  - `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_40_unheld_non_buy_cards_show_gate_attribution_only or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics' -q` -> 4 passed。
  - `PYTHONPYCACHEPREFIX=/private/tmp/v20_4_40_pycache_main arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
  - QA 補充 official replay：`LIMIT_LOCK + AVOID + heat NORMAL` 顯示 `LIMIT_LOCK/需開板回測`，未顯示 `heat NORMAL/需降溫`；QA 結論 `通過`。
- 殘留風險：未跑 full pytest、production runner artifact、live Telegram、DB read/write；`AVOID + heat NORMAL + price_behavior NORMAL` 的細部 wording / gate ranking 仍可另開任務優化。
- 邊界：未改 RR 公式、strategy decision、can_buy/is_valid_entry、DB schema/write、live Telegram。

## Previous Completed Work

- task_id：`phase_a_after_close_unheld_buy_prepare_v20_4_39`
- 狀態：code done / QA 通過；報文版本升 `v20.4.39`。
- 問題：2026-06-04 盤後 v20.4.38 光寶科類未持倉 ordinary BUY 仍需明日開盤後確認，但 summary / 漏斗 / 卡片寫成 `新倉建議`、`可買`、`40%倉`、`買點成立`、`新增有效進場`，手機閱讀容易誤讀成可下單。
- 關鍵行為：
  - 盤後未持倉 ordinary `BUY` 且非 `trend_continuation` 時，改歸 `可準備（不可買）`。
  - 卡片標題改為 `🟡 明日準備｜不可買｜開盤後確認`。
  - 買點行改為 `買點：尚未成立｜盤後僅追蹤｜明日開盤後確認｜不追價`。
  - Summary 在 prepare-only case 顯示 `新倉：無有效進場` 與 `可準備：N 檔需明日開盤後確認，未確認前不可下單`。
  - RR / 技術 / 單檔回測輔助行仍保留。
  - mixed 盤後 `trend_continuation` 小倉 BUY + ordinary prepare 時，trend 小倉仍可行動，不被 `新倉：無有效進場` 覆蓋。
  - 盤中 ordinary BUY 與既有 `trend_continuation` 可買路徑未回退。
- 驗證：
  - `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'test_v20_0_14_message_list_uses_single_report_phase_when_phase_drifts or test_v20_0_14_post_market_fixture_uses_next_day_plan_semantics or test_v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or test_trend_continuation_official_report_has_separate_small_buy_bucket' -q` -> 4 passed。
  - `PYTHONPYCACHEPREFIX=/private/tmp/v20_4_39_pycache_main arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
  - QA 自補 explicit `report_phase='盤後'` mixed official message-list probe -> `通過`。
- 殘留風險：未跑 full pytest、production runner artifact、live Telegram、DB read/write；`trend_continuation` 盤後 summary 仍沿用 `新增有效進場` 詞彙，若要細分命名需另開任務。
- 邊界：未改 RR 公式、strategy decision、DB schema/write、live Telegram。

## Previous Completed Work

- task_id：`20260604_144316_6186_online_research_pair`
- 狀態：research done / fixed docs updated；本輪未改產品代碼、未改 DB、未發 Telegram。
- 結論：策略寬度不是全域放寬，而是條件分層：
  - `可準備`：報文 / 漏斗層升格，仍不可買；用來標出差一條件的候選。
  - `趨勢延續小倉`：只限回踩站回同源 setup，daily_price evidence positive，樣本 >=30，5D win >=55%，5D avg >0，倉位 <=15%，回踩低點下方停損。
  - 一般 `可買`：仍走既有 BUY / RR / can_buy / source gate，不因 evidence、題材、分數、回測摘要單獨放寬。
- 硬邊界：RR不足未解除、HOT/EXTREME、LIMIT_LOCK / LIMIT_REBOUND / WEAK_REBOUND、FAILED_BREAKOUT / fake breakout、market_grade D、NO_VOLUME、source-error / unresolved-conflict 都不得升級可買。
- 建議下一步：Phase A `可準備（不可買）` 已於 v20.4.39 落地；Phase B 才補 `趨勢延續小倉` portfolio cap / forward monitor。
- 研究文件：`RESEARCH.md` 已壓縮保存本輪方案。

## Previous Completed Work

- task_id：`fix-v20-4-37-rr-insufficient-message-readability`
- 狀態：code done / QA 通過 / committed; git completion gate passed。
- 結論：v20.4.37 報文中 `等RR修復｜RR不足` 被寫成 `證據：資料不足`、以及僅追蹤標的進 summary 回測的手機誤讀已修復；版本升 `v20.4.38`。
- 關鍵行為：
  - 光寶科類 `等RR修復｜RR不足` 卡片數據行改為 `不適用（RR不足）｜原因：RR不足，等待RR修復`，不再像資料源缺失。
  - summary 回測摘要只列入可買 / 趨勢延續 / 可準備候選語境；僅追蹤 / 等RR修復標的不再顯示 `回測（光寶科）`。
  - 建準類候選回測仍保留，避免修光寶科時誤刪候選回測。
- 驗證：
  - `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_38_rr_wait_card_reason_and_backtest_summary_readability or 0604_v20_4_37_generate_mobile_consistency_message_list_replay or v20_4_37_single_backtest_lines_are_not_aggregated or v20_4_36_non_actionable_unheld_hides_score_numbers' -q` -> 4 passed。
  - `PYTHONPYCACHEPREFIX=/private/tmp/v20_4_38_pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
  - actual `generate()` -> `v20.4.38`，summary 不含 `回測（光寶科）`，光寶科卡片顯示 RR不足原因。
  - QA 補 official formatter probe -> `通過`。
- 殘留風險：未跑 full pytest、production runner artifact、live Telegram、DB read/write；交易執行排序仍屬旁支未處理。
- 邊界：未改 RR 公式、strategy decision、DB schema/write、live Telegram。

## Previous Completed Work

- task_id：`2026-06-04-v20.4.37-generate-mobile-consistency`
- 狀態：code done / QA 通過 / committed; git completion gate passed。
- 結論：06/04 真實 `generate()` 報文首屏、漏斗、詳情索引與卡片分類已收斂到同源一致；版本升 `v20.4.37`。
- 關鍵行為：
  - 首屏未持倉括號納入 prepare bucket count，`不可追高觀察 1` 不再只出現在漏斗 / 索引。
  - 今日已買摘要改為 `今日已買 N（已風控 M/觀察 K）`，不再使用不可追溯的 `風控中`。
  - 未持倉回測摘要取消跨股票聚合；多檔同回測 body 時改為單檔行，例如 `回測（建準）：...`、`回測（緯創）：...`。
  - actual `generate()` 實跑輸出 `v20.4.37`；即時價會讓未持倉分類數在 `1/6/1`、`2/5/1` 等形狀間變動，但首屏 / 漏斗 / 索引合計保持同源一致；分類數與 Owner 原 specimen 的 `1/5/2` 不同是即時價變動，不是 formatter 漂移。
- 驗證：
  - `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_37 or 0604_v20_4_36_mobile_readability or single_backtest or unheld_funnel_hides_zero_count_buckets or evidence_sample_count' -q` -> 4 passed。
  - `PYTHONPYCACHEPREFIX=/private/tmp/v20_4_37_pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `arch -arm64 ./.venv/bin/python - <<'PY' ... generate() ... PY` -> passed；輸出 `v20.4.37`。
  - QA 補 official final message-list parser -> `通過`。
- 殘留風險：未跑 full pytest、production runner artifact、live Telegram、DB read/write；光寶科 `RR不足` 顯示 `證據：資料不足` 屬旁支原因分流風險，本輪未處理。
- 邊界：未改 RR 公式、strategy decision、DB schema/write、live Telegram。

## Previous Completed Work

- task_id：`v20_4_36_0604_report_readability_convergence`
- 狀態：code done / QA 通過 / committed; Git completion gate passed。
- commit：`bbee321`。
- 結論：06/04 v20.4.36 報文手機閱讀誤讀已收斂到 focused L2 範圍；版本維持 `v20.4.36`。
- 關鍵行為：
  - 正常 source 狀態不再逐卡顯示「持倉與現價已確認」或「現價與 OHLCV 已確認」。
  - 普通 `前次 observe / 修復中 / 連續觀察 1 天 / 權重 +1` 歷史行不再逐卡刷屏；高風險 / execution memory 類歷史仍保留。
  - 未持倉原因優先級改為淘汰 / 突破失敗 / 風控優先於過熱；量能不足顯示 `證據：量能不適用`。
  - 建準類 BUY 若同卡回測偏弱 / 無明顯優勢 / 樣本不足，補 `回測僅輔助，分批小倉、不追價`。
  - 首屏今日買入摘要改為 `今日已買 N｜風控中 M`，避免裸寫 `今日新建倉 3`。
- 驗證：
  - `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k '0604_v20_4_36_mobile_readability or v20_4_36_non_actionable or v20_4_36_failed_unheld or v20_4_36_single_backtest or structural_artifacts_cover_three_fail_closed_cases or presentation_noise' -q` -> 9 passed。
  - `arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
  - QA 額外 official `formatTelegramMessages` probe 通過，確認普通 history 隱藏但 `position_events` / sold execution memory 仍保留。
- QA 狀態：`通過`。
- 殘留風險：未跑 production runner artifact / live Telegram / DB read-write；full `tests/test_generator_report.py -q` 仍有 26 個 legacy contract failures，本輪不宣稱全量修復。
- 邊界：未改 RR 公式、strategy decision、DB schema/write、live Telegram。

## Previous Completed Work

- task_id：`trend_continuation_v20_4_36_validation_monitor_report_noise_20260603`
- 狀態：code done / local focused validation passed / QA conditional pass due runner_gap / committed / pushed。
- commits：
  - `9eea5c4 Validate trend continuation trigger and hide data basis`
  - `947c1dd Document trend validation closeout`
- 結論：v20.4.36 的 trend_continuation 已補「真能觸發」驗證、只讀監控、手機資料依據隱藏與回測行降噪。
- 關鍵行為：
  - 新增 `tests/test_trend_continuation.py`，確認正式 `strategy()` 在回踩延續 fixture 會輸出 `decision_type="trend_continuation"` / BUY / 小倉 `<=15%`，official report 出現「趨勢延續」與「小倉」。
  - extended spike 無回踩不開 trend_continuation BUY；負 evidence 不 BUY；research helper 與 production detector 對同一 fixture 命中一致。
  - 新增 `scripts/monitor_trend_continuation.py` 只讀監控；缺 Supabase read credentials 時 fail closed 為 `source-error`，不產生假 live win rate。
  - `presentation/report.py` 新增 `SHOW_DATA_BASIS=False`，預設不顯示第三則「資料依據」；`SHOW_DATA_BASIS=True` 可恢復，manifest/source_status/evidence_status 仍保留。
  - `core/generator.py` 的 structural/maturity evidence checks 改讀 manifest/source/status/use/limit/conflict，不再依賴可見資料依據文字；未持倉同 setup_key 回測行去重。
- 驗證：
  - `py_compile` passed。
  - `arch -arm64 ./.venv/bin/python -m pytest tests/test_trend_continuation.py tests/test_generator_report.py -k 'trend_continuation or data_basis or presentation_noise or v20_4_18_structural_artifacts or v20_4_20_maturity_report' -q` -> 17 passed。
  - `python3 scripts/monitor_trend_continuation.py --no-config --trade-date 2026-06-03` -> exit 2 / `status="source-error"` / no fake live rate。
  - `git diff --check` passed。
- QA 狀態：`conditional pass`。原因：QA agent 兩次報告舊測試狀態（聲稱 6240-6310 仍為 v20.4.35 / visible data basis），但主 repo 文件與同一命令輸出均顯示已修；列為 runner_gap follow-up。
- 邊界：未改 RR 公式、DB schema/write、live Telegram；版本維持 `v20.4.36`。

## Earlier Completed Work

- task_id：`trend_continuation_buy_path_phase2_20260603`
- 狀態：code done / QA 通過 / committed / pushed。
- commits：
  - `900d107 Add trend continuation buy path`
  - `f5a540c Document trend continuation closeout`
- 結論：階段二已實裝 trend_continuation 買入路徑；Owner 授權的「證據可開 BUY」例外只限此路徑。
- 關鍵行為：
  - 正式策略共用 `scripts/research_trend_continuation.py` 的回踩站回判定函式，避免研究 / 實盤口徑漂移。
  - `services/analysis.py` 新增 `decision_type="trend_continuation"`；positive same-source evidence 才 BUY，缺 / 負 evidence 降級 `trend_observation` / WAIT。
  - extended spike / 無回踩不開 trend_continuation BUY，不放寬追高。
  - 倉位 `<=15%`，止損在回踩低點下方，退出 / 持有對齊 5 日 edge；沿用既有同日入場即錯風控。
  - `core/generator.py` 版本升 `v20.4.36`；official report 新增 `🟢 趨勢延續買入｜小倉`、獨立 funnel / summary / 卡片 / 資料依據。
  - trend_continuation BUY 時即使資料源正常，也強制顯示策略樣本與候選資料 basis，避免可買卡片缺證據鏈。
- 驗證：
  - `py_compile` passed。
  - focused tests 6 passed，17 warnings。
  - `git diff --check` passed。
  - QA `通過`；額外 probe 確認缺 OHLCV/source 不產生 `decision_type=trend_continuation` BUY，也不顯示 trend_continuation 小倉支持語氣。
- 邊界：未改 RR 公式、DB schema/write、live Telegram；legacy `strong_follow` 缺 OHLCV 時仍可能 BUY，屬 out-of-scope follow-up，除非 Owner 要求所有 BUY 全域 source gate。

## Latest Completed Handoff

- task_id：`research_daily_price_backfill_and_trend_sample_expansion_20260603`
- 狀態：direct production backfill done / committed / pushed；QA conditional pass；Git completion gate passed。
- commits：
  - `caab930 Record daily price backfill results`
  - `83fd163 Document daily price backfill closeout`
  - 上一輪 tooling commit：`5045045 Add daily price backfill research tooling`
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
- 狀態：research done / committed / pushed；QA conditional pass；Git completion gate passed。
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
- 狀態：code done / committed / pushed；QA conditional pass；Git completion gate passed。
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
- 狀態：done / committed / pushed；Git completion gate passed。
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
- 根因分類：`runner_gap` + `文件不足` + `post-cycle closeout`。產品修復已 push，但 `DISPATCH.md` / `CURRENT_STATE.md` 曾殘留未收口語句，重開或被追問時容易把焦點帶回上一輪 diff，而不是處理流程失效本身。
- 流程補強：新增 `tools/cao_agent/check_architect_closeout_gate.sh`，在 git completion passed 後掃描 `DISPATCH.md` / `CURRENT_STATE.md` 是否仍有未收口語句，並要求 Recently Done 與 Git completion gate 狀態一致。
- 新收口順序：產品或流程任務完成後，先跑 git completion gate，再更新 closeout docs，最後跑 architect closeout gate；任一 gate fail，不得 final 寫完成。
- 這不是新增死規則；它把「不要靠記憶判斷是否已推」改成可重跑檢查。

## Previous Completed Handoff

- task_id：`per_stock_evidence_score_funnel_p0_p3_20260602`
- 狀態：done / committed / pushed；Git completion gate passed。
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
- 狀態：done / committed / pushed；Git completion gate passed。
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
- 狀態：done / committed / pushed；Git completion gate passed。
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
- 狀態：done / committed / pushed；Git completion gate passed。
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
- 狀態：done / committed / pushed；Git completion gate passed。
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

- CAO auto wrapper QA conclusion parser 屬歷史 runner gap，若再處理需另開流程任務並以當前 git 狀態取證。
- Tech worktree 曾殘留舊 candidate diff；新任務前應自動清理或阻塞並明確提示。
- QA production-read 任務已可用 `CAO_QA_USE_REPO_CONFIG=1` 避免 dummy config；QA sandbox DNS 仍可能失敗，可用 `scripts/smoke_market_theme_evidence_readonly.py --auxiliary-render-artifact-json` 生成 safe read-only artifact。
- QA worktree handoff sync 已補：每次 QA runner 啟動前從主 repo 同步固定 handoff Markdown，避免 stale TASK/CHANGELOG/QA_REPORT 造成反覆 conditional。
- 流程強化：完整報文任務的 QA probe 必須覆蓋 Summary 首屏、卡片、漏斗、交易執行 / 明日計畫，不只驗單一 formatter 或 manifest。
- Git completion gate 已補：repo 落地任務 final 前必須確認 worktree clean、branch 有 upstream、local HEAD 等於 upstream HEAD；標準命令為 `tools/cao_agent/check_git_completion_gate.sh`。
