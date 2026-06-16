# QA_REPORT: strategy_soft_gate_patch_v21_1_20260616

## 測試範圍

- Strategy hard / soft gate split。
- HOT / EXTENDED / LIMIT_REBOUND display and funnel state。
- Low-RR gate behavior。
- Official generator message list regression。
- `等接近` mobile card de-duplication。
- DB replay after patch。

## 關聯風險掃描

- 風險 1: 軟阻擋被誤升成可買。
  - 反證: soft-gate promotion only returns `可準備`; tests assert hot confirmed evidence is prepare, not buy.
- 風險 2: 真硬阻擋被放行。
  - 反證: LIMIT_LOCK / EXTREME / AVOID / failed breakout / RR<1.0 still hard gate.
- 風險 3: source-error 被掩蓋成可準備。
  - 反證: missing source remains hard in `_unheld_hard_gate_reasons`; only LIMIT_REBOUND source-only display avoids fake `等資料`.
- 風險 4: 只改文案，策略沒變。
  - 反證: DB replay state counts changed after patch: `可準備 364`, `可買 700`, `deadlock_suspected=false`.
- 風險 5: 為了降噪刪掉突破區資訊。
  - 反證: card still keeps `距突破` and one explicit breakout zone reference in `進場`。

## 跨區塊語意一致性

- `可準備` remains non-actionable preparation.
- `隔日確認` is used for limit-up rebound / follow-through that cannot be chased.
- HOT / EXTENDED is no longer always evidence-unavailable; EXTREME / AVOID remains hard.
- Low RR is hard only when risk is genuinely poor (`RR<1.0`) or low quality + no setup.
- `等接近` no longer shows redundant `可買` line; waiting rule is explicit but compact.

## 使用者誤讀風險

- `可準備` can still be read as recommendation; summary/card wording must continue saying open/retest confirmation before action.
- Outcome audit still flags several categories; this means further calibration is needed, not that every flagged group should be bought.

## 失敗標本反證

- Owner failure specimen:
  - multi-day rebound still shown as淘汰/等資料/等接近.
  - strategy appeared to never generate buy or add paths.
- Replayed evidence:
  - `has_real_buyable_path=true`
  - `has_prepare_path=true`
  - `funnel_blocks_snapshot_tradeable=false`
  - `snapshot_tradeable_blocked_by_funnel_days=0`
  - `可買 700`
  - `可準備 364`

## 質疑與反證

- 質疑: HOT / 漲停反彈是否仍被硬擋？
  - 反證: HOT + supporting/confirmed evidence can become `可準備`; LIMIT_REBOUND becomes `隔日確認`.
- 質疑: RR 是否仍無腦卡 1.5？
  - 反證: RR hard gate now only hard at `<1.0`, or `<1.5` with low quality and `NO_SETUP`.
- 質疑: 是否用了假跨日資料？
  - 反證: replay artifacts read DB daily-price paths; no runtime memory or local cache is used as proof.

## 未測項目

- 未 live Telegram。
- 未 DB write / backfill / prune。
- 未驗證實際券商下單或 intraday fill。

## QA 結論

通過。

本輪修正已落地並通過 full pytest + DB replay。策略仍有後續細分空間，但原本「硬阻擋導致沒有買點路徑」的主要問題已被 replay 反證。
