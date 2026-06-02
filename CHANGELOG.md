# CHANGELOG: Phase 0 + B1-B5 前置修復與手機閱讀回歸

  ## 任務尺寸與風險

  - 任務尺寸: risk_patch
  - 風險理由: 修改使用者可見 Telegram 報文 formatter、漏斗 count 與強弱語意 gate，影響手機閱讀下的可行動性判讀。

  ## 修改內容

  - 將報文版本由 v20.4.28 升為 v20.4.29。
  - Phase 0-1: score source_status 為不足 / 缺失時，S 分數維持保守顯示；補齊 insufficient / missing alias。
  - B1: 弱勢遠離持倉條件行移除重複 觀察： 前綴。
  - B2: score 可用但盤面同時弱勢或遠離突破時，不再顯示 極強。
  - B3/B4: 保留持倉風控完整列出與排序一致契約，並以既有 regression 覆蓋。
  - B5: 弱反彈待確認 / 漲停反彈待確認 改進獨立 隔日確認 漏斗 bucket；同步 summary、execution checklist、未持倉漏斗與卡片分組。

  ## 修改檔案

  - core/generator.py
  - presentation/report.py
  - tests/test_generator_report.py

  ## 最小改動策略

  - 只改 TASK 指定的 formatter / funnel helper / message-list regression probes。
  - 未改策略核心分數、RR 公式、DB schema、DB write path、backfill 或 Telegram live delivery。
  - B5 只針對明確反彈待確認 blocker 獨立計數，避免回退既有強勢準備與 cross-day repair 契約。

  ## 契約影響

  - 使用者可見報文版本升為 v20.4.29。
  - 報文 message list 文字契約變更:
      - 禁止 條件：觀察：觀察天數未確認。
      - 禁止弱勢 / 遠離突破盤面同時顯示 極強。
      - 未持倉漏斗在有隔日確認卡片時顯示獨立 隔日確認 N。
  - 無 payload shape、DB contract、CLI 參數或 public DB interface 變更。

  ## 直接消費者同步

  - formatTelegramPositionCard() / formatTelegramUnheldCard() 同步 score gate 與盤面語意。
  - unheld_funnel_state() / build_unheld_funnel() / format_unheld_funnel() 同步 隔日確認 bucket。
  - today_conclusion_text() / format_execution_checklist() 同步隔日確認 count。
  - tests/test_generator_report.py 補手機閱讀與 formatter regression probes。

  ## 未影響模組

  - 未改 services/analysis.py。
  - 未改 RR 計算、交易狀態機、持倉 decision 產生邏輯。
  - 未改 DB schema / RLS / grant / policy / index / constraint。
  - 未執行 production write、backfill、live Telegram delivery。

  ## 已跑自檢命令

  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py：passed
  - PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py：119 passed，225 warnings
  - git diff --check：passed
  - 備註: 直接用 .venv/bin/python -m pytest 曾因 x86_64 Python 載入 arm64 pydantic_core collection 失敗，已依既有專案方式改用 arch -arm64 重跑通過。

  ## 殘留風險

  - 本輪只覆蓋 TASK 指定 Phase 0 + B1-B5 前置修復；不代表 evidence_score / final_confidence / decision_eligible major 改造完成。
  - QA 仍需補獨立手機閱讀反證；Tech 自檢不等於 QA 通過。

  ## 旁支待辦

  - evidence_score / final_confidence / decision_eligible 策略重構另開。
  - funnel evidence modifier major 調整另開。
  - Phase 3 自動化 production 另開。
  - DB source-of-truth 補強或 schema 變更另開。
