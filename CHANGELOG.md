# CHANGELOG: data-authenticity-hardening-fail-closed

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 風險判斷：改到 production runtime 的 evidence / holdings / Telegram summary fail-closed 行為與可見版本字串，因此升 patch 到 v20.3.1。

  ## 修改內容

  - 移除持倉來源不可用時的 0 股 fallback；load_positions() 在缺 Supabase 設定、DB 讀取失敗、positions 0 rows 時改回 {} 並標示 missing-source / source-error / unavailable。
  - position_events source-error / missing-source 不再回全 0 event summary；只有 DB query 成功且空資料才視為今日真實無事件。
  - generate_report() 在持倉或今日交易事件來源不可用時直接 fail closed，輸出最小 Telegram summary：新倉無有效進場、持倉 unavailable、市場證據 unavailable，不再繼續掃行情產生交易建議。
  - watchlist breadth runtime fallback 不再進入 sources、不再產生 weak/runtime、不再影響 confirmed / actionability；只保留為 watchlist_breadth_diagnostic 非交易診斷。
  - formatter 對缺 DB evidence/cache 的市場/題材證據輸出 absent/missing-source，並顯示 watchlist breadth fallback 已停用於決策。
  - core/generator.py 使用者可見版本由 v20.3.0 升到 v20.3.1。
  - 新增/同步 fail-closed、formatter、版本 header 測試。

  ## 修改檔案

  - core/generator.py
  - core/market_theme_evidence.py
  - services/position_store.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tests/test_notifier.py
  - tests/test_position_store.py

  ## 最小改動策略

  - 只處理 TASK.md 指定的 runtime fake/fallback 風險點：holdings fallback、position_events source-error 與 watchlist breadth evidence fallback。
  - 未重構 strategy、watchlist、DB schema、Supabase function、stock API adapter 或 replay/backfill 工具。
  - tests fixture 保留，只新增直接消費者回歸測試。

  ## 契約影響

  - Telegram header：v20.3.0 -> v20.3.1。
  - services.position_store.load_positions()：來源不可用時不再回傳全 watchlist 0 股資料，改回 {} 並設 warning。
  - services.position_store.load_today_position_events()：DB query 成功空資料仍回真實 0 event summary；missing-source / source-error 回 unavailable metadata 並設 warning。
  - core.generator.generate_report()：持倉或今日交易事件來源 warning 存在時回傳 fail-closed message list，不產生正常交易/持倉/可買 summary。
  - core.market_theme_evidence.build_market_theme_evidence()：DB evidence/cache 缺失且無真實 structured source 時為 absent；runtime watchlist breadth 僅在 watchlist_breadth_diagnostic，不列入 sources / confirmed。
  - Telegram 市場證據文案：移除 市場證據：weak/runtime / 題材證據：weak/runtime，改為 absent/missing-source。

  ## 直接消費者同步

  - Telegram message formatter / generator：formatTelegramMessages()、formatTelegramSummary()、generate_report() 測試已同步 v20.3.1 與 fail-closed summary；position_events source-error 不會顯示為 今日無交易。
  - production strategy decision path：未改 strategy decision；缺持倉來源時 generator 在 strategy 掃描前停止。
  - DB repository / Supabase adapter：position_store 缺來源不再 fake 0 股，position_events source-error 不再 fake 0 event；未改 schema 或 live write。
  - evidence chain builder：market_theme_evidence 不再把 runtime breadth fallback 當 source-of-truth。
  - CLI / dry-run report output：generate() 經 generate_report() 同步 fail-closed；既有行情全失敗測試補 mock 持倉來源以保留行情 unavailable 覆蓋。
  - notifier：版本 header 測試同步到 v20.3.1。

  ## Tech 證據表

  ┌───────────────────────────────┬───────────────────────────────────┬─────────────────────────────┬───────────────────┬───────────────────────────────────────────┬───────────────────┬───────────────┬──────────────────┐
  │ path                          │ function                          │ keyword                     │ rg evidence       │ import-or-call path                       │ classification    │ risk          │ action           │
  ├───────────────────────────────┼───────────────────────────────────┼─────────────────────────────┼───────────────────┼───────────────────────────────────────────┼───────────────────┼───────────────┼──────────────────┤
  │ services/position_store.py    │ load_positions                    │ fallback                    │ 原本              │ core/generator.py -> load_positions()     │ runtime_reachable │ 缺 DB/設定時  │ 移除 fallback，  │
  │                               │                                   │                             │ _fallback_positio │                                           │                   │ 假裝全 0 股， │ 改 {} +          │
  │                               │                                   │                             │ ns() / 使用 0 股  │                                           │                   │ 可能產生新倉/ │ warning；        │
  │                               │                                   │                             │ fallback          │                                           │                   │ 持倉錯誤結論  │ generator fail   │
  │                               │                                   │                             │                   │                                           │                   │               │ closed           │
  │ services/position_store.py    │ load_today_position_events        │ empty event fallback        │ 原本 exception    │ core/generator.py -> load_today_position_ │ runtime_reachable │ DB error 被當 │ source-error 回  │
  │                               │                                   │                             │ 回 _empty_event_  │ events()                                  │                   │ 今日 0 event  │ unavailable；DB  │
  │                               │                                   │                             │ summary           │                                           │                   │               │ query 成功空資料 │
  │                               │                                   │                             │                   │                                           │                   │               │ 才回真 0 event   │
  │ core/generator.py             │ generate_report                   │ unavailable                 │ 新增持倉 warning  │ runtime Telegram / CLI generate path      │ runtime_reachable │ 持倉來源缺失  │ 持倉 missing/    │
  │                               │                                   │                             │ 後停止            │                                           │                   │ 仍繼續出交易  │ source-error/    │
  │                               │                                   │                             │                   │                                           │                   │ 建議          │ unavailable 時回 │
  │                               │                                   │                             │                   │                                           │                   │               │ 最小不可行動     │
  │                               │                                   │                             │                   │                                           │                   │               │ summary          │
  │ core/market_theme_evidence.py │ build_market_theme_evidence       │ fallback, runtime_fallback  │ runtime_fallback  │ generator.market_theme_summary_evidence() │ runtime_reachable │ watchlist     │ 改為 non-trading │
  │                               │                                   │                             │ 不再由 runtime    │                                           │                   │ breadth       │ diagnostic，不進 │
  │                               │                                   │                             │ breadth 產生      │                                           │                   │ fallback 被當 │ sources，不      │
  │                               │                                   │                             │                   │                                           │                   │ 市場證據      │ confirmed        │
  │ core/market_theme_evidence.py │ format_market_theme_summary_lines │ weak/runtime                │ 舊 weak/runtime   │ Telegram summary                          │ runtime_reachable │ 缺 DB/cache   │ 改 absent/       │
  │                               │                                   │                             │ 分支已移除        │                                           │                   │ 時文案像弱證  │ missing-source   │
  │                               │                                   │                             │                   │                                           │                   │ 據成立        │                  │
  │ core/generator.py             │ price fallback error text         │ fallback                    │ yahoo_error；     │ stock API real-source retry               │ runtime_reachable │ 可能誤判為假  │ 保留；這是 TWSE/ │
  │                               │                                   │                             │ fallback          │                                           │                   │ 資料 fallback │ Yahoo 真實來源   │
  │                               │                                   │                             │ twse_error；      │                                           │                   │               │ retry，不是 fake │
  │                               │                                   │                             │ retry...          │                                           │                   │               │ data             │
  │ scripts/dry_run_replay.py     │ synthetic_history, main           │ synthetic, dry_run          │ --source          │ manual dry-run script only                │ dry_run_only      │ synthetic     │ 保留；入口強制   │
  │                               │                                   │                             │ synthetic,        │                                           │                   │ replay 若升   │ --dry-run，不寫  │
  │                               │                                   │                             │ requires --dry-   │                                           │                   │ production 會 │ DB               │
  │                               │                                   │                             │ run               │                                           │                   │ 污染結論      │                  │
  │ scripts/backfill_signals.py   │ main                              │ synthetic, dry_run          │ source choices    │ guarded backfill script                   │ dry_run_only      │ synthetic     │ 保留；default 真 │
  │                               │                                   │                             │ include           │                                           │                   │ backfill 寫   │ 實 TWSE，正式寫  │
  │                               │                                   │                             │ synthetic;        │                                           │                   │ DB            │ 入需顯式 confirm │
  │                               │                                   │                             │ default twse;     │                                           │                   │               │                  │
  │                               │                                   │                             │ write needs       │                                           │                   │               │                  │
  │                               │                                   │                             │ --confirm-write   │                                           │                   │               │                  │
  │ services/strategy_evidence.py │ report builders                   │ sample, default, setdefault │ sample count /    │ evidence report                           │ false_positive    │ 無假資料來源  │ 保留             │
  │                               │                                   │                             │ dict helpers      │                                           │                   │               │                  │
  │ services/signal_store.py      │ record_daily_signals              │ default, setdefault         │ JSON serializer / │ DB signal write path                      │ false_positive    │ 無假資料來源  │ 保留             │
  │                               │                                   │                             │ dict grouping     │                                           │                   │               │                  │
  │ core/generator.py             │ backtest summary helpers          │ sample, local_execution     │ sample count /    │ formatter/backtest context                │ false_positive    │ 無假資料來源  │ 保留             │
  │                               │                                   │                             │ callback labels   │                                           │                   │               │                  │
  │ services/analysis.py          │ edge_fake_breakout                │ fake                        │ strategy pattern  │ strategy decision path                    │ false_positive    │ 名稱含 fake， │ 保留             │
  │                               │                                   │                             │ name              │                                           │                   │ 但不是假資料  │                  │
  │ core/condition_engine.py      │ condition labels                  │ fake_breakout               │ condition enum/   │ strategy condition output                 │ false_positive    │ 名稱含 fake， │ 保留             │
  │                               │                                   │                             │ string            │                                           │                   │ 但不是假資料  │                  │
  │ tests/*                       │ fixtures                          │ fixture, mock, sample       │ runtime scan `rg  │ import tests                              │ testdata          │ fixture" core │ no production    │
  │                               │                                   │                             │ "from tests       │                                           │                   │ services      │ import/call path │
  │                               │                                   │                             │                   │                                           │                   │ scripts       │                  │
  │                               │                                   │                             │                   │                                           │                   │ supabase` 無  │                  │
  │                               │                                   │                             │                   │                                           │                   │ 結果          │                  │
  └───────────────────────────────┴───────────────────────────────────┴─────────────────────────────┴───────────────────┴───────────────────────────────────────────┴───────────────────┴───────────────┴──────────────────┘

  註：functions 目錄在此 worktree 不存在；已掃 supabase/functions/telegram-execution/index.ts。

  ## 未影響模組

  - 未改策略分數、買賣條件、持倉狀態機。
  - 未改 DB schema / migration。
  - 未改 watchlist。
  - 未執行 live Supabase write、正式 backfill、live Telegram delivery。
  - 未改 stock API 真實來源 adapter。
  - 未改 Supabase Edge Function。

  ## 已跑自檢命令

  - python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_position_store.py tests/test_notifier.py：失敗，系統 python 不存在。
  - .venv/bin/python -m pytest ...：失敗，pydantic_core arm64 / x86_64 架構不匹配。
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_position_store.py tests/test_notifier.py：88 passed, 13 warnings。
  - arch -arm64 .venv/bin/python -m pytest：162 passed, 13 warnings。
  - git diff --check：通過。
  - rg -n "mock|dummy|sample|fixture|fallback|synthetic|hardcoded|default|fake|placeholder|TODO|testdata|demo|local|dry_run" services core scripts supabase -S：已用於上方證據表。
  - rg -n "from tests|import tests|testdata|fixture" core services scripts supabase -S：無 runtime import/call tests fixture。

  ## 殘留風險

  - scripts/dry_run_replay.py 仍保留 synthetic dry-run replay；目前分類為 dry_run_only，若未來要禁止所有 synthetic even dry-run，需要 PM 另定義。
  - 測試需用 arch -arm64 執行，直接 .venv/bin/python 在目前 runner 架構會遇到 native wheel mismatch。

  ## 旁支待辦

  - 若 Owner 要把 dry-run synthetic replay 也完全移除，需另開清理/流程任務。
  - position_events source-error 已在本輪補為 unavailable contract；後續若要在正常非 fail-closed 報文顯示更細的 unavailable 區塊，可另開 UX 任務。
