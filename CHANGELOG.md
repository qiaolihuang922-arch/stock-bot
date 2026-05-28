# CHANGELOG:

  ## 任務尺寸與風險

  - 本輪 Architect 指令：normal_patch。
  - 判斷理由：本輪不改產品代碼、不改測試，只重寫 CHANGELOG.md 使交付摘要覆蓋既有候選 diff；但候選 diff 本身包含 v20.2.0 Telegram 使用者可見 evidence feature、formatter header、message 文案與 notifier/header 測試同步，影
    響面高於 tiny_patch。
  - 原候選功能風險：minor / L3，因為新增市場 / 題材 evidence 使用者可見區塊與 confirmed / weak / mixed / stale / absent contract，但不改策略 decision、DB、schema、cache、provider 外部資料源、live write、backfill 或 live
    Telegram。

  ## 修改內容

  - 重寫本輪完整 CHANGELOG，修正先前 CHANGELOG.md 仍描述 v20.1.3 盤後 summary 修正、未覆蓋目前候選 diff 的問題。
  - 候選 diff 已實作 v20.2.0 market theme evidence feature：
      - core/market_theme_evidence.py 擴充 source contract，加入 source_type、source_name、freshness_reason、level、sources、source_types、confirmed_source_types、theme、market_direction、execution_implication 等
        evidence 欄位。
      - confirmed 判斷改為必須同時具備 fresh 且 supportive 的 watchlist_breadth 與 market_index 或 sector_index，不得再只靠 report-derived、單一來源、缺 contract 欄位或 legacy family 湊出 confirmed。
      - freshness precedence fix：freshness=stale / unavailable / missing 會優先降級，即使 freshness_reason=same_trade_date 也不得 confirmed；older_than_threshold 視為 stale。
      - 新增 weak / mixed / stale / absent 降級邏輯與手機優先 summary lines。
      - core/generator.py 將 Telegram VERSION 升至 v20.2.0，把 report as_of 傳入 evidence provider，並移除高風險 AI / 電子供應鏈仍偏多 主線句，改為 市場偏多但買點未成立。
      - 測試同步 v20.2.0 header、evidence 五類 fixture、freshness precedence、formatter summary、notifier payload/header smoke。

  ## 修改檔案

  - core/market_theme_evidence.py
  - core/generator.py
  - tests/test_market_theme_evidence.py
  - tests/test_generator_report.py
  - tests/test_notifier.py
  - CHANGELOG.md

  ## 最小改動策略

  - 本輪只修正交付摘要，不再修改產品代碼或測試。
  - CHANGELOG 只覆蓋目前 worktree 已存在的候選 diff，不新增需求、不補 PM 未定義行為、不擴大輸出契約。
  - 不做 unrelated formatter 重構、不碰 strategy decision、不接外部 provider、不新增持久化。

  ## 契約影響

  - Telegram header / formatter 可見版本升至 v20.2.0。
  - Market theme evidence public payload 擴充欄位；保留既有 source_family_details / source_families，並新增 sources / source_types / confirmed_source_types 等結構化欄位。
  - Evidence level contract 明確為 confirmed / weak / mixed / stale / absent。
  - confirmed contract 收斂：必須有 fresh supportive watchlist_breadth 加上 fresh supportive market_index 或 sector_index。
  - formatter summary 新增短句 evidence 區塊：先顯示 level 與限制，再顯示最多三個 runtime source freshness 摘要。
  - Telegram message list 型別與 notifier payload shape 不變；summary 仍為 formatter 產出的最後一則訊息。
  - 不改 DB payload、strategy decision、watchlist 成員、持倉主行動、買賣建議或下單清單。

  ## 直接消費者同步

  - Owner 手機 Telegram 報文：tests/test_market_theme_evidence.py 與 tests/test_generator_report.py 覆蓋 weak / confirmed / stale / mixed / absent 相關輸出與不可買限制。
  - core/generator.py 報文組裝：已同步 VERSION = "v20.2.0"，並將 market_summary.as_of 傳給 evidence provider 作為 runtime freshness 來源。
  - Telegram notifier message list / payload contract：tests/test_notifier.py 已同步最後 summary header v20.2.0，並確認 send_many() 仍保留最後 message 原文與 reply_markup=None contract。
  - Formatter snapshot / regression tests：tests/test_generator_report.py 已同步所有既有 header 期望到 v20.2.0，並檢查不可買、無新增下單、主線文案與 summary 順序未被 evidence confirmed 誤導。
  - 後續 DB/cache 規劃消費者：本輪沒有新增 DB/cache contract，無需同步 migration、schema 或 provider write path。

  ## 未影響模組

  - 未改 strategy decision、買點、RR、冷卻、回測、量能或風控條件。
  - 未改持倉主行動、加碼 / 減碼 / 停損 / 停利規則。
  - 未改 watchlist 成員、scheduler / cron、行情 provider 或外部 provider adapter。
  - 未新增 Supabase schema、table、migration、RLS、index 或 rollback。
  - 未寫 Supabase cache，未新增長期 disk cache。
  - 未改 DB write path、DB payload schema、snapshot persistence。
  - 未執行 replay/backfill 寫庫，未執行正式 backfill。
  - 未執行 live Telegram delivery。
  - 未執行 live Supabase write。
  - 未下載新依賴，未接 news scraping、付費 API 或長期 scheduler。

  ## 已跑自檢命令

  - .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py
      - 結果：失敗於 collection。
      - 原因：目前 shell 預設 interpreter 以 x86_64 載入主 repo .venv 的 arm64 pydantic_core，出現 incompatible architecture。
  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py
      - 結果：69 passed, 21 warnings。
      - warnings 來自既有依賴 deprecation / Python 3.9 support 訊息，非本輪新增測試失敗。

  ## 殘留風險

  - Tech 自檢只代表交付前檢查，不宣告 QA 通過。
  - Architect 指出 QA 目前是 conditional pass：freshness block 已解除，但需複核本次重寫後的 CHANGELOG.md 是否與整個 worktree diff 一致。
  - 本輪沒有執行 full pytest、replay/backfill dry-run、live write 檢查或 QA L3 完整矩陣；需由 QA 依 TASK.md、本 CHANGELOG、git diff 與必要局部源碼重新複核。
  - 現有測試使用主 repo .venv；若 runner 以非 arm64 interpreter 執行，會重現 pydantic_core architecture mismatch，需要 runner 固定使用 arch -arm64 .venv/bin/python 或準備 matching architecture venv。
  - Evidence formatter 目前只列前三個 runtime source freshness；若未來 PM 要更完整 source audit，需要另開任務定義手機摘要與詳情分工。

  ## 旁支待辦

  - QA 依 conditional pass 要求複核：CHANGELOG.md 是否完整覆蓋 core/market_theme_evidence.py、core/generator.py、tests/test_market_theme_evidence.py、tests/test_generator_report.py、tests/test_notifier.py 與本文件。
  - 若後續要把 evidence 接到 DB/cache/provider/live pipeline，需另走 PM/Owner approval gate；本輪不得順手落地。
  - 若需要解決 venv architecture mismatch，應由 runner / 環境任務處理，不併入本產品 diff。
