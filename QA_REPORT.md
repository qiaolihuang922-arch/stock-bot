# QA_REPORT:

  ## 測試範圍

  - 任務尺寸 / qa_level：risk_patch / L3-lite。本輪最值得驗的是 fail-closed 契約，不把範圍擴成 replay/backfill/live delivery。
  - 已讀：TASK.md、CHANGELOG.md、git status、git diff、core/generator.py、core/market_theme_evidence.py、services/position_store.py、相關測試。
  - 已跑：
      - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_position_store.py tests/test_notifier.py：88 passed。
      - arch -arm64 .venv/bin/python -m pytest：162 passed。
      - git diff --check：通過。
      - QA 額外反證腳本：watchlist breadth 在 DB evidence 缺失時 confirmed=False、level=absent、runtime_fallback=False，且 summary 不含 confirmed / weak/runtime。

  ## 風險預算與停止條件

  本輪只抓 3 個高價值風險：

  1. 缺持倉來源仍產生買賣 / 持倉建議：以 generate_report() fail-closed 測試與程式碼檢查驗證。
  2. watchlist breadth fallback 被包裝成市場證據或 confirmed：以 evidence provider 額外負面案例驗證。
  3. TASK / CHANGELOG / diff 不一致導致 Architect 吸收錯 diff：以 git status、git diff --stat、檔案清單核對。

  停止條件：直接相關 fail-closed 測試通過、額外反證通過、無 schema/watchlist/live diff、可吸收 diff 與 worktree 殘留已分清。

  ## 關聯風險掃描

  - services/position_store.py：缺 Supabase、DB error、positions 0 rows 皆回 {} 並設 warning，不再回全 watchlist 0 股 fallback。
  - services/position_store.py：position_events source-error / missing-source 回 unavailable metadata 並設 warning，不再回全 0 event summary；DB query 成功但空資料仍可作為真實 0 event。
  - core/generator.py：load_positions() / load_today_position_events() 後若有 warning，立即回最小不可行動 Telegram message list，不進入行情掃描與 strategy decision。
  - core/market_theme_evidence.py：watchlist breadth 改為 watchlist_breadth_diagnostic，不進 sources，不產生 confirmed。
  - 禁止 diff：未見 DB schema、migration、watchlist、supabase function 修改；未執行 live write/backfill/Telegram delivery。

  ## 跨區塊語意一致性

  Owner 手機閱讀順序檢查：

  - 第一行 header 顯示 v20.3.1。
  - 接著先出現持倉或今日交易事件來源 warning，再出現 今日結論。
  - 新倉：無有效進場 與 原因：missing-source 在市場證據前，沒有先推薦股票。
  - 持倉 顯示 unavailable，不產生交易建議；今日交易事件 source-error 不會顯示成 今日無 / 今日 無。
  - 市場證據 顯示 unavailable，watchlist breadth 明確標為非交易診斷。

  未看到 今日可買、confirmed、weak/runtime 在缺來源路徑中重新出現。

  ## 使用者誤讀風險

  主要誤讀風險已被壓住：缺資料時第一屏不會把 fallback breadth、0 股假持倉或 position_events source-error 包成可買 / confirmed / 今日無交易。

  殘留風險：fail-closed summary 目前是最小報文，會犧牲正常詳情追溯；這符合本輪「缺來源不行動」優先級，不阻塞本輪。

  ## 質疑與反證

  - 質疑 Tech 證據表中「watchlist breadth 只作 non-trading diagnostic」：QA 額外建了支持度偏強的 results_map，確認仍為 absent、confirmed=False，formatter 不輸出 weak/runtime。
  - 質疑「持倉缺來源是否仍會掃行情後產生交易」：generate_report() 在 position warning 後直接 return [summary], None，相關測試覆蓋。
  - 質疑「今日交易事件 DB error 是否仍被當成今日無」：新增 source-error 測試確認 load_today_position_events() 不回股票全 0 summary，generate_report() 直接 fail closed，且 DB query 成功空資料仍是真實 0 event。
  - 質疑「版本同步」：core/generator.py 為 v20.3.1，相關 formatter / notifier 測試已同步；supabase/functions/telegram-execution/index.ts 仍是 v19.3，但本輪未修改 Edge Function，屬不同 callback API 版本，非本輪 Telegram
    report header。
  - 發現交付一致性問題：CHANGELOG.md 宣稱新增 tests/test_position_store.py，測試也實際依賴該檔，但該檔目前是 untracked；git diff --stat 不包含它。

  ## 未測項目

  - 未跑正式 replay/backfill、live Supabase write、live Telegram delivery，符合 TASK 禁止事項。
  - 未做全 repo runtime keyword matrix 重新驗證，只抽查本輪 runtime reachable 修改點與 Tech 證據表高風險項。
  - 未驗證 production DB 真實連線，僅驗證缺來源 / error / empty table / empty event query 的 fail-closed 行為。

  ## QA 結論

  通過

  Architect 已明確納入 tests/test_position_store.py，並補掉 QA 殘留的 position_events source-error 假 0 event 風險；未見 schema / watchlist / live write / backfill / Telegram delivery diff。
