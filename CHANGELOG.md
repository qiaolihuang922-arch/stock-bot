# CHANGELOG: Telegram Breakout Distance Always Visible v20.2.1

  ## 任務尺寸與風險

  - 任務尺寸：tiny_patch
  - 風險判斷：只修 Telegram formatter 卡片盤面行顯示與 header 版本，不改策略 decision、突破門檻、資料來源、DB、watchlist、live Telegram 或 backfill。

  ## 修改內容

  - core/generator.py 的 VERSION 由 v20.2.0 升為 v20.2.1。
  - 新增卡片專用 card_breakout_distance(data)：
      - 優先使用 data.breakout_distance。
      - 若 data.breakout_distance 缺失、None 或空字串，fallback 到 result.breakout_distance。
      - 缺資料時回傳 None，避免輸出 0%、None%、空括號或假距離。
  - 持倉卡片 formatTelegramPositionCard 與未持倉卡片 formatTelegramUnheldCard 改用同一距離讀取規則。
  - 補 tests/test_generator_report.py 覆蓋：
      - 持倉：已突破、臨界突破、接近突破、遠離突破。
      - 未持倉：已突破、臨界突破、接近突破、遠離突破。
      - data.breakout_distance=None 時 fallback 到 result.breakout_distance。
      - 完全缺距離時不得輸出假距離。
  - 同步 tests/test_notifier.py、tests/test_market_theme_evidence.py、tests/test_generator_report.py 的 v20.2.1 header 期望。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_notifier.py
  - tests/test_market_theme_evidence.py
  - CHANGELOG.md（由 runner 以本回覆覆寫）

  ## 最小改動策略

  - 只改卡片盤面行的距離來源選擇，不改 semantic_position 的既有括號距離格式。
  - 不新增報文區塊、不重排 summary、不改漏斗、不改持倉主行動。
  - 測試只覆蓋本任務指定 formatter 與 direct consumer header smoke。

  ## 契約影響

  - 使用者可見 Telegram header 升為 v20.2.1。
  - 持倉與未持倉卡片盤面行在有距離資料時，一律保留既有括號距離。
  - 缺距離資料時維持省略距離，不輸出假距離。
  - 未改函式回傳結構、message list shape、Telegram payload shape、DB payload 或報文分組。

  ## 直接消費者同步

  - Owner 手機 Telegram 報文：持倉 / 未持倉卡片盤面行同步。
  - Telegram message list formatter output：tests/test_generator_report.py header 與卡片輸出同步。
  - Telegram notifier payload consumer：tests/test_notifier.py header smoke 同步，payload shape 未改。
  - Market theme evidence formatter coverage：tests/test_market_theme_evidence.py header 期望同步。

  ## 未影響模組

  - 未改策略 decision。
  - 未改突破門檻或分類邏輯。
  - 未改 services/analysis.py。
  - 未改 core/watchlist.py。
  - 未改 DB schema / migration / Supabase write path。
  - 未執行 live Telegram delivery。
  - 未執行 replay / backfill。
  - 未改 market / theme evidence 的買點判斷。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py
      - 結果：72 passed, 21 warnings
  - git diff --check
      - 結果：通過，無 whitespace error。
  - git status --short
      - 結果：顯示本輪產品 / 測試檔與 CHANGELOG.md 修改，符合本次交付摘要範圍。

  ## 殘留風險

  - 測試環境 .venv 需用 arch -arm64 執行，直接用預設架構 Python 會遇到既有 binary architecture mismatch。
  - 本輪未跑 full pytest，符合 TASK 的 L1 / tiny_patch 停止條件。

  ## 旁支待辦

  - 無本輪阻塞旁支。
  - 若後續要把缺距離改成明確文案「距離缺資料」，需由 PM 另定顯示契約；本輪沿用可省略距離的 TASK 允許形狀。
