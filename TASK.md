# TASK: telegram_mobile_first_preface_20260608

## 任務狀態
- task_id: `telegram_mobile_first_preface_20260608`
- 任務類型: `normal_patch`
- 狀態: `done`
- 版本建議: `v20.4.48`
- QA 分級: `L2`

## Owner 問題
Owner 要「開始製作優化報文」。目前 official dry-run 會先推很長的持倉/未持倉卡片，完整決策簡報在第 3 則；手機閱讀時容易先看到大量細節，延後才知道「今天到底能不能買、持倉先處理什麼」。

## 使用者可見結果
- 第 1 則 `【持倉標的】` 開頭新增 `【先看結論】`。
- 首屏先顯示：新倉是否有效、今日買入是否已轉風控、持倉處理優先級、未持倉不是買入清單、完整簡報在第 3 則。
- 原 message order 保持：持倉、未持倉、簡報、未來30日關注。

## 非目標
- 不改策略、RR、持倉決策、DB read/write、future watch source。
- 不 live Telegram delivery。
- 不重排 Telegram message list，避免破壞 notifier reply markup 附在最後訊息的既有契約。

## 影響模組與直接消費者
- `presentation/report.py`: Telegram message renderer。
- `core/generator.py`: 使用者可見版本字串。
- `tests/test_generator_report.py`: 手機首屏與 message order 回歸。
- 直接消費者: Owner 手機 Telegram、GitHub runner dry-run/bot output、`services.notifier.send_many`。

## 輸出契約
- `messages[0]` 仍為持倉訊息，且包含 `【持倉標的】`。
- `messages[0]` 在第一張持倉卡前包含 `【先看結論】` preface。
- `messages[1]` 仍為未持倉訊息。
- `messages[2]` 仍為 `🧾 v20.4.48 簡報`。
- `messages[3]` 若有 future watch，仍為 `【未來30日關注】`。

## 版本契約
使用者可見報文版本升為 `v20.4.48`。

## 驗收條件
- focused pytest 覆蓋首屏 preface、既有 message order、notifier reply markup。
- `py_compile` 通過。
- official `generate_report(dry_run=True)` 產生 4 則報文，第一則首屏包含 `【先看結論】` 與 `新倉：無有效進場`。

## 範例或 Fixture
Official dry-run 2026-06-08:
- `MESSAGES 4`
- message 1 starts with `【06/08 盤後｜v20.4.48】` / `【持倉標的】` / `【先看結論】`
- `今日買入：5 檔已全部轉入風控`

## 失敗標本與驗收路由
- 失敗標本: 2026-06-08 dry-run 首屏先顯示長持倉卡，決策簡報在第 3 則才出現。
- 驗收路由: official generator `generate_report(dry_run=True)` + message list artifact；不得只驗 helper。

## 明確禁止事項
- 禁止 live Telegram delivery。
- 禁止 DB schema/RLS/grant/policy/role/index/constraint 修改。
- 禁止把未持倉淘汰/僅追蹤寫成推薦。

## 阻塞條件
- official dry-run 無法產生最終 message list。
- 首屏 preface 與第 3 則簡報語意衝突。

## 本輪停止條件
- focused tests + dry-run artifact 證明第 1 則首屏可先讀結論，且第 3 則完整簡報保留。

## 任務狀態

- task_id：`cao_wsl_deployment_repair_20260608`
- 任務類型：process / runner
- 狀態：done
- 版本建議：不升 Telegram 報文版本
- QA 分級：L1

## Owner 問題

Owner 指出我前一輪沒有先照部署文檔走，要求補齊部署流程，讓本地能正常跑 CAO agent runner。

## 使用者可見結果

- WSL Ubuntu 內 CAO API / UI 可啟動。
- `tools/cao_agent/bootstrap_local.sh` 在 WSL 內全綠。
- `tools/cao_agent/ensure_cao_services.sh` 在 WSL 內可直接啟動 / 確認 API 與 UI。

## 非目標

- 不發 live Telegram。
- 不改報文策略 / RR / DB schema / production write。
- 不重跑產品修復。

## 影響模組與直接消費者

- `.gitattributes`
- `tools/cao_agent/ensure_cao_services.sh`
- `tools/cao_agent/bin/codex`
- `DISPATCH.md`
- `CURRENT_STATE.md`
- 直接消費者：Windows + WSL 本地 CAO runner 部署流程。

## 輸出契約

- CAO shell scripts 在 WSL checkout 中使用 LF。
- CAO web 啟動不得依賴 macOS-only `arch -arm64`。
- Linux / WSL 無 `sandbox-exec` 時，Codex wrapper 應直接執行 `CODEX_APP_BIN`。

## 驗收條件

- WSL bootstrap 全部 `[ok]`。
- WSL `ensure_cao_services.sh` 輸出 CAO API/UI URL。
- Windows 端可 HTTP 連到 `127.0.0.1:9889/docs` 與 `127.0.0.1:5173/`。
- `codex --version` 透過 WSL wrapper 可執行。

## 失敗標本與驗收路由

- 失敗標本：
  - Windows 原生 `cao` 因 `ModuleNotFoundError: No module named 'fcntl'` 無法跑。
  - WSL 直接跑 CRLF `.sh` 會出現 `set: pipefail\r: invalid option name`。
  - UI 腳本在 Linux 會因 `/usr/bin/arch -arm64 npm` 失敗。
  - WindowsApps 內 `codex` Linux ELF 在原位置無執行權限。
- 驗收路由：WSL bootstrap -> profile/worktree -> ensure services -> Windows HTTP probe -> Codex wrapper version probe。

## 禁止事項與阻塞條件

- 不得 live Telegram delivery。
- 不得把 CAO service 起來等同於產品報文已發送。
