# QA_REPORT:

## 測試範圍

- 任務：`github_actions_scheduled_bot_delivery_restore_20260608`。
- 範圍：GitHub Actions schedule -> RUN_MODE -> Run bot step -> `main.py` / notifier delivery guard。
- 未跑 live Telegram。

## 關聯風險掃描

- 原 workflow 只有 `0 6 * * 1-5` schedule，且 expression 將所有 schedule event 映射為 `daily_evidence`。
- `Run bot` step 在 `daily_evidence` 會直接 skip，這能解釋「runner 有跑但 TG 沒推」。
- 修正未碰報文 formatter、策略、DB 或 notifier HTTP 行為。

## 跨區塊語意一致性

- `daily_evidence` 仍是只產證據、不送 TG。
- `bot` schedule 重新進入 `python main.py`。
- manual dispatch 仍可用 `run_mode=bot` / `daily_evidence`。

## 使用者誤讀風險

- 不能把本輪測試結果說成已 live delivery 成功；本輪只證明 scheduled bot delivery chain 會進入 `main.py`。
- 不能把 CAO runner 缺 binary 誤解成 TG 推送根因；TG 根因在 workflow schedule 分流。

## 失敗標本反證

- 失敗標本：schedule 事件被映射成 `daily_evidence`，`Run bot` dry-run 會輸出 skip，不會呼叫 `python main.py`。
- 反證 1：workflow text 目前同時包含 `0 6 * * 1-5` 與 `10 6 * * 1-5`。
- 反證 2：workflow text 依 `github.event.schedule` 分流到 `daily_evidence` 或 `bot`。
- 反證 3：`RUN_MODE=daily_evidence` dry-run 仍 skip `Run bot`。
- 反證 4：`RUN_MODE=bot` fake-python dry-run 會呼叫 `main.py`，且未呼叫 Telegram API。

## 質疑與反證

- `tests/test_workflow_runtime_config.py`：10 passed。
- `tests/test_main_delivery_guard.py tests/test_notifier.py`：5 passed。
- py_compile：passed。
- pytest 有 `.pytest_cache` 權限 warning，不影響測試結果。

## 未測項目

- 未做 live Telegram delivery。
- 未讀 GitHub Actions production log。
- 未驗證 GitHub 實際排程觸發時間；需 push 後由 GitHub schedule 執行。
- 未恢復缺失的本機 `cao` / `cao-server` binary。

## QA 結論

通過。

本輪已用 dry-run / fake runner 反證 TG 沒推的主要鏈路缺口：scheduled workflow 被導到 `daily_evidence`，導致 bot step skip。修正後 scheduled bot path 會呼叫 `python main.py`，且未執行 live Telegram delivery。
