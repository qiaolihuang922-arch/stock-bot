# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸: tiny_patch
  - 風險判斷: 只修 scripts/smoke_market_theme_evidence_readonly.py 的 read-only credential fallback；不改策略、Telegram、DB schema、payload、message list、報文分組或 live write path。

  ## 修改內容

  - 新增 read-only smoke credential resolver，解析順序符合 TASK.md:
      - URL: env SUPABASE_URL -> config.SUPABASE_URL
      - key: env SUPABASE_READONLY_KEY -> env SUPABASE_KEY -> config.SUPABASE_READONLY_KEY -> config.SUPABASE_KEY
  - _build_readonly_client() 改用 resolver；缺 URL 或 key 時直接回傳 None，不建立 Supabase client、不進行 DB read。
  - 缺憑證時的 internal reason 改為泛用訊息 missing required Supabase read credentials，不輸出 secret value、hash、partial value、fingerprint 或長度。
  - 補直接測試覆蓋 config fallback、env key 優先序、缺憑證 fail closed、fake client factory 未被呼叫、render output 不含 secret 派生資訊。

  ## 修改檔案

  - scripts/smoke_market_theme_evidence_readonly.py
  - tests/test_market_theme_evidence_handoff.py

  ## 最小改動策略

  - 只在 read-only smoke script 內新增 credential resolution helper，沒有抽成全 repo credential framework。
  - 測試使用 fake config module 與 fake client factory，不讀真實 .env，不碰 live Supabase。
  - 保留既有 smoke render 欄位與 read-only loader 行為，只修 client 建立前的 credential source selection。

  ## 契約影響

  - 改變 credential resolution contract，符合本輪 TASK.md 指定 fallback。
  - CLI / smoke 輸出欄位順序、message list、Telegram 報文、payload shape、DB schema、DB query 語意均未改。
  - 新增 resolve_readonly_smoke_credentials() 供 script 內部與直接測試驗證；回傳 credentials 只在記憶體使用，不寫入 stdout/stderr。
  - 未加入 SUPABASE_SERVICE_ROLE_KEY 或其他高權限 credential fallback。

  ## 直接消費者同步

  - scripts/smoke_market_theme_evidence_readonly.py main() 仍透過 _build_readonly_client() 建 client；已同步使用新 resolver。
  - 直接測試 tests/test_market_theme_evidence_handoff.py 已同步覆蓋 read-only smoke credential fallback contract。
  - Architect / QA / Owner 手動執行 smoke command 的使用方式未變。

  ## 未影響模組

  - 未改策略 decision。
  - 未改 Telegram formatter、header、VERSION、message list contract 或手機閱讀內容。
  - 未改 DB schema / RLS / grant / policy / role。
  - 未做 live Supabase write、formal backfill 或 live Telegram delivery。
  - 未改 market theme evidence 資料模型、loader confirmed 判斷、production row classification、watchlist 或持倉狀態機。
  - 未清理或重構其他 smoke scripts。

  ## 已跑自檢命令

  - .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q：31 passed
  - PYTHONPYCACHEPREFIX=/private/tmp/stock-bot-pycache .venv/bin/python -m py_compile scripts/smoke_market_theme_evidence_readonly.py tests/test_market_theme_evidence_handoff.py：通過
  - git diff --check：通過
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q：52 passed, 17 warnings
  - 補充: 非 arch -arm64 跑同組 pytest 時遇到既有 .venv architecture mismatch，pydantic_core 為 arm64、當前 shell 需要 x86_64；已按既有 runner 慣例用 arch -arm64 重跑通過。

  ## 殘留風險

  - 本輪沒有用真實 Supabase credential 做 live smoke；只用 fake client 驗證 resolver contract，避免讀取或輸出真實 secret。
  - 若 production/local config.py 中 key 名稱不是 SUPABASE_READONLY_KEY 或 SUPABASE_KEY，仍會 fail closed；本輪不擴張命名 contract。
  - 新 helper 回傳 credentials 給 client factory；目前沒有 render/log 這些值，後續若新增 debug output 必須維持 secret redaction。

  ## 旁支待辦

  - 其他 smoke scripts 若也需要 env/config fallback，需另開任務；本輪未做全 repo credential refactor。
  - CI secret 命名、其他 credential alias、production read-only role 權限驗證不在本輪範圍。
