# TASK: future_watch_mops_fundamentals_context_20260604

## 任務狀態

- task_id：`future_watch_mops_fundamentals_context_20260604`
- 任務類型：normal_patch
- 狀態：ready_for_qa
- 版本建議：維持 `v20.4.47`
- QA 分級：L2

## Owner 問題

Owner 要在法說會段增加股票 EPS 與營收年增；營收資料用當月，當月沒有就用上一個官方已公告月份。同時法說會不應只顯示泛稱 `法人說明會`，要顯示 conference / 說明會名稱。

## 使用者可見結果

- `未來30日法說會` 行顯示 MOPS summary / conference 名稱，不再只顯示 `法人說明會`。
- 每檔法說會補 `EPS {年度Q季}` 與 `營收YoY {年月}`；缺資料不硬編。
- 營收來源使用 TWSE/TPEX 官方 OpenAPI 最新月營收 snapshot；若當月尚未公告，自然使用上一個官方已公告月份。
- EPS 來源使用 TWSE/TPEX 官方 OpenAPI 最新季 EPS snapshot。

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

- 法說會格式：`日期 代號 名稱｜conference｜EPS ...｜營收YoY ...｜關注原因：...`。
- 不顯示 `source=MOPS`。
- fundamentals source fail-closed：無 EPS / 營收資料時不顯示假值。

## 驗收條件

- Focused future-watch tests 通過。
- py_compile 通過。
- `git diff --check` 通過。
- Read-only official `generate()` smoke：法說會段包含 conference 名稱、EPS、營收YoY。

## 失敗標本與驗收路由

- 失敗標本：Owner 指出同檔股票多場法說會要能看出差別，並要求補 EPS / 年收增長。
- 驗收路由：MOPS parser / fundamentals source -> future_watch formatter -> focused tests -> official `generate()` read-only smoke。

## 禁止事項與阻塞條件

- 不得假造台股影響事件。
- 不得把 source-error 靜默顯示成無事件。
