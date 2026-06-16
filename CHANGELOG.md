# CHANGELOG: near_breakout_tracking_contract_v21_1_20260616

## 修改內容與檔案

- `presentation/report.py`
  - `_breakout_distance_label` 改為 `<=5%` 顯示 `接近突破`。
- `core/generator.py`
  - `_unheld_structural_reject` 拆出硬失敗與軟阻擋。
  - 接近突破區內的非硬失敗觀察，不再被弱勢/品質軟阻擋直接打成淘汰。
  - 弱反彈仍排除在接近突破保護之外，避免把弱反彈誤放寬。
  - `unheld_funnel_assessment` 接住 `entry_quality=C`、接近突破、非硬失敗的 `隔日確認` 中間態。
  - `should_hide_rr` / `hidden_rr_reason` / final label 遠離判斷同步為 `>5%`。
- `tests/test_generator_report.py`
  - 新增聯電等價 replay：`4.25%` 接近突破 + C 品質觀察不得顯示 `淘汰` / `遠離突破` / `遠離觸發`。
  - 距突破 label 測試補 `4.25%`。

## 契約影響

- 報文:
  - `4.25%` 從 `遠離突破` 改為 `接近突破`。
  - 接近突破但品質 C 的觀察股，維持追蹤 / 隔日確認，不再掉入淘汰。
- 策略:
  - 沒有新增買入條件。
  - 弱反彈與突破失敗仍按既有硬風險處理。
- DB:
  - 無 schema change。
  - 無 write/backfill/prune。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `formatTelegramMessages` replay covered。
- `formatTelegramUnheldCard` / summary funnel covered。
- Runner / live Telegram 未執行。

## 未影響模組

- 持倉停損 / 減碼 / 停利未改。
- cross-day DB source gate 未改。
- market/theme evidence、future watch、fundamentals 未改。

## 自檢命令與結果

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short -k "near_breakout_soft_blocker or breakout_distance or rejected_weak_rr or far_from_trigger_tracks"`
  - `6 passed, 12 subtests passed`
- Broader report / strategy:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_analysis_engine.py tests\test_trend_continuation.py -q --tb=short`
  - `255 passed, 46 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `482 passed, 8 skipped, 110 subtests passed`

## 覆蓋層級

- helper label: covered。
- official card formatter: covered。
- official message list / summary: covered。
- weak rebound negative path: covered。
- live Telegram: not run by design。

## 殘留風險

- 若 production runner 仍顯示舊文案，優先查 runner commit / deployment path。
- `.pytest_cache` local cache write 仍有 WinError 5 warning，不影響測試結果。
