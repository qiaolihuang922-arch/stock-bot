# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：只改 Telegram 盤後第三則顯示內容、presentation deps bridge 與可重跑 probe；不改 strategy decision、RR 計算、持倉狀態機、DB schema/write、VERSION 或 live delivery。

## 修改內容

- `presentation/report.py`
  - 盤後第三則恢復 `持倉風控檢查` 清單。
  - 盤後第三則恢復 `未持倉漏斗（非執行）` 摘要。
  - `資料依據` 從空泛四句改為合併證據摘要：市場短期背景、持倉數、未持倉分類數、執行記憶邊界、持倉 RR 邊界。
  - 持倉 RR 顯示仍以最終使用者可見主行動為準；主行動是 `新倉風控觀察` 時顯示 `新倉 RR：不適用（既有持倉）`。
- `core/generator.py`
  - 將既有 `unheld_tracking_only_count` 傳入 presentation deps，供第三則資料依據統計未持倉分類。
- `tests/test_generator_report.py`
  - 更新 `test_v20_4_21_afterhours_mobile_readability_probe`，覆蓋盤後第三則清單、漏斗、資料依據合併摘要、執行記憶與 RR 邊界。

## 修改檔案

產品 / 測試 diff：

- `presentation/report.py`
- `core/generator.py`
- `tests/test_generator_report.py`

Architect handoff：

- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`

## 契約影響

- 使用者可見報文文案有變更：
  - 盤後第三則重新包含持倉風控檢查與未持倉漏斗。
  - 資料依據包含持倉 / 未持倉數量與證據用途邊界。
  - 今日買入且主行動為 `新倉風控觀察` 的持倉卡不顯示具體新倉 RR 數字。
- Message list 數量、payload shape、DB contract、版本常量均未變更。
- 報文版本維持 `v20.4.21`，未回退。

## 直接消費者同步

- Telegram message renderer：同步盤後第三則清單與資料依據。
- Owner 手機閱讀路徑：probe 檢查持倉卡、未持倉卡、第三則簡報與資料依據。
- v20.4.x report tests 已同步。

## 未影響模組

- 策略核心與買賣決策。
- RR 計算公式與加碼 RR 顯示契約。
- 持倉狀態機。
- DB schema / RLS / grant / policy / role / index / constraint。
- DB write、backfill、live Telegram delivery。
- Telegram reply markup / delivery consumer。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py::GeneratorReportTest::test_v20_4_21_afterhours_mobile_readability_probe tests/test_generator_report.py::GeneratorReportTest::test_presentation_report_module_has_no_storage_or_evidence_write_imports`：2 passed，17 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：92 passed，181 warnings。
- `.venv/bin/python - <<'PY' ... generate_report(dry_run=True) ... PY`：第三則含持倉風控檢查、未持倉漏斗與合併資料依據。
- `git diff --check`：passed。

## QA 反證

- Re-QA output：`.cao_agent_context/outputs/20260601_185800_22905_stock_qa_code_readonly.answer.txt`，結論 `通過`。
- QA 補四持倉 probe，確認旺宏 / 光寶科 / 建準 / 智原風控行保留在第三則。
- QA 確認資料依據包含市場短期背景、持倉數、未持倉分類數、執行記憶邊界與持倉 RR 邊界，且未回到 raw source/status/table dump。
- QA 確認 presentation / deps bridge 未新增 DB writer、schema alter、evidence writer 或 live delivery path。

## 殘留風險

- 本輪未處理 Telegram reply markup 附著最後一則 message 的旁支風險。
- 本輪未做 production replay / backfill / live delivery / DB write。
- 其他非本輪指定文案美化、排序、策略分數與資料完整性問題未處理。
