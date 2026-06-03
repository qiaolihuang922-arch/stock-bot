# TASK: research_daily_price_backfill_and_trend_sample_expansion_20260603

## 任務狀態

- task_id: research_daily_price_backfill_and_trend_sample_expansion_20260603
- 任務尺寸: risk_patch / research
- 狀態: ready_with_blockers
- QA 分級建議: L3
- 版本建議: 不升 Telegram / 正式策略版本；研究 CLI / artifact 可標明本輪日期與參數。

## Owner 問題

Owner 要繼續既有 TASK：補齊 watchlist 12 檔多年日線資料，讓「回踩延續」研究樣本不只停在目前不足樣本。

本輪只做兩件事：

1. backfill_daily_price_history.py 支援 approved write path 的 dry-run / write / read-after-write。
2. research_trend_continuation.py 產出 12 檔 universe、per-symbol hit count、total hit count，並判斷 total >= 30。

## 使用者可見結果

- Owner 可用 CLI dry-run 檢查將回填哪些 12 檔、哪些日期、多少 rows。
- Owner 可在 approved write path 存在時執行實際回填，並讀回 daily_price 驗證。
- Owner 可取得研究 artifact，直接看到：
- universe 是否為 watchlist 12 檔
- 每檔命中次數
- total sample count
- 是否達到 >=30
- 1 / 3 / 5 / 10 日 forward return 統計
- 若找不到 watchlist 12 source-of-truth 或 approved write path，結果必須是 blocked / fail closed，不得自行猜測或手寫 SQL。

## 非目標

- 不改正式策略。
- 不開 trend_continuation 買入路徑。
- 不改 Telegram 報文。
- 不改 services/analysis.py、core/condition_engine.py、core/generator.py。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不 live Telegram。
- 不手寫 production DML。
- 不把研究結果包裝成交易建議。

## 影響模組

- scripts/backfill_daily_price_history.py
- scripts/research_trend_continuation.py
- 必要時只可新增 / 調整同層研究測試、fixture、script helper。
- 可使用 repo 既有 DB/service client 與 approved write interface，但不得新增 schema 或繞過既有接口。

## 直接消費者

- Owner / Architect：執行 CLI 與讀研究 artifact。
- QA：驗收 dry-run、write path contract、read-after-write、fail-closed、artifact schema。
- 後續 PM/Tech：只用 artifact 判斷是否另開階段二策略任務。

## 輸出契約

### backfill_daily_price_history.py

CLI 必須支援：

- --dry-run
- --symbols
- --start YYYY-MM-DD
- --end YYYY-MM-DD
- --years N
- --skip-existing
- --read-after-write

未指定 --symbols 時，必須解析 watchlist 12 檔 source-of-truth；無法唯一確認時 blocked。

輸出必須包含：

- mode: dry-run / write
- resolved universe symbols
- universe count
- requested date range
- market data source 狀態
- approved write path/interface 名稱
- per-symbol planned rows / existing rows / rows to write / skipped rows
- dry-run 時明確顯示 result: no-write
- write 後 read-after-write 的 per-symbol row count 與日期範圍
- fail-closed reason

禁止輸出 credential、token、DSN、完整 secret env。

### research_trend_continuation.py

artifact 必須包含：

- source: daily_price
- universe symbols
- universe count = 12
- date range
- pattern definition summary
- per-symbol:
- symbol
- daily_price rows used
- hit count
- forward return count for 1 / 3 / 5 / 10 days
- average / median forward return for 1 / 3 / 5 / 10 days
- aggregate:
- total hit count
- threshold: 30
- meets_min_sample_count: true/false
- blocked reason：
- missing-watchlist-source
- missing-approved-write-path
- missing-credentials
- source-error
- daily-price-read-error
- universe-not-12
- insufficient-data

## 版本契約

已存在且不得回退：

- 正式策略與 Telegram generator 不變。
- daily_price schema 不變。
- production write 只能走既有 approved interface。
- 缺 source、缺憑證、讀寫失敗時 fail closed。
- watchlist universe 必須是 12 檔；無法確認 source-of-truth 時 blocked。
- sample count 未達 30 時，不得宣稱可進入買入策略實裝。

不確定契約：

