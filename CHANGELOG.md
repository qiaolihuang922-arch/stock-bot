# CHANGELOG: explicit_approach_zone_wording_v21_1_20260616

## 修改內容與檔案

- `presentation/report.py`
  - 新增 `_breakout_trigger_zone_text`，從 `retest_zone_low/high` 產生 `突破區 low~high`。
  - `等接近` 的 `進場 / 缺口 / 可買 / 明日觸發` 改用具體突破區。
  - 無價位時 fallback 成 `突破區/回測支撐`。
- `tests/test_generator_report.py`
  - 更新 far-from-trigger regression。
- `tests/test_trade_state_machine.py`
  - 更新等接近卡片契約。

## 契約影響

- 使用者可見文案變清楚。
- 策略決策不變：仍是不買，等接近或形成其他買點型態。
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

## 自檢命令與結果

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_trade_state_machine.py -q --tb=short -k "far_low_volume or breakout_distance_gate or unheld_far_from_trigger or 等接近"`
  - `3 passed, 212 deselected, 5 warnings`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `484 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Official dry-run:
  - 技嘉:
    - `進場：不買，等接近突破區 399~400.99｜原因：尚未接近突破區`
    - `缺口：距突破 15.23%，尚未接近突破區 399~400.99`

## 覆蓋層級

- formatter: covered。
- official generator dry-run: covered。
- live Telegram: not run by design。

## 殘留風險

- `.pytest_cache` 仍有 WinError 5 warning，不影響測試結果。
