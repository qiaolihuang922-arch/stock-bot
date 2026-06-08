# CHANGELOG: historical_analogy_granularity_20260608

## 修改內容與修改檔案
- `core/generator.py`
  - 版本升至 `v20.4.52`。
- `core/future_watch.py`
  - TWSE 歷史類比新增型態標籤與壓力級別。
  - 評分加入量能 ratio 與 5 日位置。
  - 輸出拆成多行：相似點、不相似/限制、下一步觀察、資料。
  - generic historical source 也補顆粒度行。
- `tests/test_generator_report.py`
  - 更新 TWSE historical analogy regression。

## 契約影響
- message list 順序不變。
- 第 4 則 historical analogy section 可多行。
- 使用者可見版本為 `v20.4.52`。
- 無 DB write、無 live Telegram delivery。

## 自檢命令與結果
- `python -m py_compile core/future_watch.py core/generator.py tests/test_generator_report.py tests/test_notifier.py` -> passed。
- `python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v20_4_47_live_twse_source_builds_pressure_timeline tests/test_generator_report.py::GeneratorReportTest::test_v20_4_47_live_twse_source_uses_severe_taiwan_crash_template tests/test_generator_report.py::GeneratorReportTest::test_v20_4_47_future_30d_watch_optional_fourth_message_official_list tests/test_generator_report.py::GeneratorReportTest::test_v20_4_47_future_watch_global_event_ranges_sort_and_fail_closed tests/test_notifier.py -q` -> 7 passed。
- `python -m pytest tests/test_market_theme_evidence.py -q` -> 38 passed。
- `generate_report(dry_run=True)` -> 4 messages, header `v20.4.52`, no live Telegram delivery。

## 覆蓋層級
- helper: TWSE historical pressure line。
- formatter: future-watch message。
- official generator: `generate_report(dry_run=True)` replay。

## 殘留風險
- Historical sample library remains fixed-size 13-event internal library。
- Volume ratio depends on TWSE fields being available; missing volume is explicitly shown as a limitation。
