# CHANGELOG: 持倉風控檢查完整列出全部持倉

  ## 任務尺寸與風險

  normal_patch。使用者可見 Telegram 報文第三則渲染變更；不碰策略 decision、RR、DB write path、未持倉漏斗。

  ## 修改內容

  - 持倉風控檢查 預設改為列出全部持倉，不再固定只顯示前 5 筆。
  - 移除預設截斷提示 另有 N 項持倉風控見詳情。
  - 風控列表排序改為沿用既有 holding_items 順序，與持倉卡 / detail index 同源。
  - 報文版本升為 v20.4.28。
  - 擴充手機閱讀 probe：6 檔持倉完整列出、無 另有 / 見詳情、排序與持倉卡 / detail index 一致。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py

  ## 最小改動策略

  只修改第三則持倉風控 checklist 的預設上限與排序來源，保留 format_holding_control_checklist(..., limit=...) 顯式參數相容性。測試只同步報文版本與本輪直接相關 probe。

  ## 契約影響

  - 使用者可見報文：第三則 持倉風控檢查 筆數改為等於持倉數。
  - 訊息順序：未改。
  - payload / DB contract：未改。
  - public helper：format_holding_control_checklist 參數形狀保留；預設行為由 5 筆截斷改為完整列出。
  - 報文版本：v20.4.27 -> v20.4.28。

  ## 直接消費者同步

  - presentation/report.py 既有呼叫透過 deps 使用 format_holding_control_checklist，不需改呼叫點；預設即套用完整列表。
  - tests/test_generator_report.py 同步版本期望與手機閱讀排序 / 不截斷 probe。

  ## 未影響模組

  - strategy decision / 主行動判斷未改。
  - RR 計算與顯示語意未改。
  - DB schema / write path 未改。
  - live Telegram delivery 未執行。
  - 未持倉漏斗、可買 / 可準備 / 僅追蹤 / 淘汰邏輯未改。
  - 交易執行與已執行 checklist 的既有截斷行為未改。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/
    test_generator_report.py::GeneratorReportTest::test_intraday_mobile_a3_holding_order_matches_cards_control_and_index：1 passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py：116 passed，225 warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py tests/test_generator_report.py：passed。
  - git diff --check：passed。
  - 另有一次未加 arch -arm64 的單測收集失敗，原因是 x86_64 Python 載入 arm64 pydantic_core binary 不相容；已用 arm64 重跑通過。

  ## 殘留風險

  - 未跑 full pytest；本輪只跑 Telegram 報文相關測試。
  - 完整列出全部持倉會增加第三則長度；TASK 明確要求不截斷，本輪未另做 Telegram 長訊息切分治理。

  ## 旁支待辦

  - 其他 Telegram 區塊若也有 另有 / 見詳情 截斷文案，不屬本輪。
  - Telegram 單則長度與多持倉極端情境可另開治理任務。
