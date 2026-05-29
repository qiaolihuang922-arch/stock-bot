# CHANGELOG: Evidence Phase 3 Production Source Mapping Blocked

## 任務尺寸與結論

- 任務尺寸：normal_patch。
- 結論：blocked。現有 code / schema / docs 無法證明 production DB 或 Owner-approved persistent source 已足夠支撐 market/theme evidence confirmed。
- 本輪未修改產品代碼、測試、DB schema、DB write path、Telegram wording、watchlist 或交易門檻。

## 修改內容

- 只完成 source mapping 判斷。
- 保留 v20.4.2 source-family gate：confirmed / ready 只能來自 `production_db` 或 `owner_approved_persistent`，且 required fields / freshness 完整。
- 停止實作 read-only loader。若硬接現有來源，會把個股策略分類、runtime 聚合或 payload dict 誤升級成 market/theme confirmed。

## 修改檔案

- 無產品代碼修改。

## Source Mapping 判斷

- `daily_signal_snapshot`
  - 可用：`production_db`、`trade_date`、`version`、個股策略狀態。
  - 不足：不是 market index；缺 sector/theme key；watchlist breadth 需 runtime 聚合；support level 不足。
  - 判斷：只能作 detail / backtest context，不得 confirmed。
- `strategy_feature_snapshots`
  - 可用：`production_db`、`trade_date`、`strategy_version`、`watch_category`、`reject_family`。
  - 不足：策略分類不是 market index；缺 sector/theme key；無 theme-level support value。
  - 判斷：只能作 detail / sorting hint，不得 confirmed。
- `strategy_outcome_metrics`
  - 可用：`production_db`、回測 outcome、`trade_date`、`strategy_version`、`horizon_days`。
  - 不足：缺 market index、theme key、watchlist breadth；不是當日 market/theme support。
  - 判斷：只能作 evidence / audit trace，不得 confirmed。
- `strategy_classification_audit`
  - 可用：`production_db`、audit severity、`trade_date`、`strategy_version`。
  - 不足：缺 confirmed 所需 market/theme source 欄位。
  - 判斷：只能作 audit trace，不得 confirmed。
- `market_daily_bars`
  - 可用：`production_db`、OHLCV、`stock_id`、`trade_date`、`source`。
  - 不足：目前是 watchlist 個股日線，不是 TAIEX / sector index contract；缺 sector/theme mapping 與 breadth。
  - 判斷：只能作 price trace，不得 confirmed。
- `daily_price`
  - 可用：`production_db`、個股 close price、`trade_date`。
  - 不足：缺 evidence contract、market index、theme key、breadth。
  - 判斷：只能作 backtest price trace，不得 confirmed。
- `runtime results_map / watchlist diagnostic`
  - 可用：同 run 診斷。
  - 不足：`runtime_diagnostic`，無 production lineage，fresh runner 不可重建。
  - 判斷：v20.4.2 gate 已禁止 fake confirmed，只能 detail。
- `market_summary.market_theme_evidence`
  - 可用：payload 已帶入時可被 formatter 顯示。
  - 不足：不是 fresh runner 可重建的 production loader；source family 與 lineage 未證明。
  - 判斷：不得自行信任為 confirmed source。

## 阻塞缺口

要讓 market/theme evidence 變成 confirmed，需先由 Owner / PM 確認或批准 production source contract，至少包含：

- 可由 GitHub fresh runner read-only 存取的 market/theme evidence table、view 或 helper。
- `market_index` 或等價市場指標來源，例如 TAIEX / sector index source contract。
- `sector_theme_key` 或等價 theme / sector key，且可映射到 watchlist 股票。
- production / persistent 的 `watchlist_breadth` source contract，或可由 production source read-only 重建的廣度計算契約。
- `as_of` / `trade_date` / freshness 欄位與過期判斷。
- `evidence_value` / `support_level` 欄位或可追溯計算契約。
- lineage：`run_id`、`snapshot_id`、`symbol`、`theme_key`、`source_name` 或等價追溯欄位。

## 契約影響

- 函式回傳結構：未改。
- message list / Telegram 報文順序：未改。
- payload shape：未改。
- 報文分組：未改。
- public helper：未改。
- version/header：未改；因未修改使用者可見 wording/header，未升到 v20.4.3。

## 直接消費者同步

- `core/generator.py`：未改，仍消費既有 `build_market_theme_evidence_provider()` 與 `format_market_theme_summary_lines()`。
- Owner 手機 Telegram 報文：未改，source 不足時仍 fail closed。
- market/theme evidence provider：未改，v20.4.2 source-family gate 保持。
- GitHub fresh runner：未新增不可重建 local/runtime/cache 依賴。

## 未影響模組

- 策略門檻：未改 BUY / SELL / RR / overheat / trading thresholds。
- DB schema / migration / SQL：未改。
- DB write stores：未改。
- watchlist：未改。
- replay/backfill：未改。
- live Supabase write：未執行。
- live Telegram：未執行。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py`
  - 結果：17 passed, 13 warnings。
- `git diff --check`
  - 結果：通過。
- `git diff --stat`
  - 結果：無產品 diff。

## 殘留風險

- 未連 production DB 驗證實際資料品質；本輪只依現有 code / schema / docs 可見 contract 判斷。
- 若 production DB 實際已有未寫入 repo 的 table / view / helper，需要 Owner 提供明確名稱與欄位 contract 後再開發。
- 現有 runtime diagnostic 仍可顯示 detail 診斷，但不會 confirmed。

## 旁支待辦

- 另開任務定義 production market/theme evidence source contract。
- 若需要新增 schema / table / provider / backfill，需 Owner 明確批准，不能併入本輪 normal_patch。
