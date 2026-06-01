# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：只改 Telegram 持倉卡 RR 顯示判斷與可重跑 probe；不改 strategy decision、RR 計算、持倉狀態機、DB schema/write、VERSION 或 live delivery。

## 修改內容

- `presentation/report.py`
  - 持倉 RR 顯示改以最終使用者可見主行動為準；若主行動是 `新倉風控觀察`，即使底層 signal 是 `ADD_10`，仍顯示 `新倉 RR：不適用（既有持倉）`。
- `tests/test_generator_report.py`
  - 更新 `test_v20_4_21_afterhours_mobile_readability_probe`：模擬今日買入但底層 `ADD_10 / allow_add=True` 的建準類情境，確認卡片仍不顯示 `RR 2.73`。
  - 強化 presentation boundary gate：顯示層不得引入 schema alter 類入口。

## 修改檔案

產品 / 測試 diff：

- `presentation/report.py`
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
  - 今日買入且主行動為 `新倉風控觀察` 的持倉卡不再顯示具體新倉 RR 數字。
- Message list 結構、payload shape、DB contract、版本常量均未變更。
- 報文版本維持 `v20.4.21`，未回退。

## 直接消費者同步

- Telegram message renderer：同步盤後卡片文案與第三則資料依據。
- Owner 手機閱讀路徑：更新 probe 檢查建準類今日買入 / 底層 ADD 情境。
- v20.4.x report tests 已同步。

## 未影響模組

- 策略核心與買賣決策。
- RR 計算公式與加碼 RR 顯示契約。
- 持倉狀態機。
- DB schema / RLS / grant / policy / role / index / constraint。
- DB write、backfill、live Telegram delivery。
- Telegram reply markup / delivery consumer。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py::GeneratorReportTest::test_presentation_report_module_has_no_storage_or_evidence_write_imports tests/test_generator_report.py::GeneratorReportTest::test_v20_4_21_afterhours_mobile_readability_probe`：2 passed，17 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：92 passed，181 warnings。
- `.venv/bin/python - <<'PY' ... generate_report(dry_run=True) ... PY`：建準卡片顯示 `數據：新倉 RR：不適用（既有持倉）`。
- `.qa_tmp/v20_4_21_holding_rr_dry_run_card.json`：`credential_values_included=false`、`schema_change=false`、`data_write=false`、`live_telegram=false`。

## QA 反證

- Re-QA output：`.cao_agent_context/outputs/20260601_183214_25279_stock_qa_code_readonly.answer.txt`，結論 `通過`。
- QA 確認 fixture 保留 `ADD_10 / allow_add=True / 今日買入`，但持倉卡仍顯示 `新倉 RR：不適用（既有持倉）`，不顯示 `數據：RR 2.73`。
- QA 確認 presentation 未新增 DB writer、evidence writer、schema alter 或 fake production data path。

## 殘留風險

- 本輪未處理 Telegram reply markup 附著最後一則 message 的旁支風險。
- 本輪未做 production replay / backfill / live delivery / DB write。
- 其他非本輪指定文案美化、排序、策略分數與資料完整性問題未處理。
