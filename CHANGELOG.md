# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 風險判斷：碰到 production DB approval/write 邊界，但本輪只新增 repo-side non-live approval package generator 與局部測試；沒有 live write、formal backfill、RLS/grant 變更或 Telegram delivery。

  ## 修改內容

  - 新增 scripts/generate_evidence_approval_package.py
      - 支援 --payload 與 optional --output-dir。
      - 產生 non-live approval package JSON / Markdown。
      - validation passed 且 source allowed 時才產生 deterministic SQL。
      - forbidden source、缺 source、mixed allowed+forbidden source 一律 fail closed，不產生 SQL。
      - SQL header 明確標示 Owner manual approval required、Agent did not execute SQL、package 不是 production deployment evidence。
  - 更新 docs/handoff/evidence_chain_market_theme_ops_artifacts.md
      - 補上 approval package generator 的使用方式、產物與 no-live boundary。
  - 更新 tests/test_market_theme_evidence_handoff.py
      - 覆蓋 allowed package、forbidden package、mixed source fail closed、SQL deterministic、CLI output-dir artifact 寫出。

  ## 修改檔案

  - scripts/generate_evidence_approval_package.py
  - tests/test_market_theme_evidence_handoff.py
  - docs/handoff/evidence_chain_market_theme_ops_artifacts.md

  ## 最小改動策略

  - 復用既有 services.market_theme_evidence_store 的 validation 與 SQL renderer，避免新增第二套 DB row validation / SQL contract。
  - 未修改 DB schema、loader confirmed 判斷、read-only smoke、Telegram formatter、策略核心或 VERSION。
  - 只補 TASK.md 指定的 generator / docs / 局部 tests。

  ## 契約影響

  - 新增 CLI artifact contract：scripts/generate_evidence_approval_package.py --payload ... [--output-dir ...]。
  - 新增 package output fields：schema_decision、mode、write_execution、payload_validation、deterministic_sql、deterministic_sql_path、risk_summary、preflight_checklist、post_run_verification_checklist、
    read_only_smoke_command、manual_approval_required、not_executed。
  - deterministic SQL 只在 validation passed 且 source family allowed 時輸出。
  - 未改既有 public helper 回傳結構、Telegram message list、payload shape、報文分組、DB schema 或 live write 行為。
  - 版本同步：TASK.md 指定本輪不升版；未修改 Telegram 使用者可見報文、header 或 VERSION。

  ## 直接消費者同步

  - Owner：可用 generator 產生 review package，仍需手動批准 SQL execution。
  - Architect：可依 package contract、TASK、CHANGELOG、QA_REPORT 判斷是否進 Owner manual approval。
  - QA：新增 tests 與 docs 可驗證 package contract、source guard、no-live-write wording、determinism。
  - 未來 manual operator：SQL header 與 package checklist 明確標示只能在 Owner 另行批准後手動執行。
  - 未來 GitHub fresh runner：未改 consumption；仍只能依 production DB read-only result，不因 package 存在而 confirmed。

  ## 未影響模組

  - 未改策略 decision、BUY/SELL、RR、加減碼、停損停利、watchlist。
  - 未改 Telegram formatter、Telegram delivery、message list 或 VERSION。
  - 未改 Supabase live write、formal backfill runner、production RLS/grant/policy/role。
  - 未改 DB schema。
  - read-only smoke fail-closed 行為未回退。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py -q
      - 結果：14 passed
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q
      - 結果：36 passed, 17 warnings
  - printf ...runtime payload... | arch -arm64 .venv/bin/python scripts/generate_evidence_approval_package.py --payload -
      - 結果：exit 2，符合 forbidden source fail closed；deterministic_sql: null
  - arch -arm64 .venv/bin/python scripts/generate_evidence_approval_package.py --payload <tmp allowed payload> --output-dir <tmp out>
      - 結果：exit 0，寫出 approval_package.json、approval_package.md、market_theme_confirmed_evidence_2026-05-29.sql
  - PYTHONPYCACHEPREFIX=/private/tmp/stock-bot-pycache arch -arm64 .venv/bin/python -m py_compile scripts/generate_evidence_approval_package.py
      - 結果：通過
      - 備註：未設 PYTHONPYCACHEPREFIX 時 macOS Python 嘗試寫 /Users/liveroom/Library/Caches/... 被 sandbox 拒絕；改用 /private/tmp 後通過。
  - git diff --check -- docs/handoff/evidence_chain_market_theme_ops_artifacts.md tests/test_market_theme_evidence_handoff.py
      - 結果：通過

  ## 殘留風險

  - 本輪未做 production DB live verification；符合 TASK 禁止事項。
  - package 的 SQL 仍需 Owner 人工審核與另行批准後才可手動執行。
  - generator 目前只把 approved package payload 正規化到既有 market_theme_confirmed_evidence row contract；若未來 Owner payload 欄位擴張，需另開任務定義契約。
  - py_compile 需指定 writable pycache 位置，否則 macOS global cache path 會被 sandbox 擋住。

  ## 旁支待辦

  - production ingestion automation：未做。
  - actual production DB execution：未做。
  - RLS/grant 正式變更：未做。
  - GitHub runner read-only env 配置：未做。
  - Telegram confirmed consumption live 驗證：未做。
  - 新外部資料來源或策略調整：未做。
