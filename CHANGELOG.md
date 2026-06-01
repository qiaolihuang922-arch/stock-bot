# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：process。
- 風險判斷：只新增可重跑 AST import boundary gate 與固定文件摘要；不改產品邏輯、Telegram 報文、DB write path、VERSION。

## 修改內容

- 在 `tests/test_generator_report.py` 新增 import boundary gate：
  - 掃描 `presentation/`、`services/`、`core/`、`main.py`、`app.py` relevant Python files。
  - 禁止 `presentation` import `services.signal_store` 或其 writer symbol。
  - 禁止 `presentation` import `services.daily_snapshot_store.record_daily_snapshots`。
  - 禁止 `presentation` import `services.strategy_evidence` / `record_strategy_evidence` / `get_supabase_client`。
  - 禁止 `services/` 與 `core/` import `presentation`。
  - allowlist 只保留 `core/generator.py -> presentation.report` transitional bridge。
- 新增 fake import fixture 測試，確認失敗輸出含：
  - `Import boundary violation: <rule>`
  - `file=<offending path>`
  - `import=<offending import>`
- 固定文件補高信號模組地圖摘要：
  - `CURRENT_STATE.md`
  - `DISPATCH.md`
  - `CLEANUP_PLAN.md`

## 修改檔案

- `tests/test_generator_report.py`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `CURRENT_STATE.md`
- `DISPATCH.md`
- `CLEANUP_PLAN.md`

## 最小改動策略

- 沿用既有 `tests/test_generator_report.py`，未新增 test file。
- 使用 AST 解析 import，不用全文 grep。
- 不改 `core/generator.py`、`presentation/report.py`、`services/*` runtime code。
- 不新增架構文檔、不做模組重構、不擴大輸出契約。

## 契約影響

- 函式回傳 / payload / message list / 報文排序：無變更。
- DB 寫入 / Supabase client / production write：無變更。
- CLI / Telegram / UI 使用者可見輸出：無變更。
- VERSION：不變，仍為 `v20.4.21`。
- 測試契約新增：import boundary 違規會以 rule/file/import 格式定位。

## 直接消費者同步

- QA：可用 fake import fixture 反證 gate 會 fail。
- Architect：可用測試結果與 git diff 收口。
- 後續開發者：在 `tests/test_generator_report.py` 看到禁止 import 與 allowlist。

## 未影響模組

- Telegram 報文內容、排序、標題、文案。
- strategy decision、RR、holding_status、買賣 / 加減碼 / 停損停利。
- DB schema、RLS、grant、policy、role、index / constraint。
- production write、backfill、live Telegram delivery。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile tests/test_generator_report.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：91 passed，177 warnings。
- `git diff --check`：passed。

## 殘留風險

- `core/generator.py -> presentation.report` 仍是 transitional bridge，本輪只 allowlist 與文件標示，未移除。
- Gate 是 import 邊界檢查，不等於完整架構清理；後續拆 helper 時仍需小步進行。

## 旁支待辦

- 另開任務移除或收斂 `core/generator.py -> presentation.report` transitional bridge。
- 不在本輪清理歷史亂檔、不重畫完整架構圖、不拆分所有 formatter/helper。
