# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 判斷：本輪碰到 production evidence chain / DB approval 邊界，但實作只新增 template、sample、docs、局部 tests；未做 live write、formal backfill、RLS/grant、Telegram 或策略變更。

  ## 修改內容

  - 新增 Owner-facing market/theme approved payload template，列出必填欄位、allowed / forbidden source family、manual approval boundary、sample/template 非 production confirmed。
  - 新增 allowed owner_approved_persistent dry-run sample，可用既有 generator 產出 JSON / Markdown / review-only SQL package。
  - 新增 forbidden runtime negative sample，驗證 fail closed、不產 deterministic SQL。
  - 更新 handoff docs，固定 sample dry-run 指令、forbidden dry-run 指令、輸出檔案與 no-live-write / review-only / not production confirmed 邊界。
  - 補局部測試覆蓋 template/sample/docs 契約、allowed sample CLI、forbidden sample CLI、sample-as-production 誤讀防線。

  ## 修改檔案

  - docs/examples/market_theme_owner_approved_payload.template.json
  - docs/examples/market_theme_owner_approved_payload.sample.json
  - docs/examples/market_theme_forbidden_runtime_payload.sample.json
  - docs/handoff/evidence_chain_market_theme_ops_artifacts.md
  - tests/test_market_theme_evidence_handoff.py

  ## 最小改動策略

  - 未重寫 scripts/generate_evidence_approval_package.py；既有 generator 已支援 non-live package、allowed source、forbidden source fail closed。
  - 只補 TASK 指定缺口：template、allowed sample、forbidden sample、handoff docs、局部 tests。
  - 未做旁支重構、清理、production automation 或全 repo 測試擴張。

  ## 契約影響

  - Generator 回傳結構：未改。
  - message list / Telegram payload / Telegram formatter / VERSION：未改。
  - DB schema / RLS / grant / production write path：未改。
  - 新增 repo artifact contract：
      - docs/examples/market_theme_owner_approved_payload.sample.json 可作 dry-run input。
      - docs/examples/market_theme_forbidden_runtime_payload.sample.json 必須 fail closed，不產 SQL。
      - template/sample 明確標示不是 production confirmed、不是 DB rows、不是 GitHub fresh runner source-of-truth。

  ## 直接消費者同步

  - Owner：handoff docs 已同步 template/sample 路徑、dry-run 命令、輸出 artifact、manual approval required。
  - Architect：CHANGELOG 與 diff 可驗證本輪只形成可審核 package workflow，未做 live write。
  - QA：新增 tests 覆蓋 allowed sample、forbidden sample、sample-as-production 誤讀風險。
  - 未來 manual operator：docs 保留 SQL review-only 與 Owner separate approval 邊界。
  - 未來 GitHub fresh runner：docs/template/sample 明確不可作 production confirmed source-of-truth；仍只能消費 production DB read-only rows。

  ## 未影響模組

  - 未改策略 decision、BUY/SELL、RR、加減碼、停損停利、watchlist。
  - 未改 Telegram formatter、message list、header、VERSION。
  - 未改 live Telegram delivery。
  - 未改 Supabase live write、formal backfill、production RLS / grant / policy / role。
  - 未新增 production ingestion automation。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q：18 passed。
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q：39 passed, 17 warnings。
  - arch -arm64 .venv/bin/python scripts/generate_evidence_approval_package.py --payload docs/examples/market_theme_owner_approved_payload.sample.json --output-dir <tmp>：exit 0，產出 approval_package.json、
    approval_package.md、market_theme_confirmed_evidence_2026-05-29.sql。
  - arch -arm64 .venv/bin/python scripts/generate_evidence_approval_package.py --payload docs/examples/market_theme_forbidden_runtime_payload.sample.json --output-dir <tmp>：exit 2，payload_validation.status=failed、
    reason=forbidden source_family、deterministic_sql=None，未產 SQL。
  - git diff --check：通過。
  - rg -n "service_role|password|apikey|api_key|postgres://|postgresql://|supabase\\.co" docs/examples docs/handoff/evidence_chain_market_theme_ops_artifacts.md tests/test_market_theme_evidence_handoff.py：無匹配。

  ## 殘留風險

  - 本輪只提供 review package workflow；不代表 production rows 已存在、SQL 已執行、read-only smoke 已通過或 Telegram 已 confirmed。
  - Allowed sample 的 reference 是 placeholder，Owner 仍需替換為真實 approved persistent reference 後才能進 production review。
  - Generator 仍只產 review-only SQL；正式 SQL execution 需 Owner 另行批准。

  ## 旁支待辦

  - production DB execution。
  - production ingestion automation。
  - formal backfill。
  - RLS / grant 正式變更。
  - production read-only smoke with real approved rows。
