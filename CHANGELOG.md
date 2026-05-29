# CHANGELOG: v20.2.3 二次 QA 阻塞修正

  ## 任務尺寸與風險

  - risk_patch：涉及持倉賣出行動、今日已賣股數與 Telegram 手機誤讀風險；本輪只補 QA 二次阻塞點，不擴大策略或資料模型。

  ## 修改內容

  - 修正持倉卡第二行 今日 ... 的資料來源：第二段停利 completed / partial 時，改用同一個 second_take_profit_execution_state() 判斷出的 DB / local execution / position event 今日已賣股數。
  - completed 案例持倉卡現在顯示 今日 賣 75股，不再和同卡 今日已賣 75 股｜第二段已執行 矛盾。
  - partial 案例持倉卡現在顯示 今日 賣 20股，不再出現 今日 無。
  - 保留既有候選 diff 的 completed 去重、partial 剩餘建議、unexecuted 第二段停利、本次建議與 v20.2.3 header。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tests/test_notifier.py
  - CHANGELOG.md（由 runner 寫入本交付內容）

  ## 最小改動策略

  - 只新增 holding_today_trade_text()，讓持倉卡今日交易欄在第二段停利 completed / partial 時復用既有 execution state helper。
  - 非第二段停利 completed / partial 情境仍沿用原本 position_events 的 event_summary_text()，避免改到其他持倉卡輸出。

  ## 契約影響

  - 使用者可見 Telegram 持倉卡文字修正：第二段停利 completed / partial 的今日交易欄會顯示 execution 已賣股數。
  - 未改函式回傳結構、message list 結構、Telegram payload shape、DB schema、報文分組順序或 public helper contract。
  - formatter header 維持 v20.2.3。

  ## 直接消費者同步

  - formatTelegramPositionCard() 已同步使用 holding_today_trade_text()。
  - tests/test_generator_report.py 已補 completed / partial 持倉卡斷言，覆蓋 今日 賣 75股、今日 賣 20股 與不得出現 今日 無。
  - Summary、持倉風控檢查與 execution checklist 沿用既有 v20.2.3 execution state 邏輯，無需額外同步呼叫方。

  ## 未影響模組

  - 未改策略閾值、RR、過熱、漲停不追、watchlist。
  - 未改 DB schema、Supabase write path、Telegram live delivery、replay/backfill。
  - 未改未持倉分類、市場題材 evidence 判斷或交易狀態機。

  ## 已跑自檢命令

  - .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_3 or v20_2_2_same_day_executed_take_profit or intraday_v20_0_10_execution_contract"：收集失敗，原因是 worktree .venv symlink 到主 repo .venv，其中
    pydantic_core 為 arm64，但本 shell 為 x86_64。
  - 使用同一 pytest 進程 stub supabase.create_client 後跑目標回歸：5 passed。
  - 使用同一 stub 跑 touched tests：tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py，76 passed。
  - git diff --check：通過。

  ## 殘留風險

  - execution stage 仍依現有欄位保守判斷賣出紀錄，若 DB / local execution 未來需要精準區分第二段、額外停利、其他賣出，仍需補正式 execution stage 欄位；本輪未改 schema。
  - 原生 pytest import 仍受本機 .venv 架構不相容影響；本輪自檢用 stub 避開不需觸發的 Supabase import，未做外部 DB/API 操作。

  ## 旁支待辦

  - 後續若要完全消除測試 stub，需要 runner 準備與目前 shell 架構一致的 worktree venv。
  - 若產品要精準區分第二段停利與其他同日賣出，另開任務定義 execution stage / migration / backfill。
