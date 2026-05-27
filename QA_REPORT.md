# QA_REPORT:

  ## 測試範圍

  依據：TASK.md、CHANGELOG.md、git diff、core/generator.py、services/analysis.py、tests/test_analysis_engine.py、tests/test_generator_report.py、tests/test_notifier.py。

  版本契約核對通過：

  - TASK.md：本輪不升版，沿用 v20.0.9。
  - CHANGELOG.md：保留 core/generator.py 的 VERSION = "v20.0.9"。
  - core/generator.py：VERSION = "v20.0.9"。
  - 測試期望：tests/test_generator_report.py 仍檢查 v20.0.9。
  - 未找到 v20.0.10 殘留於上述契約檔案。

  執行測試：

  - tests/test_analysis_engine.py tests/test_generator_report.py tests/test_notifier.py -q
  - 結果：69 passed, 21 warnings
  - warnings 為既有套件 deprecation / Python 3.9 警告，非本輪失敗。

  額外 QA 反證：

  - 直接呼叫 holding_signal() 驗證今日買入一般 reduce 轉 NEW_POSITION_RISK_WATCH。
  - 直接呼叫 holding_signal() 驗證今日買入後硬停損仍為 STOP_100。

  ## 關聯風險掃描

  可吸收 diff：

  - TASK.md
  - CHANGELOG.md
  - core/generator.py
  - services/analysis.py
  - tests/test_analysis_engine.py
  - tests/test_generator_report.py

  worktree 殘留 / 不建議整包合併：

  - DISPATCH.md 仍有未提交 diff，但不在 CHANGELOG.md 修改檔案清單內，屬 Architect-controlled 狀態文件；本 QA 不把它視為 Tech 可吸收 code diff，需 Architect 另行決定是否保留。

  直接消費者核對：

  - core.generator.holding_status() 已把 position_events 與持倉股數傳入策略層。
  - render_stock()、ensure_holding_decision()、generate_report() 路徑有同步事件感知決策。
  - formatTelegramPositionCard()、summary action/note、明日清單、詳情 decision lines 已支援 POST_REDUCE_WATCH / NEW_POSITION_RISK_WATCH。
  - tests/test_notifier.py 通過，message list 發送端消費路徑未破壞。

  清理 / 瘦身 / refactor 證據表：

  - 本輪不是清理 / 瘦身 / refactor 任務，不適用 path / claim / evidence / risk / action 表。

  ## 跨區塊語意一致性

  Owner 手機閱讀順序核對：

  - Header 版本為 v20.0.9。
  - 緯創 sold_shares only fixture：策略層輸出 POST_REDUCE_WATCH，formatter 卡片顯示「減碼後觀察」，summary 明日清單顯示「緯創｜+5.00%｜減碼後觀察｜修復才恢復優先級」。
  - 同一 fixture 未出現「📌 減碼｜」「決策：減碼 25%」「緯創｜+5.00%｜減碼｜」。
  - 今日買入一般 reduce：QA 反證輸出 NEW_POSITION_RISK_WATCH 新倉風控觀察 0。
  - 今日買入硬停損：QA 反證輸出 STOP_100 停損 100% 1。
  - 今日已賣後風控升級：測試覆蓋 REDUCE_50 增量減碼與 STOP_100 不被硬鎖。

  未回退項目：

  - action-noise：test_summary_with_holding_and_buy_has_no_zero_tracking_noise 仍通過。
  - 淘汰去點名：test_rejected_summary_shows_count_not_full_four_stock_names 仍通過。
  - 未持倉漏斗母集合：test_unheld_funnel_prepare_count_has_separate_tracking_parent 仍通過。

  ## 使用者誤讀風險

  未發現會讓 Owner 把「已減碼後觀察」誤讀成「明日再減碼同級」的輸出；卡片、summary、詳情都避開同級 減碼 25% 主行動。

  未發現今日買入一般弱化被誤讀成「剛買就減碼 50%」；一般 reduce 被降為「新倉風控觀察」，硬停損仍明確顯示停損。

  剩餘需注意：DISPATCH.md 是 worktree 殘留，不應和本輪 code diff 整包合併，否則 Architect 狀態可能被非本輪 QA 吸收。

  ## 質疑與反證

  PM 是否漏需求：

  - 未發現。TASK.md 已列版本契約、直接消費者、event-aware reduce、硬風控覆蓋與手機閱讀路徑。

  Tech 是否漏同步：

  - 未發現直接消費者漏同步。策略函式新增 optional 參數，既有呼叫方不傳仍維持原行為；formatter 關鍵路徑已傳入事件資料。

  測試是否能證明沒有破壞直接消費者：

  - 指定三組測試通過，並涵蓋 strategy、formatter 長報文、notifier message list。
  - QA 額外用不落檔直接呼叫反證今日買入一般 reduce 與硬停損分支。

  QA 主動找到指定清單之外的風險：

  - 找到 DISPATCH.md worktree 殘留；已標記不可作為 Tech code diff 一起吸收。

  ## 未測項目

  未跑 full pytest、replay/backfill dry-run、live Telegram、live Supabase write；依本輪 L2 範圍與禁止事項可接受。

  未驗證正式資料庫今日交易事件來源，只驗證 position_events 進入策略與 formatter 後的契約；本輪未改 DB schema / position_store schema。

  ## QA 結論

  通過

  限制：僅通過可吸收 diff；不得建議整包合併目前 worktree，DISPATCH.md 殘留需 Architect 另行處理。
