# TASK: 證據鏈第一批硬衝突修復 P1/P2/P4

## 任務狀態

- task_id: evidence_gate_p1_p2_p4_20260602
- 任務類型: risk_patch
- 狀態: ready_for_tech
- QA 分級建議: 至少 L2；若共用 renderer、funnel builder、position card、Telegram message list 多處共享契約被改動，升 L3。
- 版本建議: 使用者可見報文版本不得回退；若本輪改動造成使用者可見分類、標籤或 header contract 變更，需同步升版與測試。

## Owner 問題

目前 evidence_manifest / 資料依據已宣告 strategy_sample、ledger、market/theme 等證據不足、不可用或只作背景，但使用者可見卡片仍輸出 S 5/5、極強、突破確認、可行動 funnel 分類、精確今日買賣 / 股數 / 均價等高置信內容，造成
「滿分結論 vs 不足證據」矛盾。

本輪只處理 P1 / P2 / P4：

- P1: 關鍵證據 missing-source / insufficient-data / source-error 時，依賴 strategy sample / RR / execution memory 的 S 分數、強弱標籤、funnel 分類必須降級或隱藏。
- P2: 卡片執行字段必須與 ledger_status / positions_status 合併門控；ledger 不足或衝突時，不能同時顯示「執行記憶不足」與精確今日 / 股數 / 均價。
- P4: RR 不可用或過熱時，未持倉 funnel 必須硬門控，不得進入會被手機閱讀誤解為準備買入的分類，不得輸出進場觸發。

## 使用者可見結果

手機閱讀 Telegram / 報文時，資料依據與卡片結論必須一致：

- 證據不足時，不再看到 S 5/5、極強、突破確認 等高置信標籤照常出現。
- 執行記憶不足時，不再看到精確今日交易、股數、均價等像已確認 ledger 的字段。
- RR 不可用或過熱時，未持倉標的不得出現在「可買 / 可準備 / 進場觸發」等可行動區塊，只能進入不可追高觀察、過熱待回測、待回測或不可行動口徑。

手機閱讀路徑示例形狀：

資料依據
- strategy_sample: insufficient-data

個股卡片
- 強度: 證據不足，暫不顯示 S 分數
- 狀態: 待回測 / 僅追蹤
- 進場: 無有效進場

執行記憶
- ledger_status: insufficient-data
- 今日執行: 執行記憶不足，暫不顯示股數 / 均價

未持倉漏斗
- 不可追高觀察 / 過熱待回測
- 不顯示進場觸發價

## 非目標

- 不改 strategy decision 結果。
- 不改 RR 計算公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 DB write path。
- 不做 production DML / backfill。
- 不做 live Telegram delivery。
- 不處理 P3 / P5 / P6 / P7 / P8。
- 不重設策略、分數模型、持倉狀態機或完整報文架構。
- 不因證據不足刪除整張卡片；本輪目標是降低或隱藏高置信顯示，讓可見結論與證據狀態一致。

## 影響模組

- evidence_manifest 到使用者可見 renderer / formatter 的證據狀態轉換層。
- 個股卡片中 S 分數、強弱標籤、突破 / 確認類文案的顯示門控。
- 今日買賣、股數、均價等 execution memory 顯示字段。
- 未持倉 funnel 分類與進場觸發輸出。
- 相關 probes / tests / fixtures。

## 直接消費者

- Telegram 報文手機閱讀者。
- 報文 summary / funnel / card renderer。
- QA probes 與 regression tests。
- 後續 runner 產生的正式報文；本輪不得 live delivery。

## 輸出契約

新增或調整一層統一證據門控，或等價集中機制。契約要求如下：

1. P1 strategy / score / strength gate

- 當卡片高置信字段依賴 strategy_sample，且對應 evidence status 為 missing-source、insufficient-data、source-error 時，不得顯示 S 5/5 或等價滿分。
- 不得顯示極強、突破確認、高置信可行動強弱文案。
- 必須降級為「證據不足 / 待確認 / 待回測 / 僅追蹤」等保守口徑，或隱藏該字段。
- 不能改內部 strategy decision 結果；只改可見標籤與分類門控。

2. P2 ledger / positions execution gate

- 今日買入、今日賣出、股數、均價、成交記憶、已買入 / 已賣出等精確執行字段，必須同時通過 ledger_status 與 positions_status 的保守檢查。
- 若 ledger 或 positions 任一為 missing-source、insufficient-data、source-error、衝突或不可判定，不得顯示精確今日 / 股數 / 均價。
- 必須顯示「執行記憶不足」或等價保守文案。
- 不得讓精確執行結論與「執行記憶不足」並存。

3. P4 RR / overheat funnel gate

- RR 不可用、RR source-error、RR insufficient-data、過熱、不可追高時，未持倉不得進入「可買」「可準備」「進場觸發」「突破買入」等可行動 funnel。
- 不得輸出具體進場觸發。
- 必須沿用或強化 v20.4.25 既有不可追高觀察 / 過熱待回測 / 待回測口徑。
- 不改 RR 算法，只改 RR 狀態對 funnel / 文案的硬門控。

4. 已存在且不得回退的契約

