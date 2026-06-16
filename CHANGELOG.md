# CHANGELOG: approach_distance_gap_v21_1_20260616

## 修改內容與檔案

- `presentation/report.py`
  - `等接近` 卡片固定以 `遠離觸發` 作為 title label。
  - `等接近` gap 改為距離型說明：`距突破 X%，仍未進入觸發區`。
  - `等接近` unlock 改為 `接近觸發區，或另出現趨勢延續/回測承接setup後再評估`，經可讀化後顯示為買點型態。
  - 避免 fallback 到 blockers[0] 的 `需解除後重新評估`。
- `tests/test_generator_report.py`
  - 更新遠離觸發標本，要求距離型 gap。
- `tests/test_trade_state_machine.py`
  - 更新卡片整合標本，要求距離型 gap。

## 契約影響

- message list:
  - `等接近` card 的 title/gap/unlock 更具體。
  - `距突破` 獨立行保留。
- 函式回傳:
  - 無 public API shape 變更。
- DB:
  - 無 schema change。
  - 無 write/backfill。
- CLI/runner:
  - 無 live Telegram delivery。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `generate_report(dry_run=True)` 已驗 official message list。
- `formatTelegramMessages` 相關 generator/state tests 已驗。

## 未影響模組

- `services.analysis` 未改。
- `core.trade_state_machine` 未改。
- 持倉、法說會、財報、歷史類比未改。

## 自檢命令與結果

- `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_trade_state_machine.py -q --tb=short`
  - `212 passed, 44 subtests passed`
- `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `479 passed, 8 skipped, 108 subtests passed`
- dry-run:
  - `generate_report(dry_run=True)`
  - 等接近卡片顯示 `遠離觸發`
  - gap 顯示 `距突破 X%，仍未進入觸發區`

## 覆蓋層級

- formatter: covered。
- official generator: covered。
- runner production artifact: 未 live delivery；需等下次 scheduled bot artifact 觀察。

## 殘留風險

- 若 production artifact 仍顯示舊文字，優先查 runner 使用的 commit / deployment path，而不是再改 formatter。
