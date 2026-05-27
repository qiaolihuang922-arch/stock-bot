# CHANGELOG:

## 修改內容

- 修復持倉策略在今日已減碼後仍重複輸出同級減碼的問題。
- `services.analysis.holding_signal()` 新增今日交易事件判斷：
  - 優先使用 `sell_pct` / `today_sold_ratio`。
  - 其次使用 `shares_before` / `before_shares` / `shares_before_trade` / `holding_shares_before` / `previous_shares` 換算。
  - 若缺交易前股數，使用 `current_shares + sold_shares` 估算交易前總股數。
- 今日已賣比例接近原建議同級減碼時，原 `REDUCE_25` / `REDUCE_50` 轉為 `POST_REDUCE_WATCH` / `減碼後觀察`。
- 今日已賣但新訊號升級為更高級減碼時，保留增量減碼；`STOP_100` 硬停損仍不被今日已賣事件遮蔽。
- 今日已買入且未跌破警戒 / 停損時，一般 reduce 訊號轉為 `NEW_POSITION_RISK_WATCH` / `新倉風控觀察`，保留硬風控覆蓋。
- Telegram formatter 同步策略層唯一主行動，讓 summary、持倉卡、明日清單、詳情一致。

## 修改檔案

- `services/analysis.py`
- `core/generator.py`
- `tests/test_analysis_engine.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 契約影響

- `services.analysis.holding_signal()` 新增 optional 參數：`position_events=None`、`current_shares=None`。既有呼叫方不傳入時維持原行為。
- `core.generator.holding_status()` 新增 optional 參數：`position_events=None`，並把持倉股數作為 `current_shares` 傳給策略層。
- 持倉策略 decision 可能新增兩個 level：
  - `POST_REDUCE_WATCH`：今日已減碼比例已接近原建議，主行動改為減碼後觀察。
  - `NEW_POSITION_RISK_WATCH`：今日剛買入且未達硬風控覆蓋，主行動改為新倉風控觀察。
- 未改 Telegram message list 數量、payload shape、DB schema、未持倉分組或 watchlist。
- 使用者可見 Telegram header 保持 `v20.0.9`，不做本輪升版，避免回退前一輪版本同步。

## 版本同步

- Owner 本輪重點是策略衝突修復；本次移植保留目前 `core/generator.py` 的 `VERSION = "v20.0.9"`。
- `tests/test_generator_report.py` 既有 header 版本期望仍為 `v20.0.9`。

## 直接消費者同步

- `core/generator.py` 的 `holding_status()` 已同步呼叫 `holding_signal()` 新參數，並由以下直接呼叫方傳入 `position_events`：
  - `render_stock()`
  - `ensure_holding_decision()`
  - `generate_report()` 持倉 summary 組裝路徑
- `formatTelegramPositionCard()` 透過 `ensure_holding_decision()` 可取得事件感知後的 `POST_REDUCE_WATCH`。
- `position_summary_action()`、`position_summary_note()`、`holding_tomorrow_trigger()`、`holding_reason_line()`、`holding_next_step_line()`、`holding_detail_decision_lines()` 已同步新主行動。
- `tests/test_notifier.py` 已重跑，確認 message list 直接消費者未破壞。

## 未影響模組

- 未改 DB schema / migrations。
- 未改 `core/watchlist.py`。
- 未改未持倉漏斗、淘汰股分類、watchlist 或行情來源。
- 未改 `services/signal_store.py`、`services/daily_snapshot_store.py`、`services/position_store.py` schema 或正式寫入邏輯。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 replay / backfill 寫入。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; m.TOKEN="dummy-token"; m.CHAT_ID="dummy-chat"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_analysis_engine.py", "tests/test_generator_report.py", "tests/test_notifier.py", "-q"]))'`
  - 結果：`69 passed, 21 warnings`

## 殘留風險

- 本輪未執行 full pytest、replay/backfill、live Telegram delivery 或 live Supabase write；依 `TASK.md` 與禁止事項未執行。
- 若 `position_events` 同時缺 `sell_pct`、`sold_shares` 與可估算股數，策略無法推導今日已賣比例，會保留原始風控建議。
- 增量減碼目前以目標比例減去已賣比例估算增量比例；QA 仍需用接近 Owner 長報文情境檢查 summary、持倉卡、明日清單與詳情不互相衝突。
