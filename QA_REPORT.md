# QA_REPORT:

## 測試範圍

- 任務：`import-boundary-gate-20260601`，process，QA L2。
- 驗證聚焦：import boundary gate、失敗訊息可定位、無新增檔案、無 runtime 行為變更、VERSION 不變。
- 未擴大到 full pytest、replay、backfill、production smoke、production DB write 或 live Telegram。

## 關聯風險掃描

- Gate 規則位於 `tests/test_generator_report.py`：
  - 掃描 `presentation/`、`services/`、`core/`、`main.py`、`app.py`。
  - `presentation` 禁止 import `services.signal_store`、`services.daily_snapshot_store.record_daily_snapshots`、`services.strategy_evidence`。
  - `services/`、`core/` 禁止 import `presentation`，但 allowlist `core/generator.py -> presentation.report` transitional bridge。
  - integration allowlist `services/notifier.py`，符合 TASK 的 runner edge。
- Runtime code 無變更：`core/generator.py`、`presentation/report.py`、`services/*`、`main.py`、`app.py` 未改。
- `core.generator.VERSION` 仍為 `v20.4.21`。
- 無新增業務模組、無新增架構文檔。

## 跨區塊語意一致性

- TASK 要求不新增 test file：符合，gate 加在既有 `tests/test_generator_report.py`。
- TASK 要求失敗輸出含 offending file/import/rule：符合，formatter 為三行格式。
- TASK 要求不升 VERSION：符合。
- TASK 要求無 DB write / live Telegram / runtime diff：符合。
- CHANGELOG 的修改檔案口徑已和主 repo 最終 staged diff 對齊，固定文件摘要會納入本輪 commit。

## 使用者誤讀風險

- 本輪無 Telegram / summary / dashboard 可見輸出變更；手機閱讀順序不變。
- 主要改善是後續拆分不靠對話記憶：違規 import 會在測試中直接指出 rule/file/import。

## 質疑與反證

- QA 額外反證：直接餵入 `from services.signal_store import record_daily_signals`、`from services.daily_snapshot_store import record_daily_snapshots`、`from services.strategy_evidence import record_strategy_evidence/get_supabase_client`、`from presentation import report`、`import presentation.report`，回傳 6 筆違規，且每筆都有 rule/file/import。
- Allowlist 不過寬：`core/generator.py -> presentation.report` 是唯一 core bridge；`services/fake_service.py` 與 `core/fake_strategy.py` 仍會被抓。
- 無 production side effect：未執行 live Telegram、DB write、backfill；測試只跑本地 unit test 與靜態 helper。

## 已跑命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile tests/test_generator_report.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：91 passed，177 warnings。
- `git diff --check`：passed。

## 未測項目

- 未跑 full pytest、replay、backfill、production read/write smoke；TASK L2/process 不要求。
- 未移除 `core/generator.py -> presentation.report` bridge；這是後續待辦。

## QA 結論

通過
