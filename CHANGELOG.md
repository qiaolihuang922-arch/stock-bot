# CHANGELOG: tg-message-order-v20.4.12

  ## 任務尺寸與風險

  - 任務尺寸：tiny_patch。
  - 風險判斷：本輪只改 Telegram message list order 與使用者可見版本；不改策略 decision、payload 欄位、DB/write/live delivery。

  ## 修改內容

  - 將 core/generator.py 的 VERSION 升級為 v20.4.12。
  - 調整 formatTelegramMessages() 回傳順序：
      - messages[0]：持倉 message。
      - messages[1]：未持倉 message。
      - messages[2]：summary + Evidence Compact。
      - optional details backup 仍在 include_detail=True 時追加於最後。
  - 持倉與未持倉 message 都加上 v20.4.12 header，符合手機端逐則閱讀路徑。
  - 更新測試，驗證完整 message list order、持倉/未持倉分離、summary/evidence 在 action messages 之後，且 Telegram output 不再殘留 v20.4.11 header。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - tests/test_market_theme_evidence.py

  ## 最小改動策略

  - 只修改 formatter 組裝順序與版本常量。
  - 沒有重構 formatter、沒有改策略計算、沒有改資料讀取、沒有改 sender 逐則送出行為。
  - 測試只同步既有版本斷言與新增/調整 message list order 驗證。

  ## 契約影響

  - formatTelegramMessages() 回傳型別維持 list。
  - message payload 仍為既有字串 message，未新增必填欄位。
  - message list 順序契約變更為：持倉 -> 未持倉 -> summary/evidence -> optional details。
  - 使用者可見版本同步為 v20.4.12。
  - 未改 DB schema、DB write path、live Telegram delivery、策略 decision payload。

  ## 直接消費者同步

  - Owner Telegram 手機閱讀路徑：第一則先看持倉，第二則看未持倉，第三則看 summary/evidence。
  - Telegram sender/consumer：services.notifier.send_many() 已確認仍依 list order 逐則送出，本輪不需修改。
  - QA/test：tests/test_generator_report.py 已覆蓋含持倉與未持倉 candidate 的完整 message list order。

  ## 未影響模組

  - BUY/SELL、加減碼、停損停利策略 engine 未改。
  - DB schema / RLS / grant / policy / role / index / constraint 未改。
  - production write、backfill、live Telegram 未執行也未新增。
  - Telegram delivery API client 未改。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py：115 passed，165 warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/notifier.py：passed。
  - git diff --check：passed。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_notifier.py tests/test_generator_report.py tests/test_market_theme_evidence.py：118 passed，165
    warnings。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_strategy_evidence.py tests/test_market_theme_evidence.py tests/
    test_notifier.py tests/test_cross_day_context.py tests/test_analysis_engine.py：167 passed，165 warnings。
  - rg -n "v20\\.4\\.11" core tests services -g '*.py'：只剩測試中的負向斷言 assertNotIn("v20.4.11", ...)。

  ## 殘留風險

  - include_detail=True 時 optional Details Backup 仍會追加在 summary/evidence 後方；這是既有 debug/detail 行為，本輪未全面改拆分規則。
  - send_many() 仍把 reply markup 掛在最後一則 message；本輪依 TASK 不改 delivery consumer 行為。

  ## 旁支待辦

  - 另開任務評估 Telegram reply markup 在新 message order 下的按鈕落點。
  - 另開任務評估 Details Backup 是否仍應作為最後一則，或需另定細部拆分契約。
