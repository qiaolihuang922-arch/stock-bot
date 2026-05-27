# CHANGELOG:

## 修改內容

- 修復今日買入持倉被加碼等級覆蓋的 QA 阻塞：
  - 新增 `is_today_buy_holding()`，同時辨識 `position_events.bought_shares > 0` 與 `today_action` 的 `BUY` / `買` / `買入` / `今日買入`。
  - `position_summary_action()`、持倉卡決策行、下一步、明日執行清單都先套用 `新倉風控觀察`，再處理 `ADD_30 / ADD_20 / ADD_10`。
  - 停損、停利、明確減碼仍高於今日買入，未改風控硬優先。
- 修復淘汰股 summary 噪音：
  - `rejected_trace_line()` 不再輸出完整淘汰股票名單，改為 `淘汰 N 檔｜主因：...｜詳情見未持倉卡`。
  - 未持倉詳情卡仍保留逐檔淘汰明細，方便追溯。
- 保持並補強等冷卻獨立分組：
  - `unheld_funnel_state()` 不再把 `等冷卻` 併入 `等回測`。
  - 未持倉漏斗保留已推送的母集合 / 子集合拆分格式：`未持倉總數`、`可買 / 可準備 / 僅追蹤 / 淘汰`、`其中僅追蹤拆分`、`非執行追蹤合計`。
  - `等冷卻` 在僅追蹤拆分中獨立計數，與未持倉卡片標題一致。
- 補測 QA 阻塞案例：
  - 今日買入持倉且 `holding_decision.level = ADD_20` 時，summary、持倉卡、明日清單不得出現加碼語意。
  - 4 檔淘汰時，summary 只顯示淘汰數量與主因，不完整點名；未持倉詳情卡仍列明細。
  - 更新既有 formatter snapshot 斷言，對齊母集合 / 子集合漏斗、`等冷卻 / 等回測` 獨立計數與淘汰去點名契約。
  - 補回 `可準備` 不併入 `僅追蹤`、但計入 `非執行追蹤合計` 的回歸測試，避免未持倉漏斗總數再次誤讀。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 契約影響

- Telegram message list 外層契約未改：
  - `formatTelegramMessages()` 仍回傳持倉標的、未持倉標的、summary 三段；`include_detail=True` 時仍在前面加完整詳情備份。
  - 未改 Telegram payload 外層結構、DB payload、函式回傳型態或 live delivery 流程。
- 使用者可見文字契約有局部變更：
  - 今日買入持倉在 summary、持倉卡、明日清單的主行動固定為 `新倉風控觀察`，不再顯示 `加碼10 / 加碼20 / 加碼30` 或 `加碼 X%`。
  - 未持倉漏斗保留 `未持倉總數` 與母集合 / 子集合拆分，`等回測` 不再包含等冷卻股票。
  - 淘汰 summary 行改為數量與主因，不再高層完整點名淘汰股。
- `VERSION` 未升版，沿用 `core/generator.py` 的 `v20.0.1`；既有 header 測試仍確認輸出包含 `v20.0.1`。

## 版本同步

- `TASK.md` 要求本輪不升版，沿用目前 `core/generator.py` 的 `VERSION`。
- 已確認本輪未修改 `VERSION`。
- 相關 formatter 測試仍覆蓋 Telegram header 實際輸出版本字串。

## 直接消費者同步

- `formatTelegramSummary()` 已同步使用今日買入優先後的持倉行動、淘汰去點名 summary、等冷卻獨立漏斗，以及未持倉母集合 / 子集合拆分。
- `formatTelegramPositionCard()` 已同步今日買入優先於 ADD 等級，卡片決策行與條件行不再輸出加碼語意。
- `format_execution_checklist()` 經由 `holding_execution_item()` 使用同一個 `position_summary_action()`，明日清單同步輸出 `新倉風控觀察`。
- `tests/test_generator_report.py` 已覆蓋 summary / 持倉卡 / 未持倉卡 / 明日清單連續報文。
- `tests/test_notifier.py` 已重跑，確認 Telegram notifier 直接消費 message list 的路徑不需改代碼。

## 未影響模組

- `services/analysis.py` 策略分數、買賣判斷來源未改。
- `core/condition_engine.py` 條件映射未改。
- `core/watchlist.py` 與股票清單未改。
- `services/stock_api.py` 行情來源未改。
- `services/signal_store.py`、`services/daily_snapshot_store.py`、`services/position_store.py` DB / 持倉讀寫未改。
- Supabase edge functions 未改。
- replay / backfill scripts 未改、未執行。
- live Telegram delivery 未執行。
- live Supabase write 未執行。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; m.TOKEN="dummy-token"; m.CHAT_ID="dummy-chat"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_generator_report.py", "-q"]))'`
  - 結果：`36 passed, 21 warnings`
- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; m.TOKEN="dummy-token"; m.CHAT_ID="dummy-chat"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_generator_report.py", "tests/test_notifier.py", "-q"]))'`
  - 結果：`39 passed, 21 warnings`

## 殘留風險

- 本輪只做 Tech 最小自檢，未宣告 QA 通過。
- 未執行 full pytest、replay/backfill、live Telegram、live Supabase write；依 `TASK.md` 與 Tech 邊界未執行。
- Summary 與漏斗文字有使用者可見變更，仍需 QA 以手機閱讀路徑檢查長報文跨區塊語意一致性。
