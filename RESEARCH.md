# RESEARCH.md

本文件保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Latest Research

- task_id: `v20-strategy-intelligence-architecture`
- 日期：2026-05-26
- 狀態：已完成，已進入並完成 `v20.0 Strategy Evidence Foundation`
- 對應 commit：`2cc4e8a feat: add v20 strategy evidence foundation`

## Question

Owner 質疑策略層過於簡單：旺宏 2337 從約 140 漲到約 160，但策略連續輸出淘汰。問題不是單一股票，而是整體策略缺少多日資料、外部事件、事後績效驗證與可反證資料層。

## Evidence

- 旺宏案例顯示：不追高可能合理，但 `弱勢淘汰` 可能錯誤壓縮「強題材 + 高波動 + 注意股」。
- 現有策略可產生報文，但缺少回答下列問題的資料：
  - `淘汰` 後是否經常大漲。
  - `等回測` 是否真的等到更好風報。
  - `RR不足` 是否真的比追價安全。
  - `可買` 是否比不可買追蹤組有更佳 MFE / MAE / 相對報酬。

## PM Findings

- v20 不應先調買賣門檻，而應先建立策略證據基礎。
- Telegram 應新增簡短 `📊 策略證據` 摘要。
- 外部新聞 / 題材可作研究資料，但不得直接產生 BUY。
- 旺宏類應先進 classification audit，而不是直接改成可買。

## Tech Findings

- 可在現有流程內新增：
  - `market_daily_bars`
  - `strategy_feature_snapshots`
  - `strategy_outcome_metrics`
  - `strategy_classification_audit`
  - `market_events` schema 草案
- replay/backfill dry-run 可支援 evidence row 計算。
- Telegram summary 可消費 evidence summary，不需要新平台。

## QA Findings

- Conditional approval：可進入 v20.0 `Strategy Evidence Foundation`。
- 第一版不得修改 BUY / SELL / RR / heat / stop / take-profit / add 門檻。
- 必須檢查 point-in-time、防未來資料洩漏、外部資料不接 BUY、evidence failure 不阻斷報文。
- QA L3 必須包含 full pytest、replay/backfill dry-run、DB payload/schema、Telegram contract、策略不變性。

## Architect Conclusion

v20 策略智能層應分階段：

1. v20.0：策略證據資料層與分類績效報告。
2. v20.1+：production schema apply / retention / live write 流程。
3. 後續：外部事件 ingestion、分類 taxonomy 重構。
4. 最後：基於數據回測調整策略門檻。

v20.0 已完成並推送。下一步若 Owner 要啟用 production DB schema 或 live evidence write，需另開批准任務。
