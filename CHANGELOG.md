# CHANGELOG: 修復 market/theme evidence gate 與 report-level fallback

  ## 任務尺寸與風險

  - 任務尺寸：normal_patch
  - QA 分級：L2
  - 風險判斷：本輪只修正 market/theme evidence payload gate、report-level fallback 與對應 regression tests；未改策略 decision、DB write path、報文分組、message list 或 VERSION。
  - 本輪為 handoff-only continuation：未再修改產品或測試程式碼，只修正交付摘要口徑。

  ## 修改內容

  - core/generator.py
      - 新增 _market_theme_confirmed_trend_eligible()，以 loader 已產出的 confirmed + source_status=available + evidence_trend.status=confirmed_trend 作為 confirmed market/theme 可消費判斷。
      - _market_theme_evidence_payload() 不再用 observed_days >= 15 作為 8 天 confirmed evidence 的 gate。
      - per-stock 缺 market_theme 時 fallback 到 report-level market_theme_evidence，因 market/theme 屬市場級證據，不因單一股票缺 per-stock market_theme 而直接 unavailable。
      - build_report_context() 的 market/theme manifest eligibility 與 payload 使用同一個 confirmed_trend 判斷 helper，讓 basis line 與 score path 對齊。
  - tests
      - 補 8 天 confirmed_trend 可 decision_eligible 的 regression。
      - 補 per-stock 缺 market_theme 時 fallback report-level evidence 的 regression。
      - 補 production trend consumption check 在 8 天 history 下仍 uses_market_theme_confirmed_evidence_history=True 的 regression。
      - 保留 strategy evidence 跨版本 outcome history regression，確認 current VERSION filter 未回歸。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tests/test_strategy_evidence.py

  ## 最小改動策略

  - 只動 TASK 指定的 generator evidence gate / fallback 路徑與必要 tests。
  - 未重構 formatter、未調整 RR、未改買賣 / 加減碼 / 停損停利決策。
  - 未修改 services/strategy_evidence.py；該檔本輪只有檢查與 regression 測試覆蓋，沒有 current diff。
  - services/strategy_evidence.py 的 VERSION filter 移除狀態沿用前一 commit，本輪未重新加入 .eq("version", VERSION)。
  - D2/B5 不屬於本 continuation 的實際 diff；若相關測試已存在，只視為既有 regression，不宣告本輪修復 rendered message。

  ## 契約影響

  - _market_theme_evidence_payload() 行為變更：confirmed_trend market/theme evidence 不再被 15-day gate 擋成 unavailable。
  - confirmed_trend 的可消費性改為沿用 loader eligibility 語意。
  - per-stock 缺 market_theme 時會 fallback report-level market/theme evidence；payload shape 不變。
  - VERSION 保持 v20.4.31。
  - Telegram / 報文 message list、分組順序、欄位名稱、DB contract、CLI 輸出 contract 未變。

  ## 直接消費者同步

  - Telegram / 報文卡片 market/theme evidence 顯示路徑已同步到新的 payload gate 與 fallback。
  - build_report_context() manifest decision eligibility 已同步使用同一 helper。
  - build_market_theme_production_trend_consumption_check 已由 regression 覆蓋 8 天 confirmed history consumption。
  - strategy evidence summary 直接消費者以 regression 確認 current VERSION filter 未回歸；本輪無 service 檔案 diff。

  ## 未影響模組

  - 未改 services/strategy_evidence.py current diff。
  - 未改 DB schema、RLS、grant、policy、role、index、constraint。
  - 未改 production write / backfill / live Telegram delivery。
  - 未改策略核心、RR 公式、買賣 / 加減碼 / 停損停利 decision。
  - 未 bump version；core/generator.py 仍為 VERSION = "v20.4.31"。
  - 未納入 D2/B5 rendered message 修復。

  ## 已跑自檢命令

  - git diff --check：passed
  - rg -n "VERSION\\s*=|v20\\.4\\.31|v20\\.4\\.32" core/generator.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py：確認 VERSION = "v20.4.31"，未 bump。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/
    test_generator_report.py::GeneratorReportTest::test_eight_day_confirmed_market_theme_is_decision_eligible tests/
    test_generator_report.py::GeneratorReportTest::test_per_stock_market_theme_missing_fallbacks_to_report_level_confirmed tests/
    test_market_theme_evidence.py::MarketThemeEvidenceTest::test_generator_consumes_eight_day_confirmed_trend_history tests/
    test_strategy_evidence.py::StrategyEvidenceTest::test_load_summary_consumes_cross_version_outcome_history：4 passed，13 warnings。
  - 直接 card probe：英業達 per-stock 缺 market_theme、report-level 8 天 confirmed market/theme fallback 時，卡片包含 證據 +8%（supporting），且不包含 證據：不適用。

  ## 殘留風險

  - 自檢只覆蓋 TASK 指定 targeted tests，未跑 full pytest。
  - production 實際 market/theme 資料品質、逐股 mapping 完整度與長期樣本分布不在本輪範圍。
  - Tech 自檢不代表 QA 通過；仍需 QA 依 L2 做獨立反證。

  ## 旁支待辦

  - 若 production evidence 缺市場級 source-of-truth 或歷史資料不足，需另開資料品質 / source-of-truth 任務。
  - 若要擴大 D2/B5 或其他 formatter consistency，需另開獨立 formatter regression 任務。
  - 若要治理跨版本 evidence retention policy，需另開版本資料策略任務。
