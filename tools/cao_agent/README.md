# CAO Agent Runners

這個目錄保存 stock-bot 的可遷移 CAO runner。重新部署到另一台電腦時，clone `stock-bot-main` 後即可取得這些腳本；歷史 outputs、臨時上下文與 worktree 不進 git。

## Requirements

- CAO CLI: `$HOME/.local/bin/cao`
- CAO server: `$HOME/.local/bin/cao-server`
- CAO MCP server: `$HOME/.local/bin/cao-mcp-server`
- Codex app: `/Applications/Codex.app/Contents/Resources/codex`
- CAO 中文前端預設目錄：`$HOME/.local/share/cao-web-zh/web`
- Python / pytest 依賴：優先使用 repo `.venv`，否則 runner 會為隔離 worktree 建立 `.venv`。

下載與重建流程見 `tools/cao_agent/DEPLOYMENT.md`。

可用環境變數覆蓋預設路徑：

- `STOCK_BOT_REPO`
- `STOCK_BOT_AGENT_CONTEXT`
- `STOCK_BOT_AGENT_OUTPUTS`
- `STOCK_BOT_AGENT_WORKTREE`
- `CAO_BIN`
- `CAO_SERVER_BIN`
- `CAO_MCP_SERVER_BIN`
- `CAO_WEB_DIR`
- `CAO_WEB_REPO_DIR`
- `CAO_LOG_DIR`
- `CAO_AGENT_PROFILE_DIR`
- `CODEX_APP_BIN`

## Local Runtime Paths

預設：

- repo root：由腳本位置自動推導。
- agent context：`<repo>/.cao_agent_context`
- outputs：`<repo>/.cao_agent_context/outputs`
- tech worktree：`<repo_parent>/stock-bot-agent-worktrees/tech_write`

`.cao_agent_context/` 已加入 repo `.gitignore`。

## Setup

```bash
tools/cao_agent/bootstrap_local.sh
```

或手動分步：

```bash
tools/cao_agent/install_agent_profiles.sh
tools/cao_agent/setup_agent_worktree.sh
tools/cao_agent/ensure_cao_services.sh
```

## Daily Entry

```bash
tools/cao_agent/run_architect_task.sh research "<研究問題>"
tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"
```

底層腳本保留給 Architect 使用：

```bash
tools/cao_agent/run_online_agent.sh stock_pm_online_readonly "<研究問題>"
tools/cao_agent/run_online_agent.sh stock_qa_online_readonly "<質疑問題>"
tools/cao_agent/run_research_pair.sh "<研究問題>"
tools/cao_agent/run_project_research.sh "<研究問題>"
tools/cao_agent/run_tech_write.sh "<實作指令>"
tools/cao_agent/run_qa_code.sh "<驗證指令>"
tools/cao_agent/cleanup_agent_worktrees.sh
```

## Prompt Guards

- PM 先判斷任務尺寸與停止條件，避免小 bug 膨脹。
- Tech 先定義最小改動策略，避免順手重構、測試過擬合或回退既有契約。
- QA 先定義 1-3 個風險預算與停止條件，避免 tiny patch 被驗成大任務。
- Tech plan 先輸出任務尺寸、最小影響面與不應觸碰模組。
- `profiles/stock_*.md.template` 保存本專案手寫 agent role cards；新機器用 `install_agent_profiles.sh` 渲染到 CAO profile 目錄。

## Safety

- Tech write 只寫隔離 worktree，不直接寫主 repo。
- QA code runner 是 read-only，只允許 `.qa_tmp/` 測試暫存。
- CAO agents 不 commit、不 push、不做 live Telegram / Supabase / backfill。
- 產品 diff 需 Architect review 後才可合併主 repo。
