# QA_REPORT: db_backed_low_repair_v21_1_20260616

## 測試範圍

- DB-backed cross-day OHLCV read path。
- 未持倉遠離突破時的 low-repair funnel classification。
- `PULLBACK_RECLAIM` 遠離時不得退回只等突破區。
- Telegram low-repair card contract。
- Full regression suite。

## 關聯風險掃描

- 風險 1: 只改文字，策略仍等回前高。
  - 反證: `unheld_funnel_state` 對 DB-backed far `PULLBACK_RECLAIM` 回傳 `等低位修復`，不再回傳 `等接近`。
- 風險 2: 假跨日資料。
  - 反證: `has_daily_price_repair_basis` 要求 `cross_day_context.source_of_truth` 包含 `daily_price` 且來源 ready。
- 風險 3: DB 欄位不足。
  - 反證: read probe 顯示仁寶 / 緯創 / 技嘉 / 旺宏 / 群創皆有 8 筆 OHLCV；unit test 驗證 OHLCV 進入 context。
- 風險 4: 低位修復被誤讀成可買。
  - 反證: card header 是 `等低位修復`，有效買點列為條件，不產生可買或可準備行動。
- 風險 5: Summary / artifact 與卡片狀態衝突。
  - 反證: funnel buckets、summary bucket、trade state machine 均接上 `等低位修復` / `WAIT_LOW_REPAIR`。

## 跨區塊語意一致性

- `距突破` 保留，仍說明距離前高突破區很遠。
- 遠離突破不再只剩「等接近突破區」；DB 有日線時改看低位修復。
- `等回測` 仍用於連漲修復後的回踩確認；`等低位修復` 用於低位支撐 / 短均 / 量能修復觀察。

## 使用者誤讀風險

- `近期支撐` 可能被誤讀成買價；卡片用 `有效買點：近期支撐不破 + 站回5日均 + 量能轉強 + 風險報酬 >= 1.5` 避免單一價格變成下單指令。

## 失敗標本反證

- Owner specimen: 仁寶 / 緯創 / 技嘉遠離突破，報文要求接近突破區才重評。
- Dry-run result:
  - 仁寶: `等低位修復｜低位修復觀察`，顯示近期支撐 / 5日均 / 量能。
  - 緯創: `等低位修復｜低位修復觀察`。
  - 技嘉: `等低位修復｜低位修復觀察`。

## 質疑與反證

- 質疑: DB 是否支援？
  - 反證: `daily_price` 已有 OHLCV，不需要擴 schema。
- 質疑: 沒 DB 時是否亂判？
  - 反證: existing far no-DB regression 仍維持 `等接近`。
- 質疑: PULLBACK_RECLAIM 是否還會被降成等接近？
  - 反證: 新增 regression 鎖定 `等低位修復`。

## 未測項目

- 未 live Telegram。
- 未 DB write / backfill / prune。
- 未驗實際 GitHub runner artifact，只驗 official local dry-run equivalent。

## QA 結論

通過。

本輪修正解決 Owner 指出的「遠離突破只能等回前高」策略/顯示問題；資料來源為 production DB `daily_price` 只讀資料，沒有假跨日記憶。
