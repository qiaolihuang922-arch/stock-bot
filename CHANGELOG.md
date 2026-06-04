# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：使用者可見第 4 則 `【未來30日關注】` 完成版；不改交易策略、DB、live Telegram。

## 修改內容

- `core/generator.py`：版本升 `v20.4.47`。
- `core/future_watch.py`：
  - TWSE 歷史類比由單純 insufficient 改成壓力情境線：情境、相似度、相似點、差異、關注條件。
  - MOPS adapter 補 `step=1` / `firstin=1`，解析官方 `t100sb02_1` 真實表格。
  - MOPS parser 改用欄位標題判定法說會資料列；資料列不必重複出現 `法人說明會` 四字。
  - MOPS 多市場查詢不再讓單一 TYPEK source-error 覆蓋已成功查到的事件。
  - 全球事件中文化，來源改為 `來源：ECB官方` / `來源：G7備援`。
- `tests/test_generator_report.py`：
  - 更新 v20.4.47 focused future-watch tests。
  - 更新全球事件來源格式與 MOPS / TWSE 完成版預期。

## 修改檔案

- `core/future_watch.py`
- `core/generator.py`
- `tests/test_generator_report.py`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`

## 契約影響

- 第 4 則歷史類比不再只顯示 `無高相似崩盤樣本`，除 source-error 外會給出最接近的壓力情境與差異。
- MOPS 查到未來 30 日法說會時列事件；查得到官方表格但無事件時不顯示法說會段；不可解析時顯示人話錯誤。
- 全球事件可見行不再使用 raw `source=`，改 `來源：...官方/備援`。

## 未影響模組

- 未改交易策略、RR、加減碼、停損停利、持倉狀態機。
- 未改 DB schema / RLS / grant / policy / write path。
- 未做 live Telegram delivery。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_future_watch2 arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_47_future or v20_4_47_live or v20_4_47_generate_report' -q` -> 9 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_47_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- Read-only live smoke with 光寶科 2301 -> TWSE 壓力情境、MOPS 06/05 / 06/22 法說會、中文全球事件 lines。

## 覆蓋層級

- helper：TWSE / MOPS / global source helpers covered。
- formatter：第 4 則完成版 wording covered。
- official report message-list：focused `formatTelegramMessages` / `generate_report(dry_run=True)` covered。
- live smoke：read-only source path covered；無 DB write、無 Telegram delivery。

## 殘留風險

- `tests/test_generator_report.py -q` 仍有 30 個 legacy snapshot / funnel failures，集中在既有未持倉分類與舊契約，不屬本輪 future-watch 完成版；本輪未宣稱全檔清零。
- 全球事件 live parser 若官方 HTML 改版或被擋，會顯示備援 source；後續可另開 official calendar parser hardening。
- TWSE 歷史類比目前是壓力情境 template，不是完整多年統計模型；已明示差異與不是崩盤等級。
