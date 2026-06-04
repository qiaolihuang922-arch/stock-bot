# TASK: future_watch_complete_v20_4_47

## 任務狀態

- task_id：`future_watch_complete_v20_4_47`
- 任務類型：normal_patch
- 狀態：ready_for_tech
- 版本建議：`v20.4.47`
- QA 分級：L2

## Owner 問題

Owner 認為 v20.4.46 `【未來30日關注】` 仍只是 source fail-closed 雛形，不是完成版：

- 歷史類比只顯示 `無高相似崩盤樣本`，沒有可讀時間線。
- MOPS 法說會一直 source-error。
- 全球事件有英文 raw 名稱與 `source=` 技術欄位。

## 使用者可見結果

第 4 則要成為完成版資訊提醒：

- 歷史類比：用 TWSE 即時 / 當月 OHLC 建立壓力情境、相似點、差異與關注條件。
- 法說會：MOPS 正確查詢與解析，能列未來 30 日法說會；查不到事件不假造，解析失敗才顯示人話錯誤。
- 全球事件：中文事件名，來源顯示 `官方` / `備援`，不再顯示 raw `source=...`。

## 非目標

- 不改交易策略、RR、持倉風控。
- 不做 DB 方向，不新增 DB read/write/backfill。
- 不發 live Telegram。
- 不修 unrelated legacy generator snapshot failures。

## 影響模組與直接消費者

- `core/future_watch.py`
- `core/generator.py`
- `tests/test_generator_report.py`
- Telegram 第 4 則 `【未來30日關注】`

## 輸出契約

- Header 版本升 `v20.4.47`。
- 歷史類比包含：情境、相似度、相似點、差異、關注、`source=TWSE`。
- 法說會成功時列：日期、代號、名稱、事件、關注原因、`source=MOPS`。
- 法說會 source-error 文案為人話，不使用 raw `source-error（MOPS）`。
- 全球事件行格式：日期 + 中文事件 + 影響面 + `來源：{source}{官方/備援}`。

## 驗收條件

- Focused future-watch tests 通過。
- py_compile 通過。
- `git diff --check` 通過。
- Read-only live smoke 可輸出 TWSE 壓力情境、MOPS 2301 未來法說會、中文全球事件。

## 失敗標本與驗收路由

- 失敗標本：Owner 貼出的 v20.4.46 第 4 則，包含 TWSE insufficient、MOPS source-error、英文全球事件。
- 驗收路由：future_watch helper -> official `formatTelegramMessages` / `generate_report` focused tests -> read-only live smoke。

## 禁止事項與阻塞條件

- 不得假造 MOPS 事件。
- 不得把歷史類比寫成崩盤預測。
- 不得新增 DB write / live Telegram。
