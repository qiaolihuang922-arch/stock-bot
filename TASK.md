# TASK: cao_wsl_deployment_repair_20260608

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
