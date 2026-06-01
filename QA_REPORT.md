# QA_REPORT:

## 測試範圍

- 任務：`report_v20_4_21_afterhours_brief_evidence_merge`，normal_patch，QA L2。
- 驗證範圍匹配 TASK：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`。
- 未擴大到 production replay、backfill、DB write、live Telegram 或 git completion gate。

## 風險預算與停止條件

1. 盤後第三則手機閱讀順序或持倉風控清單回歸。
   - 驗證：第三則順序為 `盤後簡報 -> 持倉風控檢查 -> 未持倉漏斗（非執行） -> 資料依據`，並補四持倉 probe。
   - 停止條件：第三則缺清單、順序錯、或有資料時未列出指定持倉風控行。
2. 資料依據變成空泛句或 raw source/status/table dump。
   - 驗證：資料依據包含市場短期背景、持倉數、未持倉分類數、執行記憶邊界、持倉 RR 邊界；同時掃 forbidden raw terms。
   - 停止條件：缺任一核心邊界，或出現 `source_status / source_of_truth / db_table / position_events` 類 raw dump。
3. RR 衝突保護或顯示層邊界回退。
   - 驗證：今日買入 / 底層 ADD 情境仍顯示 `新倉 RR：不適用（既有持倉）`，不顯示 `數據：RR 2.73`；presentation 未新增 DB writer / schema alter / evidence writer 依賴。
   - 停止條件：新倉風控觀察持倉露出具體新倉 RR，或 presentation 新增 write/schema/live delivery path。

## 關聯風險掃描

- `git diff --name-only`：`CHANGELOG.md`、`QA_REPORT.md`、`TASK.md`、`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`。
- `git diff --check`：passed。
- `core/generator.py` 只新增 `unheld_tracking_only_count` 到 presentation deps，未新增 DB write/schema/live delivery。
- `presentation/report.py` 無 import；未命中 DB client、writer、schema alter 或 table write path。
- TASK / CHANGELOG / diff 口徑一致：normal_patch、v20.4.21 不回退、無 DB schema/write/live Telegram。

## 跨區塊語意一致性

- `tests/test_generator_report.py`：92 passed，181 warnings。
- Targeted tests：afterhours mobile probe、manifest visible fields、presentation boundary 共 3 passed，17 warnings。
- QA 自訂四持倉 probe 通過：第三則 message count 為 3；章節定位順序為 `盤後簡報 -> 持倉風控檢查 -> 未持倉漏斗 -> 資料依據`。
- QA 自訂 probe 確認有：
  - 旺宏 / 光寶科 / 建準：`新倉風控觀察｜明日未修復降級`
  - 智原：`續抱觀察｜無法接近買點則降級`
  - `持倉與價格資料可支持風控檢查（持倉 4 檔）`
  - `未持倉 1 檔已分類`
  - 執行記憶與持倉 RR 邊界文案

## 使用者誤讀風險

- 手機閱讀順序已按第三則整體檢查，不只檢查單一 helper。
- `未持倉漏斗（非執行）` 保留非執行標記，降低把追蹤名單誤讀成下單建議的風險。
- 持倉 RR 文案保留「既有持倉若不是加碼情境，只顯示新倉 RR 不適用」，並補「持倉主行動以風控為準」。
- 未發現回到 raw source/status/table dump。

## 質疑與反證

- Tech probe 可能只覆蓋建準單一持倉：QA 補四持倉 probe，旺宏 / 光寶科 / 建準 / 智原行為符合 TASK。
- 資料依據合併可能只保留數量、缺使用邊界：測試與 probe 覆蓋市場短期背景、持倉數、未持倉分類數、執行記憶邊界、持倉 RR 邊界。
- presentation deps bridge 可能引入寫入能力：diff 與 boundary test 未發現新增 DB writer/schema/evidence writer 依賴。

## 已跑命令

- `git diff --check`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：92 passed，181 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py::GeneratorReportTest::test_v20_4_21_afterhours_mobile_readability_probe tests/test_generator_report.py::GeneratorReportTest::test_presentation_report_module_has_no_storage_or_evidence_write_imports`：2 passed，17 warnings。
- Re-QA output：`.cao_agent_context/outputs/20260601_185800_22905_stock_qa_code_readonly.answer.txt`，結論 `通過`。

## 未測項目

- 未執行 live Telegram delivery。
- 未做 production DB write、backfill、DML、schema / RLS / grant / policy 實機檢查。
- 未跑 production replay 或 evidence 全矩陣。
- 未驗 Telegram reply markup 附著位置。

## QA 結論

通過
