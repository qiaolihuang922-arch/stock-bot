# QA_REPORT:

  ## 測試範圍

  本輪依 TASK.md 判定為 normal_patch / L2，沒有擴成 full pytest、replay、backfill 或 production live write。

  已驗證：

  - TASK.md、CHANGELOG.md、git diff --name-only 一致。
  - 可吸收 diff：4 個產品候選檔案 + CHANGELOG.md。
  - 產品候選 diff：
      - scripts/smoke_market_theme_evidence_readonly.py
      - scripts/write_market_theme_confirmed_evidence.py
      - services/market_theme_evidence_store.py
      - tests/test_market_theme_evidence_handoff.py
  - 交付文件 diff：
      - CHANGELOG.md
  - config.py 不在 tracked diff；git ls-files config.py 無輸出。
  - git diff --check 通過。
  - 指定測試通過：49 passed, 17 warnings。

  執行命令：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_market_theme_evidence_handoff.py -q
  - git diff --check
  - CLI approved dry-run / forbidden runtime dry-run smoke
  - helper 層 direct-consumer smoke：runtime / unknown / mixed / production row

  ## 風險預算與停止條件

  本輪最值得抓的風險：

  1. 交付邊界錯誤
     驗證：比對 CHANGELOG.md、git diff --name-only、git status --short。
     結果：符合；產品候選 4 檔，交付文件 1 檔，dummy config.py 未納入 diff。
  2. source fail-closed 被繞過
     驗證：指定測試 + 額外 helper smoke。
     結果：runtime / unknown / mixed 都是 status=insufficient-data、telegram_confirmed=false、strategy_consumer=fail-closed。
  3. approved production / persistent row 無法被直接消費者接受
     驗證：指定測試 + helper smoke。
     結果：allowed production row 為 confirmed=True，readonly smoke 為 status=ok、telegram_confirmed=true、strategy_consumer=pass。

  停止條件：完成 Owner 指定 L2 驗證清單即停止；未做 full pytest、production write、backfill、live Telegram。

  ## 關聯風險掃描

  CHANGELOG.md 已不再自相矛盾；沒有「未編輯 CHANGELOG.md」或等價文字。

  CLI dry-run 反證：

  - approved sample：return code 0，validation=pass，write_execution=disabled，candidate_rows=1。
  - forbidden runtime sample：return code 2，validation=fail，write_execution=disabled，candidate_rows=0，reason 為 forbidden source_family。

  指定測試已覆蓋：

  - fake execute read-after-write pass。
  - read-after-write exception secret redaction。
  - env/config credential fallback。
  - source fail-closed。
  - allowed persistent / production source row。

  diff 掃描未見：

  - DB schema / migration 檔案變更。
  - core/generator.py / Telegram formatter / VERSION 變更。
  - backfill、live Telegram delivery 入口變更。

  ## 跨區塊語意一致性

  TASK.md 要求「產品候選 diff 4 個檔案，交付文件 diff 是 CHANGELOG.md」；CHANGELOG.md 與 git diff --name-only 一致。

  TASK.md 要求不改 Telegram、策略、DB schema、live write；diff 實際只落在 evidence store、write CLI、readonly smoke script、handoff tests、CHANGELOG。

  CHANGELOG.md 的自檢命令與 QA 實跑命令一致，結果也一致：49 passed, 17 warnings。

  ## 使用者誤讀風險

  本輪未改 Telegram 報文、summary、header 或 VERSION，因此沒有新的 Owner 手機報文閱讀路徑要驗 snapshot。已確認 diff 未碰 Telegram formatter 與 core/generator.py。

  仍需注意的後續風險：--execute 路徑若真實 upsert 成功但 read-after-write 失敗，輸出會 fail closed 並把 written_rows/rows_written 顯示為 0。本輪禁止 production live write，所以不阻塞；但未來若開放正式寫入，這個文案可能讓
  Owner 誤讀「沒有任何 DB 副作用」。

  ## 質疑與反證

  主動反證 Tech 未單獨列出的直接消費者路徑：

  - build_market_theme_evidence_readonly_smoke(load_confirmed_market_theme_evidence(...))
  - runtime direct confirmed row 被降為 insufficient-data / false / fail-closed。
  - unknown provider 被降為 insufficient-data / false / fail-closed。
  - mixed production_db + runtime 被降為 insufficient-data / false / fail-closed。
  - production row 可通過為 ok / true / pass。

  清理 / 瘦身 / refactor 證據表要求：本輪不是清理任務，未適用；未看到刪除候選或「可刪 / 不可刪」判斷。

  ## 未測項目

  - 未做 production live Supabase write。
  - 未做 formal backfill / replay。
  - 未發 live Telegram。
  - 未驗 GitHub runner 真實 secrets。
  - 未驗 production evidence table 實際資料內容正確性。
  - 未做 full pytest，符合本輪 normal_patch / L2 停止條件。

  ## QA 結論

  通過

  可吸收範圍限於目前 tracked diff：4 個產品候選檔案與 CHANGELOG.md。不要把 worktree 本機 dummy config.py 或任何未追蹤環境檔併入交付。
