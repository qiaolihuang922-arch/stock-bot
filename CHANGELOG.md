# CHANGELOG: evidence chain 候選整包交付摘要修正

  ## 任務尺寸與風險

  - 本輪任務尺寸: process
  - 上游候選尺寸: normal_patch
  - 風險判斷: 本輪只修正交付摘要內容，保留既有 evidence chain 候選 diff；不修改產品代碼、測試、策略 decision、DB schema、Telegram formatter、Telegram VERSION、live write 或 backfill。

  ## 修改內容

  - 重新整理 evidence chain 候選整包交付摘要，移除交付狀態自相矛盾描述。
  - 明確列出產品候選 diff 與交付文件 diff 的邊界。
  - 保留既有 evidence chain 候選內容與驗證結果描述。
  - 明確補充 dummy config.py 是隔離測試用本機檔，未納入 git diff。
  - 明確記錄指定 arm64 pytest 與 git diff --check 自檢結果。
  - 不宣告 QA 通過；Tech 自檢只代表交付前檢查。

  ## 修改檔案

  ### 產品候選 diff：4 個檔案

  - scripts/smoke_market_theme_evidence_readonly.py
  - scripts/write_market_theme_confirmed_evidence.py
  - services/market_theme_evidence_store.py
  - tests/test_market_theme_evidence_handoff.py

  ### 交付文件 diff：CHANGELOG.md

  - CHANGELOG.md

  ### 未納入 diff

  - config.py 是隔離 worktree 測試用 dummy config，未納入 git diff。

  ## 最小改動策略

  - 只依 TASK.md 與 Architect 指令修正交付摘要。
  - 不清空、不重置、不改寫既有 evidence chain 候選 diff。
  - 不新增產品檔案、不改測試期望、不做旁支重構。
  - 不把環境用 dummy config.py 納入交付範圍。

  ## 契約影響

  - dry-run contract: approved dry-run 可產生合法 dry-run 結果；forbidden dry-run 必須 fail closed，不產生可執行寫入。
  - fake execute contract: fake execute 只用於測試 read-after-write contract，不代表 production live write。
  - read-after-write exception contract: read-after-write exception 必須做 secret redaction，不輸出 URL、read key、service-role key、截斷值或 hash。
  - source status contract: runtime / unknown / mixed source 必須是 status=insufficient-data、telegram_confirmed=false、strategy_consumer=fail-closed。
  - allowed production row contract: allowed production row 必須可 pass。
  - credential resolution contract: env 優先；env 缺失時可 fallback repo config；service key alias 兼容 SERVICE_ROLE_KEY 與 SUPABASE_SERVICE_ROLE_KEY。
  - 版本同步: 本輪不改 Telegram VERSION，未改 Telegram header。
  - 未改函式回傳結構、message list、Telegram payload、報文分組、DB schema 或 DB 寫入 payload。

  ## 直接消費者同步

  - scripts/write_market_theme_confirmed_evidence.py: 同步 evidence chain write CLI 的 dry-run、fake execute、read-after-write、source fail-closed 與 credential fallback 路徑。
  - scripts/smoke_market_theme_evidence_readonly.py: 同步 readonly smoke 對 source status / allowed production row 的檢查路徑。
  - services/market_theme_evidence_store.py: 同步 evidence store 對 source status、telegram confirmation、strategy consumer 與 redaction 的契約支援。
  - tests/test_market_theme_evidence_handoff.py: 同步直接消費者測試，覆蓋 dry-run、fake execute、read-after-write exception、runtime / unknown / mixed source fail-closed、allowed production row。
  - QA 後續可依 TASK.md、本 CHANGELOG.md、git diff 與上述測試檔做整包驗證。

  ## 未影響模組

  - 未改 DB schema / migration / table / column / RLS / grant / policy / role。
  - 未執行 live Supabase write、formal backfill、replay。
  - 未發 live Telegram。
  - 未改策略 decision、BUY / SELL / RR / 加減碼 / 停損停利門檻。
  - 未改 watchlist。
  - 未改 Telegram formatter、summary、header、message list contract 或 VERSION。
  - 未改產品方向，未擴成 evidence chain 架構重設或全 repo refactor。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q
      - 結果: 49 passed，17 warnings
  - git diff --check
      - 結果: 通過

  ## 殘留風險

  - 本輪 Tech 自檢只覆蓋 TASK.md 指定的最小 evidence chain 測試與 whitespace 檢查，不代表 QA 通過。
  - fake execute 仍只代表測試用 read-after-write contract，不代表 production live write 已驗證。
  - 真實 GitHub runner、production secret 配置與 live Supabase 寫入不在本輪 Tech 自檢範圍。
  - 若 QA 發現 source fail-closed、secret redaction、allowed production row 或 diff 邊界不符合 TASK.md，需依 QA 結論回退或重修。

  ## 旁支待辦

  - production evidence table 實際資料內容正確性不在本輪處理。
  - DB schema / RLS / grant / policy 設計不在本輪處理。
  - production backfill / replay dry-run 不在本輪處理。
  - live Telegram 與 Telegram 文案呈現不在本輪處理。
  - runner 長期環境治理與 secrets 管理重構不在本輪處理。
