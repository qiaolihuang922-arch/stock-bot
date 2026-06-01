# TASK: 修復未持倉過熱降溫卡片 RR 顯示不一致

## 任務狀態

- task_id: normal_patch_unheld_overheat_rr_display
- 任務類型: normal_patch
- 狀態: ready_for_tech
- QA 分級建議: L2
- 版本建議: 使用者可見報文文案格式修正；除非既有版本契約要求，否則不升 VERSION。

## Owner 問題

未持倉標的同為「可準備｜過熱降溫」時，RR 顯示不一致：

- 聯電、華邦電顯示：RR -（過熱）
- 技嘉顯示：RR 0.00（不足）

技嘉的 RR 0.00 來自 calc_rr 結果，但在過熱 / 不可買待降溫狀態下，使用者可見 RR 應優先反映 blocker reason「過熱」，避免同類過熱股混用 0.00（不足） 與 -（過熱）。

## 使用者可見結果

手機 Telegram 報文中，未持倉卡片若分類 / 買點為過熱降溫或不可買待降溫，即使 rr=0.0，也應顯示等價於：

技嘉｜可準備｜過熱降溫
RR -（過熱）

不得顯示：

RR 0.00（不足）

## 非目標

- 不改策略 decision。
- 不改 calc_rr 公式或 RR 計算結果。
- 不改 DB schema、DB write path、production data。
- 不改持倉狀態機、買賣 / 加減碼 / 停損停利建議。
- 不 live Telegram delivery。
- 不做全量報文重排、全量文案清理或策略分類重設。
- 不處理其他非過熱 blocker 的 RR 顯示規則，除非現有契約已涵蓋且為避免回退所必需。

## 影響模組

Tech 需先定位實際未持倉 Telegram 卡片 formatter / message list 產生處與相關 probe / fixture。預期影響範圍限於：

- 未持倉標的卡片 RR 顯示 formatter。
- 對應 Telegram 報文 probe / fixture / snapshot 類測試。

不得擴及策略計算、資料寫入或 live delivery 模組。

## 直接消費者

- Owner 在手機上閱讀的 Telegram 報文。
- 產生 Telegram message list / dry-run output 的 runner。
- 現有報文 probe / regression test。

## 輸出契約

未持倉卡片 RR 顯示優先序需符合：

1. 若未持倉標的目前分類 / 買點 / action-watch 顯示為「過熱降溫」或「不可買待降溫」，且 blocker reason 為「過熱」，使用者可見 RR 顯示必須使用 blocker reason：
- RR -（過熱）
- 或既有同義格式，但必須清楚呈現「過熱」且不可呈現 0.00（不足）。
2. 即使內部 rr / calc_rr 結果為 0.0，上述過熱 blocker 顯示仍優先。
3. 非過熱、非不可買待降溫、非過熱降溫標的的既有 RR 顯示契約不得回退：
- 若既有格式為 RR 0.00（不足），本任務不得改成過熱。
- 若既有格式為有效 RR 數字，本任務不得改變數值、排序或分組。

## 已存在且不得回退的契約

- calc_rr 結果仍可為 0.0，本任務只改使用者可見顯示優先序。
- 未持倉「可準備｜過熱降溫」與「不可買待降溫」不可被呈現成可直接買入。
- 同一未持倉標的的卡片狀態、漏斗 / 分組標題與 RR blocker 文案需一致。
- 無可買時不得因 RR 顯示修正而產生推薦式文案。
- VERSION 不得任意變更；若 repo 既有規則要求使用者可見報文格式修正需升版，Tech 必須同步版本並在 CHANGELOG 說明。

## 驗收條件

1. 新增或更新 probe 覆蓋技嘉類 fixture：
- 未持倉。
- action/watch 狀態顯示為 可準備｜過熱降溫。
- blocker reason 為 過熱。
- rr=0.0。
- 產出的未持倉卡片包含 RR -（過熱） 或既有等價格式。
- 產出的未持倉卡片不包含 RR 0.00（不足）。
2. 至少保留一個非過熱 RR 不足案例，確認仍可顯示既有 RR 0.00（不足） 或原本格式，避免把所有 rr=0.0 都改成過熱。
3. 手機閱讀路徑需核對同一份報文內：
- 分組 / 卡片狀態為過熱降溫。
- RR 顯示 reason 也是過熱。
- 不出現同類過熱股 RR 文案混用。

## 範例 / fixture

輸入形狀示意：

symbol: "2376"
name: "技嘉"
holding: false
action_label: "可準備"
watch_label: "過熱降溫"
blocker_reason: "過熱"
rr: 0.0
calc_rr: 0.0

期望輸出形狀：

技嘉｜可準備｜過熱降溫
RR -（過熱）

禁止輸出形狀：

技嘉｜可準備｜過熱降溫
RR 0.00（不足）

## 明確禁止事項

- 禁止修改策略 decision 或使技嘉從「過熱降溫」變成可買。
- 禁止修改 calc_rr 公式來達成顯示結果。
- 禁止 production DB write / schema / RLS / grant / policy / role / index / constraint 變更。
- 禁止 live Telegram 發送。
- 禁止把本任務擴成全量 Telegram 報文重構。
- 禁止只改文字而不補 probe / regression coverage。
- 禁止用「看起來正常」代替可重跑測試證據。

## 阻塞條件

若 Tech 無法從現有 fixture / formatter 判斷以下任一項，需 blocked 回報 Architect，不得自行假設：

- 哪個欄位是未持倉卡片的權威 blocker reason。
- 「過熱降溫」或「不可買待降溫」在 message payload 中的實際欄位來源。
- 既有 VERSION 契約是否要求本次報文格式修正升版。
- 現有測試環境缺 pytest / 依賴且無法補齊。

## 本輪停止條件

完成範圍到：

- 技嘉類 fixture 可準備｜過熱降溫 + rr=0.0 + blocker=過熱 的未持倉卡片顯示修正。
- 防回退 probe 通過。
- 至少一個非過熱 rr=0.0 案例未被誤改。
- Tech 在 CHANGELOG 提供可重跑命令與結果，QA 以手機閱讀路徑補反證。

以下旁支不納入本輪，若發現只記待辦：

- 其他 blocker reason 的文案優先序重整。
- 全部 RR formatter 命名或架構清理。
- 策略分類是否合理。
- DB 歷史資料或 production 既有報文回補。
