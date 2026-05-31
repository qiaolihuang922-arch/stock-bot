# CHANGELOG: market/theme 2026-05 historical fetch

## 任務尺寸與風險

- 任務類型：risk_patch。
- 原因：涉及 production DB market/theme 歷史資料寫入、confirmed evidence duplicate business-key 清理、read-after-write audit。

## 修改內容

- 擴充 `scripts/backfill_market_theme_sources.py`：
  - 新增 `--historical-range`，可按日期範圍抓 TWSE historical MI_INDEX。
  - 修正 TWSE 歷史來源為 `https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?response=json&date=YYYYMMDD&type=IND|MS`。
  - 支援 IND 欄位 `漲跌百分比(%)`，並保留 `漲跌百分比` 相容。
  - 支援 MS table `漲跌證券數合計`，由 `股票` 欄位解析 `up/down/flat/limit_up/limit_down`。
  - `market_theme_index_daily_bars` 與 `market_theme_confirmed_evidence` 一起由同一 repo script 寫入。
  - 寫入前依 correction audit business key 刪除既有同 key rows，再寫入本次唯一版本，避免不同 `as_of` 批次重複：
    - confirmed evidence：`trade_date, market_index, sector_theme_key`
    - index bars：`trade_date, index_scope, market_index, sector_theme_key`
  - source gaps fail closed：任一交易日缺 official index 或 breadth row 時不寫入。
- 擴充 `tests/test_market_theme_source_backfill.py`：
  - 覆蓋 afterTrading endpoint 與參數。
  - 覆蓋 IND `漲跌百分比(%)`。
  - 覆蓋 MS `股票` 欄位 breadth parsing。
  - 覆蓋 source gap 不進 write path。
  - 覆蓋 duplicate confirmed rows 依 audit business key 收斂。

## 修改檔案

- `scripts/backfill_market_theme_sources.py`
- `tests/test_market_theme_source_backfill.py`

## 契約影響

- CLI 新增 `--historical-range`。
- `scripts/backfill_market_theme_sources.py --write --confirm-write --historical-range` 會處理兩張 production 表：
  - `market_theme_confirmed_evidence`
  - `market_theme_index_daily_bars`
- duplicate 處理規則改為 repo script 內按 audit business key replace，不再保留同 key 多個 `as_of` 批次。
- 無 DB schema、RLS、grant、policy、index、constraint 變更。

## 直接消費者同步

- `scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json --limit 20000` 的 duplicate business-key 口徑未改，已用作 read-after-write audit。
- `sector_theme_members` 仍只作 mapping source，audit 結論維持 `mapping_only`，不計入 daily history。
- 策略後續可透過 production `market_theme_confirmed_evidence` 歷史取得 market/theme evidence trend，不再只能看到 05/29 latest-only。

## 未影響模組

- Telegram / UI 報文。
- strategy buy/sell scoring / ranking。
- `daily_signal_snapshot` history semantics。
- DB schema / index / constraint / RLS / grant / policy。
- live Telegram delivery。

## 已跑自檢與 production 寫入

- `PYTHONPATH=. arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_source_backfill.py -q`
  - 結果：14 passed。
- `git diff --check`
  - 結果：通過。
- dry-run：
  - `PYTHONPATH=. arch -arm64 .venv/bin/python scripts/backfill_market_theme_sources.py --historical-range --start-date 2026-05-04 --end-date 2026-05-29 --dry-run`
  - 結果：ready，`source_gaps=[]`。
  - candidate rows：`market_theme_confirmed_evidence=180`、`market_theme_index_daily_bars=200`。
  - coverage：`2026-05-04` to `2026-05-29`，20 trade dates。
- production write：
  - `PYTHONPATH=. arch -arm64 .venv/bin/python scripts/backfill_market_theme_sources.py --historical-range --start-date 2026-05-04 --end-date 2026-05-29 --write --confirm-write`
  - 結果：executed。
  - written rows：`market_theme_confirmed_evidence=180`、`market_theme_index_daily_bars=200`。
  - schema_change：false；live_telegram：false。
- independent read-only audit：
  - `PYTHONPATH=. arch -arm64 .venv/bin/python scripts/smoke_market_theme_evidence_readonly.py --correction-audit-json --limit 20000`
  - 結果：`status=pass`，`next_action=["read_only_audit_complete"]`。
  - `market_theme_confirmed_evidence`：180 rows，20 trade dates，date range `2026-05-04` to `2026-05-29`，`latest_source_only=false`，duplicate groups 0。
  - `market_theme_index_daily_bars`：200 rows，20 trade dates，date range `2026-05-04` to `2026-05-29`，`latest_source_only=false`，duplicate groups 0。
  - `sector_theme_members`：12 active rows，`mapping_only`，duplicate groups 0。

## 殘留風險

- TWSE historical endpoint 偶發回應不完整或連線錯誤；script 已 fail closed，但後續若要自動每日補資料，應加重試與 source gap 明細輸出。
- 本輪只補 2026-05-04 到 2026-05-29；更多月份 backfill 另開任務。
- 尚未把 market/theme evidence trend 擴展成新的策略加權規則；本輪只完成資料抓取、寫入與 audit 通過。
