# QA_REPORT:

## 測試範圍

- 任務：`future_watch_event_impact_explanation_20260604`。
- 範圍：future-watch 第 4 則台股影響事件來源移除、影響說明、official `generate()` smoke。
- 未擴大到策略、DB、live Telegram。

## 關聯風險掃描

- `core/future_watch.py` 只改 global event formatter / impact note，不含 DB client、upsert、delete 或 Telegram send。
- `core/generator.py` 未改，報文版本維持 `v20.4.47`。
- 資料查詢窗口仍是未來 30 日；本輪不改資料來源。

## 跨區塊語意一致性

- 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報後。
- 第 4 則仍不使用 `可買`、`新倉建議`、`今日下單` 等交易語意。
- 第 4 則段落順序仍為 `歷史類比` -> `未來30日法說會` -> `未來30日台股影響事件`。
- MOPS / 台股影響事件 source-error 仍 fail closed，不會被顯示成無事件。

## 使用者誤讀風險

- 第三段原本顯示 `來源：...`，手機閱讀價值低；已改為 `說明：...`，直接回答為什麼影響台股。
- 歷史類比現況不改算法：目前是 TWSE 即時大盤 / 近月 OHLC + 壓力模板，不是多年歷史資料庫相似度模型。

## 失敗標本反證

- 原風險：Owner 指出第三段來源可以去除，應增加為什麼影響台股的說明。
- 反證 1：focused tests 檢查第三段沒有 `來源：`。
- 反證 2：focused tests 檢查第三段每筆有 `說明：`。
- 反證 3：official `generate()` read-only smoke 第三段不再顯示 source，改顯示台股影響說明。

## 質疑與反證

- Focused future-watch tests：11 passed。
- py_compile：passed。
- `git diff --check`：passed。
- Official `generate()` read-only smoke：
  - 第三段不含 `來源：`。
  - 利率/匯率事件顯示 `影響外資風險偏好與台股估值；牽動美元/台幣與外資流向`。
  - 通膨事件顯示 `牽動Fed路徑與科技股估值；影響外資風險偏好與台股估值`。
  - 政治風險事件顯示 `提高避險情緒與供應鏈不確定性`。
  - 無 DB write、無 Telegram delivery。

## 未測項目

- 未跑 full `tests/test_generator_report.py -q`。
- 未跑 production runner artifact。
- 未做 live Telegram。
- 未做 DB read/write smoke。
- 未做全球事件 official calendar parser hardening。
- 未做台股影響事件分級模型。

## QA 結論

通過。

本輪台股影響事件顯示修正通過：第三段去除來源欄位，改用說明直接交代事件為什麼影響台股。
