# QA_REPORT:

## 測試範圍

- 任務：`future_watch_taiwan_crash_template_library_20260604`。
- 範圍：第 4 則歷史類比樣本庫、相似事件選擇、official generator smoke。
- 未擴大到策略、DB、live Telegram。

## 關聯風險掃描

- `core/future_watch.py` 只新增常量樣本庫與 scoring helper。
- 沒有新增 DB client、write path、backfill 或 Telegram send。
- 報文版本維持 `v20.4.47`。

## 跨區塊語意一致性

- 第 4 則仍 append 在持倉 / 未持倉 / 決策簡報後。
- `歷史類比` 仍是資訊提醒，不是可買 / 可賣指令。
- MOPS 法說會、EPS / 營收、台股影響事件格式未改。

## 使用者誤讀風險

- 舊三段模板會讓使用者覺得樣本太少；現在外露 `樣本庫 台股歷史急跌 13件`。
- 報文仍只顯示最相近一條，避免手機端過長。
- `差異` 明確保留 `不是崩盤等級` 這類辨識，降低把類比讀成預測的風險。

## 失敗標本反證

- 失敗標本：Owner 指出模板太少，要求加入台股歷史股災模板做分析。
- 反證 1：focused tests 檢查樣本庫長度 13。
- 反證 2：06/04 mild pressure fixture 配到 `2015 台股急跌/中國股災外溢` 並顯示樣本庫。
- 反證 3：2024/08/05 severe fixture 配到 `2024/08/05 台股日圓套利平倉急殺`。
- 反證 4：official `generate()` smoke 顯示樣本庫且無 `全球股災`。

## 質疑與反證

- Focused future-watch tests：12 passed。
- py_compile：passed。
- `git diff --check`：passed。
- Official `generate()` read-only smoke：
  - `CHECK_LIBRARY=True`。
  - `CHECK_NO_GLOBAL_CRASH=True`。
  - 無 DB write、無 live Telegram。

## 未測項目

- 未做多年 OHLC 歷史資料表。
- 未做事件後 3/5/10 日統計勝率。
- 未跑 live Telegram。
- 未做 DB read/write smoke。

## QA 結論

通過。

本輪台股歷史急跌樣本庫修正通過：第 4 則已從三段硬模板改為 13 件台股歷史事件庫 scoring，並在正式 `generate()` read-only 路徑顯示樣本庫。
