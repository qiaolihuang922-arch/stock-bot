# CHANGELOG

## 2026-05-26 - v19.5.1 QA blocker 補修：0 追蹤摘要文案

### 修改內容
- 依 `QA_REPORT.md` 阻塞結果補修 v19.5.1 summary view model。
- 修正 `holding_count and buy_count and tracking_count == 0` 時 `今日結論` 仍輸出 `未持倉 0 檔僅追蹤` 的問題。
- 新文案改為：
  - `明日執行 2 項，持倉 1、可買 1；未持倉無追蹤`
- 同步處理同一 helper 內 `無持倉 + 可買 + tracking_count == 0` 的 0 追蹤噪音，避免輸出 `其餘 0 檔僅追蹤`。
- 補 formatter unit test，覆蓋：
  - 有持倉。
  - 有合格 BUY。
  - 無不可買追蹤候選。
  - `今日結論` 不得包含 `未持倉 0 檔僅追蹤` 或 `其餘 0 檔僅追蹤`。
  - 明日執行清單仍同時列出持倉與可買項。
  - 漏斗 / 詳情索引仍顯示 `不可買追蹤 0` 與 `未持倉追蹤 0`，保持數字可追溯。
- 未修改 v19.5.1 既有能力：
  - `明日執行清單（持倉優先）`
  - `未持倉漏斗（非執行）`
  - `可準備（不可買）`
  - `詳情索引：持倉 / 執行 / 未持倉追蹤 / 淘汰`
  - summary-last / reply_markup-last contract

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

### 風險點
- 本次只修 summary 結論文案分支，不改漏斗與詳情索引的 `0` 數量顯示；這是為了保留數字可追溯，不讓 QA 失去對帳依據。
- `未持倉無追蹤` 是主結論降噪文案；QA 仍需確認它與漏斗的 `不可買追蹤 0`、索引的 `未持倉追蹤 0` 不衝突。
- 本次未跑 full pytest、live Telegram、live Supabase write、TWSE live、正式 replay/backfill。

### 建議 QA 驗證範圍
- Summary / formatter：
  - 有持倉 + 合格 BUY + 0 個等待候選時，`今日結論` 不得再出現 `未持倉 0 檔僅追蹤`。
  - 同場景應顯示 `未持倉無追蹤`。
  - 明日執行清單仍保留持倉項盈虧百分比與可買項。
  - 漏斗仍顯示 `可買 1｜不可買追蹤 0`。
  - 詳情索引仍顯示 `持倉 1｜執行 2｜未持倉追蹤 0｜淘汰 0`。
- Telegram contract：
  - 預設 messages list 順序仍是 `持倉標的 -> 未持倉標的 -> 總覽摘要`。
  - `reply_markup` 仍附在最後摘要段。
- 不變性：
  - 不改 strategy action / decision / is_tradeable / is_best_candidate。
  - 不改 RR / 過熱 / 漲停 / 加碼 / 停利 / 停損硬門檻。
  - 不改 DB schema、snapshot payload、replay/backfill。
- 已執行最低必要驗證：
  - `.venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py`
  - 結果：`35 passed`
