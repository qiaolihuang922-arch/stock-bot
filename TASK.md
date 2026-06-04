# TASK: future_watch_query_interface_optimization_20260604

## 任務狀態

- task_id：`future_watch_query_interface_optimization_20260604`
- 任務類型：normal_patch
- 狀態：ready_for_qa
- 版本建議：維持 `v20.4.47`
- QA 分級：L2

## Owner 問題

Owner 認為未來 30 日關注功能需要優化即時接口查詢，增加查詢參數與查詢範圍控制，避免 MOPS / 全球來源拖慢整份推送。

## 使用者可見結果

- 第 4 則報文格式維持不變。
- MOPS 查詢改成有預算、有優先級、有市場別參數的 readonly 查詢。
- 已知上市 / 上櫃 / 興櫃 / 公開發行市場別時，先查對應 TYPEK，不再盲掃四種市場。
- 查詢結果仍 fail closed：不可解析不假造法說會，查到官方事件才顯示。

## 非目標

- 不改交易策略、RR、持倉風控、買賣決策。
- 不做 DB 方向，不新增 DB read/write/backfill。
- 不發 live Telegram。
- 不改全球事件完整官方 calendar parser。

## 影響模組與直接消費者

- `core/future_watch.py`
- `tests/test_generator_report.py`
- Telegram 第 4 則 `【未來30日關注】`

## 輸出契約

- `collect_mops_events()` 支援 `max_targets`、`max_queries`、`max_seconds`。
- MOPS POST 參數包含 `encodeURIComponent=1`、`step=1`、`firstin=1`、`off=1`、`TYPEK`、`year`、`month`、`co_id`。
- 回傳 diagnostics：`query_count`、`target_count`、`budget_exhausted`、`source_error_count`。
- 報文顯示不新增噪音欄位；diagnostics 供測試與後續調校。

## 驗收條件

- Focused future-watch tests 通過。
- py_compile 通過。
- `git diff --check` 通過。
- Read-only live smoke：光寶科 2301 仍列 MOPS 06/05 / 06/22 法說會，且已知上市市場時 MOPS query count 降到 2。

## 失敗標本與驗收路由

- 失敗標本：Owner 對「接口會很久」的擔心，以及既有 MOPS `股票 × 月份 × TYPEK` 全掃路徑。
- 驗收路由：future_watch helper diagnostics -> focused tests -> read-only live smoke。

## 禁止事項與阻塞條件

- 不得用 DB cache 解決本輪問題。
- 不得假造 MOPS 事件。
- 不得把 source-error 靜默顯示成無事件。
