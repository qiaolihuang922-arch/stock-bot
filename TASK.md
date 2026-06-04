# TASK: 修正 v20.4.37 RR不足/等RR修復 報文可讀性

## 任務狀態

- task_id: fix-v20-4-37-rr-insufficient-message-readability
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見報文契約有變更，建議升版 v20.4.38；不得回退 v20.4.37
- QA 分級建議: L2

## Owner 問題

Owner 貼出的 2026-06-04 盤中 v20.4.37 完整報文中，光寶科卡片狀態是：

👀 等RR修復｜RR不足

但同一卡片數據行顯示：

RR 0.98｜不適用（RR不足）｜證據：資料不足｜V 0.86x

手機閱讀時會把「證據：資料不足」誤讀成資料源缺失，而實際主因是 RR 不足 / 等 RR 修復。

同一份 summary 又列出：

- 回測（建準）...偏弱
- 回測（光寶科）...偏弱

但光寶科目前是 等RR修復 / 僅追蹤，不是可買或不可追高候選。summary 的回測句會讓使用者誤以為光寶科接近可買。

## 使用者可見結果

手機閱讀 v20.4.38 報文時：

- 光寶科若狀態為 等RR修復｜RR不足，同一卡片 evidence/reason 不得顯示成像資料源缺失的 證據：資料不足
- RR 不足原因要明確指向「RR不足 / 等RR修復」，不是資料缺漏
- summary 回測摘要不得把 等RR修復 / 僅追蹤 標的寫得像可買候選或接近可買候選
- 可買、不可追高、僅追蹤/等RR修復 的語意在 summary 與卡片內一致

## 非目標

- 不改策略 decision
- 不改 RR 公式
- 不改篩選門檻
- 不改 DB schema / RLS / grant / policy / role
- 不新增或修改 DB write path
- 不 live Telegram delivery
- 不處理交易執行排序，除非該排序直接阻塞本輪 replay 驗收
- 不做全量報文重構
- 不清理 unrelated formatter 文案

## 影響模組與直接消費者

影響模組：

- Telegram 報文 formatter
- final message-list 組裝路徑
- summary 回測摘要輸出路徑
- 版本字串/header 常量，如本 repo 有集中版本定義

直接消費者：

- Owner 手機 Telegram 報文
- formatTelegramMessages 的 official output
- actual generate() final message-list
- QA replay artifact / snapshot 類驗收輸出

## 輸出契約

已存在且不得回退的契約：

- 報文不得回退到低於 v20.4.37
- 光寶科原 decision/state 不得被本任務改成可買、不可追高、淘汰或其他策略結果
- RR 0.98、V 0.86x 等既有數值不得因 formatter 修正被重新計算
- 👀 等RR修復｜RR不足 這類狀態語意必須保留
- 無可買時不得用像推薦的 summary 文案
- 空區塊、0-count、無新增下單占位預設不顯示

本輪可改的使用者可見契約：

- 當標的狀態為 等RR修復｜RR不足 時，卡片 evidence/reason 文案需改為明確 RR 原因，例如形狀：
- RR 0.98｜不適用（RR不足）｜原因：RR不足，等待RR修復｜V 0.86x
- 或等價短句，但不得出現會被理解為資料源缺失的 證據：資料不足
- summary 回測摘要只可列入可買 / 不可追高等實際候選語境；若列入僅追蹤標的，必須明確標成僅追蹤，不得像候選建議
- 若光寶科仍屬 等RR修復 / 僅追蹤，summary 示例形狀應偏向：
- 僅追蹤：光寶科 RR不足，等待RR修復
- 不應是：
- 回測（光寶科）...偏弱

## 版本契約

- 若 Tech 修改任何使用者可見報文文案、summary 行為或 header 顯示，版本需升為 v20.4.38
- 不得回退 v20.4.37
- 若 repo 內存在多處版本常量，Tech 必須同步到 final Telegram header 實際輸出；若無法確認版本來源，需 blocked

