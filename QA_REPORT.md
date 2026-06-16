# QA_REPORT: strategy_rule_outcome_audit_v21_1_20260616

## 測試範圍

- DB read-only outcome audit tool。
- Forward 1/3/5/10 日 outcome 對齊。
- 每條 strategy gate 分組驗證。
- Artifact read-only contract。

## 關聯風險掃描

- 風險 1: 工具寫 DB。
  - 反證: artifact 固定 `db_write=false` / `schema_change=false` / `live_telegram=false`，腳本只讀 `daily_price`。
- 風險 2: outcome 用假資料。
  - 反證: `attach_outcomes` 只從 `rows_by_stock` 的 forward daily_price rows 取未來 close；測試覆蓋 1/3/10 日 return。
- 風險 3: 只驗證可買，不驗證阻擋 gate。
  - 反證: artifact 分別輸出 `by_funnel_state`、`by_primary_blocker`、`by_decision_type`、`by_entry_quality`、`by_volume_state`、`by_heat_state`。
- 風險 4: 把 audit flag 誤當可買建議。
  - 反證: QA 結論只說需要下一輪策略檢討，不宣告任何標的可買。

## 跨區塊語意一致性

- Outcome audit 與前一輪 buy-path replay 一致：
  - 系統不是 deadlock。
  - `等回測` 不是承諾可買。
  - 有些 gate 可能偏嚴，需要下一輪策略調整。

## 使用者誤讀風險

- `買點品質D` 整體後續偏強，不代表所有 D 都該買；它代表品質分數目前可能混入了「強勢但還沒確認」的案例。
- `HOT / 漲停不追` 後續偏強，不代表能追漲停；它代表過熱 gate 可能需要拆成「完全不追」與「隔日可準備 / 分批觀察」。
- `wait_breakout_low_rr` 偏強，代表 RR gate 可能太硬，下一輪要檢查 stop/target 設定是否導致 RR 被低估。

## 失敗標本反證

- 原質疑: 多日連漲仍被擋，策略是否假判斷。
- 反證:
  - artifact 顯示多個偏強被擋 gate：
    - `漲停反彈待確認` 5 日勝率 `73.91%`。
    - `漲停不追` 5 日勝率 `63.04%`。
    - `HOT` 5 日勝率 `61.76%`。
  - 這證明 Owner 的質疑成立一部分：策略不是死機，但部分 gate 偏保守。

## 質疑與反證

- 質疑: `等量能` 是否太嚴？
  - 反證: `等量能` 5 日勝率 `46.01%`，平均 `+0.221%`，目前不算主要過嚴 gate。
- 質疑: `急彈待回測` 是否太嚴？
  - 反證: `急彈待回測` 5 日勝率 `42.86%`，平均 `+0.1287%`，等回測有依據。
- 質疑: `過熱 / 漲停不追` 是否太嚴？
  - 反證: 是，artifact flags 指向需要下一輪分層修正。

## 未測項目

- 未模擬 intraday fill。
- 未模擬實際下單 / position event。
- 未做 live Telegram。
- 未寫 DB。
- 未修改策略，故尚未驗證修正後報文。

## QA 結論

conditional pass。

Outcome audit 工具與 artifact 通過；但策略本身暴露出 7 個需要下一輪修正的 gate，不能宣告策略完成。
