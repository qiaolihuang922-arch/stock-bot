# CHANGELOG: future_fundamentals_and_unheld_status_20260608

## 修改內容與修改檔案
- `core/generator.py`
  - 版本升至 `v20.4.51`。
  - QA visible refs 同步 `未持倉狀態`。
  - 全淘汰未持倉 funnel 顯示為 `未持倉 N 檔全部不可行動`。
- `presentation/report.py`
  - Summary 首行移除 0-count。
  - `未持倉漏斗（非執行）` 改為 `未持倉狀態`。
- `core/future_watch.py`
  - 新增 `collect_target_fundamentals(...)`。
  - `build_future_watch_payload(...)` 增加 `target_fundamentals`。
  - `format_future_watch_message(...)` 新增 `關注標的財報` 區塊。
  - 法說會區塊不再承載逐股基本面資料。
- `tests/test_generator_report.py`, `tests/test_market_theme_evidence.py`
  - 同步版本與未持倉狀態文案。
  - 補沒有法說會的關注股仍輸出財報的測試。

## 契約影響
- message list 順序不變。
- 使用者可見版本為 `v20.4.51`。
- Future watch payload 增加 `target_fundamentals`。
- 無 DB write、無 live Telegram delivery。

## 自檢命令與結果
- `python -m py_compile core/generator.py core/future_watch.py presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py` -> passed。
- `python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v20_4_47_future_30d_watch_optional_fourth_message_official_list tests/test_generator_report.py::GeneratorReportTest::test_afterhours_cards_are_denoised_without_first_read_preface tests/test_generator_report.py::GeneratorReportTest::test_v20_4_12_complete_message_list_orders_holdings_unheld_summary_evidence_details tests/test_notifier.py tests/test_market_theme_evidence.py -q` -> 44 passed。
- `generate_report(dry_run=True)` -> 4 messages, header `v20.4.51`, no live Telegram delivery。

## 覆蓋層級
- formatter: Summary / future watch。
- official generator: `generate_report(dry_run=True)` replay。
- market theme QA path: `tests/test_market_theme_evidence.py`。

## 殘留風險
- `營收YoY` 使用既有 fundamentals source 的月營收 YoY，不是新增年度營收資料源。
- Full historical report suite remains separate baseline cleanup。
