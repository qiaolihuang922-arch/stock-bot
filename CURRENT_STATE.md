# CURRENT_STATE.md

請先讀 `AGENTS.md`、再讀 `DISPATCH.md`，本文件只保留短上下文與穩定狀態。

## Stable Context

- Owner 主要看 Telegram 報文；Summary 必須以手機閱讀為第一視角。
- live Telegram delivery 需要 Owner 單獨批准；本輪與上一輪都沒有 live delivery。
- production source-of-truth 是 Supabase / GitHub runner；local runtime/cache 只能做同 run 輔助。
- DB schema / RLS / grant / policy / role / index / constraint 變更必須先問 Owner。
- `core/generator.py` 的 `VERSION` 目前維持 `v20.4.47`。
- 固定 8 份 Markdown 不刪除：`AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`。

## Latest Completed Work

- task_id：`today_buy_all_risk_summary_wording_20260608`
- 狀態：done / QA passed / committed / pushed to `origin/main`。
- Owner 標本：2026-06-08 dry-run Summary 同時出現 `今日已買 5（已風控 5）` 與 `今日交易已建立新倉 5 檔`，造成「已風控」卻像「新倉成立」的誤讀。
- 修正：
  - `presentation/report.py` 新增今日買入已風控名稱判斷。
  - 全部今日買入已停損 / 減碼 / 硬風控時，結論改為 `今日已買 N 檔，已全部轉入風控/停損減碼`。
  - 明細改為 `今日買入後風控：N 檔（...）`。
  - 部分風控部分觀察時，結論改為 `今日已買 N 檔（已風控 M/觀察 K）`。
  - 全部仍新倉風控觀察時，保留既有 `今日交易已建立新倉`。
- 驗證：
  - focused `tests/test_generator_report.py` -> 4 passed, 3 subtests passed。
  - `py_compile presentation/report.py tests/test_generator_report.py` -> passed。
  - official `generate_report(dry_run=True)` Summary -> `今日已買 5 檔，已全部轉入風控/停損減碼；新增有效進場：無。`，`今日買入後風控：5 檔（英業達、智原、建準、聯電、旺宏）`。
- 未影響：
  - 未改 `core/generator.py` 版本。
  - 未改 strategy / RR / DB write / backfill / notifier / GitHub Actions。
  - 未 live Telegram delivery。

## CAO Deployment Status

- Windows 原生 CAO 已確認不可用：`cli-agent-orchestrator` 依賴 Unix `fcntl`。
- WSL Ubuntu 已安裝並可用。
- WSL 內已安裝：
  - `uv`
  - CAO CLI / server / MCP
  - `git`
  - `tmux`
  - Linux `node` / `npm`
  - CAO web UI
  - stock agent profiles
  - Tech worktree
- CAO services 已啟動並從 Windows 可連：
  - API：`http://127.0.0.1:9889/`
  - UI：`http://127.0.0.1:5173/`
- WSL Codex CLI：
  - Windows app 內 `resources/codex` 是 Linux ELF binary，但 WindowsApps 目錄不可執行。
  - 已複製到 `/root/.local/bin/codex-real` 並可執行，版本 `codex-cli 0.137.0-alpha.4`。
- repo runner patch：
  - `.gitattributes` 固定 `tools/cao_agent` shell/wrapper/sandbox 檔為 LF。
  - `ensure_cao_services.sh` 改用 `NPM_BIN` / `npm`，不再硬寫 macOS `arch -arm64 /usr/local/bin/npm`。
  - `tools/cao_agent/bin/codex` 在 Linux/WSL 無 `sandbox-exec` 時直接執行 `CODEX_APP_BIN`。
- WSL 執行入口需帶：

```bash
export PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/mnt/d/reserch/stock-bot/tools/cao_agent/bin
export STOCK_BOT_REPO=/mnt/d/reserch/stock-bot
export CODEX_APP_BIN=/root/.local/bin/codex-real
cd /mnt/d/reserch/stock-bot
bash tools/cao_agent/bootstrap_local.sh
bash tools/cao_agent/ensure_cao_services.sh
```

## Previous Completed Work

- task_id：`github_actions_scheduled_bot_delivery_restore_20260608`
- 狀態：done / committed / pushed to `origin/main`。
- 修正 GitHub scheduled TG bot 沒推送：`0 6 * * 1-5` 保留 daily evidence；新增 `10 6 * * 1-5` 作為 bot schedule；schedule expression 明確 mapping 到 `RUN_MODE=bot` 或 `daily_evidence`。
- 驗證：workflow runtime config tests 10 passed；delivery guard/notifier tests 5 passed；py_compile passed；未 live Telegram delivery。

## Data / Evidence Status

- 本地 Supabase read-only config 可讀 positions / position_events，2026-06-08 dry-run 能產出 4 則 Telegram message。
- 2026-06-08 active holdings dry-run Summary 中 5 檔今日買入均已轉風控：英業達、智原、建準、聯電、旺宏。
- `.pytest_cache` 在 Windows 有 permission warning，不影響測試結果。

## Next Development

- CAO deployment patch commit / push 後，下輪若再修報文，應優先用 WSL 正式 Architect entry；仍需用 Owner 貼出的 final report 層標本或 official dry-run artifact 驗收，不得只驗 helper fixture。
- 如果 Owner 要再查 DB key / 連線，先用 read-only probe，不輸出 secret。
- 如果 Owner 要驗 TG 發送，必須先明確批准 live Telegram delivery；否則只用 dry-run/log/artifact。

## Runner Gaps To Fix Later

- 本機 CAO runner 缺 `cao` / `cao-server` binary；需要另開流程治理任務補安裝或 fallback。
- QA production-read 若 sandbox / DNS / 權限受限，應走 safe read-only artifact，標明 source、版本、無 credential、無 write、無 live delivery。
- Workflow / runner / report 任務需要保留 final report 層 artifact，避免只驗 helper 或 synthetic fixture。
