# QA_REPORT:

  ## 測試範圍

  本輪 QA 風險等級按 TASK.md 判定為 risk_patch / L2+。驗證聚焦 repo-side non-live artifact、dry-run contract、SQL safety、read-only smoke、fresh runner fail-closed；未擴成 full pytest、replay、正式 backfill 或 live DB 驗
  證。

  檢查輸入：

  - TASK.md
  - CHANGELOG.md
  - git status --short
  - git diff --stat
  - services/market_theme_evidence_store.py
  - scripts/validate_market_theme_evidence_ingestion.py
  - scripts/smoke_market_theme_evidence_readonly.py
  - db/sql/evidence_chain_market_theme_ops_manual_template.sql
  - docs/handoff/evidence_chain_market_theme_ops_artifacts.md
  - tests/test_market_theme_evidence_handoff.py
  - tests/test_market_theme_evidence.py

  可吸收 diff：

  - tracked 修改：CHANGELOG.md、services/market_theme_evidence_store.py、tests/test_market_theme_evidence_handoff.py
  - 必須一併納入的新增 artifact：db/sql/evidence_chain_market_theme_ops_manual_template.sql、docs/handoff/evidence_chain_market_theme_ops_artifacts.md、scripts/smoke_market_theme_evidence_readonly.py、scripts/
    validate_market_theme_evidence_ingestion.py

  worktree 殘留：

  - 未見與本輪無關的額外 tracked 修改。
  - 以上 4 個 untracked 檔案是 TASK 要求的新增 artifact，不應被當成無關殘留；但 Architect 合併時需明確 add，不能只看 git diff --stat。

  已跑驗證：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence_handoff.py tests/test_market_theme_evidence.py -q：28 passed，17 warnings。
  - arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py --trade-date 2026-05-29：exit 2，fail-closed，telegram_confirmed: false。
  - git diff --check：通過。
  - git diff -- core/generator.py core/market_theme_evidence.py：無 diff；core/generator.py VERSION 仍為 v20.4.3。
  - 額外負面 CLI：runtime_diagnostic + confirmed payload with --include-sql：exit 2，valid=false，may_render_manual_sql=false，未輸出 manual_sql。
  - 額外 smoke 反證：只提供 SUPABASE_SERVICE_ROLE_KEY、不提供 SUPABASE_READONLY_KEY：exit 2，env: missing，未 fallback service role。

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. fake/local/runtime/report-derived payload 被包裝成 confirmed 或輸出 SQL。驗證：局部測試與額外 CLI 負面 payload。停止條件：invalid payload 不輸出 manual_sql，live_write=false。
  2. read-only smoke 誤用 service role 或在 fresh runner 缺 env 時不 fail closed。驗證：缺 read-only env 與 service-role-only env。停止條件：exit 2、status: fail-closed、telegram_confirmed: false。
  3. SQL/docs 被 Owner 誤讀為已上線或已回填。驗證：SQL/doc header 與 boundary 掃描。停止條件：明確標示 manual only、非 migration、未 live write、未 formal backfill、未 production RLS/grant change、未 Telegram delivery。

  停止於 L2+ 局部驗證，因 TASK 明確禁止無 Owner 批准時擴到 full pytest / live DB / formal backfill。

  ## 關聯風險掃描

  TASK.md、CHANGELOG.md、diff 一致：Tech 交付了 validation helper/CLI、read-only smoke helper/CLI、manual SQL template、handoff docs、局部測試。未看到 Telegram formatter、message list、strategy threshold、watchlist、
  runner secrets、formal backfill runner 的 diff。

  SQL template 安全邊界可接受：Step A/B/C 均以註解形式提供 manual template，包含 Owner approval 與 placeholders；Step D 是 read-only verification queries。未發現 project URL、password、service role key 或 connection
  string。

  需注意但不阻塞：services/market_theme_evidence_store.py 既有 _build_client() 仍可讀 SUPABASE_SERVICE_ROLE_KEY，但新增 smoke CLI 自建 _build_readonly_client()，只接受 SUPABASE_READONLY_KEY，額外反證確認 service-role-
  only env 不會被 smoke 使用。

  ## 跨區塊語意一致性

  CHANGELOG 宣稱本輪不升版、不改 Telegram；diff 驗證 core/generator.py 與 core/market_theme_evidence.py 無變更，VERSION 仍為 v20.4.3，符合 TASK 版本契約。

  validation / smoke / docs / SQL 的語意一致：

  - validation：invalid 不產生 SQL，live_write=false。
  - smoke：read-only、write disabled、缺 env / 0 rows / error fail closed。
  - docs：repo artifact ready，不等於 production live。
  - SQL：manual only，不是 migration，不是已上線證據。

  ## 使用者誤讀風險

  Owner 手機 Telegram 路徑本輪預期不變。未改 generator / formatter / VERSION；缺 production confirmed rows 時 smoke 顯示 telegram_confirmed: false，不會因 repo artifact 存在而變成「題材 confirmed」或「新倉可買」。

  Operational artifact 的誤讀風險已被文件和 SQL header 壓住：docs 明確說 repo-side only、未 live write、未 formal backfill、未 production RLS change、未 Telegram delivery。SQL template 也明確寫 manual only、agent must
  not execute、not evidence production is live。

  ## 質疑與反證

  Tech 自檢之外新增反證：

  - 用 runtime_diagnostic 偽 confirmed payload 跑 validation CLI，結果 fail closed，沒有 manual_sql。
  - 用 SUPABASE_SERVICE_ROLE_KEY 但不提供 SUPABASE_READONLY_KEY 跑 smoke，結果仍 missing env / fail-closed，證明新增 smoke 不 fallback service role。
  - 掃描 SQL/docs/scripts 中 live/write/Telegram/service-role 相關文字，確認 manual boundary 與 non-live statement 存在。

  質疑結果：未發現 TASK / CHANGELOG / diff 的實質矛盾；未發現本輪 artifact 會直接造成 live write、正式 backfill 或 Telegram 誤報 confirmed。

  ## 未測項目

  未連 production DB，未驗證實際 RLS/grant/policy 結果；這需 Owner 手動執行 SQL 後回傳結果。

  未做 formal backfill、live ingestion、live Telegram delivery，符合 TASK 非目標。

  未跑 full pytest / replay / backfill dry-run，因 TASK 指定本輪 L2+ 且禁止無理由擴大驗證。

  ## QA 結論

  通過

  本輪可吸收範圍是上述 tracked diff 加 4 個新增 artifact；不得把 worktree 整包狀態不分辨地合併。結論只代表 repo-side production ops artifact ready for Owner manual execution，不代表 production ingestion / backfill /
  RLS / read-only runner 已正式上線。
