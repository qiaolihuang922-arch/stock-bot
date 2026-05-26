# CHANGELOG

## 2026-05-26 - v19.5 收盤決策壓縮與執行清單升級

### 修改內容
- 依 `TASK.md` 實作 v19.5 minor，版本顯示更新為 `v19.5`。
- 僅改顯示 / 排序 / summary view model 層，未改策略 action、交易判斷、DB、replay/backfill。
- 總覽摘要改為 v19.5 決策壓縮結構：
  - `🧭 今日結論`
  - `🧭 原因`
  - `✅ 明日執行清單`
  - `未持倉漏斗`
  - `📎 詳情索引`
- 新增結構化 summary helper：
  - 持倉執行項保留目前收益百分比，例如 `英業達｜+19.37%｜核心風控觀察｜守警戒價`。
  - 未持倉執行項保留等待 / 不買 / 不追價語意，例如 `建準｜等RR修復｜不追價，等RR達標`。
  - 明日執行清單最多顯示 5 項；若後面仍有風控或追蹤項，會顯示 `另有 N 檔...見詳情`。
  - 未持倉漏斗統計 `可買 / 可準備 / 等回測 / 等RR修復 / 等量能 / 淘汰`。
  - 弱勢淘汰壓縮為可追溯名稱與主因，例如 `淘汰 1：旺宏｜主因：弱反彈待確認`。
- 保留 v19.4.1 Telegram contract：
  - `formatTelegramMessages()` 預設仍回傳 `持倉標的 -> 未持倉標的 -> 總覽摘要`。
  - 總覽摘要仍是 `messages[-1]`。
  - `include_detail=True` 時完整詳情 chunk 仍在摘要之前。
  - `services/notifier.send_many()` 既有最後摘要段綁定 `reply_markup` 行為未改。
- 更新 formatter 測試：
  - v19.5 摘要新增區塊。
  - 持倉執行清單保留盈虧百分比。
  - 合格 BUY 進入執行清單且不被等待狀態覆蓋。
  - 等量能 / 等RR修復 / 等回測保留不可買或不追價語意。
  - 弱勢淘汰仍可在摘要追溯名稱與主因。

### 修改檔案
- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

### 未影響模組
- `services/analysis.py`
- `services/stock_api.py`
- `services/signal_store.py`
- `services/daily_snapshot_store.py`
- `services/position_store.py`
- `services/notifier.py`
- `services/ai.py`
- `services/learning.py`
- `core/watchlist.py`
- `core/signal_snapshot.py`
- `core/signal_validator.py`
- `scripts/dry_run_replay.py`
- `scripts/backfill_signals.py`
- Supabase Edge Function
- DB schema
- DB 寫入邏輯
- replay / backfill 正式流程
- 股票池
- RR / 過熱 / 漲停不追 / 加碼 / 停利 / 停損硬門檻
- `decision / action / is_tradeable / is_best_candidate`

### 直接消費者同步
- `generate_report()`：
  - 仍回傳 `(messages, reply_markup)`。
  - messages list 順序未回退，摘要仍最後。
- `formatTelegramMessages()`：
  - 回傳 list contract 未改。
  - `include_detail=True` contract 未改。
- `main.py`：
  - 不需修改，仍可把 `messages, reply_markup` 交給 `send_many()`。
- `services/notifier.send_many()`：
  - 未修改，仍將 `reply_markup` 綁到最後一段摘要。
- `generate()`：
  - list join fallback 未改，仍可把多段訊息用分隔線合併成字串。

### 風險點
- 摘要變成新的決策入口，QA 需確認使用者不會把 `可準備 / 等回測 / 等RR修復 / 等量能` 誤解為可買。
- 弱勢淘汰被壓縮到摘要統計與主因行，QA 需確認 12 檔標的仍可追溯。
- 明日執行清單最多 5 項，若候選很多，需確認 `另有 N 檔...見詳情` 出現且不隱藏風控。
- 回測仍只透過既有排序 adjustment 影響同類追蹤順位，沒有進入 BUY 或 hard rule。
- 本次未跑 full pytest、live Telegram、live Supabase write、正式 replay/backfill。

### 建議 QA 驗證範圍
- Summary / formatter：
  - `messages[-1]` 顯示 `v19.5`。
  - 摘要包含 `🧭 今日結論`、`✅ 明日執行清單`、`未持倉漏斗`、`📎 詳情索引`。
  - 明日執行清單最多 5 項，且持倉項含目前盈虧百分比。
  - 合格 BUY 進入明日執行清單前段，不被等待狀態覆蓋。
  - 等待標的顯示 `不買 / 不追價 / 等觸發` 語意。
  - 弱勢淘汰名稱與主因仍可追溯。
- Telegram contract：
  - 預設 messages list 順序仍是 `持倉標的 -> 未持倉標的 -> 總覽摘要`。
  - `include_detail=True` 時完整詳情 chunk 在摘要之前。
  - `reply_markup` 仍附在最後摘要段。
- 不變性：
  - 不改 strategy action / decision / is_tradeable / is_best_candidate。
  - 不改 RR / 過熱 / 漲停 / 加碼 / 停利 / 停損硬門檻。
  - 不改 DB schema、snapshot payload、replay/backfill。
- 已執行最低必要驗證：
  - `.venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py`
  - 結果：`34 passed`
  - `.venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py tests/test_daily_snapshot_store.py`
  - 結果：`41 passed`
