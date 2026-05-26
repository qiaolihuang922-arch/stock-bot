# TASK: v20.0 Strategy Evidence Foundation

## 任務狀態

- 日期：2026-05-26
- 版本：`v20.0`
- version_level：`major`
- qa_level：`L3`
- 狀態：已完成並推送
- 對應 commit：`2cc4e8a feat: add v20 strategy evidence foundation`

## 需求摘要

v20.0 第一版目標是建立「策略可被證據驗證」的基礎，而不是直接調整 BUY / SELL 門檻。

要解決的問題：

- 策略分類需要能事後驗證，例如 `淘汰`、`等回測`、`RR不足` 後 1 / 3 / 5 / 10 日表現。
- 旺宏類案例不能只靠單日文字判斷；需保留當下策略特徵、後續 outcome 與分類語意 audit。
- 所有產物仍服務既有流程：定時 GitHub Actions / 腳本 -> 策略產出 -> 證據資料更新 -> Telegram 報文。

## 使用者可見變化

- Telegram summary 增加 `📊 策略證據 v20.0`。
- 資料不足時顯示 `樣本不足，不判讀`。
- 可顯示分類警示 / audit note，但不得包裝成買賣指令。

## 允許修改

- 策略證據資料層。
- 分類績效報告。
- Telegram 策略證據摘要。
- replay / backfill dry-run evidence path。
- schema 草案與相關測試。

## 明確禁止

- 不改 BUY / SELL 判斷。
- 不改 `decision=BUY`、`is_tradeable=True`、`action_pct` 產生條件。
- 不放寬 RR / 過熱 / 漲停不追 / 停損 / 停利 / 加碼硬門檻。
- 不把新聞、題材、外部評論直接接入買點。
- 不做脫離 Telegram 報文的新平台或重型儀表板。
- 不執行正式 Supabase write、production schema apply、live Telegram delivery，除非 Owner 另行批准。

## 驗收重點

- full pytest 通過。
- replay/backfill dry-run 通過且不寫庫。
- DB payload/schema 支援冪等與 point-in-time。
- Telegram `messages[-1]` summary-last 與 `reply_markup` last contract 不回退。
- evidence failure 不阻斷既有 Telegram 報文。
- feature snapshot 不含 future outcome。
- external events 不影響 BUY / `is_tradeable` / `action`。
