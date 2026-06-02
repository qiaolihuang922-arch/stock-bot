# CHANGELOG: 修復證據 wiring 與 D2/B5 漏斗一致性

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 風險原因：影響正式報文 evidence 消費路徑、strategy evidence 歷史讀取、D2/B5 使用者可見漏斗 / 卡片一致性。
  - 本輪 continuation 僅補正 handoff 內容；未再修改產品或測試程式碼。

  ## 修改內容

  - services/strategy_evidence.py
      - load_strategy_evidence_summary() 移除 daily_signal_snapshot.version == version filter。
      - 改為可讀取近期 trade_date 歷史中的跨版本 outcomes，避免 evidence 因版本散落長期空轉。
      - 保留原本不足資料時 fail closed 的語意。
  - core/generator.py
      - build_report_context() 呼叫 market_theme_summary_evidence() 時傳入 trade_date。
      - market_theme_summary_evidence() 在 market_summary 是字串時，也會用 trade_date 呼叫 load_confirmed_market_theme_evidence()。
      - market_summary 是 dict 且缺內嵌 evidence 時，loader 使用 market_summary.trade_date / as_of / 外部 trade_date。
      - 官方 report path 可消費 confirmed evidence 與 evidence_trend。
  - 測試
      - 新增 strategy evidence 跨版本 outcome history probe，確認樣本數可進入 summary 且不走 version filter。
      - 新增 official report string market_summary trade_date loader 與 consumption check。
      - 新增 D2/B5 rendered message probe，覆蓋 等冷卻 / 隔日確認 卡片與漏斗計數一致。

  ## 修改檔案

  - services/strategy_evidence.py
  - core/generator.py
  - tests/test_strategy_evidence.py
  - tests/test_market_theme_evidence.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 只移除造成跨版本 evidence 空轉的 version filter。
  - 只補 trade_date wiring 到既有 confirmed market theme evidence loader。
  - 只補針對 TASK 驗收條件的最小 regression probes。
  - 未重構 formatter、未改策略方向、未新增資料來源、未改 DB schema / write path。
  - 未 bump 版本；VERSION 保持 v20.4.31。

  ## 契約影響

  - load_strategy_evidence_summary() 回傳 payload / 文字 shape 保持既有格式；讀取範圍改為跨版本近期歷史。
  - market_theme_summary_evidence() public helper 增加可選 trade_date=None 參數；既有呼叫方不傳仍相容。
  - 正式 generate_report / formatTelegramMessages 路徑可透過 trade_date 消費 confirmed market theme evidence 與 evidence_trend。
  - Telegram / 報文 message list、欄位名稱、分組名稱與版本字串不變。
  - D2/B5 漏斗與卡片分類維持既有使用者可見名稱，只修正同份 rendered message 內的計數 / 卡片一致性。

  ## 直接消費者同步

  - build_report_context() 已同步傳入 trade_date。
  - 官方報文市場題材 evidence 消費路徑已由新增測試覆蓋。
  - build_market_theme_production_trend_consumption_check 相關 consumption check 已覆蓋 uses_history=True。
  - D2/B5 summary / funnel / unheld card 手機閱讀路徑已由 rendered message 測試覆蓋。

  ## 未影響模組

  - 未改 RR 公式。
  - 未改買賣 / 加減碼 / 停損停利核心決策規則。
  - 未改 DB schema、RLS、grant、policy、role、index、constraint。
  - 未改 production write / backfill / live Telegram delivery。
  - 未觸碰 scripts/diagnose_evidence_sources.py。
  - 未改 VERSION；仍為 v20.4.31。

  ## 已跑自檢命令

  - git diff --check：passed
  - rg -n "VERSION\\s*=|v20\\.4\\.31|v20\\.4\\.32" core/generator.py tests：確認 core/generator.py 仍為 VERSION = "v20.4.31"，未見新版本 bump。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/
    test_strategy_evidence.py::StrategyEvidenceTest::test_load_summary_consumes_cross_version_outcome_history tests/
    test_market_theme_evidence.py::MarketThemeEvidenceTest::test_official_report_string_market_summary_passes_trade_date_to_confirmed_loader tests/
    test_market_theme_evidence.py::MarketThemeEvidenceTest::test_readonly_smoke_cli_outputs_consumption_check_json_with_mocked_persistent_rows tests/
    test_generator_report.py::GeneratorReportTest::test_unheld_cooling_and_next_day_rendered_counts_match_cards：4 passed，13 warnings。
  - 另有一次未加 arch -arm64 的 pytest 嘗試失敗，原因是 x86_64 Python 載入 arm64 pydantic_core wheel 架構不相容；已用 runner 既有 arm64 口徑重跑通過。

  ## 殘留風險

  - 自檢只覆蓋 TASK 指定 targeted tests，未跑 full pytest。
  - production evidence 實際資料品質、逐股 mapping、長期樣本分布不在本輪修補範圍。
  - Tech 自檢不代表 QA 通過；QA 仍需依 L3 反證 official path 與手機閱讀一致性。

  ## 旁支待辦

  - 若 production evidence 缺逐股 theme / setup payload，需另開資料品質或 source-of-truth 任務。
  - 若要治理版本散落造成的歷史資料長期可讀性，需另開版本 / evidence retention 任務。
  - 若要擴大檢查所有 D2/B5 邊界分類，需另開 formatter / classifier regression suite 擴充任務。
