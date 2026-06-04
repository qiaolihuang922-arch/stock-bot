# TASK: future_watch_event_impact_explanation_20260604

## 任務狀態

- task_id：`future_watch_event_impact_explanation_20260604`
- 任務類型：tiny_patch
- 狀態：ready_for_qa
- 版本建議：維持 `v20.4.47`
- QA 分級：L1

## Owner 問題

Owner 問歷史類比現在怎麼查數據，並要求第三段 `未來30日台股影響事件` 去除來源顯示，改成說明為什麼影響台股。

## 使用者可見結果

- 第三段事件行不再顯示 `來源：...`。
- 第三段事件行改顯示 `說明：...`，用影響面轉成人話解釋台股影響。
- 歷史類比現況要在交付中說清楚：目前讀 TWSE 即時大盤 / 近月 OHLC，計算單日跌幅、高檔回落、盤中震盪、樣本天數，再套固定壓力情境模板，不是多年歷史資料庫相似度模型。

## 非目標

- 不改交易策略、RR、持倉風控、買賣決策。
- 不做 DB 方向，不新增 DB read/write/backfill。
- 不發 live Telegram。
- 不改全球事件完整官方 calendar parser。
- 不改歷史類比算法。
- 不改 DB 方向或加 cache。

## 影響模組與直接消費者

- `core/future_watch.py`
- `tests/test_generator_report.py`
- Telegram 第 4 則 `【未來30日關注】`

## 輸出契約

- 第三段格式：`日期 事件｜影響面：...｜說明：...`。
- 第三段不得出現 `來源：`。
- `說明` 可由 `impact_note` / `reason` 覆蓋；缺省時由 `impact` 產生台股影響說明。

## 驗收條件

- Focused future-watch tests 通過。
- py_compile 通過。
- `git diff --check` 通過。
- Read-only official `generate()` smoke：第三段不含 `來源：`，每筆含 `說明：`。

## 失敗標本與驗收路由

- 失敗標本：Owner 指出的 `來源可以去除，應該要增加說明為什麼影響`。
- 驗收路由：future_watch formatter -> focused tests -> official `generate()` read-only smoke。

## 禁止事項與阻塞條件

- 不得假造台股影響事件。
- 不得把 source-error 靜默顯示成無事件。
