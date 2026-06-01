# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：使用者可見 Telegram 報文 assembly 拆分與版本升級，涉及 public formatter entry 與 message list regression；不碰策略 decision、RR、holding 狀態機或 DB write path。

## 修改內容

- 新增 `presentation/report.py`，承接 Telegram 三則報文 assembly。
- 新增 `presentation/__init__.py`。
- `core/generator.py`：
  - `VERSION` 升到 `v20.4.21`。
  - `formatTelegramMessages(...)` 保留原 public signature，改為相容 wrapper，將既有 helper 以 `deps` 注入 `presentation.report.render_telegram_messages(...)`。
  - maturity artifact worktree hash 排除標準輸出檔 `.qa_tmp/evidence_maturity_report.json`，避免 artifact 驗自己造成 hash drift。
- `tests/test_generator_report.py`：
  - 同步版本期望到 `v20.4.21`。
  - 新增 AST gate，確認 presentation module 不 import / call `record_daily_signals`、`record_strategy_evidence`、`get_supabase_client`、`record_daily_snapshots`，且不直接 mutate `results_map` / `result` / `holding_decision`。
- `tests/test_market_theme_evidence.py`：同步版本期望到 `v20.4.21`。
- `tools/cao_agent/check_evidence_handoff_gate.sh`：
  - 同步 generator version gate 到 `v20.4.21`。
  - 支援本輪 task_id `pm-20260601-presentation-report-split`。
  - 排除被驗證 artifact 自身，讓 maturity artifact gate 可重跑。

## 修改檔案

- `core/generator.py`
- `presentation/__init__.py`
- `presentation/report.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`
- `tools/cao_agent/check_evidence_handoff_gate.sh`

## Path / Claim / Evidence / Risk / Action

| path | claim | evidence | risk | action |
| --- | --- | --- | --- | --- |
| `presentation/report.py` | Telegram message assembly 已移出 `core/generator.py` | `render_telegram_messages(...)` 負責持倉 message、未持倉 message、第三則 evidence message 與 details backup assembly | 目前仍透過 deps 使用 generator 既有 formatter helper，尚未完成全量 presentation/helper 分層 | 本輪保留 helper 原址，只拆第一刀 assembly |
| `presentation/__init__.py` | 新 presentation package 可被 import | `from presentation import report` 測試可載入 | 若未納入 git 會導致 `ModuleNotFoundError` | 已納入可吸收 diff |
| `core/generator.py` | public compatibility 保留 | `formatTelegramMessages(...)` signature 未變，轉呼叫 `render_telegram_messages(...)` | deps 注入仍可能把既有 helper mutation 帶入；本輪未改 helper 行為 | 以 AST gate 防止新 module 自身 import/write/mutate，後續再拆 helper |
| `tests/test_generator_report.py` | 顯示層 side-effect gate 可重跑 | 新 AST test 檢查 forbidden imports/calls/mutation roots；formatter regression 89 tests passed | AST gate 不是完整 purity proof | 作為第一刀 gate，後續可補 runtime immutability fixture |
| `tests/test_market_theme_evidence.py` | market/theme 使用者可見報文版本不回退 | 36 tests passed | 未跑 full repo pytest | L2 範圍接受，full pytest 另列非本輪 |
| `tools/cao_agent/check_evidence_handoff_gate.sh` | maturity handoff gate 支援 v20.4.21 | maturity report + gate passed，maturity_score=100 | gate 排除 artifact 自身，若輸出到其他路徑仍需傳入正確 path | 保留標準 gate 命令 |

## 最小改動策略

- 只抽出 `formatTelegramMessages` 內的 Telegram message assembly，不搬移策略 helper、不重寫卡片 formatter、不改候選排序或 decision 判斷。
- `core/generator.py` 保留 import path 與函式 signature，避免既有 runner / CLI / tests 改呼叫方式。
- 新 presentation module 不直接 import `core.generator`，也不直接接觸 DB / evidence writer；資料準備與 side effect 仍由原 orchestration 層負責。
- 版本更新只同步與報文 header / artifact / gate 直接相關的測試與 gate。

## 契約影響

- Public import contract：`core.generator.formatTelegramMessages` 仍可 import / call，signature 未變。
- Telegram message contract：仍回傳三則主 messages；`include_detail=True` 時 Details Backup 仍追加在最後。
- Message order：維持 messages[0] 持倉、messages[1] 未持倉、messages[2] 簡報＋資料依據。
- 使用者可見版本：header / evidence title / artifact version 同步升為 `v20.4.21`。
- 無有效進場：既有 fixture regression 維持，不顯示可買推薦感的「最強標的」。
- DB / payload / write path：未新增 DB schema、未改 Supabase read/write、未改 `record_daily_signals`、未改 `record_strategy_evidence`。

## 直接消費者同步

- 既有 `formatTelegramMessages` caller 不需改 import path。
- `generate_report(...)` 仍透過 `core.generator.formatTelegramMessages(...)` 產生 Telegram messages。
- `tests/test_generator_report.py` 覆蓋直接 formatter call path、三則 messages 順序、無有效進場與 maturity gate。
- `tests/test_market_theme_evidence.py` 同步版本契約，覆蓋 market/theme evidence 使用者可見報文路徑。
- `tools/cao_agent/check_evidence_handoff_gate.sh` 同步 maturity artifact consumer。

## 未影響模組

- 未改策略 decision module / `strategy(...)`。
- 未改 RR 計算。
- 未改 `holding_status` 或持倉狀態機。
- 未改 `record_daily_signals`。
- 未改 `record_strategy_evidence`。
- 未改 DB client / Supabase service。
- 未改 live Telegram delivery runner。
- 未做 full generator 重構或報文文案重寫。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `bash -n tools/cao_agent/check_evidence_handoff_gate.sh`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：125 passed，177 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python scripts/generate_structural_evidence_artifact.py --maturity-report --case production_all_sources_available > .qa_tmp/evidence_maturity_report.json && tools/cao_agent/check_evidence_handoff_gate.sh . .qa_tmp/evidence_maturity_report.json`：passed，maturity_score=100。
- `git diff --check`：passed。

## 殘留風險

- 本輪是第一刀保守拆分，presentation module 仍透過 deps 使用 `core/generator.py` 既有 formatter helpers；尚未完成完整 presentation/helper 分層。
- AST gate 證明新 module 本身不 import / call DB 或 evidence write，也不直接 mutate 指定 input root；無法證明所有注入 helper 內部完全無 mutation，但本輪未改 helper 行為且回歸測試通過。
- 未跑 full pytest；依 TASK 範圍只跑 formatter / market theme / maturity gate 聚焦自檢。

## 旁支待辦

- 更完整的 strategy / presentation helper 分層另開任務。
- 所有 generator helper 的全量搬移另開任務。
- Telegram reply markup 附著最後一則 message 的 delivery consumer 風險另開任務評估。
- 報文文案重寫、策略指標、DB persistence、live delivery 流程改造均不在本輪。
