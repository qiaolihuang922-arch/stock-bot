# CHANGELOG:

  ## 任務尺寸與風險

  - 任務類型：risk_patch
  - 原因：本輪改 Telegram 使用者可見 message list、2356 execution-memory stale-state guard、報文版本字串；未改 BUY / SELL / TP / SL 策略 decision engine、DB schema/write path、live delivery。

  ## 修改內容

  - 將報文版本升為 v20.4.11。
  - formatTelegramMessages() 輸出順序固定為：
      1. summary_message：手機第一屏決策摘要、版本、報告日/交易日、source health。
      2. action_body_message：持倉卡與未持倉/新倉分組，給 Owner 手機直接看行動主體。
      3. evidence_compact_message：壓縮 holdings、execution memory、candidate source、strategy/market evidence 狀態。
      4. details_backup_message：僅 include_detail=True 時追加，放完整備查 detail，位於最後。
  - 2356 第二段停利 execution memory 增加 stale guard：跨日 position_events 只有一般停利或單筆舊停利，未確認第二段 event 時，fail closed 為 停利記憶不足，不顯示第二段已執行、不輸出重複已賣股數、不進已執行清單。
  - 新增 compact evidence formatter，將 source/backtest/detail 長行壓縮到 evidence/details，保留 decision-critical source truth。
  - evidence_manifest 補 stock.<name>.execution_memory 欄位，對齊 positions / position_events source truth。

  ## 修改檔案

  本輪產品可吸收 diff：

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py

  目前 worktree 仍存在、但不得用本輪產品結論整包吸收的旁支 diff：

  - core/market_theme_evidence.py
  - scripts/smoke_market_theme_evidence_readonly.py
  - services/strategy_evidence.py
  - tests/test_strategy_evidence.py
  - tools/cao_agent/run_auto_dev_cycle.sh
  - tools/cao_agent/run_qa_code.sh

  說明：上述旁支 diff 來自先前 market/theme、strategy evidence 與 runner 流程任務；本輪只以 generator 報文順序、2356 execution-memory 顯示 guard、噪音壓縮與對應測試作為可吸收產品範圍。

  ## 最小改動策略

  - 只碰 Telegram generator、完整報文測試與版本檢查。
  - 未改策略核心、持倉決策計算、DB schema、DB write、backfill、live Telegram。
  - 沒有重構旁支模組；既有 v20.4.10 source manifest / fail-closed 契約保留並擴充 execution_memory 欄位。

  ## 契約影響

  - 使用者可見版本：v20.4.11。
  - Message list contract：summary -> action body -> compact evidence -> optional details backup。
  - Public helper / payload：未改 DB payload、write shape、strategy decision return shape。
  - 報文分組：持倉卡與未持倉卡合併為同一 action body message；直接測試 helper 已同步。
  - 2356 stale execution-memory：未確認第二段 event 時 fail closed，不再沿用舊停利狀態當第二段完成。

  ## 直接消費者同步

  - Owner Telegram 手機閱讀：先看 summary，再看行動主體，再看 compact evidence，最後才是 details backup。
  - production report / Telegram rendering path：formatTelegramMessages() 已同步輸出順序。
  - QA fixture：補完整 06/01 類 message list、2356 still holding no confirmed second TP、noise reduction missing source。
  - 下游人工判斷：保留 holdings / execution_memory / source health 關鍵真相，不把缺源候選放入可買或明日下單。

  ## 未影響模組

  - BUY / SELL / TP / SL 策略 decision engine 未改。
  - DB schema、RLS、grant、policy、role、index/constraint 未改。
  - production write path、live Telegram delivery、replay/backfill 未改。
  - market/theme evidence 與 strategy sample source-of-truth 分層未改。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py
      - 結果：passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/strategy_evidence.py
      - 結果：passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py
      - 結果：79 passed，warnings 為既有第三方 deprecation。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_strategy_evidence.py tests/test_market_theme_evidence.py tests/test_notifier.py
      - 結果：129 passed，warnings 為既有第三方 deprecation。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_cross_day_context.py tests/test_analysis_engine.py
      - 結果：38 passed。
  - git diff --check
      - 結果：passed。

  ## 殘留風險

  - QA 已驗證 Architect 提供的 production read-only artifact：2356 `positions` 目前為 `shares=0 / CLOSED`，`position_events` 有 sell summary 但無 second-stage-like labels。這可支持 report fail-closed guard，但不代表已校正 ledger。
  - 工作樹已有前序 dirty files；本輪實作只依 TASK 範圍修改 generator 與相關測試，未處理旁支 dirty diff。
  - Telegram reply markup 仍可能附在最後一則 message，屬既有旁支 delivery consumer 風險，本輪未改。

  ## 旁支待辦

  - 另開任務評估 Telegram reply markup 在 summary-first message order 下的按鈕落點。
  - 若 Owner 認定 2356 實際未賣，另開 production ledger/source-of-truth 稽核任務；本輪未寫 DB、不修正 ledger。
  - 若 production ledger 需要更明確標記第二段停利 stage，另開資料契約任務；本輪未改 DB schema。

  ## 清理 / 瘦身 / refactor 證據表

  - 不適用。本輪不是清理 / 瘦身 / refactor 任務。