- 無可買時不得使用像推薦的文案；必須是「新倉：無有效進場」或等價不可買表述。
- 可買、可準備、僅追蹤、淘汰 / 不可行動必須分開。
- 分組標題、卡片狀態、漏斗、索引、詳情必須一致。
- 空區塊、0-count、無新增下單占位預設不顯示。
- 使用者可見版本字串不得回退。
- v20.4.25 的不可追高觀察 / 過熱待回測 / 待回測口徑不得被弱化；若無法確認既有常量或測試，必須 blocked 並交回 Architect 補充。

## 版本契約

- 若只新增證據門控且不改報文 header 格式，可維持現行版本字串。
- 若使用者可見報文分類、標籤或 header contract 被調整，必須升版，不得回退。
- Tech 必須在 CHANGELOG 寫明實際版本常量 / header 是否改動，以及原因。

## 驗收條件

Tech 必須先補可重跑 probes，再實作修復。驗收至少覆蓋：

1. P1 probe: strategy_sample 不可用

- fixture: strategy_sample 為 missing-source / insufficient-data / source-error 任一狀態。
- 修復前可重現：卡片仍出現 S 5/5、極強 或 突破確認。
- 修復後要求：高置信 S 分數 / 強弱 / 突破確認降級或隱藏；資料依據與卡片一致。

2. P2 probe: ledger / positions 不足

- fixture: ledger_status 或 positions_status 為 insufficient / missing / source-error / conflict。
- 修復前可重現：卡片仍顯示精確今日買賣、股數、均價。
- 修復後要求：不顯示精確執行字段；只顯示執行記憶不足或等價保守文案。

3. P4 probe: RR 不可用 / 過熱

- fixture: 未持倉標的 RR unavailable / source-error / insufficient-data / overheat。
- 修復前可重現：標的仍進入可行動準備分類或輸出進場觸發。
- 修復後要求：標的只能進入不可追高觀察 / 過熱待回測 / 待回測 / 僅追蹤 / 不可行動；不得輸出進場觸發。

4. 回歸要求

- 有完整證據的既有正常案例，不得被錯誤降級。
- strategy decision 原始結果、RR 計算值、DB payload/write 不得因本輪改動變更。
- Telegram 手機閱讀路徑需檢查 summary、funnel、卡片、資料依據四者一致。
- 測試結果只能宣告覆蓋 P1/P2/P4，不得宣告證據鏈全量完成。

## 範例或 Fixture

最小 fixture 形狀可由 Tech 依現有測試架構落地，但必須能重跑並保留為 regression：

Case P1
evidence_manifest.strategy_sample.status = insufficient-data
card.before = "S 5/5 / 極強 / 突破確認"
card.after = "證據不足 / 待確認 / 不顯示 S 分數"

Case P2
evidence_manifest.ledger_status = missing-source
evidence_manifest.positions_status = insufficient-data
card.before = "今日買入 100 股 / 均價 123.45"
card.after = "執行記憶不足 / 不顯示股數與均價"

Case P4
rr.status = unavailable 或 overheat
position_state = no_position
funnel.before = "可準備 / 進場觸發 123.45"
funnel.after = "不可追高觀察 / 過熱待回測 / 無有效進場"

## 明確禁止事項

- 禁止改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止改 DB write path 或新增 production DML。
- 禁止 live Telegram delivery。
- 禁止改 strategy decision 結果。
- 禁止改 RR 計算公式。
- 禁止把 local cache、runtime dict、agent 對話當作跨日 execution memory。
- 禁止以隱藏 evidence_manifest 來消除矛盾；必須讓可見卡片 / funnel 跟 evidence status 一致。
- 禁止把 P3/P5/P6/P7/P8 併入本輪。
- 禁止只改文案不補可重跑 probes。
- 禁止在 ledger 不足時仍輸出精確今日 / 股數 / 均價。
- 禁止 RR 不可用或過熱時輸出未持倉進場觸發。

## 阻塞條件

- 找不到 evidence_manifest、ledger / positions 狀態或 RR 狀態進入 renderer / funnel 的資料路徑。
- 現有報文版本常量或 v20.4.25 口徑無法定位，且會影響本輪版本契約判斷。
- 無法建立三類可重跑 probes。
- 測試環境缺 pytest / dependency 且 runner 無法補齊。
- 任何修復必須改 DB schema/write、strategy decision 或 RR 公式才做得到。
- 需求外發現 P3/P5/P6/P7/P8 問題但不阻塞 P1/P2/P4 驗收時，只能記待辦，不得擴大本輪。

## 本輪停止條件

完成標準：

- P1/P2/P4 三類失敗各有一個可重跑 probe 能先重現、後驗證修復。
- 使用者可見 summary / funnel / card / 資料依據在三類 fixture 下語意一致。
- 完整證據正常案例不被誤降級。
- CHANGELOG 清楚列出修改檔案、契約影響、版本是否同步、自檢命令與結果。
- QA 至少 L2，且除重跑 Tech 測試外，補一個手機閱讀誤讀路徑、負面案例或契約風險反證。

不納入本輪：

- P3/P5/P6/P7/P8。
- 全量證據鏈治理。
- strategy / RR / DB / live delivery 的任何功能性改動。
- 新增持久化 source-of-truth 或 backfill。
