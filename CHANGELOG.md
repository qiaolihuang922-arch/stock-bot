# CHANGELOG:

  ## 任務尺寸與風險

  - 任務類型：risk_patch
  - 風險原因：使用者可見 Telegram 持倉 / 未持倉卡顯示門控，涉及 S 分數與強弱高信心文字，但不改 strategy decision、RR、DB、live delivery。

  ## 修改內容

  - 在 presentation/report.py 新增 score source status 顯示門控。
  - 顯示 S n/5 或 score/strength 相關高信心盤面文字前，讀取 stock.<name>.score.source_status。
  - available / derived：保留原本 S 5/5 與 盤面：突破確認 / 極強 等文字。
  - 非 available / derived：持倉與未持倉卡改顯示 S 證據不足 或 S 不可用，盤面降級為 強弱證據不足｜待確認。
  - 保留 price / RR / volume 顯示，不因 score 不可用把整卡降級成 price source missing。
  - 補 regression probe：持倉 insufficient-data、未持倉 source-error、available/derived 正常案例。

  ## 修改檔案

  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 只在 presentation formatter 加小型 helper，不碰 strategy decision、RR 公式、DB schema/write、Telegram live delivery。
  - 測試使用既有 generator.formatTelegramPositionCard / generator.formatTelegramUnheldCard wrapper，直接驗證 report card rendering path。
  - 未改 core/generator.py 的 VERSION、message list 結構、分組順序或 payload shape。

  ## 契約影響

  - 使用者可見文字契約變更：score source status 不足時，同卡不得再顯示 S n/5 或依賴 score/strength 的高信心盤面文字。
  - 無回傳結構變更。
  - 無 payload shape 變更。
  - 無 message list 順序變更。
  - 無 DB contract 變更。
  - 版本同步：已檢查 core/generator.py 目前 VERSION = "v20.4.25" 與 header tests；repo 內未找到硬性本輪必升版規則，未回退也未擅自升版。

  ## 直接消費者同步

  - 持倉卡：formatTelegramPositionCard 已同步使用 score source gate。
  - 未持倉卡：formatTelegramUnheldCard 已同步使用 score source gate。
  - 既有 generator wrapper 仍透過 presentation deps 呼叫 formatter，無需改呼叫參數。
  - QA / regression test 已新增持倉與未持倉 probe。

  ## 未影響模組

  - 未改 services/analysis.py
  - 未改 strategy decision / 買賣 / 加減碼 / 停損停利判斷
  - 未改 RR 公式
  - 未改 DB schema / RLS / grant / policy / role / index / constraint
  - 未新增 production write / backfill / live Telegram delivery
  - 未改主 repo，未 commit / push

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'score_source or breakout_distance'
      - 結果：失敗，原因是 x86_64 Python 載入 arm64 .venv 的 pydantic_core，架構不相容。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'score_source or breakout_distance'
      - 結果：6 passed, 105 deselected, 13 warnings
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py
      - 結果：111 passed, 221 warnings
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py tests/test_generator_report.py
      - 結果：passed
  - git diff --check
      - 結果：passed

  ## 殘留風險

  - 目前 build_report_context 仍會由 OHLCV 推導 score status；「price/OHLCV/RR 可用但 score source-error」這類情境需要上游已在 evidence_manifest 提供獨立 score status，本輪只修 presentation 消費門控。
  - QA 仍需補 TASK 要求的額外反證路徑，例如 missing score source status。

  ## 旁支待辦

  - 其他 evidence gate 缺口與其他顯示門控清單項不在本輪處理。
  - 若 Architect/Owner 要所有使用者可見文案修復固定升版，需另補明確版本治理規則。
