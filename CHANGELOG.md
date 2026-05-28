# CHANGELOG:

## 修改內容

- 修復 `formatTelegramMessages()` 同一輪 Telegram message list 內的 phase drift 風險：message list 生成時只決定一次 `report_phase`，並傳入 summary、未持倉卡、execution/checklist/index/reason 類 phase-sensitive helper。
- `formatTelegramSummary()` 新增 optional `report_phase` 參數；由 `formatTelegramMessages()` 呼叫時不再自行重新讀取不同 phase，直接沿用同輪 phase。
- 盤後路徑改用 `今日交易紀錄` / `明日計畫 N` / `明日追蹤` 語意，避免 summary/index/reason/unheld card 出現盤中 `今日盤中交易執行`、`交易執行 N`、`分批執行` 或可被讀成今日下單的未持倉可買文案。
- `generate_report()` 也在同輪開頭固定一次 `report_phase`，同步用於 header、DB/evidence 記錄參數與 `formatTelegramMessages()`。
- 依 `TASK.md` 版本契約同步使用者可見 header / `VERSION` 為 `v20.0.14`。
- 補上 phase drift fixture 與穩定盤後 fixture；既有盤中文案測試改成明確傳入 `report_phase="盤中"`，避免測試受實際執行時間影響。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_notifier.py`
- `CHANGELOG.md`

## 契約影響

- `formatTelegramMessages()` 新增 optional `report_phase=None` 參數；未傳入時仍由函式內部決定一次 phase，message list 順序仍維持：持倉、未持倉、summary。
- `formatTelegramSummary()` 新增 optional `report_phase=None` 參數；直接呼叫且未傳入時仍可自行讀取 phase，從 `formatTelegramMessages()` 呼叫時使用同輪 phase。
- `today_conclusion_text()`、`today_reason_text()`、`format_execution_checklist()`、`detail_index_text()` 也新增 optional phase 傳遞；未傳入時保留既有盤中 helper 預設語意，避免直接 helper 呼叫方被迫同步。
- 使用者可見 header / version 字串為 `v20.0.14`。
- Telegram payload shape、notifier `send_many()` 介面、DB schema、DB payload、watchlist、scheduler、策略 decision 均未改。

## 版本同步

- `core/generator.py` 已同步 `VERSION = "v20.0.14"`。
- `tests/test_generator_report.py` header 期望已同步為 `v20.0.14`。
- `tests/test_notifier.py` notifier 直接消費者測試已同步含 `v20.0.14` header 的 summary。

## 直接消費者同步

- `formatTelegramMessages()`：固定同輪 `report_phase` 後傳入未持倉卡與 summary；summary 仍作為最後一則 message。
- `formatTelegramSummary()`：改用傳入的 `report_phase` 產生 header、source summary、今日結論、原因、execution/checklist/index。
- 未持倉卡 formatter：使用同輪 `report_phase` 決定 `盤中觸發` / `明日觸發` 與盤後 `明日追蹤` 文案。
- Execution/checklist/index/reason helpers：已同步 `report_phase`，盤後不再輸出 `交易執行 N` 或 `分批執行` 類盤中語意。
- `generate_report()`：同輪 report phase 傳入 `formatTelegramMessages()`，並同步 DB/evidence 記錄參數；未新增 live write 行為。
- Notifier 直接路徑：`services/notifier.py::send_many()` 行為未改，測試確認最後一則 summary header 仍保留。

## 未影響模組

- 未改 `services/analysis.py` 策略 decision。
- 未改 `core/condition_engine.py` 條件映射。
- 未改行情來源與 `get_market_phase()` 判斷邏輯本身。
- 未改 DB schema / migrations / payload shape。
- 未改 watchlist。
- 未改 scheduler / cron。
- 未改 replay/backfill。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `pytest tests/test_generator_report.py tests/test_notifier.py`
  - 結果：失敗，`pytest: command not found`；shell PATH 未包含 pytest。
- `.venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py`
  - 結果：collection 失敗；目前 Python 以 `x86_64` 執行，但已準備套件中的 `pydantic_core` 為 `arm64`。
- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py`
  - 結果：`52 passed, 21 warnings`。

## 殘留風險

- 本輪只固定 Telegram message list 同輪 `report_phase` 與 phase-sensitive formatter/helper 文案；未重新設計 market phase 判斷、策略 decision 或 DB 寫入時機。
- `price_label_for_source()` 仍是行情載入 / 詳情渲染層的即時 phase helper；本輪未擴大到行情來源與完整詳情備份的重構。
- 測試需用 `arch -arm64 .venv/bin/python` 執行；直接 `pytest` 不在 PATH，直接 `.venv/bin/python` 會因架構不符失敗。
