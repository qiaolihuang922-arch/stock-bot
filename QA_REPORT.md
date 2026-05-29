# QA_REPORT:

  ## 測試範圍

  本輪判定：normal_patch / QA L2。未擴大到 full pytest、replay、backfill、live Telegram、live Supabase。

  已驗證：

  - TASK.md、CHANGELOG.md、git diff --stat/name-only 一致。
  - 可吸收 diff 僅限：CHANGELOG.md、core/generator.py、core/market_theme_evidence.py、tests/test_generator_report.py、tests/test_market_theme_evidence.py、tests/test_notifier.py。
  - forbidden diff：supabase、scripts、services、core/watchlist.py、config.py、requirements.txt、db/migrations 無 diff。
  - worktree 殘留：測試過程只使用 .qa_tmp/，未修改 tracked file；.qa_tmp/config.py 屬測試暫存，不應納入合併。

  執行命令：

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py tests/test_signal_validator.py tests/test_analysis_engine.py -q
      - 結果：120 passed, 21 warnings
  - git diff --check
      - 結果：通過
  - QA 自訂反證腳本：
      - runtime fallback 缺 index 時不 confirmed。
      - existing evidence source 存在時不誤標缺 DB/cache。
      - fallback evidence 不改原始交易 decision。
      - 手機 summary 順序與禁用文案檢查通過。

  ## 風險預算與停止條件

  最值得抓的風險：

  1. weak/runtime fallback 被誤升成 confirmed 或買入暗示。
  2. 缺 DB/cache 時文案仍模糊 absent，Owner 手機看不出缺來源。
  3. fallback evidence 影響交易分類或版本 header 未同步。

  對應驗證：

  - Fixture A/B 類型測試與 QA 自訂反證。
  - 接近 Telegram 長報文手機閱讀順序檢查。
  - 版本 header v20.3.0 檢查。
  - forbidden diff 檢查。

  停止條件已達成：

  - 無 DB/cache + runtime supportive 顯示 weak/runtime。
  - runtime 不足顯示 absent/missing-source 並列缺來源。
  - 缺 market/sector index 不出現 confirmed。
  - 交易分類不變。
  - 使用者可見版本為 v20.3.0。
  - 未擴張到 L3。

  ## 關聯風險掃描

  core/generator.py 只升 VERSION 並在 market_theme_summary_evidence() 傳入 missing_db_evidence=True。未看到策略 engine、DB schema、watchlist universe、live/backfill 路徑變更。

  直接消費者已覆蓋：

  - Telegram summary formatter。
  - market/theme evidence provider。
  - notifier 最後一則 header 保留。
  - generator report 長報文 fixture。

  QA 補充反證：existing structured evidence source 存在時，provider 不會新增 runtime fallback，也不會輸出 缺 DB evidence table/cache。

  ## 跨區塊語意一致性

  手機 summary 檢查結果：

  - 今日結論 / 新倉：無有效進場 先出現。
  - market/theme evidence 後出現，定位為背景證據。
  - 市場證據：weak/runtime 與 題材證據：weak/runtime 均明確寫「缺 index evidence，未確認」。
  - 未出現 confirmed、市場確認轉強、可進場、新增可買 等誤導語意。

  ## 使用者誤讀風險

  目前輸出能讓 Owner 區分：

  - 這是內部觀察池 runtime breadth。
  - 缺大盤/族群指數 evidence。
  - 尚未 confirmed。
  - 不構成買入、加碼或準備建議。

  未發現會讓 Owner 誤判買、賣、加碼、停損、等待或追蹤優先級的本輪新增問題。

  ## 質疑與反證

  主動質疑：

  - 若 market_theme_evidence 有現有 sources，Tech 的 fallback 是否仍會誤判缺 DB/cache？
      - 反證：自訂 existing source 案例通過，runtime_fallback=False，未列 缺 DB evidence table/cache。
  - weak runtime evidence 是否會改交易 decision？
      - 反證：呼叫 formatter evidence 後，results_map 原 decision 前後一致。
  - 手機上 weak/runtime 是否可能被讀成買入訊號？
      - 反證：summary 中先出現 新倉：無有效進場，evidence 區塊只說未確認；禁用買入語意未出現。

  ## 未測項目

  依 TASK 停止條件未測：

  - full pytest。
  - replay/backfill dry-run。
  - live Telegram delivery。
  - live Supabase write。
  - production DB schema / evidence table 存在性。
  - 正式 market_index / sector_index 外部資料接入。

  這些是旁支待辦，不阻塞本輪 normal_patch。

  ## QA 結論

  通過
