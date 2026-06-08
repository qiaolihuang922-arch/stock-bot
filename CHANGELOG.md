# CHANGELOG: trade_state_machine_v21_20260608

## 修改內容與修改檔案
- `core/trade_state_machine.py`
  - 新增 v21.0 read-only 狀態機。
  - 支援持倉與未持倉兩種 scope。
  - 輸出 `state/action/trigger/transition/reason/source/db_write/schema_change`。
  - 提供 read-only artifact builder。
- `core/generator.py`
  - 版本升至 `v21.0`。
  - 在正式 render 前套用 `apply_trade_state_machine`。
  - 新增 `trade_state_machine_line` / `trade_state_machine_artifact` helper。
- `presentation/report.py`
  - 持倉與未持倉卡片新增 `交易狀態` 可見行。
- `tests/test_trade_state_machine.py`
  - 新增未持倉等量能、持倉停損、artifact、official card replay 測試。
- `tests/test_generator_report.py`, `tests/test_market_theme_evidence.py`
  - 版本同步到 `v21.0`。

## 契約影響
- 使用者可見報文新增每檔 `交易狀態` 行。
- message list 順序不變。
- 不新增 DB 欄位，不寫 DB。
- 不執行 live Telegram delivery。

## 直接消費者同步
- official `generate_report(dry_run=True)` 已重放。
- GitHub runner 走同一 generator / presentation 路徑，push 後會生成 v21.0 報文。

## 未影響模組
- Supabase schema / RLS / grant / policy 未改。
- DB write path 未改。
- Telegram live sender 未改且未執行。
- historical analogy / fundamentals 邏輯未改。

## 自檢命令與結果
- `python -m py_compile core/trade_state_machine.py core/generator.py presentation/report.py tests/test_trade_state_machine.py` -> passed。
- `python -m pytest tests/test_trade_state_machine.py -q` -> 4 passed。
- focused generator + state-machine replay -> 7 passed。
- `python -m pytest tests/test_market_theme_evidence.py -q` -> 38 passed, 13 subtests passed。
- `generate_report(dry_run=True)` -> v21.0 messages generated, no live Telegram delivery。
- Full `tests/test_generator_report.py tests/test_trade_state_machine.py` currently conditional: 160 passed / 39 failed, mostly legacy exact-message assertions and existing old funnel wording expectations after adding v21 state line.

## 覆蓋層級
- helper: state machine pure functions。
- formatter: card visible state line。
- official generator: dry-run replay。
- production source: read-only only through existing generator sources。

## 殘留風險
- v21.0 是 read-only derived state machine v1；尚未把 state snapshot 寫回 DB。
- Full generator regression 需要下一輪整理大量精準字串測試，或改成狀態機契約式驗收。
