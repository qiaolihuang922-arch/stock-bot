# CHANGELOG: rebound_retest_source_gate_v21_1_20260616

## 修改內容與檔案

- `services/analysis.py`
  - `can_buy` 距離硬拒絕從 `>4%` 改為 `>5%`，對齊 v21.1 接近突破區。
- `core/generator.py`
  - source-only gate 若非結構硬失敗，不再落到 `淘汰` / `隔日確認`；改為 `等資料`。
- `presentation/report.py`
  - 新增最近修復支撐回測文字，支撐價只取 `cross_day_context.recent_daily_price_points` 的 DB-backed `daily_price`。
  - 多日反彈修復等待回測改為「回測最近修復支撐不破」，不再硬要求先站回前高/突破區。
  - 保留急彈追價分支的前高/突破區回測，避免把急彈直接放寬。
  - source/策略樣本缺失的 title 保留具體原因：`策略樣本來源異常`、`策略樣本證據不足`、`資料來源缺失`。
  - source/策略樣本不可用時，風險報酬不再顯示成可用買點證據。
  - 等資料卡片去除冗餘 trade-state、診斷原因與不可用數據行。
- `tests/test_analysis_engine.py`
  - 新增 `4.8%` 仍可通過距離門檻的 regression。
- `tests/test_generator_report.py`
  - 新增 near-breakout source-missing 不得淘汰 regression。
  - 更新多日修復回測 regression，驗證最近修復支撐文字。
  - 更新 source gate regression，驗證 fail-closed 但不展示可用 RR。

## 契約影響

- 報文:
  - 旺宏 / 群創這類多日修復不再被強制顯示成淘汰；若仍未可買，顯示為 `等回測｜反彈修復待回測`。
  - 聯電這類 source 缺失不再顯示為策略淘汰。
  - 等資料卡片更短，保留「進場 / 缺口 / 可買 / 觸發 / 價格」。
- 策略:
  - 沒有新增直接買入條件。
  - 連漲修復的下一步從「回前高」改為「回測最近修復支撐不破」。
  - 漲停 / 過熱 / 急彈追價仍不追。
- DB:
  - 無 schema change。
  - 無 write/backfill/prune。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `formatTelegramUnheldCard` covered。
- `formatTelegramMessages` summary/message-list covered。
- `generate_report(dry_run=True)` official generator path covered。
- Runner / live Telegram 未執行。

## 未影響模組

- 持倉風控核心未改。
- fundamentals / future watch / history analogy 未改。
- DB schema、RLS、grant、policy、role 未改。

## 自檢命令與結果

- Focused report / strategy:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_analysis_engine.py tests\test_trade_state_machine.py tests\test_unheld_gap_format.py tests\test_trend_continuation.py -q --tb=short`
  - `268 passed, 46 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `484 passed, 8 skipped, 110 subtests passed`
- Official dry-run:
  - `generate_report(dry_run=True)`
  - 未持倉可見結果包含:
    - `聯電 2303` -> `等資料｜策略樣本證據不足`
    - `群創 3481` -> `等回測｜反彈修復待回測`
    - `旺宏 2337` -> `等回測｜反彈修復待回測`

## 覆蓋層級

- helper: covered。
- formatter: covered。
- official message list: covered。
- official generator dry-run: covered。
- production runner artifact: not run。
- live Telegram: not run by design。

## 殘留風險

- production runner 若仍顯示舊文案，先查 runner commit/deployment path。
- `.pytest_cache` local cache write 仍有 WinError 5 warning，不影響測試結果。
