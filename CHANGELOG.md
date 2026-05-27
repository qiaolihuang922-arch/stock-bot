# CHANGELOG:

## 修改內容

- 將 Telegram formatter 的使用者可見版本常量從 `v20.0.1` 同步為 `v20.0.9`。
- 將 Telegram header 相關 formatter 測試期望從 `v20.0.1` 同步為 `v20.0.9`。
- 以 formatter 直接輸出核對 header 第一行包含 `v20.0.9`，且不包含 `v20.0.1`。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 契約影響

- 使用者可見 Telegram 報文 header 版本字串改為 `v20.0.9`。
- `core/generator.py` 的 `VERSION` 常量已同步為 `v20.0.9`，`formatTelegramSummary()` header 會使用同一個常量輸出。
- 未改 Telegram message list 數量、順序、payload shape、函式回傳型態、分組名稱、summary 規則、持倉 / 未持倉分類或 DB 寫入契約。

## 版本同步

- `TASK.md` 版本契約要求使用者可見 Telegram header 顯示 `v20.0.9`。
- 已同步 `core/generator.py` 的 `VERSION` 常量為 `v20.0.9`。
- 已同步 `tests/test_generator_report.py` 中 header 版本字串期望為 `v20.0.9`。

## 直接消費者同步

- `formatTelegramSummary()` 直接消費 `VERSION` 常量，header 輸出已同步。
- `formatTelegramMessages()` 直接消費 `formatTelegramSummary()` 產生 summary message，message list 外層契約未改。
- `tests/test_generator_report.py` 已同步兩個使用者可見 header 版本期望：
  - 一般 summary message header。
  - `include_detail=True` 時最後 summary message header。
- Owner 手機 Telegram 閱讀者會在報文第一屏 header 看到 `v20.0.9`。

## 未影響模組

- `services/analysis.py` 策略判斷未改。
- `core/condition_engine.py` 條件映射未改。
- `services/stock_api.py` 行情來源未改。
- `services/signal_store.py`、`services/daily_snapshot_store.py`、`services/position_store.py` DB / snapshot / 持倉讀寫未改。
- `core/signal_snapshot.py`、`core/signal_validator.py` snapshot 組裝與驗證未改。
- `core/watchlist.py` 股票清單未改。
- replay / backfill scripts 未改、未執行。
- Telegram live delivery 未執行。
- Supabase live write 未執行。

## 已跑自檢命令

- `rg -n "v20\\.0\\.1|v20\\.0\\.9" -g '!CHANGELOG.md' -g '!TASK.md' -g '!DISPATCH.md' -g '!CURRENT_STATE.md' -g '!AGENTS.md' -g '!QA_REPORT.md'`
  - 結果：程式與測試只剩 `core/generator.py`、`tests/test_generator_report.py` 使用 `v20.0.9`；另有 `CLEANUP_PLAN.md` 歷史狀態文字含 `v20.0.1`，非 Telegram header 程式常量或測試期望，本輪未改固定總控文件。
- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; m.TOKEN="dummy-token"; m.CHAT_ID="dummy-chat"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_generator_report.py", "-q"]))'`
  - 結果：`34 passed, 21 warnings`
- `arch -arm64 .venv/bin/python - <<'PY' ...`
  - 核對 formatter output header 第一行：`【05/27 盤後｜v20.0.9】`
  - 結果：`contains_v20_0_9=True`、`contains_v20_0_1=False`

## 殘留風險

- 本輪只做 Tech 最小自檢，未宣告 QA 通過。
- 未執行 full pytest、replay/backfill、live Telegram delivery 或 live Supabase write；依 `TASK.md` 與 Tech 邊界未執行。
- `CLEANUP_PLAN.md` 仍有一筆歷史狀態文字提到 `v20.0.1 Evidence Readiness Message`；它不是本輪使用者可見 Telegram header 版本來源或測試期望，且 Tech 本輪不改 Architect 總控文件。
