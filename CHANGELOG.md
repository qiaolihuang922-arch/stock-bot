# CHANGELOG: v20.2.4 QA 阻塞修正 - 強勢準備 summary overflow 不混桶

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - 判斷：本輪只修 Telegram summary 的強勢準備 overflow 顯示與補測試；不改策略 threshold、DB、watchlist、live/backfill，因此不是 risk_patch。
  - 本輪是 QA 阻塞修正：保留既有 v20.2.4 候選 diff，只做最小增量修正。

  ## 修改內容

  - 修正 強勢準備 summary overflow：
      - 隱藏項若全部同一狀態，仍可輸出 另 N 檔同狀態見詳情。
      - 隱藏項若跨多種狀態，改輸出分類數量，例如 另 3 檔：過熱降溫 1、突破回測 2，見詳情。
  - 補 6 檔跨狀態可準備 fixture：
      - 驗證 summary 最多列 3 檔明細。
      - 驗證 overflow 不使用誤導的 同狀態。
      - 驗證可買仍為 0。
      - 驗證漏斗與未持倉詳情一致。

  ## 修改檔案

  - core/generator.py
      - 本輪增量：修正 format_strong_prepare_summary() overflow 文案。
      - 既有候選 diff 保留：v20.2.4 版本、強勢準備層、可準備 funnel、summary / 漏斗 / 詳情同步。
  - tests/test_generator_report.py
      - 本輪增量：新增 test_v20_2_4_r3_hot_prepare_overflow_counts_hidden_statuses。
      - 既有候選 diff 保留：v20.2.4 R3 強勢偏熱 formatter fixture。
  - core/market_theme_evidence.py
      - 既有候選 diff 保留，未在本輪 QA 阻塞修正中改動。
  - tests/test_market_theme_evidence.py
      - 既有候選 diff 保留，未在本輪 QA 阻塞修正中改動。
  - tests/test_notifier.py
      - 既有候選 diff 保留，未在本輪 QA 阻塞修正中改動。

  ## 最小改動策略

  - 只改 format_strong_prepare_summary() 的 overflow 行為。
  - 不重排 summary 區塊。
  - 不修改強勢準備 bucket 判斷。
  - 不修改 BUY / WAIT / FAIL 決策。
  - 不碰 DB、watchlist、live Telegram、backfill。

  ## 契約影響

  - Telegram summary 顯示契約有最小修正：
      - 強勢準備 overflow 不再把跨狀態隱藏標的寫成 同狀態。
      - 同狀態 只在隱藏項實際同一狀態時輸出。
  - 未改函式回傳結構。
  - 未改 Telegram payload shape。
  - 未改 message list 順序。
  - 未改策略 decision 或 threshold。
  - 版本維持 v20.2.4。

  ## 直接消費者同步

  - Owner 手機 Telegram summary：已同步 overflow 文案。
  - Telegram formatter output：已補 6 檔跨狀態 fixture。
  - 未持倉漏斗：測試確認 可買 0｜可準備 6（不可買）｜僅追蹤 1｜淘汰 1。
  - 未持倉詳情卡：測試確認 6 檔仍分別顯示 可準備｜漲停鎖價 / 過熱降溫 / 突破回測。
  - Notifier / market evidence 相關既有 v20.2.4 測試已一起重跑。

  ## 未影響模組

  - 策略 threshold：未改。
  - RR / 過熱 / 冷卻 / 回測 / 量能 / 突破門檻：未改。
  - DB schema / Supabase write：未改、未執行 live write。
  - Watchlist：未改。
  - Live Telegram delivery：未執行。
  - Replay / backfill：未執行。
  - 持倉停利 / 停損 / execution dedupe：未改。

  ## 已跑自檢命令

  - python -m pytest tests/test_generator_report.py -k "v20_2_4_r3_hot"
      - 結果：collection error；原因是預設 x86_64 Python 載入 .venv 中 arm64 pydantic_core 架構不相容。
  - /usr/bin/arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_4_r3_hot"
      - 結果：2 passed, 59 deselected。
  - /usr/bin/arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -k "v20_2_4" tests/test_market_theme_evidence.py tests/test_notifier.py -k "v20_2_4 or market_theme or notifier"
      - 結果：19 passed, 59 deselected。
  - git diff --check
      - 結果：通過。

  ## 殘留風險

  - 自檢需用 arch -arm64 .venv/bin/python；預設 Python 仍會因 runner / venv 架構不一致無法 collection。
  - 未跑 full pytest，符合本輪 normal_patch / QA 阻塞修正的最小驗證範圍。
  - 未執行 live Telegram、Supabase write、正式 backfill。

  ## 旁支待辦

  - 若未來要重新設計整份未持倉準備 / 僅追蹤排序，應另開 normal_patch 或 minor 任務。
  - runner 可另補：在 worktree .venv 指向 arm64 主 repo venv 時，自動用 arch -arm64 跑測試，避免預設 x86_64 Python collection error。
