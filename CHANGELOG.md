# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：risk_patch。
- 風險：修正 WAIT breakout RR 缺口判斷，影響使用者可見等待原因。
- 邊界：未改策略 decision、decision_type 產生邏輯、DB write path、live Telegram delivery。

## 修改內容

- `core/condition_engine.py`
  - 修正尾端 `rr >= 1.0` 通用兜底，避免 `decision_type="wait_breakout_low_rr"` 在 `rr=1.2` 時被覆蓋成 RR 通過。
- `tests/test_condition_engine.py`
  - 新增可重跑 probe，驗證 `wait_breakout_low_rr + WAIT + rr=1.2` 會保留 RR 缺口。
  - 同步驗證直接原因標籤包含 `RR不足`。

## 修改檔案

- `core/condition_engine.py`
- `tests/test_condition_engine.py`

## 契約影響

- `condition_engine(result)["rr"]`：當 `decision_type="wait_breakout_low_rr"` 且 `rr < 1.5` 時維持 `False`。
- `summarize_conditions(..., "WAIT")`：上述情境回傳非空缺口，且包含 `rr`。
- 既有 `rr -> RR不足` 標籤映射未改。
- 函式回傳結構、payload shape、message list 順序、DB contract、CLI 輸出未變更。

## 直接消費者同步

- `core.signal_snapshot._reason_labels` 透過既有 `condition_engine -> summarize_conditions` 路徑取得 `RR不足`。
- `core.generator` 仍使用既有 condition / summarize / label 路徑；本輪未改報文格式或排序。

## 未影響模組

- `services/analysis.py` strategy decision / decision_type 產生邏輯。
- DB schema、RLS、grant、policy、role、index / constraint。
- DB write path、backfill、live Telegram delivery。
- 報文版面、版本字串、分組排序。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/condition_engine.py core/signal_snapshot.py tests/test_condition_engine.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_condition_engine.py`：1 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_analysis_engine.py`：33 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_condition_engine.py tests/test_analysis_engine.py`：34 passed。
- `git diff --check`：passed。

## 殘留風險

- 本輪只覆蓋 `wait_breakout_low_rr + rr=1.2` 的 condition gap 與直接原因標籤。
- 未審計所有 WAIT 類型 RR 門檻，避免擴大任務。

## 旁支待辦

- 全部 WAIT 類型 RR 門檻審計另開任務。
- 報文整體版面與手機閱讀降噪另開任務。
- production ledger / Telegram delivery consumer 檢查不在本輪範圍。
