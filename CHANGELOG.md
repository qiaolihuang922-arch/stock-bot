# CHANGELOG:

## 任務尺寸與風險

- task_type: risk_patch。
- 風險判斷：修改盤後 Telegram 使用者可見交易摘要，涉及 message list 文字契約。
- 邊界：未碰策略 decision、DB write、live delivery、VERSION。

## 修改內容

- 修復盤後第三則簡報只看 `watch_items` 判斷新倉，漏掉已進入 `holding_items` 的今日買入標的。
- 當 `holding_items` 有 today buy 時，第三則改顯示：
  - `今日交易：已建立新倉 N 檔（...）`
  - `新增有效進場：無` 或需明日確認的候選數
- 無 today buy、無可買 watch 時，不誤報今日已有新倉，仍保留 `新增有效進場：無`。
- 補手機閱讀 probe，覆蓋「持倉卡有今日買入、第三則不得出現今日無有效新倉」場景。

## 修改檔案

- `presentation/report.py`
  - 新增 `_today_buy_holding_names()`。
  - `_afterhours_brief_lines()` 納入 `holding_items` 的 today buy 判斷。
- `core/generator.py`
  - 將既有 `is_today_buy_holding()` 注入 presentation deps，避免重寫 today buy 判斷口徑。
- `tests/test_generator_report.py`
  - 新增 afterhours today-buy holding probe。
  - 同步既有盤後 today buy 測試預期。

## 最小改動策略

- 只重用既有 `is_today_buy_holding()`，不新增資料來源、不改 holding / event 結構。
- 只改盤後第三則簡報 formatter 與直接 deps。
- 不改策略判斷、排序邏輯、DB、live Telegram、VERSION。

## 契約影響

- 使用者可見盤後第三則文字變更：
  - today buy holding 存在時，不再輸出 `今日無有效新倉`。
  - 額外可買機會仍以 `新增有效進場` 分開表達，避免把今日已買標的包裝成可追買推薦。
- 回傳結構、payload shape、DB contract、CLI 輸出無變更。
- VERSION 未變更，仍為 `v20.4.21`。

## 直接消費者同步

- `format_brief_data_evidence_message()` 的 presentation deps 已同步新增 `is_today_buy_holding`。
- `formatTelegramMessages()` 盤後 message list 透過既有 deps 自動消費新行為。
- 測試同步覆蓋 Owner 手機閱讀路徑。

## 未影響模組

- 策略 decision / RR 計算 / holding status：未改。
- DB schema / RLS / grant / policy / role / index / constraint：未改。
- DB write / backfill / replay：未改。
- live Telegram delivery：未執行、未改。
- VERSION：未改。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：95 passed，189 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py core/generator.py tests/test_generator_report.py`：passed。
- `git diff --check`：passed。

## 殘留風險

- 今日買入名稱順序沿用既有持倉排序，不另改成輸入 fixture 順序；本輪不改排序契約。
- 只跑了相關報文測試檔，未跑 full pytest。

## 旁支待辦

- 光寶科買入解釋、技嘉 RR 0.00、縮量漲停風險、智原 observation_days 均未處理，依 TASK.md 留待後續任務。
- Telegram reply markup 附著最後一則 message 的 delivery consumer 風險未處理。
