# CHANGELOG: 證據鏈第一批硬衝突修復 P1/P2/P4

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 風險判斷：改動 Telegram 使用者可見報文的 evidence gate / card / funnel 顯示門控，涉及持倉執行記憶與未持倉可行動分類，但未改 strategy decision、RR 公式、DB schema/write 或 live delivery。

  ## 修改內容

  - P1：未持倉卡片把 strategy_sample status 納入可見高置信顯示門控；strategy_sample missing / insufficient / source-error 時，不再顯示可買、S 5/5、突破確認等高置信口徑，改為策略樣本證據不足 / 來源異常與無有效進場。
- P2：持倉卡片 execution 欄位改為同時檢查 positions 與 ledger / execution_memory status；任一為 missing-source / insufficient-data / source-error / unresolved-conflict 時，不顯示精確股數、均價、今日買賣，改顯示「執行記憶不足」保守文案。
  - P4：未持倉 funnel source status 已納入 strategy_sample 狀態，保留既有 RR 不足 / 不可追高 / 過熱待回測 / 無有效進場門控；source-error 不會隱藏可用價格，但會阻斷可行動分類。
  - 新增 P2 可重跑 probe；保留並通過既有 P1/P4 probes 與 source-error 不隱藏價格 probe。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 只在既有 report_context.evidence_manifest 到 presentation renderer 的轉換層補門控。
  - P2 不新增資料來源，不改 execution memory 計算，只消費既有 stock.<name>.position 與 stock.<name>.execution_memory status。
  - 未重構報文架構，未改 strategy decision、RR 公式、DB schema/write、live Telegram。

  ## 契約影響

  - 使用者可見持倉卡片：ledger / positions 不可信時，execution 行由精確 倉位 / 均價 / 今日買賣 改為保守 執行記憶不足。
  - 使用者可見未持倉卡片：strategy_sample 不可用時，高置信 S 分數 / 強弱分類 / 進場觸發降級為不可買與無有效進場。
  - 報文版本：未修改 core.generator.VERSION，仍使用既有 v20.4.25；本輪未改 header 格式。
  - 未改 payload shape、DB contract、DB write path、RR 計算值或 strategy 原始結果。

  ## 直接消費者同步

  - presentation/report.py 的持倉卡與未持倉卡已同步使用 core/generator.py 注入的 evidence helper。
  - tests/test_generator_report.py 已同步新增 / 調整 regression probes，覆蓋 P1/P2/P4 的可重跑驗收路徑。

  ## 未影響模組

  - 未改 services/analysis.py。
  - 未改 DB schema、RLS、grant、policy、role、index、constraint。
  - 未改 DB write / backfill / Supabase write path。
  - 未執行 live Telegram delivery。
  - 未處理 P3/P5/P6/P7/P8。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'holding_card_hides_precise_execution_when_ledger_insufficient or
    strategy_sample_source_error_blocks_action_without_hiding_available_price or manifest_fails_closed_for_missing_candidate_sources'：3 passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py：108 passed，221 warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed。
  - git diff --check：passed。
  - 補充：未加 arch -arm64 的首次 pytest collection 因本機 Python 架構與 arm64 pydantic_core wheel 不符失敗；已用既有 arm64 runner 方式重跑通過。

  ## 殘留風險

  - Tech 自檢只覆蓋 tests/test_generator_report.py 與 py_compile，不代表 QA 通過。
  - P2 目前是可見 renderer fail-closed；若未來新增其他持倉 execution 顯示 formatter，需要同步套用同一 ledger / positions 合併門控。
  - 全量證據鏈治理與 P3/P5/P6/P7/P8 不在本輪範圍。

  ## 旁支待辦

  - 另開任務處理 P3/P5/P6/P7/P8。
  - 後續可盤點所有持倉 execution 顯示入口，確認沒有新 formatter 繞過 report_context.evidence_manifest 門控。
