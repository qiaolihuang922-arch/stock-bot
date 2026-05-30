# CHANGELOG: Market Theme Confirmed Evidence Repo-side Write CLI

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch。
  - 風險判斷：新增 repo-side DB write path 介面，但預設 dry-run；測試只使用 fake client 驗證 --execute upsert payload，未做 production live write。

  ## 修改內容

  - 新增 scripts/write_market_theme_confirmed_evidence.py：
      - 預設 dry-run / validate，不寫 DB。
      - 輸出 public.market_theme_confirmed_evidence、validation status、row count、conflict target、sanitized upsert preview。
      - --execute 僅在 payload validation passed、source family allowed、SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 存在時才進入 upsert。
      - 缺 env 或 forbidden source family fail closed，exit non-zero，不輸出 secret。
  - 更新 services/market_theme_evidence_store.py：
      - 新增 approved payload 到既有 table contract row 的 mapping。
      - 固定 target table、write columns、upsert conflict target。
      - 新增 write env validation、client builder、可 fake client 測試的 upsert helper。
      - 未修改 read-only loader confirmed 判斷。
  - 更新 docs/examples 與 handoff docs：
      - 說明 dry-run / execute 指令、env 前置條件、allowed / forbidden source family。
      - 明確非 schema evidence rows 走 repo script / approved service API，不再要求 Owner 手動跑普通 DML。
      - 保留 schema/RLS/grant/policy/role 變更需 Owner 事前確認。
  - 補局部測試：
      - allowed sample dry-run。
      - forbidden source fail closed。
      - 缺 env --execute fail closed。
      - fake client --execute upsert table / payload / conflict target。

  ## 修改檔案

  - scripts/write_market_theme_confirmed_evidence.py
  - services/market_theme_evidence_store.py
  - tests/test_market_theme_evidence_handoff.py
  - docs/handoff/evidence_chain_market_theme_ops_artifacts.md
  - docs/examples/market_theme_owner_approved_payload.template.json
  - docs/examples/market_theme_owner_approved_payload.sample.json

  ## 最小改動策略

  - 只沿用既有 schema SQL 與 handoff helper 中已確認的欄位、source allowlist / denylist、conflict target。
  - 不新增 schema、不改 read-only loader、不改 approval package generator 的既有行為。
  - 新 CLI 與 helper 僅服務本輪 write interface；未重構 evidence chain 架構。

  ## 契約影響

  - 新增 CLI contract：scripts/write_market_theme_confirmed_evidence.py --payload ... [--execute]。
  - 新增 helper contract：write plan / env validation / upsert helper。
  - Upsert payload 只包含既有 table contract 欄位；conflict target 固定為 trade_date,market_index,sector_theme_key,source_family,source_name,as_of。
  - 未改 Telegram formatter、message list、payload、報文分組、策略 decision、DB schema、RLS/grant/policy/role。
  - 版本同步：TASK.md 指定不升版；本輪未改 core/generator.py 的 VERSION 或 Telegram header。

  ## 直接消費者同步

  - Operator / Architect：handoff docs 已新增 dry-run / execute / env / fail-closed 使用方式。
  - QA：新增局部測試覆蓋 TASK 指定四類 CLI/write path 條件。
  - public.market_theme_confirmed_evidence read-only loader：未改；仍只接受 production DB 中符合 confirmed 條件與 allowed persistent source family 的 rows。
  - GitHub fresh runner：未改；仍不能消費 local/runtime/template/sample artifact。

  ## 未影響模組

  - 未改 DB schema / migration。
  - 未改 RLS / grant / policy / role。
  - 未做 production live Supabase write。
  - 未做 formal backfill。
  - 未做 live Telegram delivery。
  - 未改策略核心、BUY/SELL、RR、加減碼、停損停利、watchlist。
  - 未改 Telegram formatter、message list contract、VERSION。

  ## 已跑自檢命令

  - .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q：22 passed。
  - .venv/bin/python scripts/write_market_theme_confirmed_evidence.py --payload docs/examples/market_theme_owner_approved_payload.sample.json：exit 0，dry-run passed，rows_to_upsert=1。
  - .venv/bin/python scripts/write_market_theme_confirmed_evidence.py --payload docs/examples/market_theme_forbidden_runtime_payload.sample.json：exit 2，forbidden source fail closed。
  - env -i PATH="$PATH" .venv/bin/python scripts/write_market_theme_confirmed_evidence.py --payload docs/examples/market_theme_owner_approved_payload.sample.json --execute：exit 2，missing SUPABASE_URL /
    SUPABASE_SERVICE_ROLE_KEY blocked。
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q：43 passed, 17 warnings。
  - PYTHONPYCACHEPREFIX=/private/tmp/stock_bot_pycache arch -arm64 .venv/bin/python -m py_compile services/market_theme_evidence_store.py scripts/write_market_theme_confirmed_evidence.py scripts/
    generate_evidence_approval_package.py：passed。
  - git diff --check：passed。

  ## 殘留風險

  - 未執行 production --execute，也未驗證真 Supabase service role write，符合 TASK 非目標。
  - plain .venv/bin/python 跑 tests/test_market_theme_evidence.py 會因主 repo .venv arm64 wheel 與 x86_64 process 不相容而 collection error；改用既有 arch -arm64 .venv/bin/python 後通過。
  - 未驗證 GitHub runner read-only consumption 或 Telegram confirmed evidence 實際報文，屬旁支非本輪。

  ## 旁支待辦

  - 真 production write 執行。
  - 大量 historical backfill。
  - GitHub runner read-only env 配置。
  - production read-only smoke。
  - RLS / read-only role 變更。
  - Telegram confirmed evidence 實際報文驗證。
  - 新外部資料源或策略調整。
