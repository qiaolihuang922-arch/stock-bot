# TASK: github_actions_scheduled_bot_delivery_restore_20260608

## 任務狀態

- task_id：`github_actions_scheduled_bot_delivery_restore_20260608`
- 任務類型：normal_patch
- 狀態：done
- 版本建議：不升 Telegram 報文版本，維持 `v20.4.47`
- QA 分級：L2

## Owner 問題

Owner 指出 TG 沒有推送，要求不得 live Telegram delivery，先用 runner / dry-run / log / artifact 查推送鏈路。

## 使用者可見結果

- GitHub scheduled workflow 重新有一條 `bot` 排程會進入 `Run bot` step。
- 既有 `daily_evidence` 排程仍保留，且仍不送 Telegram。
- 手動 workflow dispatch 預設仍是 `bot`。

## 非目標

- 不發 live Telegram。
- 不改 Telegram 報文內容、版本、策略、RR、DB schema/write/backfill。
- 不改 `main.py` delivery guard 或 `services/notifier.py` send 行為。

## 影響模組與直接消費者

- `.github/workflows/stock-bot-clean.yml`
- `tests/test_workflow_runtime_config.py`
- `tools/cao_agent/run_online_agent.sh`
- 直接消費者：GitHub Actions scheduled runner、manual dispatch、CAO PM/QA online runner。

## 輸出契約

- `0 6 * * 1-5` schedule 對應 `daily_evidence`，只跑證據自動化，不送 TG。
- `10 6 * * 1-5` schedule 對應 `bot`，會進 `python main.py` 的 TG 推送鏈路。
- `RUN_MODE=daily_evidence` 時 `Run bot` step 必須 skip。
- `RUN_MODE=bot` 時 `Run bot` step 必須呼叫 `python main.py`。

## 版本契約

- 不升 `core/generator.py` 的 `VERSION`。

## 驗收條件

- workflow runtime config tests 通過。
- delivery guard / notifier tests 通過。
- py_compile 通過。
- 驗證不得呼叫 Telegram API；bot step 測試必須用 fake python / dry-run 方式反證。

## 失敗標本與驗收路由

- 失敗標本：目前 `.github/workflows/stock-bot-clean.yml` 只有一條 schedule，且所有 schedule 事件都被映射成 `daily_evidence`，導致 `Run bot` step 輸出 `Run bot skipped for run_mode=daily_evidence`，TG 不會推送。
- 驗收路由：workflow schedule mapping -> `Run bot` shell step dry-run -> `main.py` delivery guard tests -> notifier multi-message tests。

## 禁止事項與阻塞條件

- 不得用 live Telegram delivery 驗證。
- 若缺 Telegram/Supabase secrets，只能用 runtime config / fake runner 驗證鏈路，不得寫入真值或外洩 secret。
