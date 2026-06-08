# CHANGELOG: telegram_mobile_first_preface_20260608

## 修改內容與修改檔案
- `presentation/report.py`
  - 新增 `_mobile_first_read_preface(...)`。
  - 在第 1 則持倉訊息、第一張持倉卡之前插入 `【先看結論】`。
- `core/generator.py`
  - 報文版本升至 `v20.4.48`。
- `tests/test_generator_report.py`
  - 新增手機首屏 preface 回歸。
  - 將本輪 touched order 測試改用 `generator.VERSION`，避免下次升版重複破壞。
- `tests/test_trend_continuation.py` / `tests/test_notifier.py`
  - 同步 `v20.4.48` 測試版本字串。

## 契約影響
- 函式回傳: `formatTelegramMessages(...)` message list 長度與順序不變。
- message list: `messages[0]` 內容增加手機首屏 preface；`messages[1]`、`messages[2]`、future watch 順序不變。
- DB 寫入: 無。
- CLI 輸出: dry-run 版本顯示 `v20.4.48`。

## 版本同步
- `core.generator.VERSION = "v20.4.48"`。

## 直接消費者同步
- Telegram 手機首屏先看到新倉/今日買入/持倉風控結論。
- `services.notifier.send_many` 仍依 message list 順序送出，reply markup 契約未改。

## 未影響模組
- 策略 scoring、RR、持倉狀態機、DB read/write、future watch source、live delivery。

## 自檢命令與結果
- `python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py tests/test_trend_continuation.py tests/test_notifier.py` -> passed。
- focused pytest:
  `tests/test_generator_report.py::GeneratorReportTest::test_first_holding_message_starts_with_mobile_decision_preface`
  `tests/test_generator_report.py::GeneratorReportTest::test_v20_4_12_complete_message_list_orders_holdings_unheld_summary_evidence_details`
  `tests/test_notifier.py`
  -> 5 passed。
- official dry-run `generate_report(dry_run=True)` -> 4 messages; message 1 starts with `【先看結論】`; no live Telegram delivery。
- broader `tests/test_generator_report.py tests/test_notifier.py` -> 160 passed / 34 failed; remaining failures are broader existing strategy/funnel expectation mismatches, not accepted as this task completion evidence.

## 覆蓋層級
- helper: `_mobile_first_read_preface` via message renderer test。
- formatter: `formatTelegramMessages` focused replay。
- official generator: `generate_report(dry_run=True)` artifact。
- runner artifact: local dry-run stdout。
- production source: read-only Supabase-backed dry-run only; no write, no live delivery。

## 殘留風險
- CAO TUI runner still has a separate automation gap; local dry-run and tests were used for this round.
- Full historical report suite is not clean and should be handled as a separate baseline cleanup/strategy task.

## 任務尺寸與風險

- 任務尺寸：process / runner。
- 風險：CAO runner 不能啟動時，後續 PM -> Tech -> QA 流程會被迫退化成手動等價流程。

## 修改內容

- `.gitattributes`
  - 固定 `tools/cao_agent/*.sh`、`tools/cao_agent/bin/*`、`tools/cao_agent/sandbox/*.sb` 使用 LF，避免 WSL 執行 CRLF shell scripts 失敗。
- `tools/cao_agent/ensure_cao_services.sh`
  - 新增 `NPM_BIN` override。
  - 移除 macOS-only `/usr/bin/arch -arm64 /usr/local/bin/npm`，改用跨平台 `npm`。
- `tools/cao_agent/bin/codex`
  - 若環境沒有 `sandbox-exec`，直接執行 `CODEX_APP_BIN`，支援 Linux / WSL。

## 修改檔案

- `.gitattributes`
- `tools/cao_agent/ensure_cao_services.sh`
- `tools/cao_agent/bin/codex`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`

## 契約影響

- CAO local deployment 可在 WSL Ubuntu 走 repo scripts。
- macOS sandbox 行為保留：有 `sandbox-exec` 時仍使用 sandbox profile。
- Linux / WSL fallback 不使用 macOS sandbox；安全邊界仍由 CAO profiles / runner role 規則約束。

## 自檢命令與結果

- WSL `bash tools/cao_agent/bootstrap_local.sh` -> git/tmux/npm/uv/Codex/CAO CLI/server/MCP/web UI 全部 `[ok]`。
- WSL `bash tools/cao_agent/ensure_cao_services.sh` -> `CAO API: http://127.0.0.1:9889/`，`CAO UI: http://127.0.0.1:5173/`。
- Windows `Invoke-WebRequest http://127.0.0.1:9889/docs` -> 200。
- Windows `Invoke-WebRequest http://127.0.0.1:5173/` -> 200。
- WSL `codex --version` -> `codex-cli 0.137.0-alpha.4`。

## 覆蓋層級

- deployment bootstrap：covered。
- CAO API/UI service check：covered。
- Codex wrapper executable path：covered。
- 未執行 live PM/Tech/QA 任務；本輪只驗 runner deployment readiness。

## 殘留風險

- WSL `CODEX_APP_BIN=/root/.local/bin/codex-real` 是本機配置，需要下輪 shell 帶入。
- 未驗證完整 `run_architect_task.sh auto` 工作流產生 PM/Tech/QA handoff。
