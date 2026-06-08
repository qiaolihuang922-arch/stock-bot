# CHANGELOG:

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
