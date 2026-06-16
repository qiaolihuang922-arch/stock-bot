# QA_REPORT: strategy_soft_gate_patch_v21_1_20260616

## 測試範圍

- Telegram holding card contract。
- Unheld `等冷卻` / `等回測` / `等型態` / `等接近` mobile card contract。
- Official generator message list dry-run。
- Full regression suite。

## 關聯風險掃描

- 風險 1: 只刪字導致策略條件消失。
  - 反證: `距突破`、突破區、回測 anchor、熱度、品質、有效買點仍保留在對應 state。
- 風險 2: `等回測` 不知道在等哪個回測。
  - 反證: dry-run 顯示 `回測：最近反彈收盤 166.5 附近不破` / `53.3 附近不破`。
- 風險 3: `等冷卻` 被誤讀成可追。
  - 反證: card shows `狀態：漲停/過熱，不追價` and only a cooling wait condition.
- 風險 4: 持倉同一股票出現多個主行動。
  - 反證: holding card now has one `決策` and one `明日處理` line.
- 風險 5: State-specific formatter breaks existing report tests.
  - 反證: targeted and full pytest passed.

## 跨區塊語意一致性

- Holdings answer what to do tomorrow, not a duplicate entry checklist.
- `等冷卻` answers what must cool down.
- `等回測` answers which anchor must hold.
- `等型態` answers which setup/quality condition is missing.
- `等接近` answers whether price is near the breakout zone or needs a separate continuation/retest setup.

## 使用者誤讀風險

- `有效買點` can still be read as an immediate buy if the state header is ignored; current card keeps state header first and retains `不買 / 等待` semantics through the title and trigger.
- `等接近` still includes “進場：不買” because it is a location gate; this is intentional and not a buy recommendation.

## 失敗標本反證

- Owner specimen: `進場 / 缺口 / 可買 / 明日觸發` repeated the same breakout or retest condition.
- Dry-run result:
  - `等冷卻`: uses `狀態` + `等待`.
  - `等回測`: uses `狀態` + `回測` + `有效買點`.
  - `等型態`: uses `狀態` + `等待` + `有效買點`.
  - `等接近`: uses `進場` + `等待`.

## 質疑與反證

- 質疑: 是否硬改文字而非按策略狀態顯示？
  - 反證: formatter branches by `funnel_state`; each state maps to a different card contract.
- 質疑: 是否刪掉策略所需資訊？
  - 反證: tests and dry-run still include distance, anchor, heat, quality, and effective trigger where relevant.

## 未測項目

- 未 live Telegram。
- 未 DB write / backfill / prune。
- 未驗證實際手機 Telegram push，只驗 official generator message text。

## QA 結論

通過。

本輪修正已覆蓋 Owner 貼出的手機閱讀問題；策略計算與 DB 資料未變更。
