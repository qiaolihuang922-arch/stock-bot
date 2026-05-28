# CAO Local Deployment

這份文件記錄新電腦重新部署 CAO agent runner 時，哪些東西要下載，哪些手寫資產已經放入 repo。

## Repo 內已保存

- `tools/cao_agent/run_*.sh`：Architect-controlled runner。
- `tools/cao_agent/env.sh`：repo-relative path 與環境變數。
- `tools/cao_agent/bin/codex`：Codex sandbox wrapper。
- `tools/cao_agent/sandbox/codex_no_network.sb`：sandbox 模板。
- `tools/cao_agent/profiles/stock_*.md.template`：PM / Tech / QA / online research agent profile 模板。
- `tools/cao_agent/install_agent_profiles.sh`：把 profile 模板渲染到本機 CAO profile 目錄。
- `tools/cao_agent/bootstrap_local.sh`：檢查可下載依賴、安裝 profile、建立隔離 worktree。

## 可下載依賴

| 依賴 | 來源 / 安裝方式 | 備註 |
| --- | --- | --- |
| CAO CLI / server / MCP server | `uv tool install "git+https://github.com/awslabs/cli-agent-orchestrator.git@main"` | 預設安裝到 `$HOME/.local/bin`。 |
| `uv` | https://docs.astral.sh/uv/ | 用來安裝 CAO。 |
| `tmux` | Homebrew: `brew install tmux` | CAO service runner 需要。 |
| Node.js / npm | https://nodejs.org/ 或 Homebrew | CAO web UI 需要。 |
| Codex app | Codex desktop app | 預設 binary：`/Applications/Codex.app/Contents/Resources/codex`，可用 `CODEX_APP_BIN` 覆蓋。 |
| CAO web UI | https://github.com/awslabs/cli-agent-orchestrator.git | 本機預設中文 UI 目錄為 `$HOME/.local/share/cao-web-zh/web`，可用 `CAO_WEB_DIR` 覆蓋。 |

## 本機重建流程

```bash
git clone <stock-bot-main-url>
cd stock-bot-main

tools/cao_agent/bootstrap_local.sh
tools/cao_agent/ensure_cao_services.sh
```

啟動後確認：

- CAO API: `http://127.0.0.1:9889/`
- CAO UI: `http://127.0.0.1:5173/`

## 重要環境變數

- `STOCK_BOT_REPO`：repo root override。
- `STOCK_BOT_AGENT_CONTEXT`：本機 agent 暫存上下文，預設 `<repo>/.cao_agent_context`。
- `STOCK_BOT_AGENT_WORKTREE`：Tech write 隔離 worktree，預設 repo 同級 `stock-bot-agent-worktrees/tech_write`。
- `CAO_AGENT_PROFILE_DIR`：CAO profile 安裝目錄，預設 `$HOME/.aws/cli-agent-orchestrator/agent-context`。
- `CAO_BIN`、`CAO_SERVER_BIN`、`CAO_MCP_SERVER_BIN`：CAO binaries。
- `CAO_WEB_DIR`：CAO web UI 目錄。
- `CAO_WEB_REPO_DIR`：CAO web UI checkout 目錄，預設是 `CAO_WEB_DIR` 的上一層。
- `CODEX_APP_BIN`：Codex app binary。

## 中文 CAO UI

目前這台機器的中文 CAO UI 是 `~/.local/share/cao-web-zh`，它是 `awslabs/cli-agent-orchestrator` checkout 上的本地修改，大小約 186MB。

這類大型外部前端不直接塞入 `stock-bot-main`。重部署時優先從 CAO upstream 取得 web UI；若中文化是本專案必須長期保留的手寫資產，應另開任務把最小中文 patch 或獨立 fork 固定下來，再由 `CAO_WEB_DIR` 指向該 checkout。
