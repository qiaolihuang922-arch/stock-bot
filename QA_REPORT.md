# QA_REPORT: near_breakout_tracking_contract_v21_1_20260616

## 測試範圍

- 距突破顯示閾值。
- 未持倉追蹤 / 淘汰 funnel。
- 接近突破 C 品質觀察。
- 弱反彈與突破失敗負面路徑。
- 官方 Telegram message list。

## 關聯風險掃描

- 風險 1: 只改 `距突破` 文案但 `數據 / RR` 行仍顯示 `遠離觸發`。
  - 反證: 測試要求聯電 replay 卡片不含 `遠離突破` 與 `遠離觸發`。
- 風險 2: 放寬接近突破後，弱反彈也被放過。
  - 反證: `rejected_weak_rr` 與大範圍 generator tests 仍通過；弱反彈真淘汰不回退。
- 風險 3: 中間態接住太寬，影響可準備 / 淘汰統計。
  - 反證: 第一次大範圍測試曾抓到此問題，已收窄後重跑通過。

## 跨區塊語意一致性

- `<=5%` 在 display、RR hidden reason、final label 均不再被稱為遠離。
- 接近突破但品質未過，卡片應是追蹤 / 觀察，不是策略淘汰。
- 真正不可買仍由「可買條件未滿」表達，不升格為有效進場。

## 使用者誤讀風險

- `隔日確認` 可能仍需要後續簡化文案，但本輪先解決錯誤狀態：4.25% 不應遠離，也不應掉到淘汰。
- 資料來源缺失仍 fail closed；本輪不把 source missing 改成可買或可準備。

## 失敗標本反證

- Owner 樣本：聯電 `4.25%` 同時顯示 `遠離突破` 與 `⛔ 淘汰｜觀察`。
- 反證 replay:
  - `breakout_distance=4.25`
  - `entry_quality=C`
  - `market_grade=C`
  - 非 `FAIL` / 非 `WEAK_REBOUND`
  - 結果: card 包含 `距突破：4.25%｜接近突破`，不含 `⛔ 淘汰` / `遠離突破` / `遠離觸發`。

## 質疑與反證

- 質疑: 是否只是硬改文字？
  - 反證: 修改同時覆蓋 display label、structural reject、funnel state、RR hidden reason。
- 質疑: 是否破壞原本淘汰規則？
  - 反證: 弱反彈、突破失敗、遠離觸發追蹤測試仍通過。
- 質疑: 是否新增買點？
  - 反證: 測試結果是追蹤 / 隔日確認，不是可買。

## 未測項目

- 未做 live Telegram delivery。
- 未跑 GitHub runner artifact。
- 未做 DB write/backfill/prune。
- Full pytest 已通過：`482 passed, 8 skipped, 110 subtests passed`。

## QA 結論

通過。
