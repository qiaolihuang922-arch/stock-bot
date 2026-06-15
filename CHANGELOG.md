# CHANGELOG: entry_quality_priority_v21_1_20260616

## 修改內容與檔案

- `services/analysis.py`
  - `entry_setup_state` 先判斷急彈/過熱/RR/量能/距離，再把品質 C/D 降為 `WAIT_CONFIRM`。
  - `setup_blocker_state("WAIT_SETUP")` 改為 `setup_missing`，不再叫 `quality_low`。
- `core/trade_state_machine.py`
  - 移除 `ENTRY_QUALITY_LOW` guard。
  - fallback transition 先看急彈、結構、過熱、主量能、RR、距離，再看市場/個股弱勢。
  - `visible_state_line` 只在 `WATCH/WAIT_SETUP` 才把 `STOCK_WEAK` 顯示為主因。
- `core/generator.py`
  - `entry_blockers` 將距離 blocker 排在 `market_grade D/E` 前。
  - `rejected_primary_reason` 將 RR、結構、距離排在市場/個股弱勢前。
  - `unheld_funnel_state` 不再因品質低直接 fallback 到等型態；`隔日確認` 只在真正沒有 setup 時降級。
  - `tomorrow_watch_state` 對 `NO_SETUP + 距突破 > 12%` 回傳 `等接近`。
  - 將 `result_setup_type` 提供給 presentation deps。
- `presentation/report.py`
  - 卡片顯示層若已是 `等型態` 但距突破超過 12%，改顯示 `等接近｜遠離觸發`。
- `tests/test_trade_state_machine.py`, `tests/test_generator_report.py`
  - 更新回歸標本，防止 `個股弱勢/D` 再搶過距離/結構主因。

## 契約影響

- 函式回傳:
  - `entry_setup_state` 對品質 C/D 不再直接輸出 `WAIT_SETUP`。
  - `unheld_funnel_state` / `tomorrow_watch_state` 更偏向具體 blocker。
- message list:
  - 未持倉標題主因更具體，不再讓 D 成為預設主因。
  - `距突破` 仍獨立顯示。
- DB 寫入:
  - 無 DB write。
  - 無 schema change。
- CLI/runner:
  - 無 live Telegram delivery。
  - runner artifact 路徑不變。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `generate_report(dry_run=True)` 已驗 official message list。
- `formatTelegramMessages` 相關 generator tests 已驗。

## 未影響模組

- 持倉停損/減碼/續抱邏輯未改。
- 法說會、財報、歷史類比未改。
- DB 回寫/backfill 流程未改。

## 自檢命令與結果

- `.\.venv\Scripts\python.exe -m pytest tests\test_analysis_engine.py tests\test_trade_state_machine.py tests\test_unheld_gap_format.py tests\test_generator_report.py -q --tb=short`
  - `257 passed, 44 subtests passed`
- `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `479 passed, 8 skipped, 108 subtests passed`
- dry-run:
  - `generate_report(dry_run=True)`
  - 緯創/仁寶/技嘉顯示 `等接近｜遠離觸發`
  - 旺宏保留 `等回測｜急彈待回測`
  - 華邦電保留 `等回測｜漲停不追`

## 覆蓋層級

- helper: covered。
- state machine: covered。
- formatter: covered。
- official generator: covered。
- runner production artifact: 未 live delivery；需等下次 scheduled bot artifact 觀察。

## 殘留風險

- 若 production source 回傳 `strategy evidence` 缺失，卡片仍會 fail closed 顯示樣本/來源不足；這是資料契約，不是本輪策略顯示 bug。
