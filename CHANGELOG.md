# CHANGELOG:

  ## 任務尺寸與風險

  - 任務類型：risk_patch
  - 判斷：本輪涉及使用者可見報文分組 / 卡片標題 / 持倉風控主行動 / D1 防抖顯示與 replay probe，屬策略報文風險修補；本次追加修正只限 QA blocked 指出的 D1 防抖 card title residual 與 CHANGELOG 對齊。
  - 版本：v20.4.33

  ## 修改內容

  - 修正 D1 防抖降級後的未持倉卡片標題：前態為淘汰 / failed / weak 且單次 BUY 被維持保守側時，不再顯示 ⛔ 不買｜進場，改顯示保守 label 前態待確認。
  - 保留現有 D1 防抖實作：單次 BUY 不直接由淘汰 / FAIL / 結構弱翻可買；連續確認且 breakout_distance <= 1% 才允許可買。
  - 保留 v20.4.33 既有 diff：同日建倉快速止損 / 減碼、過熱 RR 隱藏、簡報原因行壓縮、未持倉回測行一致、盤中盤後共用降噪、策略證據報文消費 probe。
  - 新增 / 更新 consumer/message-list 測試：06/03 replay probe 斷言整份 message list 不含 不買｜進場，並斷言光寶科 D1 防抖卡片顯示 不買｜前態待確認。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - services/analysis.py
  - tests/test_analysis_engine.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tests/test_strategy_evidence.py

  未修改：

  - services/strategy_evidence.py

  ## 最小改動策略

  - 本次 QA blocked 修正只改 presentation/report.py 的 D1 防抖降級 title label 分支，未更動 BUY 判斷、RR 公式、DB path 或整體策略方向。
  - 測試只在既有單卡 probe 與 06/03 message-list replay probe 補上 不買｜進場 反證。
  - 未重構、未新增依賴、未修改主 repo、未 commit / push。

  ## 契約影響

  - 使用者可見報文版本同步為 v20.4.33。
  - 未改函式回傳結構、payload shape、DB schema/write path 或 public helper contract。
  - 使用者可見卡片文字契約有修正：D1 防抖保守降級時，secondary label 不再使用進場語意，改為 前態待確認。
  - 報文分組契約維持：被 D1 防抖擋下的單次 BUY 留在保守 / 淘汰側，不列入可買。

  ## 直接消費者同步

  - presentation/report.py 的未持倉卡片 title 消費 core/generator.py funnel / evidence adjustment 結果，已同步 D1 防抖顯示。
  - tests/test_generator_report.py 已覆蓋直接卡片 consumer 與 official generator message-list replay。
  - 06/03 同層 message-list replay probe 存在且通過。

  ## 未影響模組

  - 未修改 RR 計算公式。
  - 未修改 DB schema、RLS、grant、policy、role、index、constraint。
  - 未修改 production DB write path。
  - 未執行 live Telegram。
  - 未執行正式 backfill。
  - 未修改 services/strategy_evidence.py。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_0603_v20_4_32_failure_specimen_message_list_replay
      - 結果：1 passed
  - arch -arm64 .venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py
      - 結果：240 passed
  - PYTHONPYCACHEPREFIX=/private/tmp/stock_bot_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py services/analysis.py tests/test_analysis_engine.py tests/test_generator_report.py
    tests/test_market_theme_evidence.py tests/test_strategy_evidence.py
      - 結果：passed
  - git diff --check
      - 結果：passed

  ## 殘留風險

  - Tech 自檢只代表交付前檢查，不宣告 QA 通過。
  - 本輪 replay 為等價 06/03 message-list probe；未執行 live Telegram、production write 或正式 backfill。
  - 測試仍有既有第三方套件 deprecation warnings，非本輪改動引入。

  ## 旁支待辦

  - 無本輪新增旁支待辦。
