# CHANGELOG: 修復 GitHub workflow Supabase service-role runtime config wiring

  ## 任務尺寸與風險

  - 任務尺寸: tiny_patch
  - 風險判斷: 只修 GitHub Actions runtime config.py 產生契約，不改策略、DB、Telegram、CLI 報文或 evidence write 寫入邏輯。

  ## 修改內容

  - .github/workflows/stock-bot.yml 的 Create runtime config step 新增 SUPABASE_SERVICE_ROLE_KEY secret 注入。
  - split-secret runtime config.py 現在會同時產生:
      - SUPABASE_KEY
      - SUPABASE_SERVICE_ROLE_KEY
      - SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY
  - STOCK_CONFIG 舊 secret 路徑保留原本寫入行為；若同時提供 SUPABASE_SERVICE_ROLE_KEY，只追加 service-role aliases，不覆蓋既有 SUPABASE_KEY。
  - runtime validation 改為只輸出 present / missing 狀態，不輸出 URL、key 原值、截斷值或 hash。

  ## 修改檔案

  - .github/workflows/stock-bot.yml
  - tests/test_workflow_runtime_config.py

  ## 最小改動策略

  - 只修改 TASK.md 指定的 workflow runtime config wiring。
  - 只新增 workflow contract 的本地靜態 / shell 驗證測試。
  - 未修改 evidence write CLI、Supabase store helper、DB schema、策略或 Telegram formatter。

  ## 契約影響

  - 改變 GitHub workflow 生成的 runtime config.py 形狀：新增 SUPABASE_SERVICE_ROLE_KEY 與 SERVICE_ROLE_KEY alias。
  - SUPABASE_KEY 保留為既有 read path key，未改名、未移除、未改成 service-role key。
  - STOCK_CONFIG 舊 secret path 未移除；舊 config 仍可只靠既有 read config 通過 workflow runtime validation，service-role 缺失只顯示 missing。
  - 未改函式回傳結構、message list、Telegram payload、報文分組、DB 寫入 payload 或 public helper contract。

  ## 直接消費者同步

  - GitHub Actions Create runtime config step 已同步新增 service-role aliases。
  - runtime 生成的 config.py 已同步 scripts/write_market_theme_confirmed_evidence.py --execute 既有 fallback contract:
      - config.SERVICE_ROLE_KEY
      - config.SUPABASE_SERVICE_ROLE_KEY
  - 既有 Supabase read path 仍使用 SUPABASE_URL / SUPABASE_KEY，不需修改直接呼叫方。
  - Evidence write CLI 本身未改；既有 handoff 測試已覆蓋 config alias fallback。

  ## 未影響模組

  - 未改 DB schema / migration / RLS / grant / policy / role。
  - 未執行 live Supabase write、正式 backfill、replay。
  - 未發 live Telegram。
  - 未改策略 decision、watchlist、Telegram 報文分類、formatter header 或使用者可見版本。
  - 未修改 TASK.md / QA_REPORT.md；CHANGELOG.md 僅更新本輪 Tech 交付摘要。

  ## 已跑自檢命令

  - .venv/bin/python -m pytest tests/test_workflow_runtime_config.py tests/test_market_theme_evidence_handoff.py -q
      - 結果: 29 passed
  - git diff --check
      - 結果: passed

  ## 殘留風險

  - 本輪只做 workflow static/local shell contract 驗證，未在 GitHub Actions 真實 runner 上執行。
  - 若 production GitHub secret 名稱不是 SUPABASE_SERVICE_ROLE_KEY，需要 Architect/Owner 修正 secret 配置；本輪不做 secrets 命名遷移。
  - STOCK_CONFIG 若內部自行定義不同 service-role 名稱，本輪不解析或重寫舊 config 內容，只在新 secret 存在時追加標準 aliases。

  ## 旁支待辦

  - Supabase evidence write 資料內容正確性不在本輪處理。
  - Evidence table schema / RLS 設計不在本輪處理。
  - replay/backfill dry-run 不在本輪處理。
  - Telegram 報文呈現不在本輪處理。
  - GitHub Actions job 全面整理與 secrets 管理重構不在本輪處理。
