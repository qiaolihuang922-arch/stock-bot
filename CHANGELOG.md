# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 風險原因：修正 Telegram 使用者可見 evidence 加權、綜合分數與版本字串；不改 RR、策略核心、DB write/schema、live delivery。

  ## 修改內容

  - core/generator.py 升版 v20.4.34。
  - 新增統一 strategy sample count 讀取邏輯，支援：
      - row_count
      - sample_rows
      - evidence_count
      - sample
      - sample_count
      - classification_sample_count
  - _strategy_sample_status()、_strategy_sample_row_count()、per-stock strategy sample evidence payload 共用同一計數來源，避免真實有效樣本數被讀成 0/None 後降為 partial。
  - 補 official message-list replay 測試：建準等價標的在 market confirmed + strategy sample 36 時，卡片顯示非 0 evidence 加權，且 綜合 != 技術。
  - 補過熱路徑測試：HOT 標的仍顯示 confirmed evidence 非 0 加權，但 funnel 保持既有等冷卻 hard block，不誤顯 partial。
  - 同步既有版本字串測試預期到 v20.4.34。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py
  - tests/test_strategy_evidence.py

  ## 最小改動策略

  - 只補 TASK 指定的 sample count 映射缺口與版本同步。
  - 未改 RR 公式、策略 decision、買賣/加減碼、停損停利、DB schema/write path、production backfill、live Telegram。
  - 未改報文版型，只讓既有 evidence/綜合欄位吃到正確樣本數。

  ## 契約影響

  - 使用者可見報文版本：v20.4.33 -> v20.4.34。
  - public helper 行為：
      - _strategy_sample_row_count() 現可從 classification_sample_count / sample_count 讀取有效樣本數。
      - _strategy_sample_evidence_payload() 在樣本數 >=10 且 source available 時回傳 status=ready、score=1.0、decision_eligible=true。
  - message list：
      - market confirmed + strategy sample >=10 時，證據顯示 confirmed/supporting 非 0 加權；綜合分數不再等於純技術分數。
  - payload / DB：
      - 未改 DB 寫入、schema、RLS、grant、policy、role、index、constraint。
      - 未新增 production write/backfill 需求。

  ## 直接消費者同步

  - Telegram / official message-list generator 已透過 formatTelegramMessages() replay 測試同步。
  - evidence payload 消費者透過 build_report_context()、compute_evidence_score()、卡片 rendered line 測試同步。
  - strategy evidence loader version-filter 回歸測試同步到 v20.4.34。

  ## 未影響模組

  - RR 公式未改。
  - 持倉狀態機、同日風控、買賣/加減碼、停損停利未改。
  - production Supabase write path 未改。
  - live Telegram delivery 未執行。
  - 報文分組規則與版型未重設。

  ## 已跑自檢命令

  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_eight_day_confirmed_market_theme_is_decision_eligible tests/
    test_generator_report.py::GeneratorReportTest::test_strategy_sample_count_accepts_classification_sample_count tests/
    test_generator_report.py::GeneratorReportTest::test_official_replay_confirmed_market_and_classification_sample_changes_composite tests/
    test_generator_report.py::GeneratorReportTest::test_hot_stock_keeps_non_zero_evidence_without_false_partial tests/
    test_strategy_evidence.py::StrategyEvidenceTest::test_load_summary_consumes_cross_version_outcome_history tests/
    test_strategy_evidence.py::StrategyEvidenceTest::test_load_summary_defaults_to_recent_60_distinct_cross_version_days：6 passed，13 warnings。
  - arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py：206 passed，241 warnings。
  - PYTHONPYCACHEPREFIX=/private/tmp/tech_write_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/strategy_evidence.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/
    test_strategy_evidence.py：passed。
  - git diff --check：passed。
  - 備註：直接 pytest 不在 PATH；直接 .venv/bin/python 以 x86_64 載入時遇到 arm64 pydantic_core 架構錯誤，已用 arch -arm64 重跑通過。

  ## 覆蓋層級

  - helper：已測 _market_theme_evidence_payload、_strategy_sample_row_count、_strategy_sample_evidence_payload。
  - data loader：已測 load_strategy_evidence_summary 不使用 .eq("version", current_version)，並保留 60 distinct cross-version days。
  - official generator / message-list：已測建準等價標的 confirmed evidence 非 0、綜合 != 技術、不顯示 partial/+0%。
  - overheat path：已測 HOT 標的 evidence 非 0，且仍維持等冷卻 hard block。
  - production source：未讀 production；本輪只用 read-only fixture/replay 驗 code path，未做 live write/delivery。

  ## 殘留風險

  - 未驗 production 真實資料是否已提供 classification_sample_count 或等價欄位；若 production source 本身缺資料，仍需 source-of-truth/read-only artifact 任務。
  - 未跑 full repo pytest。
  - 未做 live Telegram、production smoke、backfill。

  ## 旁支待辦

  - 若 Owner 要確認所有標的 production evidence 品質，另開 read-only production artifact 任務。
  - 若要校準 evidence 權重大小或 RR/策略核心，另開獨立策略任務，不併入本輪。
