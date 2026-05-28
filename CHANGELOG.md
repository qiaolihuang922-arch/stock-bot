# CHANGELOG:

## 修改內容

- 修復已完成同級停利後仍重複輸出同級 `停利 25% / 50%` 的持倉主行動；改為 `POST_PROFIT_WATCH / 停利後觀察`，並保留更高級停利與硬風控覆蓋。
- 延續既有今日交易事件處理：今日已減碼接近同級建議時輸出 `POST_REDUCE_WATCH / 減碼後觀察`；今日剛買入且未觸發硬風控時輸出 `NEW_POSITION_RISK_WATCH / 新倉風控觀察`。
- 補上觀察天數 `observation_days` 傳遞與未修復降級：多日觀察且仍弱勢、遠離觸發時降為 `RISK_WATCH / 風控觀察`；修復後可回到續抱。
- 修正未持倉上漲但不可買分類：`遠離觸發` 不再直接列淘汰，改列 `等回測`；真正弱勢、弱反彈、突破失敗、市場弱仍列淘汰。
- QA conditional pass 後追加殘留文案修正：未持倉卡若 `state == 弱勢淘汰` 或 `unheld_funnel_state == 淘汰`，買點等待文案改由淘汰主因決定，例如 `等市場轉強`、`等結構修復`、`等重新轉強`，不再因 RR 不足顯示 `等RR達標`。
- 非淘汰 RR 不足標的維持 `等RR修復` 分組與 `等RR達標` 買點等待文案。

## 修改檔案

- `services/analysis.py`
- `core/generator.py`
- `tests/test_analysis_engine.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 契約影響

- `services.analysis.holding_signal()` 新增 optional 參數 `observation_days=0`；既有呼叫方不傳入時維持原行為。
- `core.generator.holding_status()` 新增 optional 參數 `observation_days=0`，並由 `render_stock()`、`ensure_holding_decision()`、`generate_report()` 傳入既有 holding/data 中的觀察天數。
- 持倉 strategy decision 新增或同步以下 level：
  - `POST_PROFIT_WATCH`：已完成同級停利，本輪未觸發更高級停利或硬風控。
  - `POST_REDUCE_WATCH`：今日已減碼比例接近原建議，主行動改為減碼後觀察。
  - `NEW_POSITION_RISK_WATCH`：今日剛買入的一般 reduce 訊號改為新倉風控觀察。
- 未持倉 Telegram 顯示契約調整：淘汰卡的買點等待文案不得使用 RR 修復語意；非淘汰 `等RR修復` 不變。
- 未改 Telegram message list 數量、payload shape、DB schema、watchlist 或 live send path。
- 使用者可見 Telegram header 保持 `v20.0.9`，本輪不升版。

## 版本同步

- 依 `TASK.md` 版本契約，本輪沿用 `core/generator.py` 的 `VERSION = "v20.0.9"`。
- `tests/test_generator_report.py` 仍檢查 `v20.0.9`，未回退 header。

## 直接消費者同步

- `core/generator.py` 的 `holding_status()` 已同步 `holding_signal()` 新參數，直接呼叫方 `render_stock()`、`ensure_holding_decision()`、`generate_report()` 已傳入 position events / observation days。
- `position_summary_action()`、`position_summary_note()`、`holding_tomorrow_trigger()`、`holding_reason_line()`、`holding_next_step_line()`、`holding_detail_decision_lines()` 已同步 `POST_PROFIT_WATCH` 等新主行動。
- `formatTelegramUnheldCard()` 已同步未持倉卡買點等待文案；`unheld_funnel_state()`、summary 漏斗、索引與淘汰主因維持同一分類來源。
- `tests/test_notifier.py` 已納入自檢範圍，確認 message list 直接消費者未破壞。

## 未影響模組

- 未改 DB schema / migrations。
- 未改 `core/watchlist.py`。
- 未改 `services/signal_store.py`、`services/daily_snapshot_store.py`、`services/position_store.py` schema 或正式寫入邏輯。
- 未改行情來源、正式 replay/backfill 寫入路徑。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 backfill。

## 已跑自檢命令

- `PYTHONPATH=/private/tmp/stockbot_test_config:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_rejected_weak_rr_uses_true_reject_reason_not_rr tests/test_generator_report.py::GeneratorReportTest::test_summary_with_holding_and_buy_has_no_zero_tracking_noise -q`
  - 結果：`2 passed, 13 warnings`
- `PYTHONPATH=/private/tmp/stockbot_test_config:$PWD arch -arm64 .venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_generator_report.py tests/test_notifier.py -q`
  - 結果：`76 passed, 21 warnings`
- 測試環境備註：直接用 `.venv/bin/python` 會因 `pydantic_core` 架構不相容失敗；改用 `arch -arm64 .venv/bin/python`。worktree 沒有 `config.py`，自檢使用 `/private/tmp/stockbot_test_config/config.py` 的空白測試設定，未讀取 `.env`、未使用真實 token，未呼叫 live API。

## 殘留風險

- 未執行 full pytest、replay/backfill dry-run、live Telegram delivery 或 live Supabase write；依 `TASK.md` 與禁止事項未執行。
- 若 production position events 缺少可估算今日買賣比例的欄位，策略仍無法推導今日已賣 / 已買狀態，會保留原始風控建議。
- 本次 conditional pass 後僅修未持倉卡殘留文案；未擴大策略分類、DB、payload 或 message list diff。
