# CHANGELOG: 05/31 holiday report execution memory fail-closed fix

  ## 任務尺寸與風險

  - 任務尺寸判斷：risk_patch。
  - 原因：涉及持倉停利去重、使用者可見 Telegram 報文主行動、明日計畫與 production cross-day execution memory fail-closed 語意。
  - 本輪只修 QA 阻塞點，保留既有候選 diff 中已合格的 execution memory、evidence 日期、trend lookback、strategy sample 分層修正。

  ## 修改內容

  - 修正 core/generator.py：
      - 當 second-stage take-profit 且 cross_day_context.source_status=ready，同時 previous_action=take_profit 或 dedupe_guard=prior_take_profit_completed/same_day_executed，但 execution_memory 缺失或 sold_shares<=0 時，
        狀態改為 blocked。
      - blocked 文案維持 fail closed：停利記憶不足 / execution memory insufficient-data｜不輸出重複停利股數。
      - blocked 狀態不落回「第二段停利」本次建議股數，也不列入 pending 明日計畫。
      - 保留已存在的正向路徑：production execution memory 有 sold_shares>0 時顯示 latest trade date、sell deltas、remaining shares，並標示第二段已執行。
      - 報文版本維持候選 diff 的 v20.4.7。
  - 擴充 tests/test_generator_report.py：
      - 新增 QA 指定負面案例：2356、2026-05-31 假日、previous_action=take_profit、dedupe_guard=prior_take_profit_completed、execution_memory=None。
      - 同測試覆蓋 execution_memory.sold_shares=0。
      - 斷言 action 為 停利記憶不足，summary/card 不含「本次建議 56 股」，且 summary 不含「明日風控｜第二段停利」。
  - 保留既有候選 diff：
      - services/cross_day_context.py 的 execution memory 組裝。
      - core/market_theme_evidence.py、services/market_theme_evidence_store.py 的 evidence date / lookback 展示。
      - services/strategy_evidence.py 的 strategy sample 分層文案。
      - tests/test_market_theme_evidence.py 相關覆蓋。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - services/cross_day_context.py
  - core/market_theme_evidence.py
  - services/market_theme_evidence_store.py
  - services/strategy_evidence.py
  - tests/test_market_theme_evidence.py

  ## 最小改動策略

  - 只在既有 second_take_profit_execution_state() 判斷中補足「source ready 但停利 execution memory 欄位不足」的 blocked 分支。
  - 未改策略閾值、買點、DB schema、production write path、live Telegram delivery、報文分組順序。
  - 未重構持倉狀態機；只同步既有直接呼叫方對 blocked state 的文案與排序。

  ## 契約影響

  - 使用者可見報文版本：v20.4.7。
  - second_take_profit_execution_state() 內部 helper 回傳沿用既有 dict shape，候選 diff 已加入 execution_memory、realized_profit_taken_ratio 供 formatter 使用。
  - message list / 報文分組順序未變。
  - payload / DB write / CLI 輸出未變。
  - production source 缺失、錯誤、資料不足，或 source ready 但 prior take-profit execution memory 欄位不足時，皆 fail closed，不輸出明確重複賣出股數。
  - 無 DB schema、RLS、grant、policy、role、index、constraint 變更。
  - 無 live write、無 live Telegram、無正式 backfill。

  ## 直接消費者同步

  - Summary：2356 欄位不足時顯示 blocked 語意，不顯示「本次建議 56 股」。
  - 持倉卡片：主行動同步為「停利記憶不足」。
  - 今日交易 / 已執行區塊：只有 production execution memory 足夠時才顯示已執行。
  - 持倉風控：blocked 顯示 fail-closed 語意。
  - 明日計畫：blocked 不進 pending plan，不列出「明日風控｜第二段停利」。
  - 索引 / detail formatter：沿用同一 position_summary_action() 與 second_take_profit_context_text()，避免跨區塊語意分裂。
  - market/theme evidence 與 strategy evidence 直接消費者保留候選 diff 的日期、lookback、sample 分層同步。

  ## 未影響模組

  - 策略核心買賣分數、進出場閾值、持倉數量計算公式。
  - DB schema / production write path / RLS / grant / policy。
  - live Telegram delivery。
  - full replay / full backfill。
  - 未持倉買點放寬或新增推薦。

  ## 已跑自檢命令

  - PYTHONPATH=. arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -q
      - 結果：71 passed。
  - PYTHONPATH=. arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_cross_day_context.py -q
      - 結果：39 passed。
  - git diff --check
      - 結果：通過。

  ## 殘留風險

  - 未跑 full pytest；本輪依 risk_patch/L2 只跑 touched paths 與直接契約測試。
  - 未連 production DB、未 live Telegram、未 replay/backfill。
  - 其他股票若也有 prior action 但 execution memory 欄位不足，會走同一路徑 fail closed；未逐檔做資料驗證。
  - TASK.md 仍有重複拼接痕跡，本輪未改任務文件。

  ## 旁支待辦

  - 若後續要覆蓋更多 historical execution memory 邊界，可另開任務補 production-like fixture matrix。
  - 若要驗證 05/31 完整手機報文實例，交由 QA 依 TASK.md、本 CHANGELOG、git diff 與局部源碼做 L2 驗收；Tech 不宣告 QA 通過。
