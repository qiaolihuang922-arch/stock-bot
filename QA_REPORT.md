# QA_REPORT:

## 測試範圍

- 任務：`future_watch_30d_section_semantics_20260604`。
- 範圍：future-watch 第 4 則段落標題、source-error 文案、前三則不污染。
- 未擴大到策略、DB、live Telegram。

## 關聯風險掃描

- `core/future_watch.py` 只改 formatter 可見文案，不含 DB client、upsert、delete 或 Telegram send。
- `core/generator.py` 未改，報文版本維持 `v20.4.47`。
- 資料查詢窗口仍由既有 collector 控制；本輪沒有放寬或擴大資料範圍。

## 跨區塊語意一致性

- 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報後。
- 第 4 則仍不使用 `可買`、`新倉建議`、`今日下單` 等交易語意。
- 第 4 則段落順序為 `歷史類比` -> `未來30日法說會` -> `未來30日台股影響事件`。
- MOPS / 台股影響事件 source-error 仍 fail closed，不會被顯示成無事件。

## 使用者誤讀風險

- 舊標題 `全球事件` 容易被讀成泛全球日曆；已改成 `未來30日台股影響事件`。
- 舊標題 `法說會提醒` 沒有明確 30 日窗口；已改成 `未來30日法說會`。

## 失敗標本反證

- 原風險：第 4 則第三區塊顯示 `全球事件`，與 Owner 要的「會影響台灣股市的事件」不一致；法說會標題也沒明確未來 30 日。
- 反證 1：focused tests 檢查第 4 則新標題順序正確。
- 反證 2：focused tests 檢查舊 `全球事件` / `法說會提醒` 段落標題不再出現。
- 反證 3：source-error 測試檢查錯誤文案也使用 `未來30日法說會` / `未來30日台股影響事件`。
- 反證 4：read-only live smoke 顯示新標題，且光寶科 06/05 / 06/22 法說會仍存在。

## 質疑與反證

- Focused future-watch tests：10 passed。
- py_compile：passed。
- `git diff --check`：passed。
- Read-only live smoke：
  - 第 4 則包含 `未來30日法說會`。
  - 第 4 則包含 `未來30日台股影響事件`。
  - 法說會內容：仍列光寶科 06/05 / 06/22。
  - 無 DB write、無 Telegram delivery。

## 未測項目

- 未跑 full `tests/test_generator_report.py -q`。
- 未跑 production runner artifact。
- 未做 live Telegram。
- 未做 DB read/write smoke。
- 未做台股影響事件分級模型。
- 未做全球事件 official calendar parser hardening。

## QA 結論

通過。

本輪語意修正達成：除了歷史類比外，另外兩個大項都在標題明示未來 30 日；第三區塊改成 `未來30日台股影響事件`，不再泛稱全球事件。
