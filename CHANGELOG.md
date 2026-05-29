# CHANGELOG: Evidence Phase 2 Source-Family Gate Reblocker Fix

  ## 修改內容

  - 任務尺寸與風險：normal_patch。本輪只修 QA_REPORT 指出的兩個 blocker，不擴大到 schema、DB write、backfill、watchlist、live Telegram 或策略門檻。
  - 修正 confirmed/ready market/theme evidence 的頂層 source_family 判斷：當 production / Owner-approved persistent source 已足夠且 evidence confirmed/ready 時，頂層 source_family 只回傳 production_db 或
    owner_approved_persistent，不再被 report_derived theme text、runtime diagnostic 或 detail-only source 污染。
  - 保留 report-derived theme source 與 runtime diagnostic 在 sources / source_family_details / limitations / detail wording 中，僅阻止它們污染 confirmed source boundary。
  - 修正 tests/test_market_theme_evidence.py::test_same_source_type_does_not_confirm 期望：同一 source_type 即使來自 production_db 與 owner_approved_persistent，仍只能算一種 confirmed source type，不得 confirmed；期望改
    為符合新的 production / owner-approved persistent source-family gate。
  - 保留並吸收 v20.4.2 wording/header candidate：core/generator.py 與 tests/test_generator_report.py 屬於本 candidate，原因是 TASK 版本契約要求 wording/header 有變時升到 v20.4.2，且 Telegram summary evidence wording 已同
    步測試。

  ## 修改檔案

  - core/market_theme_evidence.py
      - 新增 production / owner-approved persistent source-family gate。
      - confirmed/ready 時優先用合法 confirmed persistent sources 決定頂層 source_family。
      - 維持 runtime/report-derived source 只能作 detail/limitations/diagnostic。
  - tests/test_market_theme_evidence.py
      - 修正 test_same_source_type_does_not_confirm。
      - 覆蓋 production/persistent confirmed、runtime diagnostic 不可 confirmed、summary wording 與 v20.4.2 header。
  - core/generator.py
      - 屬於本 candidate：保留 VERSION = "v20.4.2"。
      - 同步缺 production source 時的短 evidence wording。
  - tests/test_generator_report.py
      - 屬於本 candidate：同步 v20.4.2 header 與 evidence wording snapshot/formatter 期望。

  ## 最小改動策略

  - 只改 source boundary helper 的 confirmed 分支與直接測試期望。
  - 沒有新增 table/schema/field/migration。
  - 沒有改 BUY / SELL / RR / overheat 門檻。
  - 沒有改 watchlist、DB write、backfill/replay write path 或 live Telegram。

  ## 契約影響

  - build_market_theme_evidence(...) 回傳結構維持既有欄位，不新增本輪新欄位；本輪只修正 confirmed/ready 時既有 source_family 的語意。
  - confirmed/ready evidence 的頂層 source_family 契約收斂為合法 persistent source boundary：production_db 或 owner_approved_persistent。
  - sources、source_family_details、limitations 仍可包含 report_derived / runtime_diagnostic，作為 detail trace 或限制說明。
  - Telegram header 保持 v20.4.2；summary evidence wording 保持短句，不輸出長 absent/missing-source 清單。

  ## 直接消費者同步

  - core/generator.py：已使用 market_theme_summary_evidence(...) / format_market_theme_summary_lines(...) 的修正結果，header 同步 v20.4.2。
  - tests/test_generator_report.py：已同步 v20.4.2 與 evidence wording 期望。
  - tests/test_market_theme_evidence.py：已同步 source-family gate、same source type 不 confirmed、runtime diagnostic 不 confirmed 的直接 contract。
  - Owner 手機 Telegram 報文：缺 production source 時仍短句顯示「證據：production 來源不足，不作確認。」；runtime 診斷只在詳情標示非確認來源。
  - GitHub fresh runner：confirmed evidence 仍要求 production DB 或 Owner-approved persistent source；runtime/local/report-derived 不可補成 confirmed。

  ## Evidence Source Mapping

  - market evidence：合法 confirmed source 須來自 production_db 或 owner_approved_persistent 的 market_index / sector_index 類 source，且具備 as_of、freshness、freshness_reason、level、supports_claims、limitations。
  - theme evidence：合法 confirmed source 須包含 persistent watchlist_breadth 搭配 market/sector source；report-derived theme text 只可作 theme label/detail，不可 confirmed。
  - strategy evidence：本輪未改 services/strategy_evidence.py；以既有 read-only strategy evidence tests 驗證未被此 reblocker patch 破壞。

  ## 未影響模組

  - 未改 DB schema / migration / SQL / table / field。
  - 未改 Supabase write path、daily write stores、正式 backfill、replay write path。
  - 未改 watchlist。
  - 未執行 live Telegram。
  - 未改 BUY / SELL / RR / overheat / trading thresholds。
  - 未改 strategy decision、持倉狀態機或交易建議邏輯。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py tests/test_generator_report.py tests/test_notifier.py tests/test_strategy_evidence.py
  - 結果：100 passed, 13 warnings in 0.59s
  - warnings 來自既有相依套件 deprecation，不影響本輪測試結果。

  ## 殘留風險

  - 本輪未連 production DB、未驗 live runner 實際資料品質；只驗證程式 contract 與 fixture 行為。
  - 若 production DB source 缺 required fields 或 freshness 無法判斷，仍會 fail closed 為 missing-source / insufficient-data / stale，不會 confirmed。

  ## 旁支待辦

  - 若 Owner 要把更多實際 DB table/view 名稱直接接入 market/theme source records，需另開任務定義 read-only loader 與欄位 mapping；本輪不新增 schema/table/field。
