# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：process
  - 風險判斷：高風險 audit，因本輪結論會決定是否恢復 evidence chain 開發；但本輪禁止產品修補，因此交付為零代碼 diff 的 integration audit matrix。
  - 本輪結論摘要：可確認多個 fail-closed guard 已存在；但 public.market_theme_confirmed_evidence 仍是 read-only-chain-incomplete，writer / ingestion / backfill / RLS role / production data smoke 未完成，不能視為端到端完
    成。

  ## 修改內容

  未修改產品代碼、測試、SQL、schema、runner 或策略；只完成 TASK 要求的 integration audit evidence matrix。

  ## 修改檔案

  - 無實際工作區檔案變更。
  - 依 Architect 指令，本輪不直接編輯 CHANGELOG.md；本最終回答即為 runner 寫入 CHANGELOG.md 的內容。

  ## 最小改動策略

  - 只讀 TASK.md 指定模組與直接鏈路。
  - 未做 bug fix、重構、清理、writer / ingestion / backfill、live DB、live Telegram。
  - 用靜態 call chain + 局部測試佐證，不擴成 full pytest / replay / production smoke。

  ## 契約影響

  - Runtime contract：無變更。
  - Telegram message list / payload / formatter / DB write path / strategy decision：無變更。
  - 版本同步：本輪不升版；core/generator.py 仍為 VERSION = "v20.4.3"。
  - Public helper：無新增、無修改。

  ## 直接消費者同步

  - Owner / Architect：可依下方 matrix 判斷哪些鏈路可繼續、哪些需另開任務。
  - 後續 Tech：只能把 next action 當新任務輸入，不得把本 audit 當已修復。
  - QA：需獨立反證每個 PASS / 正向結論，尤其 clean runner、fake fallback、read-only-only 斷點。

  ## Evidence Matrix

  ┌─────────────────────────────────────┬────────────────────────────────┬────────────────────────────────────┬────────────────────────────────────────┬────────────────────────────────┬──────────────────────────────────┐
  │ path/table                          │ claim                          │ evidence                           │ current status                         │ risk                           │ next action                      │
  ├─────────────────────────────────────┼────────────────────────────────┼────────────────────────────────────┼────────────────────────────────────────┼────────────────────────────────┼──────────────────────────────────┤
  │ core/generator.py::generate_report  │ 缺持倉 DB config / DB error 不 │ load_positions() 缺 client 回 {} + │ PASS                                   │ 若判斷錯，Owner 會把無持倉誤讀 │ QA 用 clean env / mocked source- │
  │ + services/                         │ 會 fallback 成全 watchlist 0   │ missing-source；DB error 回 {} +   │                                        │ 為真實 0 股並產生錯誤新倉 / 持 │ error 反證；若失敗另開 position  │
  │ position_store.py::load_positions   │ 股                             │ source-error；generate_report() 讀 │                                        │ 倉決策                         │ fail-closed bug                  │
  │                                     │                                │ 到 get_position_store_warning() 後 │                                        │                                │                                  │
  │                                     │                                │ 輸出 unavailable 並提前返回 fail-  │                                        │                                │                                  │
  │                                     │                                │ closed summary                     │                                        │                                │                                  │
  │ services/                           │ 缺 position events source 不會 │ 缺 client 回                       │ PASS                                   │ 今日交易讀取失敗若被當 0       │ QA 反證 missing-source / source- │
  │ position_store.py::load_today_posit │ fake 全 0 今日事件             │ _unavailable_event_summary()，含   │                                        │ event，會誤導「今天沒買 / 沒   │ error / empty query 三種路徑     │
  │ ion_events                          │                                │ available=False /                  │                                        │ 賣」                           │                                  │
  │                                     │                                │ today_events_known=False；DB error │                                        │                                │                                  │
  │                                     │                                │ 同樣 unavailable；只有 query 成功  │                                        │                                │                                  │
  │                                     │                                │ 且空資料才 _empty_event_summary()  │                                        │                                │                                  │
  │ core/generator.py::generate_report  │ 缺價格 / 無有效日線時 fail     │ load_stock_signal error 被加入     │ PASS                                   │ 價格缺失若被補假值，會產生     │ 後續若要強化需另開行情 source-   │
  │                                     │ closed，不產生正常候選         │ data_errors；not results_map 時返  │                                        │ fake BUY / RR / 排序           │ error 顯示任務                   │
  │                                     │                                │ 回「無有效數據：行情來源未返回可用 │                                        │                                │                                  │
  │                                     │                                │ 日線」或「無有效數據」             │                                        │                                │                                  │
  │ services/stock_api.py               │ 行情來源仍有 TWSE -> Yahoo     │ get_twse() / get_yahoo_history()   │ CONDITIONAL                            │ fallback 是真實外部 source，但 │ QA 應確認 fallback 不被解讀為    │
  │                                     │ fallback，但不是 fake          │ 都從公開行情 API 取日線；失敗記    │                                        │ GitHub fresh runner 依賴網路； │ production DB evidence；行情穩定 │
  │                                     │ confirmed；是外部行情備援      │ LAST_ERRORS 並回 None；LAST_OHLCV  │                                        │ 若兩源都失敗則無有效數據       │ 性另開資料源任務                 │
  │                                     │                                │ 是 same-run OHLCV cache，供 daily  │                                        │                                │                                  │
  │                                     │                                │ snapshot 寫入                      │                                        │                                │                                  │
  │ services/                           │ 缺 DB config / query error /   │ _build_client() 無 config ->       │ PASS                                   │ market/theme 缺資料若          │ QA 反證 support_level=strong、   │
  │ market_theme_evidence_store.py::loa │ no rows / non-confirming rows  │ missing-source；query exception -> │                                        │ confirmed，會誤導題材支持      │ stale、missing fields、no rows   │
  │ d_confirmed_market_theme_evidence   │ fail closed                    │ source-error; no rows -> absent;   │                                        │                                │                                  │
  │                                     │                                │ invalid / stale / rejected / weak  │                                        │                                │                                  │
  │                                     │                                │ -> insufficient-data 或 source-    │                                        │                                │                                  │
  │                                     │                                │ error                              │                                        │                                │                                  │
  │ core/                               │ loader fail-closed status 會保 │ 對 absent/missing-source/source-   │ PASS                                   │ report-derived / runtime       │ QA 反證 runtime diagnostic       │
  │ market_theme_evidence.py::build_mar │ 留為 production source 不足，  │ error/insufficient-data 呼叫       │                                        │ breadth 可能被誤當 confirmed   │ supportive case 不可 confirmed   │
  │ ket_theme_evidence_provider         │ 不用 runtime 補 confirmed      │ build_market_theme_evidence(...,   │                                        │                                │                                  │
  │                                     │                                │ missing_db_evidence=True)，再覆寫  │                                        │                                │                                  │
  │                                     │                                │ source_status 與                   │                                        │                                │                                  │
  │                                     │                                │ source_of_truth=production_db；    │                                        │                                │                                  │
  │                                     │                                │ format 顯示「production 來源不足」 │                                        │                                │                                  │
  │                                     │                                │ 與 runtime 診斷非確認              │                                        │                                │                                  │
  │ core/market_theme_evidence.py       │ local / runtime / cache /      │ NON_PERSISTENT_SOURCE_FAMILIES 包  │ PASS                                   │ fake source family 若通過會污  │ QA 用 malformed confirmed dict / │
  │                                     │ worktree / test_fixture /      │ 含 runtime/local/cache/worktree/   │                                        │ 染 confirmed evidence          │ runtime fallback / report-       │
  │                                     │ report_derived 不可 confirmed  │ test_fixture/report_derived；      │                                        │                                │ derived only 反證                │
  │                                     │                                │ _source_can_confirm() 要           │                                        │                                │                                  │
  │                                     │                                │ persistent family 且非 non-        │                                        │                                │                                  │
  │                                     │                                │ persistent；confirmed 要 watchlist │                                        │                                │                                  │
  │                                     │                                │ + market/sector fresh persistent   │                                        │                                │                                  │
  │                                     │                                │ source                             │                                        │                                │                                  │
  │ services/                           │ cross-day memory 只採 DB       │ PERSISTENT_SOURCE_TABLES           │ PASS                                   │ local same-run event 變成跨日  │ QA 反證 clean runner + local     │
  │ cross_day_context.py::build_cross_d │ persistent tables；同 run      │ whitelist；today_position_events   │                                        │ 記憶會影響隔日判斷             │ today events mixed-source        │
  │ ay_contexts                         │ today events 不升格為跨日      │ 只寫 same_run_*；無 DB source 時   │                                        │                                │                                  │
  │                                     │ source_of_truth                │ status missing-source/             │                                        │                                │                                  │
  │                                     │                                │ insufficient-data/source-error，   │                                        │                                │                                  │
  │                                     │                                │ previous fields reset              │                                        │                                │                                  │
  │ core/                               │ generator 使用 cross-day       │ generate_report() 用               │ PASS                                   │ DB error 若仍保留 partial      │ QA 針對 partial rows +           │
  │ generator.py::cross_day_contexts    │ context，但 source-error 時不  │ build_cross_day_contexts(client=ge │                                        │ rows，summary / sorting 會假歷 │ position_events error 反證       │
  │ consumer                            │ 產生 previous state/action/    │ t_supabase_client())，exception    │                                        │ 史                             │                                  │
  │                                     │ weight                         │ fallback client=None；context      │                                        │                                │                                  │
  │                                     │                                │ status 非 ready 時 builder 清空    │                                        │                                │                                  │
  │                                     │                                │ historical fields                  │                                        │                                │                                  │
  │ .github/workflows/stock-bot.yml +   │ GitHub fresh runner 由 git     │ workflow checkout、install         │ PASS                                   │ 若 runner 依賴 local cache /   │ QA 檢查 no local file state 被用 │
  │ main.py                             │ checkout + secrets 建          │ requirements、用 secrets 建 TOKEN/ │                                        │ worktree state，正式 TG 不可重 │ 作 source-of-truth               │
  │                                     │ config.py，不帶本地 runtime 狀 │ CHAT_ID/SUPABASE_URL/              │                                        │ 建                             │                                  │
  │                                     │ 態                             │ SUPABASE_KEY，執行 python main.py; │                                        │                                │                                  │
  │                                     │                                │ main.py 呼叫 generate_report() +   │                                        │                                │                                  │
  │                                     │                                │ send_many()                        │                                        │                                │                                  │
  │ public.market_theme_confirmed_evide │ schema artifact exists, but    │ db/sql/                            │ READ_ONLY_ONLY                         │ fresh runner 可能永久 absent / │ Owner-approved writer /          │
  │ nce                                 │ production writer /            │ evidence_phase_4_market_theme_conf │                                        │ missing-source；不能證明       │ ingestion / backfill / RLS /     │
  │                                     │ ingestion / backfill not found │ irmed_evidence.sql 建 table/index/ │                                        │ production confirmed data 可產 │ smoke 任務                       │
  │                                     │ in audited code                │ check；rg insert/upsert/table 只找 │                                        │ 生                             │                                  │
  │                                     │                                │ 到 services/                       │                                        │                                │                                  │
  │                                     │                                │ market_theme_evidence_store.py     │                                        │                                │                                  │
  │                                     │                                │ select reader，未找到 writer       │                                        │                                │                                  │
  │ services/                           │ loader read-only，confirmed 條 │ TABLE_NAME; _confirmed_row() 要    │ PASS                                   │ 若條件漂移，strong 可能被誤收  │ QA 反證 enum / stale /           │
  │ market_theme_evidence_store.py      │ 件符合 TASK baseline           │ support_level in                   │                                        │ 為 confirmed                   │ rejected / weak                  │
  │                                     │                                │ {'confirmed','supporting'} +       │                                        │                                │                                  │
  │                                     │                                │ evidence_status='confirmed' +      │                                        │                                │                                  │
  │                                     │                                │ freshness='fresh'; unsupported     │                                        │                                │                                  │
  │                                     │                                │ support level -> source-error      │                                        │                                │                                  │
  │ public.market_theme_confirmed_evide │ SQL 明確未配置 RLS /           │ SQL header: RLS / permissions      │ UNKNOWN_NEEDS_ARCHITECT_OR_OWNER_INPUT │ GitHub runner 可能無權讀表，導 │ Owner 批准 production read-only  │
  │ nce RLS / read-only role            │ permissions；本輪未做          │ environment-specific，manual       │                                        │ 致 source-error / absent       │ role / RLS verification          │
  │                                     │ production role smoke          │ decide before exposing table       │                                        │                                │                                  │
  │ market_theme raw source -> writer   │ End-to-end incomplete: raw     │ raw source: no implemented         │ BLOCKED                                │ 若當成完整鏈路，後續 evidence  │ 先開 market_theme evidence       │
  │ -> table -> loader -> provider ->   │ source / writer / ingestion /  │ producer found；writer: none       │                                        │ chain 會建立在空表或不可讀表上 │ ingestion/backfill/RLS/prod      │
  │ Telegram -> strategy boundary       │ backfill / production smoke    │ found；table: SQL exists；loader:  │                                        │                                │ smoke 任務，再恢復下一階段       │
  │                                     │ missing；loader/provider/      │ load_confirmed_market_theme_eviden │                                        │                                │                                  │
  │                                     │ Telegram display boundary      │ ce; provider:                      │                                        │                                │                                  │
  │                                     │ present                        │ build_market_theme_evidence_provid │                                        │                                │                                  │
  │                                     │                                │ er; Telegram:                      │                                        │                                │                                  │
  │                                     │                                │ format_market_theme_summary_lines; │                                        │                                │                                  │
  │                                     │                                │ boundary: limitations include 不改 │                                        │                                │                                  │
  │                                     │                                │ 個股買點 / 不改核心交易門檻        │                                        │                                │                                  │
  │ positions                           │ writer 是 Telegram execution   │ supabase/functions/telegram-       │ PASS                                   │ writer / reader 斷裂會讓持倉建 │ QA 反證 function path 與 Python  │
  │                                     │ function；reader 是            │ execution/index.ts insert          │                                        │ 議不可用                       │ reader table/fields 是否一致     │
  │                                     │ position_store; generator /    │ position_events and update         │                                        │                                │                                  │
  │                                     │ formatter 直接消費             │ positions; services/               │                                        │                                │                                  │
  │                                     │                                │ position_store.py selects          │                                        │                                │                                  │
  │                                     │                                │ positions; core/generator.py loads │                                        │                                │                                  │
  │                                     │                                │ into holdings                      │                                        │                                │                                  │
  │ position_events                     │ writer 是 Telegram execution   │ TS function inserts                │ PASS                                   │ 今日買賣 guard / sell pct /    │ QA 反證 source-error 不被當 0    │
  │                                     │ function；reader 是            │ position_events;                   │                                        │ same-day guard 失準            │ event                            │
  │                                     │ position_store /               │ load_today_position_events()       │                                        │                                │                                  │
  │                                     │ cross_day_context; generator   │ selects today rows;                │                                        │                                │                                  │
  │                                     │ 多處消費 today events          │ cross_day_context._fetch_event_row │                                        │                                │                                  │
  │                                     │                                │ s() reads history; generator       │                                        │                                │                                  │
  │                                     │                                │ passes position_events into        │                                        │                                │                                  │
  │                                     │                                │ render / holding logic             │                                        │                                │                                  │
  │ daily_signal_snapshot               │ writer exists；reader exists； │ record_daily_snapshots() upserts   │ CONDITIONAL                            │ 若 snapshot 缺或版本不足，     │ 另開 data coverage audit /       │
  │                                     │ used for backtest context and  │ daily_signal_snapshot; scripts/    │                                        │ backtest/cross-day context 降  │ backfill dry-run approval if     │
  │                                     │ cross-day previous state       │ backfill_signals.py can upsert;    │                                        │ 級；不應 fake ready            │ needed                           │
  │                                     │                                │ load_backtest_context() and        │                                        │                                │                                  │
  │                                     │                                │ build_cross_day_contexts() select  │                                        │                                │                                  │
  │                                     │                                │ it                                 │                                        │                                │                                  │
  │ daily_price                         │ writer exists；reader exists   │ daily_snapshot_store._price_payloa │ CONDITIONAL                            │ 缺 price rows 會讓 backtest    │ QA 反證 no price rows -> no      │
  │                                     │ for backtest context; only     │ d() requires open/high/low/close/  │                                        │ context empty；不應補假績效    │ backtest context, not fake       │
  │                                     │ complete OHLCV written         │ volume; record_daily_snapshots()   │                                        │                                │ positive                         │
  │                                     │                                │ upserts daily_price;               │                                        │                                │                                  │
  │                                     │                                │ load_backtest_context() selects    │                                        │                                │                                  │
  │                                     │                                │ stock_id,trade_date,close          │                                        │                                │                                  │
  │ market_daily_bars                   │ writer exists in strategy      │ record_strategy_evidence() upserts │ WRITE_ONLY                             │ 表存在但未被 TG / strategy 直  │ 另開 DB consumption cleanup /    │
  │                                     │ evidence / backfill; no        │ market_daily_bars; scripts/        │                                        │ 接消費，可能讓 Owner 誤以為已  │ reader design 任務               │
  │                                     │ production reader found in     │ backfill_signals.py upserts;       │                                        │ 用於 evidence 判斷             │                                  │
  │                                     │ generator path                 │ load_strategy_evidence_summary()   │                                        │                                │                                  │
  │                                     │                                │ does not read it                   │                                        │                                │                                  │
  │ strategy_feature_snapshots          │ writer + reader + formatter/   │ record_strategy_evidence() and     │ PASS                                   │ 若表缺資料，strategy evidence  │ QA 反證 schema missing error     │
  │                                     │ context consumer exist         │ backfill upsert;                   │                                        │ summary 樣本不足，不應影響     │ text remains non-blocking to     │
  │                                     │                                │ load_strategy_evidence_summary()   │                                        │ core decision                  │ main report                      │
  │                                     │                                │ reads; cross_day_context reads;    │                                        │                                │                                  │
  │                                     │                                │ Telegram summary can include       │                                        │                                │                                  │
  │                                     │                                │ strategy evidence                  │                                        │                                │                                  │
  │ strategy_outcome_metrics            │ reader exists, production      │ load_strategy_evidence_summary()   │ CONDITIONAL                            │ GitHub fresh runner may read   │ 另開 outcome writer/backfill     │
  │                                     │ writer not in                  │ and cross_day_context read;        │                                        │ stale/empty outcome metrics    │ status audit                     │
  │                                     │ record_strategy_evidence;      │ scripts/backfill_signals.py writes │                                        │ unless backfill has run        │                                  │
  │                                     │ backfill writer exists         │ outcome rows;                      │                                        │                                │                                  │
  │                                     │                                │ record_strategy_evidence()         │                                        │                                │                                  │
  │                                     │                                │ currently does not upsert outcome  │                                        │                                │                                  │
  │                                     │                                │ metrics                            │                                        │                                │                                  │
  │ strategy_classification_audit       │ writer + reader exist;         │ record_strategy_evidence() and     │ CONDITIONAL                            │ Audit rows may display         │ 另開 classification audit        │
  │                                     │ formatter-only/audit trace     │ backfill upsert audit rows;        │                                        │ classification warning but not │ consumption design if it should  │
  │                                     │                                │ load_strategy_evidence_summary()   │                                        │ prove strategy corrected       │ influence decisions              │
  │                                     │                                │ reads latest audit;                │                                        │                                │                                  │
  │                                     │                                │ cross_day_context fetches but does │                                        │                                │                                  │
  │                                     │                                │ not add to context_sources         │                                        │                                │                                  │
  │ signal_runs / signal_items /        │ writer exists; mostly signal   │ record_daily_signals() inserts     │ REFERENCE_ONLY                         │ Existing DB data may not       │ 另開 signal history consumption  │
  │ signal_outcomes                     │ history / outcome maintenance; │ runs/items; update_due_outcomes()  │                                        │ influence current strategy     │ task if Owner wants strategy use │
  │                                     │ not direct generator strategy  │ inserts outcomes;                  │                                        │ despite being stored           │                                  │
  │                                     │ source in audited path         │ cross_day_context.PERSISTENT_SOURC │                                        │                                │                                  │
  │                                     │                                │ E_TABLES whitelists them but       │                                        │                                │                                  │
  │                                     │                                │ builder does not fetch them        │                                        │                                │                                  │
  │ services/signal_store.py            │ production daily signal writer │ generate_report() calls            │ CONDITIONAL                            │ Live write side effects remain │ QA should not require live DB    │
  │                                     │ can write DB, but this audit   │ record_daily_signals() during      │                                        │ outside audit; failures append │ write without Owner approval     │
  │                                     │ did not execute it             │ report generation; this Tech run   │                                        │ DB warning only                │                                  │
  │                                     │                                │ did not call generate_report() or  │                                        │                                │                                  │
  │                                     │                                │ live DB                            │                                        │                                │                                  │
  │ services/daily_snapshot_store.py    │ daily snapshot writer can      │ generate_report() calls            │ CONDITIONAL                            │ Snapshot gaps reduce future    │ Data coverage/backfill task with │
  │                                     │ write DB, but this audit did   │ record_daily_snapshots(); writer   │                                        │ backtest/cross-day evidence    │ Owner approval                   │
  │                                     │ not execute it                 │ requires phase / weekday /         │                                        │                                │                                  │
  │                                     │                                │ complete watchlist / valid         │                                        │                                │                                  │
  │                                     │                                │ snapshots                          │                                        │                                │                                  │
  │ services/strategy_evidence.py       │ strategy evidence write/read   │ generator comment states evidence  │ PASS                                   │ If future code consumes        │ QA grep for direct decision      │
  │                                     │ is non-decision support;       │ layer does not loosen decisions;   │                                        │ evidence as decision input,    │ threshold changes around         │
  │                                     │ formatter summary only         │ summary formatting returns sample/ │                                        │ current audit conclusion       │ evidence consumers               │
  │                                     │                                │ audit text; no BUY/SELL threshold  │                                        │ becomes stale                  │                                  │
  │                                     │                                │ writes found                       │                                        │                                │                                  │
  │ tests/* direct evidence             │ Existing tests cover key fail- │ Ran targeted tests: tests/         │ PASS                                   │ Tests are local/mocked, not    │ QA still needs independent反證,  │
  │                                     │ closed contracts               │ test_position_store.py, tests/     │                                        │ production data smoke          │ not just rerun                   │
  │                                     │                                │ test_cross_day_context.py, tests/  │                                        │                                │                                  │
  │                                     │                                │ test_market_theme_evidence.py,     │                                        │                                │                                  │
  │                                     │                                │ tests/test_strategy_evidence.py => │                                        │                                │                                  │
  │                                     │                                │ 41 passed                          │                                        │                                │                                  │
  └─────────────────────────────────────┴────────────────────────────────┴────────────────────────────────────┴────────────────────────────────────────┴────────────────────────────────┴──────────────────────────────────┘

  ## 未影響模組

  - 策略門檻：未改。
  - Telegram formatter / message list / payload：未改。
  - DB schema / SQL / RLS / role：未改。
  - Watchlist：未改。
  - Runner / GitHub workflow：未改。
  - Live Telegram：未執行。
  - Live Supabase write：未執行。
  - Replay / backfill：未執行。

  ## 已跑自檢命令

  - git diff --check：通過，無輸出。
  - git diff --stat：產品代碼 / 測試 / SQL / runner 無輸出；本輪只有交付文件 diff。
  - git status --short：交付期間顯示 `M CHANGELOG.md` / `M TASK.md`，屬本輪審計文件更新；無產品代碼、測試、SQL、schema、runner 或策略 diff。
  - PYTHONPATH=. .venv/bin/python -m pytest tests/test_position_store.py tests/test_cross_day_context.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py：首次因 x86_64 Python 載入 arm64 pydantic_core
    失敗，屬本地架構啟動方式問題。
  - PYTHONPATH=. arch -arm64 .venv/bin/python -m pytest tests/test_position_store.py tests/test_cross_day_context.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py：41 passed, 17 warnings。warnings
    為依賴 deprecation / Python 版本警告，非本輪 contract failure。

  ## 殘留風險

  - public.market_theme_confirmed_evidence 端到端鏈路未完成：缺 writer / ingestion / backfill / RLS read-only role / production data smoke。
  - 本輪未連 production DB，無法證明正式表有資料、runner role 可讀、RLS policy 正確。
  - strategy_outcome_metrics 在 production report path 主要是 reader；writer 目前可見於 backfill script，fresh runner 是否持續生成 outcome metrics 仍是 conditional。
  - market_daily_bars 有 writer 但未找到正式 generator reader，屬 write-only / reference-only 風險。
  - signal_runs / signal_items / signal_outcomes 已寫入和維護，但目前不是 generator cross-day builder 的實際 fetch source；若 Owner 期待策略消費，需要另開任務。
  - 局部測試是 mocked/local，不等於 QA 通過，也不等於 production smoke。

  ## 旁支待辦

  - 另開 Owner-approved 任務：market_theme_confirmed_evidence writer / ingestion / backfill 設計與實作。
  - 另開 Owner-approved 任務：production RLS / read-only role / GitHub runner actual data smoke。
  - 另開 audit / cleanup 任務：分類 market_daily_bars、signal_runs/items/outcomes 是否要成為策略 reader source，或明確標示 reference-only。
  - 另開 data coverage 任務：確認 strategy_outcome_metrics 的正式 writer/backfill 狀態與 freshness。
  - 另開 runner/env 改善：測試命令需固定 arch -arm64 或提供 worktree-native venv，避免架構誤啟動。
