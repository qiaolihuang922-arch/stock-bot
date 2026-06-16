# QA_REPORT: strategy_buy_path_db_replay_audit_v21_1_20260616

## 測試範圍

- DB read-only replay tool。
- Replay artifact 結構。
- `等回測` 下一狀態統計。
- Snapshot raw tradeable vs official funnel state false-negative 檢查。

## 關聯風險掃描

- 風險 1: 工具寫 DB。
  - 反證: artifact 固定 `db_write=false` / `schema_change=false` / `live_telegram=false`，腳本只呼叫 Supabase `select`。
- 風險 2: 策略其實永遠不可買。
  - 反證: 730 天 replay 產生 `可買/趨勢延續 700` stock-days，含 `可準備` 為 `1035` stock-days。
- 風險 3: funnel 把 raw tradeable 錯擋。
  - 反證: `snapshot_tradeable_blocked_by_funnel_days=0`。
- 風險 4: `等回測` 被誤解為必然可買。
  - 反證: `等回測` 下一狀態包含 `可買 3`、`可準備 4`，也包含 `等冷卻 68`、`淘汰 14`、`等接近 27`、`等RR修復 9`。

## 跨區塊語意一致性

- Replay 結論支持目前語義：
  - `等回測` 是候選等待，不是承諾可買。
  - 可買路徑存在，但不是每次回測都會買。
- Artifact 沒有宣稱回測策略一定有效，只證明沒有明顯 deadlock。

## 使用者誤讀風險

- 若只看單檔當日，會以為系統永遠不買。
- Replay 顯示主要卡點是 `遠離觸發 2148`、`個股弱勢 947`、`量能不足 360`、`弱反彈待確認 265`、`突破失敗 223`。
- 這些 gate 會在不同市場階段切換，不是單一路徑永遠卡死。

## 失敗標本反證

- 原質疑: 連續多日沒有可買，可能策略卡死。
- 反證:
  - `diagnosis.deadlock_suspected=false`
  - `diagnosis.has_real_buyable_path=true`
  - first buy examples 包含南亞科、群創、智原、英業達、旺宏、聯電等真實日期。

## 質疑與反證

- 質疑: `待回測後是否一定變可買？`
  - 反證: 不一定；artifact 的 next-state counts 顯示多數會轉等冷卻 / 等接近 / 淘汰。
- 質疑: `真的會出現在真實股市嗎？`
  - 反證: 使用 Supabase `daily_price` 真實歷史日線 replay，非 synthetic。

## 未測項目

- 未模擬 intraday fill。
- 未模擬實際下單 / position event。
- 未做 live Telegram。
- 未寫 DB。

## QA 結論

通過。
