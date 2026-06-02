# CHANGELOG:

  ## 任務尺寸與風險

  - 任務尺寸：risk_patch
  - 風險判斷：使用者可見 Telegram summary / fail-closed 報文分組契約修正；不改策略 decision、RR、DB、live delivery。

  ## 修改內容

  - 最小修復 Final Re-QA blocked 點：source-missing / fail-closed 第三則 summary 不再輸出空執行占位：
      - 移除 ✅ 今日盤中交易執行
      - 移除 無新增下單
      - 移除結論行中的 交易執行：無新增下單
  - 補強 QA 指出的 source_missing_no_empty_execution_placeholder probe，確認 source-missing 第三則 brief 與全訊息都不含空執行占位。
  - 保留現有候選 diff 的既有契約：主要 Telegram summary path 不顯示 無新增下單、交易執行 0、僅追蹤 0、淘汰 0；全 0 未持倉漏斗仍隱藏。

  ## 修改檔案

  - core/generator.py
  - tests/test_generator_report.py
  - 既有候選 diff 仍包含：presentation/report.py、services/stock_api.py、tests/test_stock_api_history.py
  - CHANGELOG.md 進場前已 dirty；依本輪指令未直接編輯。

  ## 最小改動策略

  - 只改 source-missing 專用 summary 手寫文案與對應測試斷言。
  - 不重構 formatter，不改 message list 整體順序，不擴大第 4/5/6/7/9/11/12 已通過反證範圍。
  - 不新增 production 讀寫、不 backfill、不 live Telegram。

  ## 契約影響

  - source-missing fail-closed summary path：不再輸出空的「今日盤中交易執行 / 無新增下單」區塊。
  - 一般盤中 summary：仍可在有實際 execution lines 時顯示 ✅ 今日盤中交易執行。
  - payload、DB contract、public helper 回傳結構未新增變更。

  ## 直接消費者同步

  - format_brief_data_evidence_message() 消費的 source-missing summary input 已同步移除空占位。
  - tests/test_generator_report.py 已補 source-missing 手機閱讀 probe，防止第三則 summary 回退。
  - Telegram Owner 手機閱讀路徑同步：fail-closed 只表達來源不足與不產生交易建議，不再像執行區塊。

  ## 未影響模組

  - 未改 strategy decision。
  - 未改 RR 公式。
  - 未改 DB schema / RLS / grant / policy / role / index / constraint。
  - 未改 DB write path。
  - 未執行 production DML / backfill。
  - 未執行 live Telegram delivery。
  - 未 commit / push。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_stock_api_history.py
      - 結果：collection failed，原因為 x86_64 Python 載入 arm64 pydantic_core 架構不相容。
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_stock_api_history.py
      - 結果：125 passed，225 warnings。
  - git diff --check
      - 結果：passed。

  ## 殘留風險

  - 本輪只代表 Tech 自檢通過，不宣告 QA 通過。
  - warnings 為既有第三方 deprecation / Python 版本提示，未在本輪處理。
  - worktree 仍有進場前已存在的 CHANGELOG.md dirty 狀態，未由本輪直接編輯。

  ## 旁支待辦

  - 無本輪新增旁支。
  - 既有清單外報文文案盤點、production source-of-truth 治理仍應另開任務。
