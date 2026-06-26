# CHANGELOG: future_watch_institutional_mobile_compact_20260626

## 修改內容與修改檔案

- `core/future_watch.py`
  - 三大法人買賣超行改為手機短格式。
  - 移除顯示日期。
  - 張數四捨五入為整數。
  - 單位 `張` 改為只顯示在行尾。
  - 標籤由 `外資/投信/自營/合計` 縮為 `外/投/自/合`。
- `tests/test_generator_report.py`
  - 更新 future-watch 顯示 regression。
  - 新增 mobile compact regression，防止日期、小數與重複單位回歸。

## 契約影響

- `關注標的財報` 中 institutional trading line 的顯示文字變短。
- 資料來源、payload、策略判斷、DB 寫入不變。

## 版本同步

- 使用者可見版本仍為 `v21.1`。
- 未修改 `generator.VERSION`。

## 直接消費者同步

- Telegram future-watch message 同步。

## 未影響模組

- 無 production DB schema/write/backfill/delete。
- 無 live Telegram。
- 無股票卡片顯示變更。

## 自檢命令與結果

- `python -m pytest tests/test_generator_report.py -k "institutional_trading or future_watch_revenue or stock_fundamentals_loads_twse_revenue_openapi or future_watch_default_sources"`
  - Result: `9 passed, 229 deselected`
- Read-only sample render:
  - 12 檔法人行已改成短格式。

## 覆蓋層級

- formatter: `format_future_watch_message`
- source: 未變更
- production source: 未寫入；只做 read-only sample render

## 殘留風險

- Full `tests/test_generator_report.py` not rerun; known legacy wording failures remain cleanup.
- CAO runner still lacks `tmux`; local equivalent flow used.
