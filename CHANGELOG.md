# CHANGELOG: presentation/report Telegram message list 降噪

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - QA 分級：L2
  - 任務類型判斷：presentation / report Telegram message list 使用者可見文案與 section visibility 降噪。
  - 風險邊界：改 message list、section 顯示與 formatter 文案；不改 strategy decision、RR、DB write、payload 寫庫或 live delivery。
  - 版本：維持 v20.4.31，未升版。

  ## 修改內容

  - 無有效進場但仍有追蹤標的時，將像推薦排名的 追蹤最強 改為不可行動語意 僅追蹤，並標明 未達進場條件。
  - Telegram summary 合併重複資訊：市場/結論 合併呈現，原因/風險 合併呈現，移除原本分散的 今日結論、原因、最強、重複風險行。
  - 交易執行保留短文案與既有行動結論，不重複完整風控長句。
  - 卡片歷史 / 回測降噪：回測或歷史不可用、樣本不足、回測：-、歷史：- 類行不逐卡顯示；可用資料仍保留精簡行。
  - 資料依據 section 正常來源時隱藏；盤中預設不顯示；僅在 missing-source、source-error、insufficient-data、unresolved-conflict 等異常狀態或 evidence manifest conflict 時顯示。
  - 盤後完整版若來源異常，仍顯示單一資料依據短訊；策略樣本狀態與卡片顯示一致，不在卡片重複 策略樣本：不可用。
  - B5 card / funnel count consistency regression 保留覆蓋：等冷卻、等回測、隔日確認拆分需與卡片分類與僅追蹤總數一致。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 只處理 TASK.md 指定的 presentation/message list 降噪與對應 rendered message probes。
  - 沒有改策略判斷、買賣 / 加減碼、停損停利、RR 公式、DB schema、DB write path、production backfill 或 live Telegram。
  - 沒有清理旁支檔案，沒有擴大為全量 template 重設。
  - 本輪未直接編輯 CHANGELOG.md；由 runner 依本回答覆寫。

  ## 契約影響

  - 使用者可見 message list 有調整：summary 文案由多行 市場 / 今日結論 / 原因 / 最強 / 風險 收斂為 市場/結論 與 原因/風險，並移除 🔥 最強 推薦語感。
  - format_cross_day_tracking_summary() 新增 optional report_context、market_mode 參數，既有回傳仍是 list of strings；直接呼叫方已同步以 keyword 傳入，不改 strategy payload。
  - 資料依據 section visibility 改為異常觸發；正常盤中 / 盤後 summary 不再固定顯示 簡報＋資料依據。
  - 卡片 formatter 不再輸出不可用歷史 / 回測行；可用 backtest line contract 保留。
  - VERSION / header 仍為 v20.4.31。
  - 無 DB 寫入、CLI 輸出、RR、策略 decision 或 public payload shape 變更。

  ## 直接消費者同步

  - presentation/report.py summary renderer 已同步消費新的 tracking summary 與資料依據 visibility helper。
  - core/generator.py cross-day tracking formatter 已同步文案與 optional signature。
  - tests/test_generator_report.py 補 / 更新 rendered message probes，覆蓋盤中、盤後、source-error、卡片歷史不可用與既有 B5 count consistency 路徑。
  - 直接消費者包含 Owner Telegram 手機閱讀、盤中 rendered message、盤後 rendered message、QA rendered snapshot/probe。

  ## 未影響模組

  - 未改 services/analysis.py
  - 未改 strategy evidence loader / DB source-of-truth
  - 未改 RR / overheat / chase hard blocker
  - 未改 DB schema / RLS / grant / policy / role / index / constraint
  - 未改 Supabase write path、production backfill、live Telegram delivery
  - 未改 VERSION，仍為 v20.4.31

  ## 已跑自檢命令

  - git diff --check：passed
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/
    test_generator_report.py::GeneratorReportTest::test_presentation_noise_intraday_no_valid_entry_uses_track_only_without_data_basis tests/
    test_generator_report.py::GeneratorReportTest::test_presentation_noise_afterhours_normal_sources_hide_data_basis tests/
    test_generator_report.py::GeneratorReportTest::test_presentation_noise_afterhours_source_error_shows_single_data_basis tests/
    test_generator_report.py::GeneratorReportTest::test_presentation_noise_card_history_unavailable_hidden_across_cards：4 passed，13 warnings
  - QA phone probe evidence（引用 QA 阻塞原因以外的既有反證結果，Tech 不宣告 QA 通過）：has_track_only=True、has_strong_tracking=False、data_basis_count=0

  ## 殘留風險

  - 本輪只跑 presentation noise targeted tests，未跑 full pytest。
  - 降噪只保證 rendered message 層；production 資料品質、策略樣本覆蓋率與長期 source-of-truth 非本輪目標。
  - 資料依據異常顯示依賴現有 source_status_summary / evidence_manifest 狀態欄位；若上游新增異常 status 名稱，需另補 mapping。

  ## 旁支待辦

  - 若 Owner 要重新設計全量 Telegram template 或 section 順序，需另開任務。
  - 若 production source 狀態欄位不完整，需另開 source-of-truth / data quality 任務。
  - 若要統一更多歷史 / 回測 formatter contract，需另開 public helper contract 任務並同步所有直接呼叫方。
