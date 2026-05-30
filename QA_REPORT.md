# QA_REPORT: 修復 GitHub workflow Supabase service-role runtime config wiring

  ## 測試範圍

  - 任務尺寸 / qa_level：tiny_patch / L1，未擴大到 full pytest、replay、backfill、live Supabase write 或 live Telegram。
  - 讀取：TASK.md、CHANGELOG.md、.github/workflows/stock-bot.yml diff、tests/test_workflow_runtime_config.py、scripts/write_market_theme_confirmed_evidence.py 直接消費者路徑。
  - 執行：
      - git diff --check：passed
      - .venv/bin/python -m pytest tests/test_workflow_runtime_config.py tests/test_market_theme_evidence_handoff.py -q：29 passed
      - QA 補充反證：用 workflow 生成的 runtime config.py 直接餵給 write_market_theme_confirmed_evidence.py --execute fake client，確認 key_source = config.SERVICE_ROLE_KEY、rows_written = 1、未洩漏 read key / service-
        role key。

  ## 風險預算與停止條件

  - 風險 1：GitHub fresh runner 生成的 config.py 仍不能被 evidence write execute consumer 使用。
    驗證：抽出 workflow Create runtime config shell，生成 config.py 後直接 import 給 write CLI fake client。結果通過。
  - 風險 2：validation / stdout / stderr 洩漏 secret 值。
    驗證：split secret、legacy STOCK_CONFIG、缺 service-role key 路徑均檢查 stdout/stderr 不含 sentinel secret。結果通過。
  - 風險 3：可合併內容與 worktree 殘留混淆。
    驗證：git status --short 顯示 .github/workflows/stock-bot.yml、CHANGELOG.md tracked modified，tests/test_workflow_runtime_config.py 是 untracked。這是本輪最主要條件風險。
  - 停止條件：L1 靜態 / shell / 直接 consumer contract 已覆蓋；不再擴大驗證 production runner、真 Supabase write、DB schema、Telegram 報文。

  ## 關聯風險掃描

  - Workflow split-secret path 已新增 SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}，並寫入：
      - SUPABASE_SERVICE_ROLE_KEY = "$SUPABASE_SERVICE_ROLE_KEY"
      - SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY
  - SUPABASE_KEY 仍存在，未被改名、刪除或替換成 service-role key。
  - STOCK_CONFIG legacy path 保留，且在有新 secret 時只追加 service-role aliases。
  - 缺 service-role secret 時 workflow runtime validation 只標示 missing，不把缺 key 包裝成 successful write；execute consumer 仍由既有 fail-closed validation 擋住。
  - 未發現 DB schema、Telegram formatter、策略、watchlist、replay/backfill 變更。

  ## 跨區塊語意一致性

  - TASK.md 要求不升使用者可見版本、不改 Telegram / CLI 報文內容；diff 未改 VERSION、Telegram formatter 或 message list。
  - Workflow validation log 只輸出 present/missing，符合 TASK.md 的 no-secret logging contract。
  - CHANGELOG.md 的產品描述大致吻合 diff，但有兩個交付一致性問題：
      - tests/test_workflow_runtime_config.py 被列為修改檔案，但目前是 untracked，未出現在 git diff --name-only。
      - CHANGELOG.md 在「未影響模組」寫「未修改 TASK.md、CHANGELOG.md、QA_REPORT.md」，但 CHANGELOG.md 本身已修改；這是文件自述錯誤，不影響產品 runtime，但會干擾 Architect 吸收。

  ## 使用者誤讀風險

  - 本輪不改 Telegram / summary / dashboard，沒有 Owner 手機報文可讀性風險。
  - 使用者可見風險轉為 GitHub Actions log：目前 log 只會顯示 runtime config: ... present/missing，不會露出 URL、read key、service-role key，Owner 不會從 log 誤讀成已執行 production write。
  - 若 Architect 只合併 tracked diff 而漏掉 untracked test，Owner 可能以為 CHANGELOG 宣稱的測試保護已進 repo；這是合併包裝風險。

  ## 質疑與反證

  - 反證「workflow 只寫 alias 但 consumer 仍讀不到」：QA 用 workflow 生成的實際 config.py 執行 write CLI fake client，結果 key_source = config.SERVICE_ROLE_KEY、write_execution = executed、fake client 1 call。
  - 反證「缺 service-role key 會被誤報成功」：split-secret path 不帶 service-role key 時，runtime config step 回傳 0 但 log 顯示 SUPABASE_SERVICE_ROLE_KEY missing / SERVICE_ROLE_KEY alias missing，未洩漏 read key；真正
    execute 寫入仍由 consumer validation 負責 fail closed。
  - 反證「STOCK_CONFIG 被覆蓋」：測試覆蓋 legacy STOCK_CONFIG 保留 SUPABASE_KEY 並只追加 aliases。
  - 反證「secret 被 log」：測試與 QA consumer smoke 都用 sentinel key 檢查 stdout/stderr，未發現洩漏。

  ## 未測項目

  - 未在真 GitHub Actions runner 執行。
  - 未執行 live Supabase write。
  - 未驗證 production GitHub secret 是否真的命名為 SUPABASE_SERVICE_ROLE_KEY。
  - 未測 replay/backfill、DB schema/RLS、Telegram 報文，符合本輪非目標與 L1 邊界。

  ## QA 結論

  conditional pass

  條件：Architect 吸收時必須明確處理 tests/test_workflow_runtime_config.py 這個 untracked 檔案。若本輪要保留 Tech 宣稱的測試覆蓋，該檔必須納入可合併 diff；若不納入，CHANGELOG.md 的「修改檔案 / 自檢命令」與實際可合併內容
  不一致，不能視為完整通過。

  可吸收 diff：.github/workflows/stock-bot.yml runtime config wiring。
  需一起決定的 worktree 殘留：tests/test_workflow_runtime_config.py untracked 測試檔。
  文件修正建議：CHANGELOG.md 移除「未修改 CHANGELOG.md」的自相矛盾敘述，或改成「未修改 TASK.md / QA_REPORT.md」。
