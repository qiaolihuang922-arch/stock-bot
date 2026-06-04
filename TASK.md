# TASK: v20.4.41 修正 2026-06-04 盤後 v20.4.40 未持倉 gate attribution 可讀性

## 任務狀態

- task_id: v20.4.41-post-market-unheld-gate-attribution-readability
- 任務類型: tiny_patch
- 狀態: ready_for_tech
- 版本建議: v20.4.41
- QA 分級: L1
- 任務日期: 2026-06-04

## Owner 問題

2026-06-04 盤後 v20.4.40 未持倉報文中，gate attribution 的手機閱讀語意不清：

- 真正可買卡與 trend_continuation 小倉 BUY 卡仍顯示「到達可買差距」，造成可行動狀態被誤讀成仍未達標。
- FAILED_BREAKOUT 顯示 RR 0/需>=1.5，但此狀態真正原因是突破失敗，應要求重新轉強。
- post-market ordinary prepare 顯示「證據：資料不足」，與盤後情境不符，應表達為盤後待確認。
- EXTREME / HOT 過熱狀態同時列 RR 或 entry quality 次因，手機閱讀上會稀釋主因。
- raw enum EXTREME / HOT / LIMIT_LOCK / LIMIT_REBOUND / WEAK_REBOUND 外露，降低報文可讀性。

## 使用者可見結果

在 v20.4.41 official Telegram message list replay 中：

- 只有未達可買條件的未持倉卡片可顯示「到達可買差距」。
- 真正可買卡與 trend_continuation 小倉 BUY 卡不得顯示「到達可買差距」。
- FAILED_BREAKOUT 卡片不顯示 RR 0/需>=1.5，只顯示「突破失敗/需重新轉強」或等價可讀文案。
- post-market ordinary prepare 卡片顯示「盤後訊號/需開盤後重新確認」；數據行不得顯示「證據：資料不足」，改為「盤後待確認/需開盤後重新確認」或等價文案。
- EXTREME / HOT 過熱解除前只顯示「極熱/需降溫」或「過熱/需降溫」，不得再列 RR / entry quality 次因。
- raw enum EXTREME / HOT / LIMIT_LOCK / LIMIT_REBOUND / WEAK_REBOUND 不得出現在使用者可見報文。

## 非目標

- 不改策略決策。
- 不改 RR 計算。
- 不改 can_buy。
- 不改 is_valid_entry。
- 不改 DB schema、DB read/write、RLS、grant、policy、role。
- 不做 live Telegram delivery。
- 不調整持倉建議、買賣 / 加減碼、停損停利策略。
- 不新增新的候選分類或交易行動。

## 影響模組與直接消費者

影響模組：

- official Telegram formatter / message list 產生路徑。
- 未持倉卡片 gate attribution 顯示邏輯。
- post-market prepare 顯示文案。
- enum-to-user-facing-label 顯示轉換。

直接消費者：

- Owner 手機閱讀的 Telegram 盤後報文。
- formatTelegramMessages official message list replay。
- QA replay artifact / message-list assertion。

## 輸出契約

報文版本：

- 使用者可見版本必須為 v20.4.41。

message list contract：

- 驗收必須走 official formatTelegramMessages / message-list replay，不得只驗 helper fixture。
- replay output 必須能檢查每張未持倉卡的 title/status/reason/data lines。

gate attribution contract：

- 「到達可買差距」只允許出現在非可買、可準備、僅追蹤、淘汰等未達可買條件卡片。
- BUY / 真正可買 / trend_continuation 小倉 BUY 卡片不得出現「到達可買差距」。

failed breakout contract：

- FAILED_BREAKOUT 可見主因只呈現突破失敗與需重新轉強。
- 不得顯示 RR 0/需>=1.5 或等價 RR failure 文案。

post-market ordinary prepare contract：

- 主狀態顯示「盤後訊號/需開盤後重新確認」。
- 數據行不得顯示「證據：資料不足」。
- 數據行改顯示「盤後待確認/需開盤後重新確認」或等價清楚文案。

overheat contract：

