# QA_REPORT: cross_day_source_truth_v21_1_20260616

## 測試範圍

- cross-day source-of-truth contract。
- `daily_price` recent close points ingestion。
- 多日弱反彈修復升級。
- 手機報文 replay summary / card。
- 趨勢延續與策略證據相關回歸。

## 關聯風險掃描

- 原問題是驗收降層：前一輪只驗 payload `closes`，沒有驗 DB source。
- 新負面測試確認：沒有 DB `daily_price` context 時，即使 payload closes 連漲，也不能觸發 `反彈修復待回測`。
- 新正面測試確認：有 DB `daily_price` context 且最近點連續抬高，才可觸發等回測。
- `daily_price` read error 會透過 cross-day source-error fail closed。
- 技術指標仍可用 Yahoo/TWSE payload，但不得被標成跨日記憶。

## 跨區塊語意一致性

- `source_of_truth` 包含 `daily_price` 時才有 `recent_daily_price_points`。
- 多日修復仍只到 `等回測`，不會變成可買或可準備。
- 報文保留「不買，等回測」與可買條件，不會誤導追高。

## 使用者誤讀風險

- 報文目前不直接顯示 `daily_price` source，避免噪音；但策略內部已改為 DB source gate。
- 若 Owner 需要可視化來源，可下一輪在 debug artifact 或報文 source line 加簡短 `來源：daily_price`，不建議每張卡常駐顯示。

## 失敗標本反證

- Owner 質疑：「最近四個價格點不查數據庫怎麼來的」。
- 反證結果：
  - 之前來源確實是 payload closes。
  - 現在 `multi_day_rebound_needs_retest` 只讀 `cross_day_context.recent_daily_price_points`。
  - read-only DB 查到旺宏 `daily_price` 最近點：135.0 -> 140.0 -> 146.5 -> 159.0。
  - official dry-run 旺宏顯示 `等回測｜反彈修復待回測`，不是 `淘汰｜弱反彈待確認`。

## 質疑與反證

- 質疑: 是否只是硬改文字？
  - 反證: 沒有 DB context 的同樣 closes fixture 現在回 `淘汰`，有 DB context 才回 `等回測`。
- 質疑: 是否用了假 DB rows？
  - 反證: `build_cross_day_contexts` 直接從 Supabase client 的 `daily_price` 查詢結果組 points；測試 fixture 明確標 source，production dry-run另用 read-only DB 查證。
- 質疑: 是否誤傷趨勢延續？
  - 反證: `test_trend_continuation` 與 generator 趨勢延續 tests 通過；缺 OHLCV source rows 時仍 fail closed。

## 未測項目

- 未做 live Telegram delivery。
- 未做 GitHub scheduled runner artifact 驗證。
- 未做 DB write/backfill/prune。

## QA 結論

通過。
