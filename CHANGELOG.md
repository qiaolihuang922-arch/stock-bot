# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - 風險判斷：新增 read-only production DB consumption / loader，並接到 market/theme evidence provider 與 Telegram summary；不改策略買賣門檻、不改 DB schema、不寫 DB、不 backfill、不 live Telegram。

  ## 修改內容

  - 新增 services/market_theme_evidence_store.py read-only loader，讀取 public.market_theme_confirmed_evidence。
  - Loader 只在同時滿足 support_level in ('confirmed', 'supporting')、evidence_status='confirmed'、freshness='fresh' 時回傳 confirmed。
  - Loader 可區分 confirmed、absent、missing-source、source-error、insufficient-data。
  - support_level=strong 視為 unexpected enum，fail closed 為 source-error，不轉譯、不兼容。
  - core/generator.py 接入 loader；GitHub fresh runner path 可只靠 production DB read-only source 重建 confirmed / fail-closed 判斷。
  - Telegram 使用者可見版本升至 v20.4.3。
  - confirmed evidence summary 改為手機短句：證據：production confirmed，市場/題材支持成立。

  ## 修改檔案

  - services/market_theme_evidence_store.py
  - core/market_theme_evidence.py
  - core/generator.py
  - tests/test_market_theme_evidence.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 只新增一個 read-only loader service，沿用既有 build_market_theme_evidence_provider() 與 Telegram formatter contract。
  - 未重構 DB layer、watchlist、position state、strategy evidence、backfill scripts。
  - 未新增本地持久狀態；loader 不寫 cache，不依賴 agent 對話或 worktree fixture 作 confirmed source。

  ## 契約影響

  - 新增 loader result contract：status、confirmed、source_of_truth=production_db、source_status、sources、rows。
  - Provider 保留 loader fail-closed status，避免把 absent/source-error/missing-source/insufficient-data 壓成泛用狀態。
  - Telegram header 版本：v20.4.3。
  - Telegram evidence summary confirmed wording 有變；message list 順序未改。
  - DB payload / write path 未改；無 Supabase write。

  ## 直接消費者同步

  - core/generator.py：market_theme_summary_evidence() 直接使用 loader result。
  - core/market_theme_evidence.py：provider 接受 loader confirmed sources 與 fail-closed statuses。
  - tests/test_market_theme_evidence.py：覆蓋 loader contract、provider consumer、strong fail-closed、summary wording。
  - tests/test_generator_report.py：同步 v20.4.3 header 期望。

  ## 未影響模組

  - 策略 BUY / SELL / 加減碼門檻：未改。
  - DB schema / RLS / migration：未改。
  - Supabase live write：未執行。
  - Backfill / replay：未執行。
  - Telegram live delivery：未執行。
  - Watchlist、position store、cross-day context、signal write path：未改。

  ## 已跑自檢命令

  - PYTHONPATH=.qa_tmp arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py：93 passed, 161 warnings。
  - git diff --check：passed。
  - 備註：本機 python 不存在，系統 python3 無 pytest；.venv 預設 x86_64 會遇到 arm64 pydantic_core 架構不符，因此用 arch -arm64 跑測試。.qa_tmp/config.py 是本地測試 shim，未納入 git diff。

  ## 殘留風險

  - 未連 production DB；loader production 權限 / RLS / 實際資料內容仍需 QA 或 Owner 在可用 production read-only 環境驗證。
  - Query 目前取 latest rows 後在程式 fail closed 驗證；若 production 同日同題材有多筆互相衝突資料，仍依最新可用 confirmed row 收斂，後續可另開任務定義衝突優先級。

  ## 旁支待辦

  - Production read-only role / RLS policy 尚未驗證。
  - Writer / backfill / ingestion 不在本輪。
  - CURRENT_STATE.md 仍顯示上一版 v20.4.2，需由 Architect 收口文件時更新。
