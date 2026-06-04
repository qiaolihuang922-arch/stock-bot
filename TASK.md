# TASK: future_watch_mops_breadth_query_fix_20260604

## 任務狀態

- task_id：`future_watch_mops_breadth_query_fix_20260604`
- 任務類型：normal_patch
- 狀態：ready_for_qa
- 版本建議：維持 `v20.4.47`
- QA 分級：L2

## Owner 問題

Owner 貼出正式第 4 則後發現 `未來30日法說會` 只剩 1 筆聯電；改版前查詢資料是對的。根因是 MOPS 查詢優化改成單檔深度優先，在 query budget 下前面標的吃掉查詢額度，後面標的被漏查。

## 使用者可見結果

- MOPS 查詢改為廣度優先：所有標的先查第一優先市場別，再進 fallback TYPEK。
- 預設查詢目標擴到 12 檔，查詢預算擴到 32 次。
- 法說會可見上限擴到 10 筆，避免查到但被 formatter 截掉。
- 正式 `generate()` 第 4 則恢復多檔法說會，包含光寶科、聯電、仁寶、英業達、緯創、群創等。

## 非目標

- 不改交易策略、RR、持倉風控、買賣決策。
- 不做 DB 方向，不新增 DB read/write/backfill。
- 不發 live Telegram。
- 不改全球事件完整官方 calendar parser。
- 不改 DB 方向或加 cache。

## 影響模組與直接消費者

- `core/future_watch.py`
- `tests/test_generator_report.py`
- Telegram 第 4 則 `【未來30日關注】`

## 輸出契約

- MOPS query order 不得讓單一標的先掃完所有 TYPEK 後才換下一檔。
- 在 `max_queries=24`、`max_targets=12` 下，第 12 檔第一優先市場別仍必須被查到。
- formatter 最多顯示 10 筆 MOPS 法說會。

## 驗收條件

- Focused future-watch tests 通過。
- py_compile 通過。
- `git diff --check` 通過。
- Read-only official `generate()` smoke：未來30日法說會不只 1 筆，且包含 06/22 光寶科。

## 失敗標本與驗收路由

- 失敗標本：Owner 貼出的第 4 則只剩 `06/05 2303 聯電` 一筆法說會。
- 驗收路由：MOPS helper query order regression -> focused tests -> official `generate()` read-only smoke。

## 禁止事項與阻塞條件

- 不得用 DB cache 解決本輪問題。
- 不得假造 MOPS 事件。
- 不得把 source-error 靜默顯示成無事件。
