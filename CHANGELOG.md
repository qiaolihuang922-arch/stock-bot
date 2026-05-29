# CHANGELOG: Evidence Chain Production Ops Repo-side Artifacts

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 風險判斷：涉及 production ingestion/backfill/RLS/read-only smoke artifact，但本輪只交付 repo 內 non-live artifact；未執行 live write、正式 backfill、production RLS/grant 變更或 Telegram delivery。

  ## 修改內容

  - 新增 ingestion payload dry-run validation helper 與 CLI。
  - 新增 read-only smoke helper 與 CLI；CLI 只接受 SUPABASE_READONLY_KEY，不 fallback service-role key。
  - 新增 Owner manual SQL template，分離 read-only role/grant、RLS policy、backfill/upsert template、read-only verification queries。
  - 新增 handoff docs，標明 repo artifact 與 Owner manual boundary。
  - 補局部測試，覆蓋 fake source 不產生 SQL、validation output、read-only smoke matrix。

  ## 修改檔案

  - services/market_theme_evidence_store.py
  - scripts/validate_market_theme_evidence_ingestion.py
  - scripts/smoke_market_theme_evidence_readonly.py
  - db/sql/evidence_chain_market_theme_ops_manual_template.sql
  - docs/handoff/evidence_chain_market_theme_ops_artifacts.md
  - tests/test_market_theme_evidence_handoff.py

  ## 最小改動策略

  - 沿用既有 build_market_theme_evidence_handoff() validator，不另開 ingestion 判斷分支。
  - 只新增 non-live scripts/docs/sql artifact 與局部 helper。
  - 未碰 core/generator.py、Telegram formatter、策略門檻、watchlist、DB live writer、正式 runner/backfill。

  ## 契約影響

  - 新增 helper：
      - validate_market_theme_evidence_ingestion_payload(payloads, include_sql=False)
      - build_market_theme_evidence_readonly_smoke(load_result)
  - 新增 CLI output contract：
      - validation：valid、may_render_manual_sql、live_write=false、sql_rendered；invalid payload 不輸出 manual_sql。
      - smoke：mode=read-only、write=disabled、status=ok|fail-closed、telegram_confirmed=true|false。
  - 既有 load_confirmed_market_theme_evidence()、Telegram message list、payload、formatter header、VERSION 未改。
  - 版本同步：TASK 指定本輪不升版；未改 Telegram 使用者可見報文與 VERSION。

  ## 直接消費者同步

  - Owner：新增 docs 與 manual SQL template，標明需 Owner approval。
  - QA：新增測試覆蓋 validation / smoke matrix / fake source fail-closed。
  - GitHub fresh runner：提供 read-only smoke CLI artifact；缺 SUPABASE_READONLY_KEY 時 fail closed。
  - core/generator.py / Telegram：未同步修改，因本輪未改既有 loader contract 或報文輸出。

  ## Repo-side vs Owner Manual Boundary

  ┌──────────────────────┬───────────────┬────────────────────────────────────────┬────────────────────────┬────────┐
  │ item                 │ repo artifact │ live side effect                       │ Owner approval needed  │ status │
  ├──────────────────────┼───────────────┼────────────────────────────────────────┼────────────────────────┼────────┤
  │ ingestion validation │ script/helper │ none                                   │ no                     │ ready  │
  │ manual SQL template  │ SQL file      │ none unless Owner executes             │ yes                    │ ready  │
  │ read-only smoke      │ script/helper │ read-only only with Owner-provided env │ yes for production env │ ready  │
  │ RLS verification     │ SQL Step D    │ read-only queries                      │ yes                    │ ready  │
  └──────────────────────┴───────────────┴────────────────────────────────────────┴────────────────────────┴────────┘

  ## Fresh GitHub Runner Smoke Matrix

  ┌───────────────────────────────────────┬───────────────────────────────────────┐
  │ condition                             │ expected                              │
  ├───────────────────────────────────────┼───────────────────────────────────────┤
  │ missing env                           │ fail-closed, telegram_confirmed=false │
  │ permission denied                     │ fail-closed, telegram_confirmed=false │
  │ 0 rows                                │ fail-closed, telegram_confirmed=false │
  │ stale rows                            │ fail-closed, telegram_confirmed=false │
  │ unsupported support_level             │ fail-closed, telegram_confirmed=false │
  │ valid fresh confirmed/supporting rows │ ok, telegram_confirmed=true           │
  └───────────────────────────────────────┴───────────────────────────────────────┘

  ## 未影響模組

  - 策略 decision / BUY / SELL / RR / 加減碼 / 停損停利：未改。
  - Telegram live delivery / formatter / VERSION：未改。
  - Supabase live write / production DB / RLS / grant / role：未執行、未自動化。
  - Watchlist、replay、formal backfill、runner secrets：未改。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q：28 passed, 17 warnings。
  - arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29：exit 2，預期 fail-closed；缺 read-only env，未建 DB client。
  - validation CLI positive `--input` JSON file：exit 0，may_render_manual_sql=true，未要求輸出 SQL。
  - validation CLI fake source `--input` JSON file：exit 2，may_render_manual_sql=false，無 manual_sql。
  - git diff --check：passed。
  - PYTHONPYCACHEPREFIX=/private/tmp/stock_bot_pycache arch -arm64 .venv/bin/python -m py_compile scripts/validate_market_theme_evidence_ingestion.py scripts/smoke_market_theme_evidence_readonly.py：passed。

  ## 殘留風險

  - 未驗證 production RLS/grant 實際結果；需 Owner 手動執行 SQL 後回傳結果。
  - 未做正式 backfill 或 live ingestion；本輪只能表示 artifact ready for Owner manual execution。
  - Smoke 需要 Owner 提供 SUPABASE_URL 與 SUPABASE_READONLY_KEY 才能讀 production。

  ## 旁支待辦

  - Owner 手動決定 read-only role name、policy name、approved source name。
  - Owner 手動批准並執行必要 SQL section。
  - QA 仍需反證無 fake confirmed、無 local state 當 production、無 live write、fresh runner fail-closed。