## 驗收條件

1. 使用 Owner 2026-06-04 盤中 v20.4.37 完整報文的等價 replay payload，打到 official formatTelegramMessages 或 actual generate() final message-list；不得 helper-only。
2. replay 後光寶科卡片仍為 👀 等RR修復｜RR不足 或等價狀態，但同一卡片不得再出現 證據：資料不足 這種資料源缺失語意。
3. replay 後 summary 不得把 回測（光寶科）...偏弱 放在會被手機閱讀成可買/不可追高候選的位置；若保留光寶科，必須明確標為僅追蹤 / 等RR修復。
4. replay 後建準既有 summary 回測語意不得被本任務誤刪或改成光寶科同類錯誤；只修本輪主 bug。
5. final message-list/header 顯示版本為 v20.4.38，或 Tech 明確證明本 repo 報文版本不由該 formatter 控制並 blocked 給 Architect。
6. QA 必須至少補一個手機閱讀路徑反證：檢查 summary 與光寶科卡片連讀時，不會把光寶科誤讀成接近可買或資料缺失。

## 範例或 Fixture

失敗標本：

- Owner 貼出的 2026-06-04 盤中 v20.4.37 完整報文
- 關鍵可見矛盾：
- 光寶科卡片：👀 等RR修復｜RR不足
- 光寶科數據行：RR 0.98｜不適用（RR不足）｜證據：資料不足｜V 0.86x
- summary：回測（光寶科）...偏弱

最小 replay fixture 要求：

- 必須能產生 final Telegram message-list
- 必須包含光寶科的 RR不足/等RR修復狀態
- 必須包含 summary 回測摘要資料
- 必須包含建準與光寶科，避免只驗單一卡片 formatter

示例輸出形狀：

- 光寶科卡片：
- 👀 等RR修復｜RR不足
- RR 0.98｜不適用（RR不足）｜原因：RR不足，等待RR修復｜V 0.86x
- summary：
- 可買/不可追高候選只列真正候選
- 光寶科若出現，只能在僅追蹤語境：僅追蹤：光寶科 RR不足，等待RR修復

## 失敗標本與驗收路由

- 失敗層級: final Telegram 報文可讀性，不是 helper 層
- 驗收路由優先序:
1. actual generate() final message-list replay
2. official formatTelegramMessages replay
3. 若 1/2 缺必要 runtime source，Tech 必須產出等價 replay artifact，並標明缺哪個 source；QA 結論最多 conditional pass
- 禁止只用 synthetic helper fixture 宣告完成

## 明確禁止事項

- 禁止修改策略 decision 讓光寶科變成可買或不可追高來掩蓋文案問題
- 禁止修改 RR 計算或門檻
- 禁止把所有 資料不足 全域替換，需限定 RR不足/等RR修復 語境
- 禁止改 DB schema/write
- 禁止 live Telegram
- 禁止將 Owner 的「直接修」解讀為跳過 Tech / QA
- 禁止把 unrelated 交易排序、全量清理、報文重構納入本輪

## 阻塞條件

- 找不到 Owner 完整報文或等價 replay payload，且無法打到 final message-list
- 無法確認 final Telegram 版本字串來源
- replay 只能打 helper，無法覆蓋 official formatter 或 actual generate path
- 修正必須改策略 decision、RR 公式或 DB schema 才能達成
- 測試環境缺依賴且無法補齊

## 本輪停止條件

完成定義：

- Tech 修正 formatter/message-list
- replay 打到 official formatTelegramMessages 或 actual generate() final message-list
- QA 以 Owner 等價 replay 反證通過
- commit / push 完成
- git completion gate 通過

旁支不納入本輪：

- 其他股票的回測品質判斷
- 交易執行排序
- 歷史資料補洞
- DB 持久化設計
- 報文整體資訊架構重設
- 全 repo 清理或重構
