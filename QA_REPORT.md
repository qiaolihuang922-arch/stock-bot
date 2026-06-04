# QA_REPORT:

## 測試範圍

- 任務：`future_watch_taiwan_crash_analogy_20260604`。
- 範圍：第 4 則 `歷史類比` 台股口徑顯示、fallback 文案、official generator smoke。
- 未擴大到策略、DB、live Telegram。

## 關聯風險掃描

- 修改只在 `core/future_watch.py` 可見字串與測試 fixture。
- 沒有新增 network source、DB client、write path 或 Telegram send。
- 報文版本維持 `v20.4.47`。

## 跨區塊語意一致性

- 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報後。
- `歷史類比` 仍是資訊提醒，不是可買 / 可賣指令。
- 台股影響事件段仍可列全球事件，但歷史類比段不再把全球股災當主樣本。

## 使用者誤讀風險

- 舊 `全球股災前段` 會讓使用者以為模型在用全球市場 crash timeline 對比台股，參考軸不清。
- 新文案改成 `台股急跌前段`，與 TWSE source 及台股報文目的一致。
- fallback 改成 `台股急跌樣本`，避免資料不足時仍暗示泛全球崩盤樣本。

## 失敗標本反證

- 失敗標本：Owner 指出歷史類比不用全球股災，只做台灣股災，全球可能不準。
- 反證：focused tests 檢查 TWSE pressure line 與 final future-watch fixture 不含 `全球股災`。

## 質疑與反證

- Focused future-watch tests：11 passed。
- py_compile：passed。
- `git diff --check`：passed。
- Official `generate()` read-only smoke：
  - 歷史類比顯示 `2015/08/20-24 台股急跌前段`。
  - `CHECK_NO_GLOBAL_CRASH=True`。
  - 無 DB write、無 live Telegram。

## 未測項目

- 未做多年台股崩盤資料庫相似度模型。
- 未跑 live Telegram。
- 未做 DB read/write smoke。

## QA 結論

通過。

本輪台股歷史類比語意修正通過：第 4 則不再使用全球股災作歷史類比主事件，fallback 也改為台股急跌樣本口徑。
