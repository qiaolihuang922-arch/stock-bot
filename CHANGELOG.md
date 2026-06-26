# CHANGELOG: future_watch_institutional_trading_20260626

## 修改內容與修改檔案

- `core/future_watch.py`
  - 新增 TWSE T86 最近可用日期候選，避免只查單一天造成假日或未發布時誤判抓不到。
  - TWSE institutional merge 改為先寫入者保留，較新的可用日期不會被舊日期覆蓋。
  - 補 TPEx OpenAPI 英文欄位解析：`SecuritiesCompanyCode`、`Foreign ... Difference`、`SecuritiesInvestmentTrustCompanies-Difference`、`Dealers-Difference`、`TotalDifference`。
  - 補 TPEx 民國日期 `Date=1150625` 轉西元 `20260625`。
- `tests/test_generator_report.py`
  - 新增 TWSE 空日回退 regression。
  - 新增 TPEx 英文欄位 regression。

## 契約影響

- Future-watch `關注標的財報` 的三大法人資料來源更完整。
- 股票卡片仍不顯示三大法人行。
- DB 寫入、策略判斷、持倉/未持倉分組不變。

## 版本同步

- 使用者可見版本仍為 `v21.1`。
- 未修改 `generator.VERSION`。

## 直接消費者同步

- Telegram future-watch message 同步受益。
- 股票卡 formatter 不變。

## 未影響模組

- 無 production DB schema/write/backfill/delete。
- 無 live Telegram。
- 無 summary decision contract 變更。

## 自檢命令與結果

- `python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_live_stock_fundamentals_merges_twse_institutional_rows tests/test_generator_report.py::GeneratorReportTest::test_live_stock_fundamentals_merges_tpex_institutional_english_rows`
  - Result: `2 passed`
- `python -m pytest tests/test_generator_report.py -k "institutional_trading or future_watch_revenue or stock_fundamentals_loads_twse_revenue_openapi or future_watch_default_sources"`
  - Result: `8 passed, 229 deselected`
- Read-only live probe:
  - `status=available`
  - `errors=[]`
  - `institutional_count=2281`
  - 12 檔 Owner 樣本皆有 institutional trading。
  - TPEx 6488 有 institutional trading，`trade_date=20260625`。

## 覆蓋層級

- source: `build_live_stock_fundamentals_source`
- parser: TWSE fields/data、TPEx English OpenAPI rows
- payload: `collect_target_fundamentals`
- formatter: `format_future_watch_message`
- production source: read-only official endpoint probe only; no DB write/live delivery

## 殘留風險

- CAO runner still lacks `tmux`; local equivalent flow used.
- Full `tests/test_generator_report.py` not rerun; known legacy wording failures remain cleanup.
