# TASK: intraday_20260601_report_sequence_execution_memory_noise_v20_4_11

## 任務狀態

- task_id：intraday_20260601_report_sequence_execution_memory_noise_v20_4_11
- 任務類型：risk_patch
- 狀態：ready_for_tech
- 版本建議：使用者可見 Telegram 報文與持倉狀態風險修正，需升版到高於 v20.4.10，建議 v20.4.11；不得回退版本。
- QA 分級建議：L2，必須驗完整 2026-06-01 類盤中報文 sequence、2356 execution memory / holdings source truth、手機噪音壓縮。若 Tech 需要改 BUY/SELL/停利停損策略決策、DB write path、schema 或 live delivery，升為
blocked，不得自行擴大。
- 本輪主問題：2026-06-01 盤中 Telegram 報文在手機閱讀順序、2356 英業達跨日 execution memory、噪音資訊密度三處造成錯誤或誤讀風險。
- 本輪停止條件：完整 06/01 類報文的 message list 順序、2356 持倉 / execution-memory 判斷、主文噪音壓縮都符合本任務契約；不處理策略重設、DB schema、production DML、live Telegram delivery、全報文重設或其他股票的新交易邏
輯。

## Owner 問題

Owner 提供 2026-06-01 盤中 v20.4.10 Telegram report，指出三個問題：

1. 報文主體 / details 的發送順序看起來錯亂，手機閱讀時像是 Summary、主體、細節互相碎片化。需要明確定義並修正最終 Telegram message sequence，讓使用者從手機可以順讀。
2. 2356 英業達看起來尚未賣出，但報文仍帶有上週第二段停利或 execution-memory 舊邏輯。必須以 production DB 的目前持倉與 execution ledger 驗證，防止 stale / false second take-profit state。
3. 報文噪音太多，source、evidence、backtest、detail 行過密。需要壓縮非決策關鍵噪音，但保留決策必要資訊與 DB/source truth。

## 使用者可見結果

手機閱讀路徑需固定為：

1. 第一則：決策摘要，只回答今天要不要買、持倉先處理什麼、新倉是否有效、資料可信狀態。
2. 中間則：可行動主體，包括持倉卡、新倉分組、僅追蹤 / 不可行動清單。
3. 倒數第二則：壓縮後的 evidence/source 摘要，只保留 decision-critical source truth、缺源與 fail-closed 原因。
4. 最後一則：details / backup / debug-like 診斷摘要。若沒有必要細節，最後一則不得硬塞空區塊或重複長句。

使用者在 Telegram 手機上從上往下讀，應先看懂決策，再看原因；滑到最後時只看到備查細節，不會被 source/backtest 長行淹沒，也不會把 2356 誤讀成已完成第二段停利或應再賣一次。

## 非目標

- 不改 BUY / SELL / HOLD / 加碼 / 減碼 / 停利 / 停損策略判斷。
- 不改 2356 以外股票的交易狀態機，除非是共用 formatter 防 stale source 的必要防護。
- 不新增或修改 DB schema、RLS、grant、policy、role、index、constraint。
- 不手寫 production DML，不做 backfill，不做 live Telegram delivery。
- 不重設整份報文設計，不新增大型 UI / renderer 架構。
- 不刪除 source truth / evidence manifest；只壓縮使用者主文呈現。
- 不把 local cache、runtime dict、agent 對話或上週報文當跨日 execution memory。

## 影響模組

預期影響範圍：

- Telegram report generator / message builder / formatter。
- Telegram message list ordering。
- 持倉卡與 execution-memory 顯示邏輯。
- source/evidence/backtest/detail 的使用者可見文案壓縮。
- 報文版本字串。
- 對應完整報文 fixture / snapshot / generator tests。

不得影響：

- DB schema 或 write path。
- production live delivery。
- replay/backfill 寫庫流程。
- strategy decision engine 的買賣判斷。
- 既有 readonly source interface 的語意。

## 直接消費者

- Owner 手機閱讀 Telegram 盤中報文。
- production report / Telegram message rendering path。
- QA 用完整 06/01 類報文驗證 message sequence、2356 source truth、噪音壓縮。
- 下游人工依報文判斷持倉處理與新倉是否可行動。

## 已存在且不得回退的契約

