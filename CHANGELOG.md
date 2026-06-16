# CHANGELOG: rebound_retest_anchor_wording_v21_1_20260616

## 修改內容與檔案

- `presentation/report.py`
  - `_recent_repair_support_text` 改為 `_recent_rebound_close_text`。
  - 回測缺口 / 可買條件使用 `最近反彈收盤 N 附近`。
  - 不再把 `daily_price` 最近收盤稱為 `修復支撐`。
- `tests/test_generator_report.py`
  - 更新 multi-day rebound official formatter 期待。
  - 補 `assertNotIn("最近修復支撐", card)` 防回退。

## 契約影響

- 使用者可見文案更精準：
  - 舊: `最近修復支撐`
  - 新: `最近反彈收盤`
- 策略判斷不變：
  - `等回測` 仍由 DB-backed `daily_price` 最近收盤序列觸發。
  - 沒有 DB-backed cross-day source 時 fail closed，不升格成 multi-day rebound。
- DB:
  - 無 schema change。
  - 無 write/backfill/prune。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- Official unheld card covered。
- Summary 未改。
- live Telegram 未執行。

## 未影響模組

- 持倉風控未改。
- 交易狀態機判斷未改。
- 距突破計算未改。
- `services/cross_day_context.py` 讀取 DB daily_price 的邏輯未改。

## 自檢命令與結果

- Targeted helper/source gate:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_cross_day_context.py -q --tb=short -k "multi_day_rebound or retest_anchor or unheld_message_contract or recent_daily_price_points"`
  - result: `1 passed, 211 deselected, 1 warning`
- Targeted official formatter:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py::GeneratorReportTest::test_v21_1_strong_rebound_uses_multi_window_retest_context tests\test_generator_report.py::GeneratorReportTest::test_v21_1_multi_day_weak_rebound_repairs_from_rejected_to_retest_wait tests\test_generator_report.py::GeneratorReportTest::test_v21_1_retest_anchor_says_breakout_zone_when_price_is_below_zone -q --tb=short`
  - result: `3 passed, 5 warnings`
- Official dry-run:
  - 群創:
    - `缺口：等待回測最近反彈收盤 53.3 附近不破`
    - `可買：回測最近反彈收盤 53.3 附近不破 + 非追高 + 量能有效`
  - 旺宏:
    - `缺口：等待回測最近反彈收盤 166.5 附近不破`

## 覆蓋層級

- formatter: covered。
- official generator dry-run: covered。
- production DB write: not applicable。
- live Telegram: not run by design。

## 殘留風險

- `.pytest_cache` 仍有 WinError 5 warning，不影響測試結果。
- 若未來要把錨點稱為支撐，需新增真正支撐計算來源與測試，不可只改文字。
