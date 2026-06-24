# QA_REPORT: report_actionability_consistency_v21_1_20260624

## 測試範圍

- Low-repair support/MA/volume state.
- Low-repair actionable card.
- RR too-low after breakout.
- Failed breakout reclaim distance wording.
- Warning-breached holding wording.
- Adjacent summary/unheld grouping tests.
- Official dry-run smoke.

## 關聯風險掃描

- 檢查 `可買` 卡是否仍有舊 `小倉：可試單｜守支撐/5日均`。
- 檢查支撐跌破是否仍說 `待守` 或 `守住支撐`。
- 檢查 RR 低值是否裸露為 `風險報酬 0.02→1.5`。
- 檢查 `前次 eliminated` 是否回到報文。
- 檢查跌破警戒的持倉是否仍說 `輕虧不加碼`。
- 檢查低位修復可買卡是否仍以 `盤面：弱勢｜弱勢` 開頭。

## 跨區塊語意一致性

- 低位修復:
  - 支撐跌破 -> `等重新築底 / 重新站回支撐`。
  - 量能 0.9x -> `偏低未失控`，不再當作硬阻擋。
- RR:
  - 已突破但 RR 低 -> `追價風險過高`。
- 突破失敗:
  - 百分比接近但價差大 -> `站回距離偏大`。
- 持倉:
  - 跌破警戒但未跌破停損 -> `警戒觀察，不加碼`。
- 可買:
  - 低位修復可買 -> 盤面改顯示低位修復 route，不再和弱勢背景互斥。

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
  - `已跌破警戒` + `輕虧不加碼` 同時出現
  - `🟢 可買｜小倉｜低位修復成立` 後接 `盤面：弱勢`
  - `風險報酬 0.02→1.5` / `0.13→1.5`
- Follow-up focused report tests: `13 passed, 218 deselected`。

## 質疑與反證

- 質疑: 是否只是硬改文字？
  - 反證: `core/generator.py` 同步調整 low-repair volume gate，並新增 `support_broken` 狀態。
- 質疑: 是否只測 helper？
  - 反證: 測到 `formatTelegramUnheldCard`、`formatTelegramMessages` 與 dry-run smoke。
- 質疑: 會不會把 0.9x 誤判成可買？
  - 反證: 0.9x 僅解除量能硬阻擋，仍需支撐 / 5日均 / RR 等條件成立。
- 質疑: 警戒持倉是不是仍像普通續抱？
  - 反證: 跌破警戒時主決策轉為 `警戒觀察，不加碼`，並禁止 `輕虧不加碼`。

## 未測項目

- 未發 live Telegram。
- 未寫 production DB。
- 未跑 full suite；已知存在 unrelated legacy expectations。

## QA 結論

通過。
