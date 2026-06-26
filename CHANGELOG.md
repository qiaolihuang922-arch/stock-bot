# CHANGELOG: future_watch_remove_history_events_20260626

## 修改內容與修改檔案

- `core/future_watch.py`
  - `default_future_watch_sources()` 不再建立 `historical_source` / `global_event_source`。
  - `build_future_watch_payload()` 不再建立 `historical_analogy` / `global_events`。
  - `format_future_watch_message()` 不再輸出「歷史類比」與「未來30日台股影響事件」。
- `tests/test_generator_report.py`
  - 更新 future-watch 報文測試，反證移除區塊不再顯示。
  - 新增 default source 反證：historical/global live builders 不得被呼叫。

## 契約影響

- 使用者可見報文移除兩個 future-watch 區塊：`歷史類比`、`未來30日台股影響事件`。
- 保留 `未來30日法說會` 與 `關注標的財報`。
- DB 寫入、策略判斷、持倉/未持倉分組、Telegram summary 不變。

## 版本同步

- 使用者可見版本仍為 `v21.1`。
- 本輪為 future-watch 噪音移除，不改策略/DB contract；已核對 header 仍由 `generator.VERSION` 控制。

## 自檢命令與結果

- `python -m pytest tests/test_generator_report.py -k "future_watch" -q`
  - Result: `8 passed, 224 deselected`
- `python -m pytest tests/test_generator_report.py -k "future_watch or low_repair or failed_breakout or rr_blocker or actionability or reclaim or chase_risk or breakout_with_low_rr" -q`
  - Result: `20 passed, 212 deselected`
- Official dry-run smoke:
  - `MESSAGE_COUNT=4`
  - `HAS_HISTORY=False`
  - `HAS_TW_EVENTS=False`
  - `HAS_FUTURE_WATCH=True`
  - `HAS_MOPS=True`
  - `HAS_FUND=True`

## 覆蓋層級

- helper/source: `default_future_watch_sources`
- payload: `build_future_watch_payload`
- formatter: `format_future_watch_message`
- official generator path: `generate_report(dry_run=True)`
- production source: no live write, no live Telegram

## 殘留風險

- Standalone historical/global event helper functions remain in code because unrelated tests still cover them; they are no longer consumed by default future-watch report path.
- Full suite not run.
