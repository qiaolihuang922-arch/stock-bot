# QA_REPORT:

## 測試範圍

- 任務：`pm-20260601-telegram-helper-split`，normal_patch，QA L2。
- 驗證聚焦：純 Telegram formatter 是否已從 `core/generator.py` 拆到 `presentation/report.py`、報文輸出契約不變、import boundary gate 仍有效、完整邏輯測試通過。
- 未做 production write、DB schema、backfill 或 live Telegram。

## 關聯風險掃描

- `presentation/report.py` 無任何 import；透過 deps 使用既有 helper，未直接依賴 DB writer / signal writer / strategy evidence writer。
- AST spot check 未發現 presentation 直接賦值 `result`、`results_map`、`holding_decision` roots。
- `core/generator.py` 仍保留 public wrapper，避免外部消費者因搬移破裂。
- `core/generator.py` 已移除搬到 presentation 的 brief evidence private helper，避免顯示 helper 雙宿主。
- `core.generator.VERSION` 仍為 `v20.4.21`。

## 跨區塊語意一致性

- Telegram 多訊息順序沿用既有契約：持倉、未持倉、brief evidence / summary 短訊，Details Backup 只在 `include_detail=True` 時追加。
- Summary、持倉卡、未持倉卡、brief data evidence 的 formatter 已搬移，但 strategy decision、RR、holding_status、DB read/write 未改。
- CHANGELOG、TASK 與實際 diff 對齊：本輪只改 `core/generator.py`、`presentation/report.py` 與固定 handoff 文件。

## 使用者誤讀風險

- 本輪不改 Telegram 文案，不新增 raw source/table dump，不新增推薦語。
- 拆分後 presentation 層仍是顯示層；策略/資料來源判斷仍在既有 core/service 流程，不因 formatter 搬移而升級或降級任何標的。

## 質疑與反證

- import boundary gate 已在 `tests/test_generator_report.py` 中通過，仍覆蓋 presentation 禁止 DB/signal/strategy writer import，以及 core/services 禁止新增 presentation import。
- 完整邏輯測試矩陣通過，覆蓋 report rendering、market/theme evidence、analysis engine、strategy evidence、position store、cross-day context、signal validator。
- 追加 dry-run replay / daily snapshot store tests 通過，降低 formatter 搬移對 runner/replay 旁路的風險。
- Refactor evidence table 已補在 `CHANGELOG.md`，列 path / claim / evidence / risk / action。
- Re-QA runner 追加手機順序 smoke 通過：持倉卡 -> 未持倉卡 -> brief evidence / summary -> Details Backup。

## 已跑命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py presentation/__init__.py tests/test_generator_report.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_position_store.py tests/test_cross_day_context.py tests/test_signal_validator.py`：187 passed，177 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_daily_snapshot_store.py tests/test_dry_run_replay.py`：12 passed，13 warnings。
- `git diff --check`：passed。
- AST spot check：presentation imports `[]`；direct assigned roots `[]`。
- `tools/cao_agent/run_qa_code.sh ...` Re-QA：通過；QA output `.cao_agent_context/outputs/20260601_172241_30673_stock_qa_code_readonly.answer.txt`。

## 未測項目

- 未跑 live Telegram。
- 未做 production DB read/write smoke。
- 未做 full pytest；本輪按 Owner 要求跑完整邏輯矩陣與兩個追加旁路測試。

## QA 結論

通過
