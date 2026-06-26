# CHANGELOG: future_watch_institutional_trading_20260626

## 修改內容與修改檔案

- `core/future_watch.py`
  - 新增 TWSE T86 與 TPEx 三大法人來源常數。
  - `build_live_stock_fundamentals_source()` 併入 institutional endpoints。
  - TWSE T86 `fields + data` 陣列轉 dict 後解析。
  - 官方股數轉為 `張`。
  - 查詢日期使用 `now - 1 day`。
  - `format_future_watch_message()` 在 `關注標的財報` 每檔加入 `昨日三大法人買賣超`。
- `presentation/report.py`
  - 移除股票卡片層三大法人輸出，避免每張卡顯示 `資料不足`。
- `tests/test_generator_report.py`
  - 更新卡片 regression：卡片不再顯示三大法人行。
  - 新增 future-watch 財報區三大法人顯示 regression。
  - 新增 TWSE T86 live-source shape merge regression。

## 契約影響

- 三大法人買賣超從股票卡移到 future-watch `關注標的財報`。
- live source 能讀官方 TWSE/TPEX 來源；無資料時只在 future-watch 財報區 fail closed。
- DB 寫入、策略判斷、持倉/未持倉分組不變。

## 版本同步

- 使用者可見版本仍為 `v21.1`。
- 未修改 `generator.VERSION`。

## 直接消費者同步

- Telegram future-watch message 同步。
- 股票卡 formatter 同步移除前一輪硬輸出。

## 未影響模組

- 無 production DB schema/write/backfill/delete。
- 無 live Telegram。
- 無 summary decision contract 變更。

## 自檢命令與結果

- `python -m pytest tests/test_generator_report.py -k "institutional_trading or future_watch_revenue or stock_fundamentals_loads_twse_revenue_openapi or future_watch_default_sources"`
  - Result: `8 passed, 228 deselected`
- Read-only live probe:
  - `STATUS=available`
  - `ITEMS=2581`
  - `INSTITUTIONAL_ITEMS=1326`
  - `HAS_2421={'foreign': -632.8, 'investment_trust': -3.0, 'dealer': -41.449, 'total': -677.249, 'unit': '張', 'market': '上市', 'trade_date': '20260625'}`
  - `ERRORS=[]`

## 覆蓋層級

- source: `build_live_stock_fundamentals_source`
- payload: `collect_target_fundamentals`
- formatter: `format_future_watch_message`
- final cards: `formatTelegramPositionCard`, `formatTelegramUnheldCard` negative check
- production source: read-only official endpoint probe only; no DB write/live delivery

## 殘留風險

- TPEx endpoint shape may vary; parser is flexible but only TWSE live probe was confirmed in this turn.
- CAO runner still lacks `tmux`; local equivalent flow used.
