# TASK: v20.4.20 Telegram 第三則 evidence 報文恢復人話分層

## 任務狀態

- task_id: telegram-evidence-human-readable-v20-4-20
- 任務類型: normal_patch
- 狀態: qa_passed
- 版本建議: v20.4.20
- QA 分級建議: L2
- 本輪主 bug: v20.4.19 盤後 Telegram 第三則把內部 evidence slot/schema 直接露出給使用者，且部分卡片 RR / strategy sample 顯示造成可用證據錯覺。

## Owner 問題

Owner 指出 v20.4.19 盤後 Telegram 報文第三則閱讀體驗很糟：

- 第三則直接露出 source/status/use/limit/conflict、英文 source、derived/missing/not-used 等內部 evidence schema。
- 手機閱讀噪音過高，不像盤後簡報。
- 需要先修合理度與衝突呈現：內部 artifact/verifier 保留 100% 能力，但使用者報文不能是 raw slot dump。
- 真正資料衝突仍要用人話說出，不能假裝無衝突。
- 持倉卡 RR 不得再衝突：持倉非加碼情境一律顯示新倉 RR 不適用。
- strategy sample missing/insufficient 不得在卡片中顯示回測數字，避免看起來像可用證據。

## 使用者可見結果

Owner 在手機 Telegram 看第三則時，看到的是「人話簡報 + 資料依據摘要」，不是 evidence schema dump。

手機閱讀路徑：

1. 第一則持倉報文：持倉卡若不是加碼情境，RR 顯示為「新倉 RR 不適用」或等價短句，不顯示新倉 RR 數字。
2. 第二則未持倉 / 非持倉報文：若 strategy sample missing/insufficient，卡片不得用樣本數、勝率、回測 RR 等數字營造可用證據；需顯示不可用 / 不納入判斷。
3. 第三則 evidence 報文：用中文短段落列出資料來源、人話限制、衝突摘要、不可用原因；不得逐 slot 顯示內部欄位名。
4. 第三則摘要若顯示「新倉：無有效進場」，不得同時顯示推薦感的最強標的、排序或評級。

示例輸出形狀：

📌 資料依據與限制

市場與價格：
使用 production 資料；可支援盤後觀察，但不單獨構成買點。

策略樣本：
目前缺少可驗證的策略樣本來源，本次不納入買賣判斷；卡片內不顯示回測數字。

執行記憶：
production ledger 與事件紀錄仍有待釐清的差異；涉及已賣出、已停利或剩餘股數時採保守顯示，不輸出未確認結論。

持倉 RR：
既有持倉若不是加碼情境，只顯示新倉 RR 不適用。

## 非目標

- 不改 DB schema、migration、RLS、grant、policy、role、index、constraint。
- 不寫 production DB、不 backfill、不手寫 DML。
- 不做 live Telegram delivery。
- 不刪除、不弱化 evidence_manifest、maturity artifact、verifier、gate。
- 不回退 v20.4.19 evidence maturity 100 能力。
- 不重設策略、不調整買賣門檻、不改 BUY/SELL decision。
- 不修 production ledger 內容本身。
- 不把 Owner 認知與 production ledger 的差異直接判定誰對誰錯。
- 不清理全 repo、不重構整個報文系統。
- 不處理 Telegram reply markup 附著最後一則 message 的旁支問題。

## 影響模組

Tech 需自行定位實際檔案；預期只限於：

- Telegram 第三則 evidence / short message renderer。
- 持倉卡 RR 顯示 formatter。
- strategy sample missing/insufficient 的卡片顯示 formatter。
- evidence_manifest 到使用者報文的 presentation layer。
- 對應 tests / fixtures。
- 版本常量與報文 header。

不得觸碰：

- production DB write path。
- evidence maturity verifier 的判斷能力。
- read-only artifact schema。
- strategy decision core。
- live Telegram sender。

## 直接消費者

- Owner 手機 Telegram 閱讀者。
- Telegram message list consumer。
- evidence_manifest / maturity artifact / verifier 內部 consumer。
- QA 報文 fixture 驗證。
- Architect 收口版本與 gate 檢查。

## 已存在且不得回退的契約

