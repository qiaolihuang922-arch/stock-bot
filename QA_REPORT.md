# QA_REPORT:

## 測試範圍

- 任務尺寸 / QA：risk_patch / L3。
- 驗收目標：market_theme 8 天 confirmed_trend 可 decision_eligible；strategy_sample 真實 classification sample >=10 可進 ready；official message-list 不再出現 confirmed+sample 足夠但 partial/+0% / 綜合=技術。
- 可吸收 diff：TASK.md、CHANGELOG.md、core/generator.py、tests/test_generator_report.py、tests/test_market_theme_evidence.py、tests/test_strategy_evidence.py。
- QA runner 狀態：自動 QA agent 啟動後遇到 Codex usage limit 互動提示，未產生可吸收 agent QA_REPORT；Architect 依 AGENTS post-cycle 要求做本地可重跑反證，未執行 live Telegram、production write、production backfill。

## 風險預算與停止條件

- 風險 1：market_theme confirmed_trend 仍被二次 15 日門檻擋住。停止條件：8 天 confirmed_trend payload 不是 score=1.0 / status=confirmed / decision_eligible=true。
- 風險 2：strategy structured sample 實際 >=10 仍被讀成 0/None。停止條件：_strategy_sample_row_count 讀不到 classification_sample_count，或 evidence payload 仍 partial。
- 風險 3：使用者可見卡片仍是 partial+0%、綜合=技術。停止條件：official replay 的建準等價卡片不含非 0 evidence boost，或過熱卡誤顯 partial。

## 關聯風險掃描

- core/generator.py 版本已升為 v20.4.34，相關 generator / market_theme / strategy_evidence 測試預期同步。
- services/strategy_evidence.py 未改，但已核對 load_strategy_evidence_summary 目前按近 60 交易日跨版本讀取 daily_signal_snapshot / daily_price，沒有 .eq("version", version)。
- 未修改 RR 公式、DB schema/write path、live Telegram、production backfill。
- git diff --check：passed。
- py_compile：passed。

## 跨區塊語意一致性

- targeted official replay passed：market confirmed + strategy sample 36 時，建準等價卡片顯示「綜合 90｜技術 78｜證據 +15%（confirmed）」；不含「證據：partial」或「證據 +0%」。
- overheat path passed：HOT 標的在 market confirmed 下仍可顯示 confirmed evidence 非 0 加權，同時保留等冷卻 hard block，不把證據誤當可買理由。
- evidence payload helper passed：8 天 confirmed_trend -> market score=1.0 / confirmed；strategy structured sample 36 -> ready / score=1.0。

## 使用者誤讀風險

- 主要誤讀「資料足夠但報文仍說證據不足」已由 official message-list replay 反證。
- 主要誤讀「綜合=技術但顯示 confirmed」已由同一 replay 反證：綜合與技術不同，且 evidence modifier > 1.0。
- 殘留風險：本輪未讀 production source；若 production 真實資料仍缺 classification_sample_count / sample_count，報文仍會 fail closed。這是資料源品質問題，不是本輪 code path。

## 質疑與反證

- QA 額外質疑：Tech 是否只修 helper、未打到 official message-list。反證：主倉跑過 tests/test_generator_report.py::GeneratorReportTest::test_official_replay_confirmed_market_and_classification_sample_changes_composite，結果 passed。
- QA 額外質疑：version filter 是否仍在 loader。反證：主倉跑過 tests/test_strategy_evidence.py::StrategyEvidenceTest::test_load_summary_consumes_cross_version_outcome_history 與 test_load_summary_defaults_to_recent_60_distinct_cross_version_days，結果 passed；同時手動核對 loader 無 .eq("version", version)。
- QA 額外質疑：只跑 targeted 會漏版本同步。反證：主倉跑過 tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py，結果 206 passed。

## 已跑命令

- arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_eight_day_confirmed_market_theme_is_decision_eligible tests/test_generator_report.py::GeneratorReportTest::test_strategy_sample_count_accepts_classification_sample_count tests/test_generator_report.py::GeneratorReportTest::test_official_replay_confirmed_market_and_classification_sample_changes_composite tests/test_generator_report.py::GeneratorReportTest::test_hot_stock_keeps_non_zero_evidence_without_false_partial tests/test_strategy_evidence.py::StrategyEvidenceTest::test_load_summary_consumes_cross_version_outcome_history tests/test_strategy_evidence.py::StrategyEvidenceTest::test_load_summary_defaults_to_recent_60_distinct_cross_version_days
  - 結果：6 passed，13 warnings。
- arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py
  - 結果：206 passed，241 warnings。
- PYTHONPYCACHEPREFIX=/private/tmp/evidence_fix_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/strategy_evidence.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_strategy_evidence.py
  - 結果：passed。
- git diff --check
  - 結果：passed。

## 未測項目

- 未跑 live Telegram。
- 未跑 production write / backfill。
- 未跑 production read-only artifact；若 Owner 要確認 production 真實資料已補齊，需要另開 read-only source artifact 任務。
- 自動 QA agent 因 usage limit 未完成；本報告是 Architect 本地反證，不冒稱 agent QA 通過。

## QA 結論

conditional pass
