# CHANGELOG: future_watch_fundamentals_spaced_layout_20260626

## 修改內容與修改檔案

- `core/future_watch.py`
  - 移除 compact fundamentals line。
  - `關注標的財報` 恢復代號、EPS、營收、法人分行顯示。
  - 檔與檔之間恢復空行。
- `tests/test_generator_report.py`
  - 更新 future-watch layout regression，防止回到擠壓單行格式。

## 契約影響

- Future-watch 財報區排版變回較鬆的分行版。
- 法人判讀、MOPS source-error 隱藏、資料來源不變。

## 版本同步

- 使用者可見版本仍為 `v21.1`。
- 未修改 `generator.VERSION`。

## 直接消費者同步

- Telegram future-watch message。

## 未影響模組

- 無 production DB schema/write/backfill/delete。
- 無 live Telegram。
- 無策略判斷變更。

## 自檢命令與結果

- `python -m pytest tests/test_generator_report.py -k "future_watch or institutional_trading"`
  - Result: `11 passed, 227 deselected`
- Read-only sample render:
  - 2356、2376、2421 財報區恢復分行與空行。

## 覆蓋層級

- formatter: `format_future_watch_message`
- source: 未變更

## 殘留風險

- Full `tests/test_generator_report.py` not rerun; known legacy wording failures remain cleanup.