- Telegram message list 順序維持：messages[0] 持倉、messages[1] 未持倉 / 非持倉、messages[2] short/evidence；include_detail=True 時 Details Backup 追加最後。
- v20.4.19 已建立的 evidence_manifest / maturity artifact / verifier 100% 能力不得刪除或降級。
- structural/maturity artifact 內部仍可保留 source/status/use/limit/conflict 等 machine-readable 欄位。
- read-only artifact 安全旗標不得回退：schema_change=false、data_write=false、live_telegram=false、credential_values_included=false。
- 缺資料、source-error、insufficient-data、unresolved-conflict 必須 fail closed。
- strategy sample 不可用時不得納入買賣判斷。
- market/theme 只能作背景，不等於買點。
- 報文版本不得回退到 v20.4.19 或更早；本輪使用者可見報文變更建議升至 v20.4.20。
- 若 Tech 發現現有實作契約與本 TASK 衝突，必須 blocked 回報，不得自行破壞內部 artifact/verifier。

## 輸出契約

### A. 第三則 Telegram Evidence Presentation Contract

第三則使用者可見報文必須：

- 使用中文人話段落或短 bullet。
- 顯示資料依據、限制、不可用原因與衝突摘要。
- 若結論是新倉無有效進場，`🔥 最強` 必須顯示無有效進場標的；不得顯示僅追蹤、不可行動或 source 不合格標的名稱與排序/評級。
- 對真正衝突顯示人話摘要，例如：
- production ledger 與 Owner 認知待釐清
- strategy sample 缺來源，本次不納入判斷
- ledger insufficient/unresolved，採保守顯示
- 不得逐筆 dump internal slot。
- 不得顯示裸欄位名作為主內容：source:、status:、use:、limit:、conflict:。
- 不得顯示 raw internal status 作為使用者句子：derived、missing、not-used、missing-source、insufficient-data、unresolved-conflict，除非被中文翻譯或包成人話說明。

內部 artifact 可繼續保留上述欄位與 raw status；限制只針對 Telegram 使用者可見報文。

### B. Conflict Summary Contract

當 evidence_manifest/artifact 有真衝突或缺資料時，第三則不得沉默，需轉成中文摘要：

- strategy sample missing-source -> 策略樣本缺可驗證來源，本次不納入買賣判斷
- strategy sample insufficient-data -> 策略樣本不足，本次不納入買賣判斷
- ledger insufficient-data -> 執行記憶不足，涉及已賣/停利/剩餘股數採保守顯示
- ledger unresolved-conflict -> ledger 與事件紀錄仍有衝突，未確認部分不輸出確定結論
- production ledger vs Owner 認知 -> production ledger 與 Owner 認知待釐清，本報文先以 production source 保守呈現

### C. 持倉 RR Display Contract

持倉卡 RR 顯示規則：

- 若標的是既有持倉且本卡主行動不是「加碼」或明確新倉評估，不得顯示新倉 RR 數字。
- 顯示為：新倉 RR：不適用（既有持倉） 或等價短句。
- 不得出現像建準案例的衝突顯示：持倉非加碼卻顯示 RR 2.73。
- 加碼情境若現有策略已有明確新倉 / 加碼 RR contract，可保留；若 Tech 無法確認 contract，先 blocked，不要自行發明加碼規則。

### D. Strategy Sample Card Contract

當 strategy sample source 是 missing / insufficient / unavailable：

- 卡片不得顯示會被理解為可用證據的回測數字，例如勝率、樣本數、回測 RR、平均報酬。
- 顯示為：策略樣本：不可用，本次不納入判斷 或等價短句。
- 第三則 evidence 需同步用人話說明不可用原因。
- 內部 artifact/verifier 仍保留 raw status 與完整欄位。

## 驗收條件

1. 第三則人話報文

- 使用 v20.4.20 fixture 產生 Telegram messages。
- messages[2] 不包含 raw slot dump。
- messages[2] 不出現裸欄位名：source:、status:、use:、limit:、conflict:。
- messages[2] 不直接露出 raw status：derived、missing、not-used、missing-source、insufficient-data、unresolved-conflict。
- 有資料缺失或衝突時，messages[2] 有中文人話摘要，沒有假裝無衝突。
- 當 messages[2] 顯示「新倉：無有效進場」時，不得同時顯示 `最強：<標的>`、排序★或評級★。

2. 內部 evidence 能力不回退

