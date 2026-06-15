# RESEARCH.md

## 2026-06-08 Telegram 降噪研究

Owner 指正：問題不是「重複」本身，而是噪音。每檔卡片可以重複結構，因為手機讀者需要逐檔判斷；真正要降的是低價值流水。

## 結論

- 不應用 `【先看結論】` 插在第 1 則前面。它只是把 Summary 再抄一次，沒有降低後面卡片負擔。
- 持倉卡片應保留逐檔風控判斷：倉位、風控、盤面、今日買入短句、決策、原因、下一步、價格。
- 未持倉卡片應保留「為什麼不能買 / 什麼條件再看」：買點、卡關主因、量化差距、解鎖、明日觸發、價格。
- 用 official `generate_report(dry_run=True)` 反證最終 message list，而不是只看 helper。

## 2026-06-15 RR / Breakout 對標研究

Owner 指正：報文內 RR 很大但仍不可買，容易讓人懷疑公式錯或策略是死規則。研究對標後，本輪結論是：RR 公式要跟常規一致，但「高 RR」不能脫離 setup 成立狀態被說成可買。

## 結論

- 常規 RR 需要三個輸入：entry、stop-loss、take-profit / target；公式為 `(target-entry)/(entry-stop)`。
- 突破交易常規不是只看距突破或 RR，還要看支撐/壓力、放量確認、預設停損與目標、避免假突破。
- 因此報文應區分：
  - `RR x達標`：setup 已成立且可行動。
  - `理論RR x`：數學上 reward/risk 好看，但 setup 未成立、等回測、過熱、品質不足或被 blocker 擋住。
  - `RR x｜需>=1.5`：RR 本身不足。
- 需要擴欄位，因為只存單一 `rr` 無法復盤 entry / stop / target / reward / risk / target basis，也無法判斷當時是 actionable 還是 theoretical。

## 參考來源

- Investopedia: risk/reward ratio compares entry-to-stop and entry-to-target.
- Investopedia: breakout trading relies on support/resistance, volume confirmation, planned exits and stop-losses.
- CenterPoint Securities: RR calculation requires entry price, target, and stop loss.
