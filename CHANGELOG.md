# CHANGELOG: telegram_mobile_readability_consolidation_20260626

## 修改內容與修改檔案

- `core/future_watch.py`
  - MOPS source-error 不再顯示。
  - Future-watch 財報區改成每檔兩行。
  - 三大法人行加入偏買/偏賣/分歧判讀。
- `core/generator.py`
  - 今日買入說明縮短。
  - 盤後持倉風控 checklist 加入停損/減碼股數。
  - REDUCE_50 / REDUCE_25 缺 `decision.shares` 時以持股數推算建議賣股數。
- `presentation/report.py`
  - 盤後 summary 新增 `明日優先`，列出前三項持倉風控動作。
- `tests/test_generator_report.py`
  - 更新 future-watch compact regression。
  - 更新 MOPS source-error 隱藏 regression。
  - 新增/更新盤後 summary 股數 regression。

## 契約影響

- Message list 內容更短；沒有可見 future-watch 資訊時不產生第 4 則。
- Future-watch row format changed.
- Strategy / DB / source payload unchanged.

## 版本同步

- 使用者可見版本仍為 `v21.1`。
- 未修改 `generator.VERSION`。

## 直接消費者同步

- Telegram 持倉卡。
- Telegram 盤後 summary。
- Telegram 未來30日關注。

## 未影響模組

- 無 production DB schema/write/backfill/delete。
- 無 live Telegram。
- 無交易策略判斷變更。

## 自檢命令與結果

- `python -m py_compile core/future_watch.py core/generator.py presentation/report.py`
  - Result: passed
- `python -m pytest tests/test_generator_report.py -k "future_watch or institutional_trading or afterhours_brief or today_buy_holding_explains or afterhours_holding_action_contract"`
  - Result: `15 passed, 223 deselected`
- Read-only sample render:
  - 12 檔 future-watch 財報每檔兩行。

## 覆蓋層級

- formatter: `format_future_watch_message`
- official generator path: `formatTelegramMessages`
- card formatter: `formatTelegramPositionCard`
- source: 未改資料源；只做 read-only sample render

## 殘留風險

- Full `tests/test_generator_report.py` not rerun; known legacy wording failures remain cleanup.
- CAO runner still lacks `tmux`; local equivalent flow used.
