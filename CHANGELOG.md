# CHANGELOG: per-stock evidence 決策分數與 B5 漏斗一致性收口

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - QA 分級：L3
  - 版本：維持 v20.4.31，未升版
  - 本輪 continuation 類型：handoff-only / process text correction；未修改產品碼或測試碼，只修正 CHANGELOG 契約描述
  - QA conditional pass 狀態：functionality passed；本次已處理條件項「CHANGELOG overclaims load_strategy_evidence_summary() all-branches dict return」

  ## 修改內容

  - strategy evidence 已移除 current VERSION-only outcome filter，改以 trade_date 近 N 日跨版本 daily_signal_snapshot / daily_price 取樣。
  - 在資料足夠可形成 outcome rows 時，strategy evidence summary 會建立 structured setup_strategy_samples 與 structured_status，依 reject_family / watch_category setup 類別聚合 sample_count、win_rate、median_mfe、
    median_mae、mfe_mae_score。
  - compute_evidence_score(report_context, name) 已改為 market/theme 共享背景 + per-stock strategy setup sample 加權合成，權重為 market 0.4 / strategy 0.6。
  - 單檔缺明確 reject_family / watch_category / setup 欄位時，不用 report layer 推導類別補缺口；即使 summary 有正向 setup sample，也 fail closed，不產生 per-stock strategy boost。
  - 弱勢 / 失敗 / EXTREME / technical=0 正向 boost 封頂，rendered card 顯示「證據：不適用」，不顯示正向「證據 +%」。
  - 補 B5 漏斗一致性 probe：隔日確認 / 等回測 / 等冷卻 拆分加總等於「僅追蹤」總數，且 card state 與 funnel state 一致。
  - 本次 handoff-only 修正 CHANGELOG 文字：不再宣稱 load_strategy_evidence_summary() 所有分支都改成 dict summary。

  ## 修改檔案

  - core/generator.py
  - services/strategy_evidence.py
  - tests/test_generator_report.py
  - tests/test_strategy_evidence.py
  - CHANGELOG.md：由 runner 依本回答覆寫；本輪未直接編輯

  ## 最小改動策略

  - 只描述 TASK 指定的 evidence score、strategy setup sample、rendered-message probe 與 B5 probe。
  - 本輪 continuation 未改產品碼、未改測試碼，僅收斂 handoff 文件契約描述。
  - 未改 RR 公式、策略方向、DB schema/write path、approved write CLI、Phase 3 runner、live Telegram。
  - 未修改 tests/test_market_theme_evidence.py，不宣稱該檔有 diff。

  ## 契約影響

  - load_strategy_evidence_summary() 不新增「所有分支都回傳 dict」的 public contract。
  - load_strategy_evidence_summary() 在 missing-source、insufficient-data、fail-closed 類分支仍保留既有 textual summary 回傳口徑。
  - load_strategy_evidence_summary() 在 feature rows / price rows 足夠並可計算 outcome rows 時，透過 report_from_rows() 回傳包含 rendered_text、text、structured_status、setup_strategy_samples、classification_report 的
    dict，用於 evidence scoring。
  - compute_evidence_score(report_context, name) 仍回傳 (score, status)；score 來源改為 market/theme background 與 per-stock strategy setup sample 加權合成。
  - per-stock strategy setup matching 只接受明確 setup 欄位；缺欄位時 unavailable，modifier = 1.0。
  - rendered score line 在 unavailable / blocked boost 時顯示「證據：不適用」，不顯示正向加成。
  - 無 VERSION bump，使用者可見版本仍維持 v20.4.31。
  - 無 DB write、live Telegram、正式 backfill、RR 公式或買賣策略契約變更。

  ## 直接消費者同步

  - Telegram rendered card 已用 probe 覆蓋：缺明確 setup + market missing + summary 正樣本時，不顯示「證據 +%」。
  - direct card consumer / stock.<name>.risk.value 仍由 build_report_context() 同步寫入 technical_confidence、evidence_status、evidence_modifier、final_confidence。
  - Summary / 未持倉漏斗 / tracking count 已用 B5 probe 覆蓋拆分一致。
  - QA 已回報 functionality passed；本次已針對 QA conditional item 修正 CHANGELOG overclaim。

  ## 未影響模組

  - 未改 presentation/report.py
  - 未改 tests/test_market_theme_evidence.py
  - 未改 DB / Supabase write path
  - 未改 Telegram live delivery
  - 未改 RR / overheat / chase hard blocker 定義
  - 未改 VERSION

  ## 已跑自檢命令

  - git diff --check：passed
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/
    test_strategy_evidence.py::StrategyEvidenceTest::test_load_summary_consumes_cross_version_outcome_history tests/
    test_generator_report.py::GeneratorReportTest::test_setup_strategy_summary_drives_per_stock_modifier_and_rendered_cards tests/
    test_generator_report.py::GeneratorReportTest::test_setup_summary_without_explicit_stock_setup_fails_closed_and_hides_boost tests/
    test_generator_report.py::GeneratorReportTest::test_b5_tracking_split_matches_card_states_and_tracking_total：4 passed
  - 兩次 pytest node-id typo 嘗試在 collection 階段失敗，原因是測試名稱輸入錯誤，未進入測試本體；已用正確 node id 重跑通過

  ## 殘留風險

  - 本輪 handoff-only continuation 未跑 full pytest；只重跑與 QA condition / TASK 直接相關的 targeted tests。
  - production evidence 長期資料品質、setup 欄位覆蓋率與樣本分布未處理，屬 TASK 非目標。
  - load_strategy_evidence_summary() 回傳型別仍依分支不同可能是 textual summary 或 structured dict；目前 CHANGELOG 已明確描述，不宣稱 all-branches dict contract。

  ## 旁支待辦

  - 若 production payload 缺明確 setup 欄位，需另開資料品質 / source-of-truth 任務，不應在 report layer 推導補缺口。
  - 若後續要把 load_strategy_evidence_summary() 統一成 all-branches structured return，需另開 public helper contract 任務並同步所有直接呼叫方與測試。