- 目前使用者可見報文版本為 v20.4.10；本輪只能升版，不得回退。
- positions 是目前持倉 source-of-truth。
- position_events 是已買 / 已賣 / 已停利 / 已減碼 execution ledger；跨日防重必須用它。
- production DB 或 Owner 指定持久來源才可作跨日 execution memory。
- 持倉 source 或 execution ledger 缺失時必須 fail closed，顯示記憶不足 / source 不足，不得輸出已賣股數或第二段停利完成。
- 同一持倉在同一份報文只能有一個主行動。
- 無可買時必須顯示「新倉：無有效進場」或等價不可買文案，不得寫成推薦。
- 缺資料、source-error、欄位不足或可信度不足時 fail closed。
- market/theme evidence、strategy sample evidence、stock decision 三層保持分離。
- DB contract、payload write shape、live delivery 行為不得因本輪變更而改變。

若 Tech 無法確認上述契約的實作位置或 readonly query/source，必須 blocked，請 Architect 補充 production read-only artifact；不得自行假設。

## 輸出契約

### Telegram Message List 順序

完整報文輸出必須是有序 message list，順序固定：

1. summary_message
- 版本、報告時間 / 資料交易日。
- 持倉首要處理。
- 新倉是否有有效進場。
- source health 一行摘要。
2. action_body_message
- 持倉卡，每檔一個主行動。
- 新倉分組：可買 / 可準備 / 僅追蹤 / 不可行動。
- 不顯示空 0-count 區塊。
3. evidence_compact_message
- 只列 decision-critical source：holdings、execution_memory、price、risk、candidate source。
- backtest / sample / source table 不得逐欄展開成長噪音；需壓成狀態行。
4. details_backup_message
- 只放必要備查診斷、被 fail-closed 的原因或 QA 可回查摘要。
- 若無 details，允許省略；不得用重複長句填滿。

Tech 必須在 CHANGELOG.md 寫明實際 message list order 與每則 message 的 consumer 目的。

### 2356 英業達持倉 / Execution Memory 契約

2356 的顯示必須同時讀取並比對：

- current holding source：production positions 或既有 readonly position interface。
- execution memory source：production position_events 或既有 readonly execution ledger interface。
- report as-of time / trade_date。

判斷規則：

- 若 positions 顯示仍有 2356 持倉，且 position_events 沒有可確認第二段停利已賣出的 event，報文不得顯示第二段停利已完成或沿用上週已執行狀態。
- 若 position_events 有第二段停利 event，但 positions 仍顯示剩餘股數，報文需顯示「已執行部分 / 剩餘續抱」或現有等價語意，不得讓使用者誤讀成全數已賣。
- 若 positions 與 position_events 日期、股數或 source_status 不一致，2356 風控區必須 fail closed：顯示「持倉 / execution memory 需確認」，不得輸出新的賣出股數、第二段停利完成、或明日重複執行。
- 若 readonly production source 讀不到，Tech 不得用 local/runtime fallback 補結論；必須 blocked 或報文 fail closed，依現有 generator 行為選擇較安全路徑。

### 噪音壓縮契約

主文保留：

- 決策：買 / 不買、持倉主行動。
- 風控：停損、停利、續抱 / 觀察理由。
- source truth：available / missing-source / source-error / insufficient-data。
- 對使用者行動有影響的 fail-closed 原因。

主文壓縮或移到 details：

- 冗長 table 名逐欄說明。
- 重複 source/backtest/sample 長句。
- 對當日行動無影響的 debug-like evidence。
- 空區塊、0-count 占位、同義重複提醒。

不得壓掉：

- source 不足造成不可買 / 不可賣的原因。
- 2356 positions / position_events 不一致或不足的警示。
- 任何會改變使用者行動判斷的風控資訊。

## 手機閱讀示例輸出形狀

第一則：

台股盤中決策 v20.4.11｜2026-06-01
持倉：先看 2356 英業達，主行動：續抱 / 風控觀察（依 source 結果）
新倉：無有效進場
Source：持倉 available；execution memory available / insufficient-data；候選 source available

中間則：

持倉
2356 英業達｜主行動：續抱
狀態：目前仍有持倉；未確認第二段停利已賣出，不顯示已完成停利
風控：停損 / 停利依既有策略輸出

新倉
無有效進場

僅追蹤
2330 ...｜只觀察，不追高

倒數第二則：

Evidence
2356 holdings：positions available，as_of 2026-06-01
2356 execution：position_events insufficient-data，未確認第二段停利 event
候選：price/source available；RR 不足者已排除行動

最後一則：

