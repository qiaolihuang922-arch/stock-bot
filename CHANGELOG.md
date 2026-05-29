# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch。
  - 原因：本輪涉及持倉停利 / 賣出行動的 Telegram 使用者可見文案，若標示不清會讓 Owner 誤讀為同級重複停利；實作範圍收斂在 formatter 與直接測試，未改策略門檻。

  ## 修改內容

  - 保留既有 v20.2.2 候選 diff，補上 QA 阻塞案例：
      - 同日已有 position_events.sold_shares > 0，但策略層仍回傳 TAKE_PROFIT_25 / TAKE_PROFIT_50 且有可賣股數時，formatter 主行動改顯示 第二段停利。
      - summary / 今日交易執行 / 持倉風控檢查 / 持倉卡會同行顯示：今日已賣 N 股｜剩餘 N 股｜本次建議 N 股。
      - 持倉卡補上第二段停利的觸發條件，避免只顯示一般 停利。
  - 補測 QA 指出的邊界 fixture：
      - 英業達今日已賣 112 股、剩餘 188 股、策略仍建議本次賣 47 股時，summary 與持倉卡必須顯示 第二段停利｜今日已賣 112 股｜剩餘 188 股｜本次建議 47 股。
  - 同步 v20.2.2 header 測試期望。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tests/test_notifier.py
  - CHANGELOG.md

  ## 最小改動策略

  - 只新增 formatter 內部判斷與文案組裝 helper。
  - 未修改 services/analysis.py 策略層回傳、停利門檻、股數計算、DB schema、watchlist、live delivery、backfill。
  - CHANGELOG.md 僅同步本輪交付摘要，未承載產品邏輯。

  ## 契約影響

  - Telegram formatter 使用者可見輸出有變更：
      - 同日已賣且仍有可執行停利建議時，主行動由一般 停利 改為 第二段停利。
      - 同行新增今日已賣股數、剩餘股數、本次建議股數。
  - formatter header 版本同步為 v20.2.2。
  - 未改 DB payload、Telegram API payload shape、message list 結構、函式回傳結構或策略 decision 結構。

  ## 直接消費者同步

  - Owner 手機 Telegram summary：已同步 第二段停利 與股數文案。
  - 今日交易執行 / 持倉風控檢查：透過 holding_execution_item、pending_trade_items、priority rank 同步。
  - 持倉卡：透過 position_summary_action、holding_detail_decision_lines、holding_reason_line、holding_next_step_line 同步。
  - notifier version header 測試：已同步 v20.2.2 期望。

  ## 未影響模組

  - 未改策略門檻、RR、過熱、漲停不追。
  - 未改強勢市場準備層。
  - 未改 DB / Supabase 寫入。
  - 未改 watchlist。
  - 未執行 live Telegram、live Supabase write、正式 backfill。
  - 未做全量報文重排或旁支清理。

  ## 已跑自檢命令

  - python -m pytest tests/test_generator_report.py -k "v20_2_2"：失敗，原因是 python command not found。
  - .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_2"：收集失敗，原因是目前 shell 為 x86_64，但 .venv 依賴含 arm64 pydantic_core。
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_2"：3 passed。
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py tests/test_analysis_engine.py：108 passed。
  - git diff --check：通過。

  ## 殘留風險

  - 本輪只處理 formatter 對同日已賣後再次停利的顯示明確性；策略層為何仍回傳 TAKE_PROFIT_25 不在本輪修改範圍。
  - 測試需用 arch -arm64 .venv/bin/python 執行；直接 .venv/bin/python 在目前 shell 架構下會遇到相依套件架構不相容。

  ## 旁支待辦

  - 測試 runner 可補強 Python 架構選擇，避免 worktree .venv 在 x86_64 shell 下誤跑。
  - 若後續 Owner 要求「同日已賣後策略層不得再回傳 TAKE_PROFIT」，需另開策略任務，不能併入本輪 formatter patch。
