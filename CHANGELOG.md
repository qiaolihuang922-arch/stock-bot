# CHANGELOG: report_conflict_future_watch_format_20260608

## 修改內容與修改檔案
- `core/generator.py`
  - 版本升至 `v20.4.50`。
- `presentation/report.py`
  - Summary 將 `今日已買` 改為 `今日買入紀錄`。
  - 未持倉 blocker 主因改為優先對齊卡片 title。
  - 新增市場弱 / 量能不足的專屬解鎖文案。
  - 策略樣本 / 資料不足改為補充 gap，不搶交易主因。
- `core/future_watch.py`
  - 法說會主行移除 EPS / 營收YoY。
  - 新增每檔法說會底下的 `財報：EPS...｜營收YoY...` 子行。
- `tests/test_generator_report.py`
  - 同步版本字串。
  - 更新法說會格式與 Summary 文案回歸。

## 契約影響
- message list 順序不變。
- 使用者可見版本為 `v20.4.50`。
- 法說會財報資訊仍只跟著被 MOPS/target 過濾後的法說會 item 出現。
- 無 DB write、無 live Telegram delivery。

## 自檢命令與結果
- `python -m py_compile core/generator.py core/future_watch.py presentation/report.py tests/test_generator_report.py tests/test_notifier.py` -> passed。
- `python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_afterhours_cards_are_denoised_without_first_read_preface tests/test_generator_report.py::GeneratorReportTest::test_v20_4_47_future_30d_watch_optional_fourth_message_official_list tests/test_notifier.py -q` -> 5 passed。
- broader focused set including complete message order -> 6 passed。
- `generate_report(dry_run=True)` -> 4 messages, header `v20.4.50`, no live Telegram delivery。

## 覆蓋層級
- formatter: Summary / unheld card / future watch format。
- official generator: `generate_report(dry_run=True)` replay。
- notifier: `tests/test_notifier.py`。

## 殘留風險
- Full historical report suite remains a separate baseline cleanup item。
- CAO/Codex TUI automation gap unrelated to this product patch。
