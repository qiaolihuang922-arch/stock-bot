# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：`normal_patch`
- 版本：`v20.4.16`
- 風險：使用者可見 Telegram formatter / golden 測試更新；不碰策略 decision、DB schema/write、live delivery。

## 修改內容

- 將報文版本升至 `v20.4.16`。
- 第一則持倉卡原 `Source：position available...` 改為人話資料行：
  - `資料：持倉與現價已確認；風控由持倉成本/停損推算`
  - 缺持倉或現價時 fail-closed：`資料：缺持倉或現價，停止持倉建議`
- 第二則未持倉卡原 `Source：price available...` 改為人話資料行：
  - 完整資料：`資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算`
  - 缺現價 / OHLCV 時 fail-closed：`資料：缺現價/OHLCV，停止新倉判斷`
- 持倉卡非加碼情境不再顯示新倉 RR 數字，改為：
  - `數據：新倉 RR：持倉不適用｜...`

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## 最小改動策略

- 只修改 Telegram 卡片資料來源 formatter、持倉卡 RR 顯示文字、版本常量與相關測試斷言。
- 保留既有三則 message 順序與卡片主欄位位置。
- 未改 strategy decision、ranking/scoring/RR 公式、DB payload、DB write path、live Telegram delivery。

## 契約影響

- 使用者可見 header / evidence 標題版本：`v20.4.15 -> v20.4.16`。
- Message list 順序：無變更。
- Payload / DB / CLI contract：無變更。
- Telegram 卡片文字契約有變更：
  - 第一則 / 第二則卡片 Source 行位置改為 `資料：...`。
  - 持倉卡新倉 RR 顯示改為不適用文案，不輸出 RR 數字。

## 直接消費者同步

- 同步 `tests/test_generator_report.py` golden assertions：
  - 完整三則 sample 版本更新。
  - 持倉卡資料行、未持倉卡資料行、缺資料 fail-closed、持倉 RR 不適用文案。
  - 新增缺 OHLCV 反向 fixture，確認不可行動且不輸出可買語氣。
- 同步 `tests/test_market_theme_evidence.py` 版本契約 assertions。

## 未影響模組

- strategy decision / buy-sell / 加減碼 / 停損停利判斷未改。
- RR、score、volume 計算公式未改。
- DB schema / RLS / grant / policy / role / index / constraint 未改。
- production DB write、backfill、live Telegram delivery 未執行。
- Telegram 三則報文主流程與分組未重排。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/notifier.py`：passed
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：117 passed，169 warnings
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_notifier.py`：3 passed
- `git diff --check`：passed

## 殘留風險

- Tech 自檢只覆蓋 formatter/golden 與 notifier 局部測試；完整手機閱讀驗收仍需 QA 依 `TASK.md` 另跑完整三則 Telegram sample。
- 第三則 evidence 仍保留既有 source/status 語彙，因本輪 TASK 限定修第一則持倉卡與第二則未持倉卡。

## 旁支待辦

- 若 Owner 後續要求第三則 evidence 也全面人話化，需另開任務，避免本輪擴大報文契約。
- Telegram reply markup 附著最後一則 message 的 delivery consumer 風險仍屬既有旁支，未納入本輪。
