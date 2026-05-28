# QA_REPORT:

  ## 測試範圍

  - 依據：TASK.md 要求 v20.0.12、Telegram summary 語意拆分、message order / payload shape 不變；CHANGELOG.md 宣稱只改 core/generator.py、tests/test_generator_report.py 與交付摘要。
  - 實測 diff：目前 tracked diff 只有 CHANGELOG.md、core/generator.py、tests/test_generator_report.py。未見策略、DB、watchlist、notifier payload 實作檔變更。
  - 可吸收候選 diff：上述 3 個 tracked 檔案。
  - worktree 殘留：git status --short 只顯示上述 3 個 modified tracked files；.qa_tmp/ 未進入 tracked status，不建議整包合併未審核內容。
  - 指定測試：
      - 初次未加 arch -arm64 收集失敗，原因是 x86_64 Python 載入 arm64 pydantic_core 架構不符。
      - 使用 arch -arm64 重跑：tests/test_generator_report.py tests/test_notifier.py -q，結果 48 passed, 21 warnings。
  - 補充 QA 正反例渲染：
      - message order 為 持倉標的 → 未持倉標的 → v20.0.12 summary。
      - AI summary 正例：有 AI / 電子供應鏈仍偏多，同時有 新增買點未成立、不追高、新倉：無有效進場。
      - 非 AI summary / 非 AI 標的反例：無 AI / 電子供應鏈仍偏多、無 電子供應鏈，改為 主線：市場偏多但買點未成立。

  ## 關聯風險掃描

  - core/generator.py：
      - VERSION = "v20.0.12" 已同步。
      - market_execution_bridge_lines(..., market_summary) 只在 market_summary 含 AI、人工智慧、電子供應鏈 時輸出 AI / 電子供應鏈主線；否則熱盤輸出中性主線。
      - formatTelegramMessages() 仍輸出 position_message、unheld_message、summary_message 三段，順序未改。
  - 直接消費者：
      - tests/test_notifier.py 驗證 reply markup 仍掛在最後一則 message；因 summary 仍是最後一則，Telegram 按鈕掛載契約未破壞。
      - 未見 Telegram payload shape 實作變更。
  - 未持倉卡：
      - 等回測 文案含 不可立即買入。
      - 淘汰 文案與 rejected reason 含 不代表看空產業。
  - 持倉文案：
      - 核心持倉摘要 helper 不再用 主線持倉保留，改為風控續抱 / 新增倉位等觸發語意。
      - 既有持倉卡仍可能保留原本「下一步：保留核心倉，觀察是否轉弱」等舊句，但未見暗示所有持倉都是 AI 主線或可加碼。

  ## 跨區塊語意一致性

  - 手機閱讀順序檢查：
      - Header：summary 顯示 【05/28 盤中｜v20.0.12】。
      - Summary：AI 有證據時先說主線偏多，但緊接著說 新增買點未成立，先等回測，不追高 與 新倉：無有效進場。
      - 持倉區：持倉仍是核心續抱 / 風控觀察語意，沒有 主線持倉保留 或 可加碼。
      - 未持倉區：等回測為不可立即買入；淘汰是技術觸發失效，不代表看空產業。
      - 詳情 / summary 數量：新增測試覆蓋可買 0、僅追蹤、淘汰數量與未持倉卡狀態一致。
  - formatTelegramMessages() 順序未變，summary 仍在最後，符合 notifier 將 reply markup 附在最後訊息的契約。

  ## 使用者誤讀風險

  - 已反證主要誤讀：
      - 非 AI / 非電子供應鏈 summary 與標的，即使 market_mode 是 進攻偏熱，不會硬輸出 AI / 電子供應鏈仍偏多。
      - AI 有證據時，summary 不只說主線，還同時說買點未成立、不追高、無有效進場。
      - 持倉不再被 summary helper 包成「主線持倉保留」，降低 Owner 誤判所有持倉可加碼的風險。
      - 等回測 / 淘汰卡不會被讀成可立即買入或產業轉空。
  - 殘留風險：
      - AI 主線判斷只看 market_summary 關鍵字，不看標的產業分類。這是粗粒度，但符合本輪不新增資料源、不改 watchlist 的限制；若未來 market_summary 文案含 AI 但標的清單非 AI，summary 仍會說 AI 主線，屬於上游 market_summary
        證據品質問題，本輪可接受。

  ## 質疑與反證

  - PM 是否漏需求：未發現 blocker；TASK 已要求 header、summary、持倉、未持倉、message list / payload 不變與手機閱讀路徑。
  - Tech 是否漏同步：已同步 formatTelegramSummary() 呼叫橋接函式時傳入 market_summary；測試同步 v20.0.12。
  - 測試是否只覆蓋正例：不是。Tech 新增非 AI / 非電子供應鏈負例；QA 另補不寫檔渲染檢查，確認手機順序與 notifier 最後訊息契約。
  - 是否有越界 diff：未見策略、DB、watchlist、payload shape、live delivery、backfill 相關改動。
  - TASK.md / CHANGELOG.md / git diff 一致性：一致。CHANGELOG 宣稱的修改檔案與實際 tracked diff 相符。

  ## 未測項目

  - 未跑 full pytest、replay/backfill dry-run、live Telegram delivery、live Supabase write；TASK 明確不要求且禁止 live / 正式副作用。
  - 未驗證真實 production market_summary 內容品質；本輪只驗 formatter 對既有 market_summary 字串的輸出契約。
  - 未檢查全 repo 無關模組；本輪 QA 分級為 L1+，且 diff 未碰策略與 DB。

  ## QA 結論

  通過
