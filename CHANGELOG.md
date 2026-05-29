# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - 風險判斷：Telegram 盤後使用者可見文案、未持倉漏斗與詳情索引契約調整；未改策略分類、資料來源、DB payload 或 live delivery。

  ## 修改內容

  - 將 Telegram formatter 版本常量升至 v20.2.5。
  - 盤後今日交易區塊改為 今日交易 / 新增交易建議：無，避免與已執行交易紀錄並存時被誤讀成今天沒有交易。
  - 未持倉漏斗在 僅追蹤 = 0 時不再輸出僅追蹤拆分行，也不輸出 等冷卻 0、等回測 0、等RR修復 0、等量能 0。
  - 可準備與僅追蹤合計文案改成清楚區分準備/追蹤：有可準備且無僅追蹤時顯示 可準備 N 檔，不列入交易執行。
  - 詳情索引改為分開列 可準備 N、僅追蹤 N、淘汰 N，不再用 未持倉追蹤 8 混稱可準備 8。
  - 新增 05/29 盤後 fixture：可買 0、可準備 8、僅追蹤 0、淘汰 2、英業達今日已賣 187 股、無新增交易建議。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_notifier.py
  - tests/test_market_theme_evidence.py

  ## 最小改動策略

  - 只改 formatter 層文案組裝與對應文字契約測試。
  - 未修改 unheld_funnel_state、策略門檻、分類邏輯、evidence provider、DB/write path、watchlist、replay/backfill。

  ## 契約影響

  - Telegram header 版本字串：v20.2.4 -> v20.2.5。
  - Telegram 使用者可見文案有變：
      - 今日交易紀錄 / 無新增 -> 今日交易 / 新增交易建議：無
      - 僅追蹤拆分行只在有非零僅追蹤分類時輸出，且只列非零分類。
      - 詳情索引不再輸出 未持倉追蹤 N，改列 可準備 N 與 僅追蹤 N。
  - 未改函式回傳結構、payload shape、DB schema 或策略 decision。

  ## 直接消費者同步

  - formatTelegramSummary 直接輸出的 Telegram message list 已同步。
  - format_unheld_funnel 與 detail_index_text 的 formatter 文字契約測試已同步。
  - notifier 保留最後一則 summary header 的測試已同步至 v20.2.5。
  - market/theme evidence 相關 summary header 測試已同步至 v20.2.5。

  ## 未影響模組

  - 策略門檻：未改。
  - 可買 / 可準備 / 僅追蹤 / 淘汰分類邏輯：未改。
  - R3 進攻偏熱判斷：未改。
  - evidence provider：未改。
  - DB schema / DB payload / Supabase write path：未改。
  - watchlist：未改。
  - live Telegram delivery：未執行、未改。
  - replay / backfill：未執行、未改。

  ## 已跑自檢命令

  - PYTHONPYCACHEPREFIX=/private/tmp/tech_write_pycache python3 -m py_compile core/generator.py tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py
      - 結果：通過。
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py tests/test_market_theme_evidence.py
      - 結果：79 passed, 21 warnings。
  - git diff --check
      - 結果：通過。

  ## 殘留風險

  - 直接用預設架構執行 pytest 會因既有 .venv 的 pydantic_core arm64 / x86_64 架構不相容在 collection 階段失敗；使用 arch -arm64 .venv/bin/python 可正常通過目標測試。
  - 本輪未做 full pytest、replay、backfill、DB payload 驗證，符合 TASK 的 L2-lite 邊界。

  ## 旁支待辦

  - 證據鏈補強、可準備排序品質、R3 熱度判斷、更多未持倉分類重設、完整報文重構、全量 snapshot 清理均未納入本輪。