- approved write path/interface 的實際名稱與位置需由 Tech 從 repo 既有程式確認；不存在則 blocked。
- watchlist 12 檔 source-of-truth 需由 Tech 從既有 config/script/DB read path 確認；不能唯一確認則 blocked。

## 驗收條件

1. backfill_daily_price_history.py --dry-run --years 1 可執行，輸出 12 檔 universe、日期範圍、planned rows，且證明沒有 write。
2. --symbols 可限制到 1-2 檔，且不影響未指定 symbol。
3. 實際 write 只使用既有 approved write path/interface；CHANGELOG.md 必須列出 interface 名稱與證據。
4. --read-after-write 可讀回每檔 row count 與日期範圍；讀取失敗必須 fail closed。
5. 缺憑證、缺 source、缺 approved write path、watchlist 不是 12 檔時，script 必須 non-zero 或明確 blocked，且不得寫入。
6. research artifact 必須顯示 12 檔 universe、per-symbol hit count、total hit count、total >= 30 判斷。
7. research 正式結論只能使用 daily_price 多年資料，不得用 synthetic fixture 當 production research conclusion。
8. QA 必須至少覆蓋 dry-run no-write、fail-closed 負面案例、artifact schema、universe count = 12、total hit count threshold。

## 範例或 Fixture

mode: dry-run
source: <market_data_source>
write_path: <approved_interface_name>
universe_count: 12
symbols: [ ...12 symbols... ]
date_range: 2025-06-03..2026-06-03
per_symbol:
- symbol: XXXX
planned_rows: 250
existing_rows: 120
rows_to_write: 130
skipped_existing: true
result: no-write

source: daily_price
universe_count: 12
symbols: [ ...12 symbols... ]
date_range: 2024-06-03..2026-06-03
threshold_min_hits: 30
per_symbol:
- symbol: XXXX
rows_used: 500
hit_count: 4
forward_returns:
d1: { count: 4, avg: 0.00, median: 0.00 }
d3: { count: 4, avg: 0.00, median: 0.00 }
d5: { count: 4, avg: 0.00, median: 0.00 }
d10: { count: 4, avg: 0.00, median: 0.00 }
aggregate:
total_hit_count: 31
meets_min_sample_count: true

## 失敗標本與驗收路由

失敗標本：

- 找不到 watchlist 12 source-of-truth。
- 找不到 approved write path/interface。
- 缺 market data source 憑證或 source-error。
- write 後 read-after-write 查不到剛寫入資料。
- artifact 沒有 per-symbol hit count 或 total hit count。
- total < 30 但輸出暗示可開買入路徑。

驗收路由：

- CLI dry-run 層：參數、universe、日期、no-write。
- approved write interface 層：確認沒有手寫 production DML。
- read-after-write 層：確認 daily_price 可讀回。
- research artifact 層：確認 12 檔、per-symbol、aggregate、>=30 判斷。
- 不驗 Telegram / official generator / formal strategy。

## 明確禁止事項

- 禁止修改正式策略、報文、DB schema。
- 禁止手寫 production DML。
- 禁止 live Telegram。
- 禁止把 local cache 當跨日 source-of-truth。
- 禁止用 synthetic fixture 代替 production research conclusion。
- 禁止在 log 中輸出 credentials、token、connection string。
- 禁止 sample count 未達 30 時開買入路徑或宣稱策略可用。

## 阻塞條件

- 無法確認 watchlist 12 檔 source-of-truth。
- 無法確認既有 approved write path/interface。
- 缺 market data source 憑證或 source-error。
- daily_price read path 不可用。
- 回填資料不足以計算 1 / 3 / 5 / 10 日 forward return。
- 任務需要 DB schema / RLS / grant / policy / role 變更時，立即停下交回 Architect/Owner。

## 本輪停止條件

本輪完成到：

- backfill script 具備 dry-run、write、read-after-write、安全日誌與 fail-closed。
- research script 產出 watchlist 12 檔多年 daily_price artifact。
- artifact 明確回答 total sample count 是否 >=30。

本輪不處理：

- 階段二買入路徑。
- 正式策略接線。
- Telegram 報文改版。
- DB schema 補強。
- watchlist 擴編或選股邏輯改動。
- market data provider 更換。
