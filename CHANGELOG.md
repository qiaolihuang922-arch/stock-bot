# CHANGELOG: write CLI Supabase credentials env/config fallback

  ## 任務尺寸與風險

  - 任務尺寸: normal_patch
  - 風險判斷: 局部 CLI / evidence store credential resolution 修復；不改 DB schema、不 live write、不改策略 decision、不改 Telegram 報文、不改 VERSION。

  ## 修改內容

  - services.market_theme_evidence_store 新增 write credential resolution：
      - SUPABASE_URL: env 優先，缺失時 fallback config.SUPABASE_URL
      - service key: env SUPABASE_SERVICE_ROLE_KEY 優先，缺失時 fallback config.SERVICE_ROLE_KEY，再 fallback config.SUPABASE_SERVICE_ROLE_KEY
      - 缺配置時 fail closed，不建立 partial client
      - validation output 只回傳 url_source / key_source / missing，不回傳 URL 或 key value
  - scripts/write_market_theme_confirmed_evidence.py 改為使用 sanitized credential validation 結果輸出 execute 狀態。
  - 補測 env/config 隔離 fixture：
      - 無 env + fake config SERVICE_ROLE_KEY 可 execute fake client
      - 無 env + fake config SUPABASE_SERVICE_ROLE_KEY alias 可 execute fake client
      - env 與 config 同時存在時 build client 使用 env sentinel
      - 全缺時 fail closed，且 stdout 不含 URL/key value

  ## 修改檔案

  - services/market_theme_evidence_store.py
  - scripts/write_market_theme_confirmed_evidence.py
  - tests/test_market_theme_evidence_handoff.py

  ## 最小改動策略

  - 只改 TASK.md 指定的 write CLI、evidence store write helper、直接相關測試。
  - 未重構 credential 架構，未改 read-only loader _build_client，未改其他 Supabase consumers。
  - 測試全部使用 fake config module / fake Supabase client / fake write client，未觸發真 Supabase write。

  ## 契約影響

  - validate_market_theme_write_env(env=None, config_module=...) output 增加 sanitized url_source、key_source，missing 的 service key 名稱改為 SUPABASE_SERVICE_ROLE_KEY|SERVICE_ROLE_KEY 以反映 alias contract。
  - build_market_theme_write_client(env=None, config_module=...) 兼容 optional config module injection；既有呼叫不傳第二參數仍正常讀 env，再 fallback repo config.py。
  - CLI execute JSON 的 env_validation 現在顯示 sanitized source status，不顯示 secret value。
  - message list、Telegram payload、DB payload schema、upsert rows、formatter header、VERSION 未改。

  ## 直接消費者同步

  - CLI consumer: scripts/write_market_theme_confirmed_evidence.py 已同步使用 store 的 sanitized validation 與 config fallback client builder。
  - evidence store caller: build_market_theme_write_client 仍由 CLI 呼叫，新增 fallback 不改 upsert contract。
  - 測試 consumer: tests/test_market_theme_evidence_handoff.py 已同步缺配置、config fallback、env precedence、secret redaction 期望。
  - rg 顯示 validate_market_theme_write_env / build_market_theme_write_client 直接產品呼叫方限於 write CLI；未發現其他產品呼叫方需同步。

  ## 未影響模組

  - 未改 market theme 策略判斷。
  - 未改 evidence DB schema、table、RLS、grant、policy、role。
  - 未改 production payload schema 或 upsert conflict target。
  - 未執行 live Supabase write、正式 backfill、live Telegram。
  - 未改 Telegram formatter、報文分組、VERSION、watchlist、replay/backfill。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q
      - 結果: 25 passed in 1.01s
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q
      - 結果: 46 passed, 17 warnings in 1.39s
      - warnings 為既有第三方 deprecation / Python 3.9 warnings。
  - git diff --check
      - 結果: passed
  - PYTHONPYCACHEPREFIX=/private/tmp/stock-bot-tech-pycache arch -arm64 .venv/bin/python -m py_compile services/market_theme_evidence_store.py scripts/write_market_theme_confirmed_evidence.py tests/
    test_market_theme_evidence_handoff.py
      - 結果: passed
      - 備註: 未設 PYTHONPYCACHEPREFIX 的第一次 py_compile 被 macOS Python 寫入 /Users/liveroom/Library/Caches/... 權限擋住，改用可寫 pycache prefix 後通過。

  ## 殘留風險

  - 本輪只驗 fake client path，未對真 Supabase 執行 --execute，符合禁止 live write 邊界。
  - config.py 的正式 secret 管理命名仍存在歷史差異，本輪只補 TASK 指定的 SERVICE_ROLE_KEY / SUPABASE_SERVICE_ROLE_KEY write fallback，未做全 repo credential refactor。

  ## 旁支待辦

  - 若後續要統一全 repo Supabase credential naming，可另開 credential config cleanup 任務。
  - 若要 production 寫入，需由上游準備 approved persistent payload，先 dry-run，再在明確允許的環境使用既有 CLI --execute。
