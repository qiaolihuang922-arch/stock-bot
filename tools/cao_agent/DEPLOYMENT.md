# CAO Local Deployment

本文件說明新電腦如何重建 CAO agent runner；repo 保存手寫資產，外部 runtime 重新下載。

## Repo Assets

- `run_*.sh`：Architect-controlled runner。
- `env.sh`：repo-relative path 與環境變數。
- `bin/codex`、`sandbox/codex_no_network.sb`：Codex sandbox wrapper。
- `profiles/stock_*.md.template`：PM / Tech / QA / research / security profile 模板。
- `install_agent_profiles.sh`：安裝 profile。
- `bootstrap_local.sh`：檢查依賴、安裝 profile、建立 worktree。
- `ensure_cao_services.sh`：啟動 / 確認 CAO API 與 UI。

## External Dependencies

| 依賴 | 來源 / 安裝 |
| --- | --- |
| CAO CLI / server / MCP | `uv tool install "git+https://github.com/awslabs/cli-agent-orchestrator.git@main"` |
| `uv` | https://docs.astral.sh/uv/ |
| `tmux` | `brew install tmux` |
| Node.js / npm | https://nodejs.org/ 或 Homebrew |
| Codex app | Codex desktop app |
| CAO web UI | CAO upstream checkout；中文化目錄可用 `CAO_WEB_DIR` 指定 |

## Rebuild

```bash
git clone <stock-bot-main-url>
cd stock-bot-main
tools/cao_agent/bootstrap_local.sh
tools/cao_agent/ensure_cao_services.sh
```

確認：

- API: `http://127.0.0.1:9889/`
- UI: `http://127.0.0.1:5173/`

## Important Env Vars

- `STOCK_BOT_REPO`
- `STOCK_BOT_AGENT_CONTEXT`
- `STOCK_BOT_AGENT_WORKTREE`
- `CAO_AGENT_PROFILE_DIR`
- `CAO_BIN`
- `CAO_SERVER_BIN`
- `CAO_MCP_SERVER_BIN`
- `CAO_WEB_DIR`
- `CODEX_APP_BIN`

## Chinese UI Note

大型外部 CAO frontend 不放進本 repo。若中文化需要長期固定，應另開任務保存最小 patch 或 fork，並由 `CAO_WEB_DIR` 指向該 checkout。
