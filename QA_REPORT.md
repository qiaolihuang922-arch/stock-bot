# QA_REPORT: report_actionability_consistency_v21_1_20260624

## 測試範圍

- Low-repair support/MA/volume state.
- Low-repair actionable card.
- RR too-low after breakout.
- Failed breakout reclaim distance wording.
- Adjacent summary/unheld grouping tests.
- Official dry-run smoke.

## 關聯風險掃描

- 檢查 `可買` 卡是否仍有舊 `小倉：可試單｜守支撐/5日均`。
- 檢查支撐跌破是否仍說 `待守` 或 `守住支撐`。
- 檢查 RR 低值是否裸露為 `風險報酬 0.02→1.5`。
- 檢查 `前次 eliminated` 是否回到報文。

## 跨區塊語意一致性

- 低位修復:
  - 支撐跌破 -> `等重新築底 / 重新站回支撐`。
  - 量能 0.9x -> `偏低未失控`，不再當作硬阻擋。
- RR:
  - 已突破但 RR 低 -> `追價風險過高`。
- 突破失敗:
  - 百分比接近但價差大 -> `站回距離偏大`。

## 使用者誤讀風險

- 已降低:
  - 可買卡現在先給行動與失效線。
  - 不再把極低 RR 數字當主訊息。
  - 支撐跌破不再像可等待守住。
- 剩餘:
  - Full legacy tests 還有舊摘要期待，需獨立整理，不阻塞本輪。

## 失敗標本反證

- Owner 06/24 盤中報文中的問題類型已用等價 replay / formatter tests 覆蓋。
- Official dry-run smoke 未出現舊誤導字串：
  - `貼近可買`
  - `前次 eliminated`
  - 舊小倉行
  - `支撐 158 待守`

## 質疑與反證

- 質疑: 是否只是硬改文字？
  - 反證: `core/generator.py` 同步調整 low-repair volume gate，並新增 `support_broken` 狀態。
- 質疑: 是否只測 helper？
  - 反證: 測到 `formatTelegramUnheldCard`、`formatTelegramMessages` 與 dry-run smoke。
- 質疑: 會不會把 0.9x 誤判成可買？
  - 反證: 0.9x 僅解除量能硬阻擋，仍需支撐 / 5日均 / RR 等條件成立。

## 未測項目

- 未發 live Telegram。
- 未寫 production DB。
- 未跑 full suite；已知存在 unrelated legacy expectations。

## QA 結論

通過。
