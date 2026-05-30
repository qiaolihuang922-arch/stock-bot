# CHANGELOG: market/theme production evidence trend fresh-run consumption check

  ## 任務尺寸與風險

  - 任務尺寸: normal_patch
  - 風險判斷: 不改策略、不改 Telegram/report 文案、不改 header、不寫 DB；風險集中在正式 generator/report path 的只讀 consumption verification contract。

  ## 修改內容

  - 在 core/generator.py 新增 build_market_theme_production_trend_consumption_check()，輸出 TASK 指定的 fresh-run consumption verification report。
  - market_theme_summary_evidence() 增加可選 evidence_loader 注入，用於 mocked persistent DB rows 的 fresh-run 等價驗證；既有呼叫方式不變。
  - 在 scripts/smoke_market_theme_evidence_readonly.py 新增 --production-trend-consumption-check-json，輸出只讀 JSON report；缺 read credentials 時 fail closed 為 missing-source，不嘗試二次建真實 DB client。
  - 補測試確認正式 generator path 消費 market_theme_confirmed_evidence trend，且 daily_signal_snapshot 即使存在也不被查詢或包裝成 trend source。

  ## 修改檔案

  - core/generator.py
  - scripts/smoke_market_theme_evidence_readonly.py
  - tests/test_market_theme_evidence.py

  ## 最小改動策略

  - 只沿用既有 load_confirmed_market_theme_evidence()、market_theme_summary_evidence()、provider 與 read-only smoke script。
  - 沒有新增 provider、workflow、historical source、DB schema、production write path 或 Telegram 顯示文案。
  - 沒有修改 VERSION，符合 TASK 的「本輪不改使用者可見 header / report 文案」契約。

  ## 契約影響

  - 新增只讀 diagnostic JSON contract:
      - mode=market-theme-production-trend-consumption-check
      - schema_change=false
      - data_write=false
      - live_telegram=false
      - source_of_truth=production.market_theme_confirmed_evidence
      - generator_consumption.uses_market_theme_confirmed_evidence_history
      - generator_consumption.uses_only_daily_signal_snapshot=false
      - generator_consumption.uses_runtime_or_local_cache_as_history=false
      - table_status.sector_theme_members=latest-only-blocked
      - table_status.market_theme_index_daily_bars=not-consumed
  - market_theme_summary_evidence() public helper 只新增 backward-compatible optional parameter；既有呼叫方不需改。
  - 未改 Telegram message list、payload、報文分組、排序、header、買賣策略 decision、DB 寫入 contract。

  ## 直接消費者同步

  - Telegram/report generator: consumption check 走 core.generator.market_theme_summary_evidence 等價正式報文 evidence path。
  - Read-only smoke CLI: 新增 --production-trend-consumption-check-json 供 Architect/QA 讀 JSON 結果。
  - QA: 測試 fixture 提供 fresh-run mocked persistent DB rows，並反證 daily_signal_snapshot 不被當 market/theme trend source。
  - 既有 ai_supply_chain_mainline_supported()、formatTelegramSummary()、formatTelegramMessages() 呼叫不變，無需同步輸出文案。

  ## 未影響模組

  - 未改策略買賣門檻、持倉狀態機、watchlist。
  - 未改 Telegram live delivery。
  - 未改 DB schema / table / column / RLS / grant / policy / role。
  - 未做 production data write、backfill、live Supabase write。
  - 未偽造五月歷史，未把 sector_theme_members latest-only 回填為五月 history。
  - 未把 market_theme_index_daily_bars 標成 consumed。

  ## 已跑自檢命令

  - .venv/bin/python -m pytest tests/test_market_theme_evidence.py -q
      - 結果: blocked by local architecture mismatch，pydantic_core arm64 wheel 被 x86_64 Python 載入失敗。
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py -q
      - 結果: 98 passed, 153 warnings
  - git diff --check
      - 結果: passed

  ## 殘留風險

  - 本輪使用 mocked persistent DB rows 驗證 fresh-run 等價路徑；未呼叫真實 production DB API，避免 Tech 階段 live 外部副作用。
  - 真實 GitHub runner 是否具備 read credentials、production rows 是否足夠，仍需 QA/Architect 在允許的 read-only 環境確認。
  - sector_theme_members 仍是 latest-only blocked；完整五月 historical source 仍未補。

  ## 旁支待辦

  - 後續若要證明完整五月 trend，需要另開 historical source 任務。
  - 後續若要消費 market_theme_index_daily_bars，需先由 PM 定義直接 consumer 與驗收條件。
  - 若 production runner 缺 read env 或 rows 不足，應維持 missing-source / insufficient-data，不得降級使用 local/runtime/cache。
