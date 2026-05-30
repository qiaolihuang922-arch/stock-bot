# CHANGELOG: market/theme 五月歷史回寫 source-of-truth 與策略消費閉環

  ## 修改內容

  - 任務尺寸與風險: risk_patch。理由是本輪涉及 backfill script/interface、DB write gate、pollution guard、read-after-write report 與 strategy/evidence trend consumption；但本次 Tech 交付摘要修正本身只收斂文件交付內容，不
    擴大產品 diff。
  - scripts/backfill_market_theme_sources.py:
      - 新增 market-theme-history-backfill JSON report，包含 TASK.md 要求的 date_range、write_execution、live_telegram、schema_change、三張表的 source audit 欄位、daily_price_signal_snapshot_rewrite、
        strategy_consumption_check 與 blocked_reasons。
      - 新增 May date range 預設值 2026-05-01 到 2026-05-29，並在 validation 中拒絕日期超出範圍的 confirmed evidence row。
      - 對 market_theme_confirmed_evidence 加入 required fields、allowed source family、forbidden source family、lineage source table、freshness、confirmed status、payload object 檢查。
      - write path 只允許 upsert validated market_theme_confirmed_evidence rows；不再刪除或寫入 sector_theme_members、market_theme_index_daily_bars。
      - sector_theme_members 在只能取得 latest company profile membership 時標記 missing/blocked；market_theme_index_daily_bars 若 DB table 不是直接消費者則 report skipped/not-consumed。
      - execute 後透過 load_confirmed_market_theme_evidence 做 read-after-write，並把 observed/recent/support streak trend metrics 放入 report。
  - tests/test_market_theme_source_backfill.py:
      - 補 dry-run report shape、latest membership blocked、May range guard、forbidden daily_signal_snapshot source guard、missing required fields guard、execute path 只 upsert confirmed evidence、read-after-write trend
        metrics 等局部測試。
  - CHANGELOG.md:
      - 交付文件 diff。內容為本最終回答，補列 CHANGELOG.md 為交付文件，移除與 worktree 狀態矛盾的舊摘要，並保留上述產品/測試實作摘要。

  ## 修改檔案

  - scripts/backfill_market_theme_sources.py
  - tests/test_market_theme_source_backfill.py
  - CHANGELOG.md

  ## 最小改動策略

  - 本次只修正交付摘要內容，未再修改產品代碼與測試。
  - 產品候選 diff 限定在 TASK.md 指定的 market/theme source backfill script 與直接測試。
  - 不順手重構、不清理旁支、不改策略方向、不改 Telegram 報文、不新增 DB schema。
  - 不把 daily_price / daily_signal_snapshot 五月資料包裝成本輪成果；只作禁止重寫契約的 report 欄位。

  ## 契約影響

  - 改變 scripts/backfill_market_theme_sources.py 的 CLI/report 輸出契約：由文字摘要改為 TASK.md 指定的 JSON report shape。
  - 改變 write path 行為：execute 只 upsert validated market_theme_confirmed_evidence，不寫入 sector_theme_members 或 market_theme_index_daily_bars。
  - 新增 validation/fail-closed contract：forbidden source family、forbidden lineage、missing required fields、日期超出 May range、latest-only membership 都會 blocked/skipped。
  - 新增 read-after-write report contract：execute 後回填 read_after_write 與 strategy_consumption_check trend metrics。
  - 未改 Telegram formatter、message list、payload、報文排序、報文分組、VERSION/header。
  - 版本同步: TASK.md 指定本輪不改 Telegram 使用者可見報文與 header，因此未同步 VERSION 或 Telegram header。

  ## 直接消費者同步

  - Architect / Owner: 透過 backfill script JSON report 判斷 source availability、write scope、pollution guard、read-after-write 與 blocked/skipped reason。
  - QA: 透過 tests/test_market_theme_source_backfill.py 驗證 report contract、write gate、pollution guard 與 read-after-write metrics。
  - Strategy/evidence trend consumer: execute path 使用 load_confirmed_market_theme_evidence 驗證 confirmed evidence history 可被讀回；本輪不改其 public return shape。
  - Telegram/report generator: 僅維持既有 evidence trend 消費關係，不改報文 contract。
  - 本輪沒有新增或改動 formatter、message list 或 Telegram payload 呼叫方。

  ## 未影響模組

  - 未改策略 BUY/SELL/RR/停損停利核心門檻。
  - 未改 watchlist、持倉狀態機、交易建議。
  - 未改 Telegram formatter、header、VERSION 或手機閱讀內容。
  - 未改 DB schema、table、column、RLS、grant、policy、role。
  - 未執行 live Telegram。
  - 未執行 live Supabase write。
  - 未執行正式 backfill。
  - 未使用 fake/local/runtime/report-derived/chat data 生成 confirmed evidence。
  - 未重寫 daily_price / daily_signal_snapshot 五月資料。

  ## 已跑自檢命令

  - pwd && git status --short: 確認工作目錄為 /Users/liveroom/stock-bot-agent-worktrees/tech_write，產品候選 diff 為 scripts/backfill_market_theme_sources.py、tests/test_market_theme_source_backfill.py。
  - sed -n '1,240p' TASK.md: 確認任務為 risk_patch，要求 market/theme May history backfill report、validation、write safety、read-after-write 與 fresh runner consumption。
  - sed -n '1,260p' CHANGELOG.md: 確認舊摘要與目前 worktree 狀態矛盾，需重寫交付摘要。
  - git diff --stat: 確認候選 diff 為 2 個產品/測試檔案，488 insertions(+), 50 deletions(-)。
  - git diff --name-only: 確認候選 diff 檔案清單與本 CHANGELOG 的產品/測試檔案一致。
  - python -m pytest tests/test_market_theme_source_backfill.py: 未執行成功，系統 python command not found。
  - .venv/bin/python -m pytest tests/test_market_theme_source_backfill.py: 通過，11 passed in 0.12s。

  ## 殘留風險

  - Tech 自檢只代表交付前檢查，不宣告 QA 通過。
  - 尚未執行 live Supabase write 或正式 backfill；execute path 仍需在批准後由 QA/Architect 依 TASK.md 驗證 dry-run、write flag、read-after-write 與 fresh runner consumption。
  - 若五月 historical source 只能取得 latest snapshot 或缺 lineage/source semantics，report 會維持 blocked/skipped，不能進入正式寫入。
  - market_theme_index_daily_bars 與 sector_theme_members 目前依直接消費者與 historical membership 可證明性限制而 skipped/blocked；若後續要寫入，需要另開任務定義直接消費者與 source-of-truth。

  ## 旁支待辦

  - 若 Owner/Architect 提供可核驗五月 market/theme historical source，另開任務接入 source loader 與 approved payload mapping。
  - 若需要正式 execute/write，另開 write approval 任務並保留 dry-run、validation、duplicate/upsert guard、read-after-write。
  - 若需要 DB schema/view/function/RLS/grant/policy/role 變更，另走 DB schema 變更流程。
  - 若後續要把 evidence trend 顯示到 Telegram summary/detail，另開 Telegram 報文任務並同步版本契約。
