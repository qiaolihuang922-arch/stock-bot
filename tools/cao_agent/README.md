# CAO Agent Runners

本目錄保存可遷移的 CAO runner、profile 模板與本機部署說明。clone repo 後可重建 CAO agents；歷史 outputs、臨時 context、worktree 不進 git。

## Requirements

- CAO CLI / server / MCP server：預設 `$HOME/.local/bin/`
- Codex app：`/Applications/Codex.app/Contents/Resources/codex`
- CAO UI：預設 `$HOME/.local/share/cao-web-zh/web`
- Python / pytest：優先 repo `.venv`，否則 runner 會為隔離 worktree 建立 `.venv`

詳細下載與重建流程見 `tools/cao_agent/DEPLOYMENT.md`。

## Runtime Paths

- repo root：由腳本位置自動推導，可用 `STOCK_BOT_REPO` 覆蓋。
- agent context：`<repo>/.cao_agent_context`
- outputs：`<repo>/.cao_agent_context/outputs`
- Tech worktree：`<repo_parent>/stock-bot-agent-worktrees/tech_write`
- profile templates：`tools/cao_agent/profiles/stock_*.md.template`

常用覆蓋變數：`CAO_BIN`、`CAO_SERVER_BIN`、`CAO_MCP_SERVER_BIN`、`CAO_WEB_DIR`、`CAO_AGENT_PROFILE_DIR`、`CODEX_APP_BIN`。

## Setup

```bash
tools/cao_agent/bootstrap_local.sh
tools/cao_agent/ensure_cao_services.sh
```

手動分步：

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

底層腳本只供 Architect 使用：

```bash
tools/cao_agent/run_project_research.sh "<研究問題>"
tools/cao_agent/run_tech_plan.sh "<規劃問題>"
tools/cao_agent/run_tech_write.sh "<實作指令>"
tools/cao_agent/run_qa_code.sh "<驗證指令>"
tools/cao_agent/cleanup_agent_worktrees.sh
```

## Agent Rules

- PM 定義需求與驗收，不改檔。
- Tech write 只寫隔離 worktree，不碰主 repo。
- QA 只讀驗證候選 diff，只可寫 `.qa_tmp/`。
- Online agents 只用公開資料與清理後 context，不讀完整 repo。
- Security agent 只讀安全檢查，不修 code。
- 所有 agents 不 commit、不 push、不做 live Telegram / Supabase / backfill。

## Frontend

- API: `http://127.0.0.1:9889/`
- UI: `http://127.0.0.1:5173/`
- 回覆 Owner 前端地址前，先跑 `ensure_cao_services.sh` 或確認兩個 port 已 listen。