Details
已壓縮 backtest/source 長句；完整 source mapping 見 QA artifact / manifest。
缺源項目已 fail closed，未進入明日下單。

## 驗收條件

1. 完整 06/01 類 Telegram 報文輸出 message list 順序符合 summary -> action body -> compact evidence -> details backup。
2. 手機閱讀時第一屏能直接判斷今日是否可買、持倉先處理什麼、source 是否足夠。
3. details / backup 類內容位於最後一則或被省略，不得插在 Summary 與行動主體中間造成碎片化。
4. 2356 必須以 production positions 與 position_events 或既有 readonly interface 比對；不得使用 local/runtime 跨日記憶作結論。
5. 2356 若仍持倉且第二段停利 event 未確認，不得顯示上週第二段停利已完成、不得輸出重複賣出股數、不得進明日重複執行。
6. positions / position_events 不一致或 source 不足時，2356 顯示 fail closed，且主文清楚說明「持倉 / execution memory 需確認」。
7. 噪音壓縮後，主文行數明顯少於 v20.4.10 類輸出，但 decision-critical source truth 仍可見。
8. 無可買時仍顯示「新倉：無有效進場」或等價不可買文案。
9. 報文版本字串升版且與實際輸出一致。
10. 既有 BUY/SELL/停利停損策略決策測試不得因本輪改變；若改變，Tech 必須 blocked。
11. CHANGELOG.md 必須列出修改檔案、message list order、2356 source truth 檢查方式、自檢命令與殘留風險。

## 範例或 Fixture

Tech 至少補或更新 3 個完整報文案例：

- fixture_20260601_like_sequence：多則 Telegram message，驗證順序為 Summary、Action Body、Evidence Compact、Details Backup。
- fixture_2356_still_holding_no_second_tp_event：positions 顯示 2356 仍持倉，position_events 無第二段停利 event；報文不得顯示第二段停利已完成。
- fixture_noise_reduction_missing_source：包含 source/backtest/detail 噪音來源；主文只保留 decision-critical source status，缺 source 的候選 fail closed，不進可買或明日下單。

若現有測試架構無法直接用 production readonly source，Tech 可使用 sanitized fixture，但必須保留欄位語意：positions、position_events、as_of/trade_date、source_status、remaining_shares/sold_shares。

## 明確禁止事項

- 禁止跳過 Tech / QA。
- 禁止 PM 或 Architect 直接改產品代碼。
- 禁止把本輪擴成策略重設、全量報文改版、DB schema 工程或 live delivery 任務。
- 禁止新增或修改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止手寫 production DML、backfill 或 live Telegram delivery。
- 禁止用 local cache、runtime dict、上週報文或 agent 對話當跨日 execution memory。
- 禁止缺 source 時輸出第二段停利完成、已賣股數或明日重複賣出。
- 禁止壓縮掉 source 不足、持倉不一致、不可買原因等決策關鍵資訊。
- 禁止用單一 formatter 測試取代完整 Telegram message list 驗收。

## 阻塞條件

Tech 遇到以下情況必須 blocked：

- 無法取得或模擬既有 readonly positions / position_events source contract。
- 需要 DB schema、RLS、grant、policy、role 或 write path 變更才能完成。
- 無法生成完整 Telegram message list，只能測單一 formatter。
- 2356 current holding 與 execution ledger 無法比對且無安全 fail-closed 呈現。
- 修正會改動 BUY/SELL/停利停損策略決策。
- 無法確認實際報文版本字串。
- 無法在測試或 fixture 中重現 06/01 類 message ordering 與 2356 stale execution-memory 風險。

## QA 要求

QA L2，必須覆蓋：

- 重跑 Tech 自檢命令。
- 驗完整 06/01 類 Telegram message list，而不是單一 formatter。
- 檢查 message order：Summary 第一則、Action Body 中間、Evidence Compact 倒數第二、Details Backup 最後或省略。
- 補一個 Tech 未覆蓋的 2356 反證：仍持倉但 execution event 缺失時，不得顯示第二段停利已完成。
- 檢查 positions / position_events source truth 欄位與 fail-closed 文案。
- 從手機閱讀角度檢查噪音壓縮：主文不被 source/backtest/detail 長句淹沒，且決策關鍵 source truth 未消失。
- 檢查無可買文案、持倉單一主行動、版本字串一致。
- 若 QA 只能驗 sanitized fixture，必須列出未測 production readonly path；若缺 production source truth 證據，結論最多 conditional pass，不得宣告完整通過。
