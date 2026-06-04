# QA_REPORT:

## 測試範圍

- 任務：`future_watch_mops_breadth_query_fix_20260604`。
- 範圍：future-watch 第 4 則 MOPS 查詢完整性、query budget starvation regression、official `generate()` smoke。
- 未擴大到策略、DB、live Telegram。

## 關聯風險掃描

- `core/future_watch.py` 只改 readonly MOPS collection / formatter item cap，不含 DB client、upsert、delete 或 Telegram send。
- `core/generator.py` 未改，報文版本維持 `v20.4.47`。
- 資料查詢窗口仍是未來 30 日；本輪修正查詢順序，不改資料來源。

## 跨區塊語意一致性

- 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報後。
- 第 4 則仍不使用 `可買`、`新倉建議`、`今日下單` 等交易語意。
- 第 4 則段落順序仍為 `歷史類比` -> `未來30日法說會` -> `未來30日台股影響事件`。
- MOPS / 台股影響事件 source-error 仍 fail closed，不會被顯示成無事件。

## 使用者誤讀風險

- 原單檔深度優先會讓使用者誤以為「只有聯電有法說會」；已改成所有標的先查第一優先市場別，避免後排標的被漏查。
- 法說會顯示上限提高到 10，避免 06/22 類較晚事件查到後又被截掉。

## 失敗標本反證

- 原風險：Owner 貼出的正式第 4 則 `未來30日法說會` 只剩 `06/05 2303 聯電` 一筆。
- 反證 1：focused regression 在 12 檔 / 24 query budget 下，第 12 檔第一優先市場別仍能查到事件。
- 反證 2：official `generate()` read-only smoke 不再只有 1 筆，恢復多檔法說會。
- 反證 3：official `generate()` read-only smoke 包含 06/22 光寶科，證明顯示上限不再截掉後段事件。

## 質疑與反證

- Focused future-watch tests：11 passed。
- py_compile：passed。
- `git diff --check`：passed。
- Official `generate()` read-only smoke：
  - 法說會不再只有聯電一筆。
  - 顯示 06/04 緯創 / 群創、06/05 光寶科 / 聯電 / 仁寶 / 英業達、06/08 英業達、06/09 仁寶、06/22 光寶科。
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

本輪 MOPS 漏查修復通過：query budget 不再讓前排標的吃掉後排標的查詢機會，official `generate()` 已從只剩聯電一筆恢復為多檔法說會。
