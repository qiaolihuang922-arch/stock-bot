# QA_REPORT.md

本文件由 QA 維護，提交給 Architect。只記錄本輪 v19.4 QA 結果。

## 任務狀態

- 狀態：QA 驗證完成
- 對應 TASK / CHANGELOG：`TASK.md`、`CHANGELOG.md`
- 提交日期：2026-05-26
- 版本：v19.4

## 測試範圍

依 `DISPATCH.md`、`TASK.md`、`CHANGELOG.md`，本輪對 v19.4 交易閉環升級做全量 QA。

覆蓋範圍：
- Formatter / snapshot / Telegram card。
- 策略不變性。
- Snapshot validator。
- Replay dry-run。
- Backfill dry-run。
- 每日資料入庫 payload 路徑。
- 額外風險：價格行右括號、Telegram 預設訊息長度、版本與新增摘要區塊。

## 執行命令

```bash
.venv/bin/python -m pytest
```

```bash
.venv/bin/python scripts/dry_run_replay.py --dry-run --validate --source synthetic --version v19.4 --start-date 2026-05-18 --end-date 2026-05-22 > /tmp/v194_replay_synthetic.csv
```

```bash
.venv/bin/python scripts/backfill_signals.py --dry-run --source synthetic --version v19.4 --start-date 2026-05-18 --end-date 2026-05-22
```

```bash
.venv/bin/python scripts/dry_run_replay.py --dry-run --validate --source twse --version v19.4 --start-date 2026-05-18 --end-date 2026-05-22 > /tmp/v194_replay_twse.csv
```

```bash
.venv/bin/python scripts/backfill_signals.py --dry-run --source twse --version v19.4 --start-date 2026-05-18 --end-date 2026-05-22
```

另執行本地 smoke checks：
- 預設 Telegram 三段訊息長度。
- 所有 `價格：` 行右括號格式。
- v19.4 摘要區塊存在。
- `build_daily_snapshot_payloads()` 完整 / 缺檔入庫 payload 行為。

## 測試結果

### Full pytest

結果：通過。

```text
89 passed, 21 warnings in 1.86s
```

警告皆來自既有第三方套件 / Python 版本 deprecation，未見 v19.4 測試失敗。

### Replay / Backfill Dry-run

Synthetic replay：

```text
VALIDATION OK
60 snapshot rows
```

Synthetic backfill：

```text
daily_price rows: 60
daily_signal_snapshot rows: 60
tradeable rows: 22
best candidate rows: 3
VALIDATION OK
DRY RUN ONLY: no database writes
```

TWSE replay：

```text
VALIDATION OK
60 snapshot rows
```

TWSE backfill：

```text
daily_price rows: 60
daily_signal_snapshot rows: 60
tradeable rows: 2
best candidate rows: 2
VALIDATION OK
DRY RUN ONLY: no database writes
```

### 資料入庫路徑檢查

本輪 diff 未修改：
- `services/daily_snapshot_store.py`
- `services/signal_store.py`
- `core/signal_snapshot.py`
- `core/signal_validator.py`
- `scripts/dry_run_replay.py`
- `scripts/backfill_signals.py`

直接 payload check：

```text
complete_recorded True
complete_signal_rows 12
complete_price_rows 12
partial_recorded False
partial_reason incomplete_watchlist
partial_missing ['2337']
partial_signal_rows 0
partial_price_rows 0
```

結論：
- 12 檔完整時會產生 12 筆 `daily_signal_snapshot` 與 12 筆 `daily_price` payload。
- 缺 1 檔時不產生 signal / price rows。
- v19.4 formatter 變更未破壞每日入庫完整性 guard。

### 額外風險檢查

預設 Telegram messages smoke check：

```text
message_count 3
message_lengths [301, 983, 938]
max_len 983
price_lines 12
bad_price_lines []
has_v19_4 True
has_priority True
has_tracking True
has_pending True
```

結論：
- 預設三段訊息均低於 Telegram 4096 字元限制。
- 12 條價格行均有完整全形右括號。
- 摘要包含 `📌 持倉處理優先級`、`🕒 隔日追蹤`、`待確認候選`。
- 版本顯示為 `v19.4`。

## 驗收項結果

- 報文新增 `📌 持倉處理優先級`：通過。
- 報文新增 `🕒 隔日追蹤`：通過。
- 報文新增 `待確認候選`：通過。
- 每個隔日追蹤標的有 `明日觸發`：通過。
- R3 強勢但過熱不進 `可買`，進等待 / 追蹤語意：通過。
- RR 不足但結構強不進 `可買`，進 `等RR修復`：通過。
- 量能不足但非弱勢進 `等量能`：通過。
- 弱勢 / 遠離觸發不進隔日追蹤優先清單：通過。
- 合格 `BUY` 仍顯示 `可買`，未被待確認覆蓋：通過。
- 今日新倉浮虧進 `新倉風控觀察 / 洗盤警戒`：通過。
- 減碼後持倉進 `減碼後觀察`：通過。
- 核心倉高浮盈回落顯示核心風控語意：通過。
- 回測參考度只影響追蹤排序，不產生 BUY：通過。
- `is_tradeable` / `is_best_candidate` 硬規則未被 tracking priority 覆蓋：通過。
- STOP / TAKE_PROFIT / REDUCE action 未被 lifecycle 顯示覆蓋：通過。
- 股票池未擴大：通過。
- DB schema 未變更：通過。

## 未測項目

本輪未執行：
- live Telegram delivery。
- live Supabase write。
- formal backfill write。
- 真實交易日線上排程觸發。
- Telegram 客戶端實機渲染截圖。

原因：
- 本輪 QA 使用 dry-run / unit / regression 驗證，不做正式寫庫與真實外部推送。
- `CHANGELOG.md` 明確本次未改 DB schema、DB 寫入邏輯、replay/backfill 正式寫入流程。

## 殘留風險

- 隔日追蹤目前是當日報文內的明日檢查清單，尚未新增跨日 tracking table；若 Owner 未來需要多日任務狀態，需另開 DB / persistence 任務。
- 新倉 / 減碼後語意依賴 `position_events`；若事件缺失，會安全回退，但無法精準判定新倉或減碼後狀態。
- 本輪 smoke check 驗證預設三段訊息長度與價格括號；真實 Telegram 客戶端仍可能受字體、複製、截圖或平台截斷影響。
- 回測排序目前只調整追蹤順序；若未來要求回測進入 decision，需重新做策略層與 snapshot 不變性驗證。
- v19.4 增加摘要內容後，目前 mock 訊息長度安全；但若未來持倉 / 未持倉卡片欄位再增加，應持續保留訊息長度 regression。

## QA 結論

QA 結論：通過。

v19.4 交易閉環升級已通過本輪全量 QA：
- formatter 通過。
- 策略不變性通過。
- snapshot / validator 通過。
- replay/backfill dry-run 通過。
- 每日入庫 payload 路徑通過。
- 價格行與 Telegram 預設訊息長度風險檢查通過。

可交回 Architect 更新狀態。
