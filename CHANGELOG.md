# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：拆純 Telegram 顯示 helper，碰多輸出區塊 formatter，但不改 strategy decision、RR、holding_status、DB write path、VERSION 或 live Telegram。

## 修改內容

- `presentation/report.py` 承接純 Telegram 顯示 helper：
  - `formatTelegramSummary`
  - `formatTelegramPositionCard`
  - `formatTelegramUnheldCard`
  - `format_brief_data_evidence_message`
  - brief evidence 的人話資料依據 helper
- `core/generator.py` 保留既有 public wrapper 與 orchestration，只透過 `_telegram_presentation_deps()` 把既有計算/helper 注入 presentation。
- `formatTelegramMessages()` 改用同一份 presentation deps，避免 message assembly 與單卡 formatter 使用兩套依賴字典。
- 沒有新增業務模組或架構文件；沿用既有 `presentation/report.py`。

## 修改檔案

產品 / 程式 diff：

- `core/generator.py`
- `presentation/report.py`
- `CHANGELOG.md`

Architect 收口 handoff（主 repo final diff 會一併提交；QA worktree 若只同步 handoff 摘要，可能不列入產品 diff）：

- `TASK.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`

## Refactor Evidence Table

| path | claim | evidence | risk | action |
| --- | --- | --- | --- | --- |
| `presentation/report.py` | 承接純 Telegram formatter 與 brief evidence 顯示 helper | 定義 `formatTelegramSummary`、`formatTelegramPositionCard`、`formatTelegramUnheldCard`、`format_brief_data_evidence_message`；AST imports 為 `[]` | presentation 可能誤帶 DB/strategy 依賴 | 只透過 deps 注入既有 helper，保留 import boundary gate |
| `core/generator.py` | 只保留 public wrapper、orchestration、transitional deps bridge | 四個 public formatter wrapper 委派到 `presentation.report`；原 brief private helper 已移除 | wrapper deps 過寬可能讓下一刀拆分不清 | 後續小步收斂 deps，禁止把 strategy/DB 移入 presentation |
| `tests/test_generator_report.py` | 既有 import boundary gate 繼續保護分層 | 完整邏輯矩陣含此檔，91 report tests 在 187 passed 中通過 | gate 不等於全量架構完成 | 每次拆分都跑此檔與完整邏輯矩陣 |
| 固定 handoff Markdown | 記錄本輪範圍、測試、殘留風險 | 主 repo final diff 包含 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`DISPATCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`；QA worktree 產品 diff 至少包含 `CHANGELOG.md` | 文件過量或與產品 diff 口徑混淆 | 分開列產品 diff 與 Architect handoff，final 前以主 repo `git diff --name-only` 對齊 |

## 契約影響

- 函式回傳 / payload / message list / 報文排序：無預期變更。
- Telegram 可見文案：無預期變更，既有測試覆蓋 summary、持倉卡、未持倉卡、brief evidence。
- DB 寫入 / Supabase client / production write：無變更。
- VERSION：不變，仍為 `v20.4.21`。
- 架構邊界：presentation 沒有 import；formatter 透過 deps 使用既有計算，不直接依賴 DB writer / strategy writer。

## 直接消費者同步

- `core/generator.py` 的既有 public formatter wrapper 保留，外部呼叫不需要改。
- `render_telegram_messages()` 仍由 presentation 組裝 Telegram 多訊息。
- import boundary gate 繼續 allowlist `core/generator.py -> presentation.report` 作 transitional bridge。

## 未影響模組

- strategy decision、RR、holding_status、買賣 / 加減碼 / 停損停利。
- DB schema、RLS、grant、policy、role、index / constraint。
- production write、backfill、live Telegram delivery。
- Telegram reply markup 與 notifier delivery consumer。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py presentation/__init__.py tests/test_generator_report.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_analysis_engine.py tests/test_strategy_evidence.py tests/test_position_store.py tests/test_cross_day_context.py tests/test_signal_validator.py`：187 passed，177 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_daily_snapshot_store.py tests/test_dry_run_replay.py`：12 passed，13 warnings。
- `git diff --check`：passed。
- AST spot check：`presentation/report.py` imports `[]`，direct assigned roots `result/results_map/holding_decision` 為 `[]`。

## 殘留風險

- `core/generator.py` 仍保留大量策略與資料 helper；本輪只移走優先 Telegram formatter。
- `_telegram_presentation_deps()` 是 transitional bridge，後續可繼續小步把純顯示依賴搬進 presentation，但不可把策略/DB 反向帶入 presentation。

## 旁支待辦

- 另開任務繼續拆 remaining pure display helpers。
- 另開任務評估 Telegram reply markup 目前附在最後一則 message 的 delivery consumer 風險。
