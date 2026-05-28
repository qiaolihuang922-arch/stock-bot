# RESEARCH.md

本文件保存最新研究任務的高信號摘要，不保留完整聊天紀錄、終端流水或長表格。

## Latest Research

- task_id: `20260528_120657_23719_online_research_pair`
- 日期：2026-05-28
- 狀態：Architect 已吸收為市場 / 題材證據鏈方向。
- 來源輸出：`/Users/liveroom/stock-bot-agent-context/outputs/20260528_120657_23719_online_research_pair.md`

## Question

Owner 指出：`v20.0.12` 只是防止無證據硬寫市場主線的保護邏輯，不是真正市場 / 題材證據鏈。研究問題是如何為 Telegram 報文建立可追溯的市場主線 / 題材證據鏈，且不做 live Supabase write、正式 backfill、live Telegram，不改策略決策。

## Evidence Sources

- 內部 watchlist：價格、量能、策略分類、買點是否成立、snapshot / strategy evidence。
- 市場 / 類股：TAIEX、電子類、科技 / 半導體相關指數。
- flow：法人買賣超、外資持股或產業持股比。
- 官方 / 公司資料：TWSE、MOPS、MOEA、MOF、TSMC IR、NVIDIA IR 等。
- 外部產業資料只能作背景，不得單獨推出今日可買或個股交易行動。

## Product Findings

- 報文若要出現市場 / 題材判斷，必須證明三層：
  - 市場層：大盤 / 電子 / 科技或半導體相關指數是否支持偏多。
  - 題材層：watchlist 內相關標的是否多數維持強勢、量能、分類未惡化。
  - 執行層：即使市場或題材偏多，個股買點、RR、回測、冷卻與風控是否成立。
- 需要 evidence 才可出現的高風險詞句：
  - `AI / 電子供應鏈仍偏多`
  - `市場主線仍在`
  - `題材仍可追蹤`
  - `不代表看空產業`
  - `市場偏多但買點未成立`
  - `主線持倉保留`
- 缺 evidence 時必須降級為：
  - `市場證據不足，僅依策略分類追蹤`
  - `題材未確認，等待價格與量能證據`
  - `本輪技術條件未成立，未判斷產業多空`
  - `新倉：無有效進場`

## Evidence Levels

- `confirmed`：至少兩類來源同向且未過期，例如 watchlist 題材 breadth + 市場 / 類股指數。
- `weak`：只有單一來源、樣本太小或證據不完整，只能寫可追蹤。
- `absent`：沒有足夠證據，不得寫主線偏多。
- `stale`：資料超過 freshness 門檻，必須標示過期並降級。
- `mixed`：官方 / 外部背景偏強但 watchlist breadth 或策略分類不支持，只能寫背景，不得 confirmed。

## Technical Direction

- 第一階段採 dry-run / payload contract，不建表、不寫庫。
- formatter 只能引用有 `source_type / source_name / as_of / level / freshness / limitations` 的 evidence。
- `market_theme_evidence` 建議欄位：
  - `as_of`
  - `level`
  - `theme`
  - `market_direction`
  - `execution_implication`
  - `sources[]`
  - `supports_claims[]`
  - `limitations[]`
  - `formatter_allowed_phrases[]`
  - `formatter_forbidden_phrases[]`
- 如果要做 production confirmed，需至少接入第二類 runtime source；若涉及 DB table、cache、scheduler、external provider，先通知 Owner。
- evidence 不得接入策略 decision；只能影響報文文字與證據區塊。

## QA Risks

- 無 evidence 時不得硬寫 AI / 電子供應鏈偏多。
- stale evidence 不得當 confirmed。
- 非 AI 場景不得誤貼 AI。
- 產業背景強但 watchlist breadth 弱時，只能 weak / mixed。
- market/theme confirmed 仍不得讓 `新倉` 顯示可買，除非原策略買點成立。
- 手機第一屏必須先看到 evidence 等級與行動限制，不是先看到主線口號。

## Architect Conclusion

- Owner 判斷正確：文案 guard 不是證據鏈。
- 證據鏈應逐步推進：
  - 已完成 dry-run helper 與 structured provider adapter。
  - 下一步若要 production confirmed，需要新增 runtime source；如需建表 / cache / external provider，先通知 Owner。
- 報文硬邊界：
  - `AI / 電子供應鏈仍偏多` 必須有 AI 題材 watchlist 廣度 + 市場 / 類股 / 產業至少一類佐證。
  - 無產業證據時，不寫 `不代表看空產業` 安撫句，只寫 `未判斷產業多空`。
  - 市場 / 題材偏多不得推導成可買，必須同屏顯示買點是否成立。

## Next Action

- 若 Owner 要繼續證據鏈 production 化，先分派 PM 定義 source、freshness、cache / schema 邊界與驗收條件。
- 暫不改 DB schema、策略 decision、live Telegram、live Supabase write、正式 backfill。
