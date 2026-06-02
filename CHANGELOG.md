# CHANGELOG:

  ## 任務尺寸與風險

  normal_patch。原因：本輪改 Telegram 使用者可見報文分類、持倉主行動文字、索引顯示與版本字串；未改策略 decision、RR、holding_status、DB write/schema 或 live delivery。

  ## 修改內容

  - 新增 A1/A2/A3 mobile reading regression tests。
  - VERSION 升至 v20.4.25。
  - 未持倉不可買 / 不可追高標的，不再以主標籤 可準備 呈現：
      - 漲停鎖價：不可追高觀察
      - 過熱降溫：過熱待回測
      - 突破回測：待回測
  - Summary、交易執行提示、未持倉漏斗、資料依據、詳情索引同步改用 不可追高觀察 口徑。
  - 普通持倉 續抱 使用者可見主行動收斂為 續抱觀察，卡片標題、決策行、持倉風控檢查一致。
  - 詳情索引的持倉欄位由數量改為 ordered holdings ticker/name 序列，和持倉卡片、持倉風控檢查對齊。
  - 既有 generator report snapshots 同步新版 VERSION 與顯示契約。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  只改報文顯示層與對應測試。內部 unheld_funnel_state 仍保留既有分類 state，不改策略分類來源；未碰 services/analysis.py、RR 計算、holding_status、DB schema/write、live Telegram。

  ## 契約影響

  - 使用者可見 VERSION：v20.4.24 -> v20.4.25。
  - 使用者可見報文文字變更：
      - 非執行準備類 count / 漏斗 / Summary 由 可準備 改為 不可追高觀察。
      - 未持倉卡片主標籤依不可進場原因顯示。
      - 持倉索引顯示 ordered holding names，不再只顯示持倉數。
      - 普通續抱持倉主行動顯示為 續抱觀察。
  - Telegram message list 數量與順序未改。
  - payload / DB contract / CLI contract 未改。
  - public helper 新增 unheld_non_actionable_prepare_label，直接用於 presentation formatter deps。

  ## 直接消費者同步

  - presentation/report.py 已同步使用新的非行動準備 label helper。
  - tests/test_generator_report.py 已同步所有直接報文 snapshot / mobile reading probe。
  - Telegram 發送端 consumer 的 message list 順序未改，不需同步 payload shape。

  ## 未影響模組

  - services/analysis.py
  - strategy decision
  - RR 計算
  - holding_status
  - DB schema / RLS / grant / policy / role
  - DB write path
  - live Telegram delivery
  - replay / backfill

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py：106 passed，217 warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed。
  - git diff --check：passed。
  - 初次未加 arch -arm64 的 pytest collection 因 local Python / pydantic_core 架構不符失敗；已用 arm64 Python 重跑通過。

  ## 殘留風險

  - 本輪只覆蓋 A1/A2/A3 第一批硬衝突；未處理 Owner 提到的降噪第二批。
  - 可準備 仍作為內部 funnel state 使用，使用者可見文字已改為不可進場口徑。
  - warnings 來自既有第三方 deprecation，非本輪新增。

  ## 旁支待辦

  - 降噪第二批另開任務。
  - 全量追高 / 追蹤詞彙盤點另開任務。
  - 全報文文案瘦身另開任務。
  - production source-of-truth / DB 治理不在本輪。
