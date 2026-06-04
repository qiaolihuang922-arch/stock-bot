# TASK: future_watch_30d_section_semantics_20260604

## 任務狀態

- task_id：`future_watch_30d_section_semantics_20260604`
- 任務類型：tiny_patch
- 狀態：ready_for_qa
- 版本建議：維持 `v20.4.47`
- QA 分級：L1

## Owner 問題

Owner 指出第 4 則語意需要更精準：除了歷史類比外，另外兩個大項都只看未來 30 天；第三點不要泛稱全球事件，改成會影響台灣股市的事件。

## 使用者可見結果

- 第 4 則三段語意改為：`歷史類比`、`未來30日法說會`、`未來30日台股影響事件`。
- 法說會與台股影響事件標題直接說明只看未來 30 日。
- source-error / empty 文案同步使用新標題，不再顯示 `全球事件` 或 `法說會提醒`。

## 非目標

- 不改交易策略、RR、持倉風控、買賣決策。
- 不做 DB 方向，不新增 DB read/write/backfill。
- 不發 live Telegram。
- 不改全球事件完整官方 calendar parser。
- 不改查詢範圍與資料來源，只改使用者可見標題 / 錯誤文案。

## 影響模組與直接消費者

- `core/future_watch.py`
- `tests/test_generator_report.py`
- Telegram 第 4 則 `【未來30日關注】`

## 輸出契約

- 第 4 則標題順序：`歷史類比` -> `未來30日法說會` -> `未來30日台股影響事件`。
- MOPS source-error：`未來30日法說會：MOPS 官方來源暫時不可解析，本次不列未確認事件`。
- 台股影響事件 source-error：`未來30日台股影響事件：官方來源暫時不可用，本次不列未確認事件`。

## 驗收條件

- Focused future-watch tests 通過。
- py_compile 通過。
- `git diff --check` 通過。
- Read-only live smoke：光寶科 2301 仍列 MOPS 06/05 / 06/22 法說會，且第 4 則使用新標題。

## 失敗標本與驗收路由

- 失敗標本：Owner 指出的「除了歷史類比外，其他兩個大項都是未來三十天而已；第三點改成會影響台灣股市的事件」。
- 驗收路由：future_watch formatter -> focused tests -> read-only live smoke。

## 禁止事項與阻塞條件

- 不得改資料查詢語意來掩蓋顯示問題。
- 不得假造 MOPS 事件或台股影響事件。
- 不得把 source-error 靜默顯示成無事件。
