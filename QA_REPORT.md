# QA_REPORT: multi_day_rebound_retest_v21_1_20260616

## 測試範圍

- 未持倉 `WEAK_REBOUND` 多日修復分類。
- 單日急彈分類不回退。
- 突破失敗仍淘汰。
- official generator dry-run。

## 關聯風險掃描

- 多日修復只把狀態從淘汰改成等回測，不會直接變可買。
- 使用當次 payload 的 `closes` 與 `price`，沒有假裝跨日記憶。
- 硬失敗 (`decision=FAIL` / `FAILED_BREAKOUT`) 不被覆蓋。
- DB 未改，無 live Telegram。

## 跨區塊語意一致性

- 卡片 title、進場、缺口、summary funnel 都一致為 `等回測`。
- summary 不再把多日修復弱反彈列入淘汰。
- 回測條件仍要求非追高與量能有效。

## 使用者誤讀風險

- `等回測` 明確表示不是可買。
- `反彈修復待回測` 比 `弱反彈待確認` 更符合連漲後狀態。
- 突破失敗仍顯示淘汰，避免把失敗型態誤升級。

## 失敗標本反證

- Owner 06/16 盤中旺宏樣本對照 dry-run:
  - before: `淘汰｜弱反彈待確認`
  - after: `等回測｜反彈修復待回測`
  - 可買條件: `先站回突破區 175.5~176.38，再回測不破 + 非追高 + 量能有效`

## 質疑與反證

- 質疑: 是否因為旺宏單檔硬寫？
  - 反證: 規則用 `closes` / `price` / `WEAK_REBOUND` / hard-fail exclusion，群創符合時同樣升為等回測。
- 質疑: 是否放寬成追高買？
  - 反證: 狀態只到 `等回測`，沒有進入 `可買` 或 `可準備`。

## 未測項目

- 未送 live Telegram。
- 未驗 GitHub scheduled runner 實際 artifact。

## QA 結論

通過。