- EXTREME 顯示「極熱/需降溫」。
- HOT 顯示「過熱/需降溫」。
- 過熱解除前不得列 RR / entry quality 次因。

enum visibility contract：

- 使用者可見報文不得包含 raw enum：
  - EXTREME
  - HOT
  - LIMIT_LOCK
  - LIMIT_REBOUND
  - WEAK_REBOUND

## 版本契約

- 必須升版至 v20.4.41。
- Telegram header / formatter version constant / replay artifact 中的可見版本必須一致。
- 不得回退至 v20.4.40 或其他版本。
- 本輪是可見報文文案與 attribution 顯示修正，不代表策略版本或 DB 契約變更。

## 驗收條件

1. official formatTelegramMessages / message-list replay 產出版本為 v20.4.41。
2. replay 中真正可買卡與 trend_continuation 小倉 BUY 卡不含「到達可買差距」。
3. replay 中至少一張未達可買條件卡仍可在合適情境顯示「到達可買差距」，證明不是全域刪除。
4. FAILED_BREAKOUT replay 卡不含 RR 0/需>=1.5 或等價 RR failure 文案，且含「突破失敗/需重新轉強」或等價文案。
5. post-market ordinary prepare replay 卡含「盤後訊號/需開盤後重新確認」，且不含「證據：資料不足」。
6. post-market ordinary prepare 的數據行含「盤後待確認/需開盤後重新確認」或等價文案。
7. EXTREME / HOT replay 卡只顯示「極熱/需降溫」或「過熱/需降溫」，且不列 RR / entry quality 次因。
8. replay 完整輸出不含 raw enum EXTREME / HOT / LIMIT_LOCK / LIMIT_REBOUND / WEAK_REBOUND。
9. QA 必須從手機閱讀路徑檢查跨區塊語意：分組標題、卡片狀態、漏斗 / 詳情不得互相矛盾。
10. Tech 自檢不得只測 helper；若只能測到 helper 或局部 formatter，CHANGELOG 必須標 partial 並列出未覆蓋 official message-list replay。

## 範例或 Fixture

失敗標本：

- 2026-06-04 盤後 v20.4.40 未持倉 official Telegram 報文。

最小 replay fixture 需覆蓋：

- 真正可買卡。
- trend_continuation 小倉 BUY 卡。
- 非可買 / 可準備 / 僅追蹤 / 淘汰中至少一張未達可買條件卡。
- FAILED_BREAKOUT 卡。
- post-market ordinary prepare 卡。
- EXTREME 卡。
- HOT 卡。
- 含 LIMIT_LOCK / LIMIT_REBOUND / WEAK_REBOUND 原始分類輸入但輸出不得外露 raw enum 的卡。

## 明確禁止事項

- 禁止修改策略決策、RR、can_buy、is_valid_entry。
- 禁止修改 DB schema / RLS / grant / policy / role / DB write path。
- 禁止 live Telegram delivery。
- 禁止用 synthetic helper fixture 取代 official formatTelegramMessages / message-list replay 作為完成證據。
- 禁止把「到達可買差距」全域刪除；它仍應出現在未達可買條件的卡片。
- 禁止讓 raw enum 出現在任何使用者可見 Telegram 報文。
- 禁止把缺資料、缺 replay artifact 或 source-error 宣告為通過。

## 阻塞條件

- 找不到 2026-06-04 盤後 v20.4.40 等價 replay payload 或 official message-list replay route。
- official formatTelegramMessages / message-list replay 無法執行，且無等價 artifact 可驗。
- 無法判定哪些卡是真正可買 / trend_continuation 小倉 BUY / 未達可買條件。
- 修正需要改策略決策、RR、can_buy、is_valid_entry、DB 或 live delivery。
- 版本常量與 Telegram header 無法同步到 v20.4.41。

## 本輪停止條件

- TASK.md 已完整定義 v20.4.41 報文可讀性修正範圍。
- Tech 可依本任務卡修改 formatter / message-list 顯示邏輯與測試。
- QA 可用 official formatTelegramMessages / message-list replay 反證 Owner failure specimen。
- 若 replay route 或 failure specimen 缺失，本輪不得進入實作通過結論，必須回報 blocked。
