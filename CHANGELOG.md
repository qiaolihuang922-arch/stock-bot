# CHANGELOG: db_backed_low_repair_v21_1_20260616

## 修改內容與檔案

- `services/cross_day_context.py`
  - `daily_price` 讀取欄位由 `close` 擴成 `open/high/low/close/volume/source`。
  - `recent_daily_price_points` 保留 OHLCV，作為跨日低位修復判斷資料。
- `core/generator.py`
  - 新增 `has_daily_price_repair_basis`，只有 production cross-day context ready 且 source 包含 `daily_price` 時才允許低位修復路線。
  - 新增 funnel state `等低位修復`。
  - 遠離突破但 DB 有日線支援時，不再把 pullback/reclaim 類型降成 `等接近`，改為 `等低位修復`。
  - 同步未持倉 funnel 統計、排序、summary、衝突掃描。
- `core/trade_state_machine.py`
  - 新增 `WAIT_LOW_REPAIR` label / action / meta。
- `presentation/report.py`
  - 新增低位修復卡片:
    - 路線、近期支撐、5日均、量能比、有效買點。
  - 盤後等待卡隱藏不適用型 `數據` 噪音。
- `tests/test_generator_report.py`
  - 新增 DB-backed low repair regression。
  - 新增 PULLBACK_RECLAIM 遠離時不得退回 `等接近` 的 regression。
- `tests/test_cross_day_context.py`
  - 驗證 `daily_price` OHLCV 會進入 `recent_daily_price_points`。

## 契約影響

- 報文版本仍為 `v21.1`。
- Telegram message list shape 不變。
- 新增使用者可見等待狀態: `等低位修復`。
- DB:
  - no schema change。
  - no write/backfill/prune。
  - 只讀既有 `daily_price` 欄位。
- Telegram:
  - no live delivery。

## 直接消費者同步

- official generator dry-run 已覆蓋。
- trade state artifact 已同步 `WAIT_LOW_REPAIR`，避免 artifact 與報文狀態不一致。

## 未影響模組

- 不改 `daily_price` 表結構。
- 不改 Render/GitHub dispatch。
- 不改 live Telegram sender。
- 不改持倉停損 / 減碼 hard-stop 邏輯。

## 自檢命令與結果

- DB read probe:
  - 仁寶、緯創、技嘉、旺宏、群創皆有 `source_of_truth` 包含 `daily_price`，各 8 筆 OHLCV。
- Targeted report/state/cross-day tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py tests\test_trade_state_machine.py tests\test_cross_day_context.py -q --tb=short`
  - result: `223 passed, 159 warnings, 46 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `491 passed, 8 skipped, 169 warnings, 110 subtests passed`
- Official generator dry-run:
  - result: `4` messages generated, no live Telegram.
  - unheld cards now show 仁寶 / 緯創 / 技嘉 as `等低位修復` with DB-backed support / 5-day MA / volume evidence.

## 覆蓋層級

- data load: covered by DB read probe and cross-day unit test。
- formatter: covered。
- official generator message list: covered by dry-run。
- runner artifact: equivalent local dry-run path covered。
- production DB write: not run by design。
- live Telegram: not run by design。

## 殘留風險

- `等低位修復` only creates a better observation route; it does not decide a stock is buyable.
- Future calibration can further tune what counts as support repair / volume repair, but must remain DB-backed.