- maturity artifact / verifier 標準命令仍可跑。
- evidence_manifest 內部仍保留 machine-readable 欄位。
- verifier 對 missing-source / insufficient-data / unresolved-conflict 仍 fail closed。
- read-only artifact 安全旗標仍存在且為 false。
- 不因隱藏 raw slot dump 而刪除內部欄位。

3. 持倉 RR 顯示

- fixture 覆蓋「既有持倉 + 非加碼」。
- 持倉卡顯示 新倉 RR 不適用 或等價短句。
- 不顯示 RR 2.73 這類新倉 RR 數字。
- 不改策略 decision，只改使用者可見顯示。

4. Strategy sample 不可用顯示

- fixture 覆蓋 missing-source 與 insufficient-data 至少一種。
- 卡片不顯示回測數字作為可用證據。
- 卡片顯示不可用 / 不納入判斷。
- 第三則同步摘要不可用原因。

5. 手機閱讀檢查

- QA 必須檢查第三則在手機閱讀下首屏/短段落可讀，不是長表格或 raw schema。
- QA 至少補一個 Tech 未覆蓋的反證：例如內部 artifact 仍含 raw fields，但 Telegram text 不含 raw dump。

## 範例或 fixture

Tech 至少建立或更新以下 fixture：

### Fixture 1: third-message-raw-slot-hidden

輸入條件：

- evidence_manifest 含 source/status/use/limit/conflict。
- 至少一筆 strategy sample missing-source。
- 至少一筆 ledger unresolved-conflict。

期望：

- 內部 artifact 保留 raw fields。
- Telegram messages[2] 顯示中文摘要。
- Telegram messages[2] 不含 raw slot dump。

### Fixture 2: holding-non-add-rr-not-applicable

輸入條件：

- 標的是既有持倉。
- 主行動不是加碼。
- 系統可計算或曾傳入新倉 RR，例如 2.73。

期望：

- 持倉卡顯示 新倉 RR 不適用。
- 不顯示 2.73 作為持倉 RR。
- strategy decision 不變。

### Fixture 3: strategy-sample-unavailable-card

輸入條件：

- strategy sample status 為 missing-source 或 insufficient-data。
- 原資料中可能存在 synthetic/sample/backtest 數字。

期望：

- 卡片顯示不可用 / 不納入判斷。
- 不顯示勝率、樣本數、回測 RR 等像可用證據的數字。
- 第三則以中文說明不可用原因。

## 明確禁止事項

- 禁止刪除 evidence maturity verifier。
- 禁止降低 maturity report / artifact schema 能力。
- 禁止把內部 artifact 改成人話而失去 machine-readable 欄位。
- 禁止用隱藏衝突的方式改善報文可讀性。
- 禁止把 missing-source / insufficient-data 包裝成可用證據。
- 禁止改 BUY/SELL/加減碼/停利停損策略決策。
- 禁止改 DB schema 或 production write path。
- 禁止 live Telegram delivery。
- 禁止手寫 production DML。
- 禁止把本輪擴成全報文重構、策略重設或 ledger 修復。

## 阻塞條件

Tech 必須 blocked，而不是自行假設，若遇到：

- 無法辨識第三則 Telegram renderer 與內部 artifact renderer 的分層位置。
- 無法確認加碼情境是否有既有 RR 顯示 contract。
- 現有 tests/fixtures 無法產生三則 messages。
- maturity artifact/verifier 標準命令缺失或無法跑。
- 修第三則必須刪除 evidence_manifest raw 欄位才做得到。
- 需要 DB schema/write/live Telegram 才能驗證。
- production ledger vs Owner 認知需要判定真相才能繼續；本輪只要求人話顯示待釐清，不修資料。

## 本輪停止條件

完成定義：

- v20.4.20 報文第三則不再顯示 raw evidence slot dump。
- 內部 evidence_manifest / maturity artifact / verifier 100% 能力保留。
- 真衝突與缺資料用中文摘要顯示。
- 持倉非加碼 RR 顯示不適用。
- strategy sample missing/insufficient 不在卡片中呈現為可用回測證據。
- QA L2 覆蓋手機閱讀、內部 artifact 不回退、至少一個反證案例。

不納入本輪，需另開待辦：

- production ledger 資料修復或 Owner 認知對帳。
- strategy sample source-of-truth 補資料。
- 買賣策略合理度重設。
- Telegram reply markup 落點調整。
- 全報文文案重構。
- DB / runner / GitHub Actions 大型流程重構。
