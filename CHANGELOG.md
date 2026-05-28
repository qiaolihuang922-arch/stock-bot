# CHANGELOG:

## 修改內容

- 修正 QA 阻塞的直接消費者漏同步：`formatTelegramUnheldCard()` 對可買且 `action >= 60%` 的未持倉詳情卡，不再顯示 `可買｜60%倉` 或 `買點：可買｜建議 60%倉｜現在可分批`。
- 未持倉詳情卡與 summary 同步顯示 `首筆最多 30%，總上限 60%` 與 `分批，不追價`；低於 60% 的既有可買文案維持 `10%倉 / 建議 10%倉 / 現在可分批` 形狀不變。
- 盤中 Telegram message list 產生詳情卡時，未持倉詳情卡觸發標籤由 `明日觸發` 改為 `盤中觸發`，避免 05/28 盤中報文仍混用明日語意。
- 保留本輪既有契約：header `v20.0.10`、summary `今日盤中執行`、英業達今日已停利後顯示已執行 / 停利後觀察、旺宏弱反彈淘汰原因。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 契約影響

- `formatTelegramUnheldCard(name, data, report_phase=None)` 新增 optional 參數 `report_phase`；直接呼叫不傳時維持原本 `明日觸發` 標籤，`formatTelegramMessages()` 會傳入當前報文 phase。
- 新增 `unheld_entry_size_detail_text()` 作為 formatter 內部 helper；只改未持倉詳情卡文案，不改策略 action、回傳結構、Telegram payload shape、message list 順序或 DB 寫入。
- 使用者可見文案改變：可買且 `action >= 60%` 的未持倉詳情卡改顯示首筆上限與總上限，不再把 60% 寫成一次性建議倉位。
- 盤中未持倉詳情卡觸發標籤改為 `盤中觸發`；非盤中直接呼叫仍可保留 `明日觸發`。

## 版本同步

- `core/generator.py` 保持 `VERSION = "v20.0.10"`。
- `tests/test_generator_report.py` 已同步檢查 `v20.0.10` header 與盤中語意。
- 未回退到 `v20.0.9`，也未更動版本以外的產品方向。

## 直接消費者同步

- `formatTelegramMessages()` 已同步傳入 `report_phase` 給 `formatTelegramUnheldCard()`，覆蓋 Owner 手機 Telegram 報文與 Telegram message list / formatter output。
- `tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_10_execution_contract` 已新增長報文 fixture 斷言：
  - 光寶科未持倉詳情卡仍保留 `可買` 狀態。
  - 未持倉詳情卡包含 `首筆最多 30%，總上限 60%` 與 `分批，不追價`。
  - 未持倉詳情卡不含 `可買｜60%倉`、`買點：可買｜建議 60%倉｜現在可分批`、`建議 60%倉`。
  - 盤中詳情卡顯示 `盤中觸發`。
- `tests/test_generator_report.py` 既有低於 60% 可買案例仍斷言 `可買｜10%倉` 與 `買點：可買｜建議 10%倉｜現在可分批`，確認低倉位文案未被改壞。
- `tests/test_notifier.py` 已納入自檢，確認 Telegram notifier message list 直接消費者未因 formatter 變更破壞。

## 未影響模組

- 未改 `services/analysis.py` 策略決策。
- 未改 `core/condition_engine.py` 條件映射。
- 未改 DB schema / migrations / Supabase write path。
- 未改 watchlist。
- 未改 replay/backfill。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `PYTHONPATH=/private/tmp/stockbot_test_config:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_intraday_v20_0_10_execution_contract tests/test_generator_report.py::GeneratorReportTest::test_summary_with_holding_and_buy_has_no_zero_tracking_noise tests/test_generator_report.py::GeneratorReportTest::test_rejected_weak_rr_uses_true_reject_reason_not_rr tests/test_generator_report.py::GeneratorReportTest::test_v19_3_3_valid_buy_is_summary_buy_group_not_watch_group tests/test_generator_report.py::GeneratorReportTest::test_v19_4_tracking_states_do_not_override_valid_buy_or_weak_reject -q`
  - 結果：`5 passed, 13 warnings`
- `PYTHONPATH=/private/tmp/stockbot_test_config:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -q`
  - 結果：`42 passed, 21 warnings`
- `PYTHONPATH=/private/tmp/stockbot_test_config:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py -q`
  - 結果：`44 passed, 21 warnings`
- 自檢備註：第一次手動指定測試時誤列不存在的 `test_valid_buy_stays_execution_not_tracking`，pytest 回報 `not found` 且未形成有效產品自檢；已改用現有可買與長報文 case 重跑並通過。

## 殘留風險

- 未執行 full pytest、replay/backfill dry-run、live Telegram delivery 或 live Supabase write；依本輪禁止事項未執行。
- `formatTelegramUnheldCard()` 若被其他舊呼叫方直接呼叫且未傳 `report_phase`，仍會維持非盤中預設 `明日觸發`；目前本輪直接消費者 `formatTelegramMessages()` 已同步盤中 phase。
- 本輪只修 QA 指出的未持倉詳情卡漏同步與盤中詳情卡觸發標籤，未擴大修改策略分類、倉位計算、payload 或報文分組順序。
