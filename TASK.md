# TASK: v20.4.36 06/04 報文手機閱讀一致性收斂

## 任務狀態

- task_id: v20_4_36_0604_report_mobile_readability_convergence
- 任務尺寸: normal_patch
- 狀態: ready_for_tech
- QA 分級建議: L2
- 版本建議: 維持 v20.4.36；不得回退版本。
- 本輪主 bug: 06/04 報文在手機閱讀時，未持倉卡片原因、正常資料提示、普通歷史提示、可買但回測偏弱、首屏今日新建倉摘要彼此造成誤讀。
- 範圍收斂: 只修報文可讀性與 message-list replay 驗收，不改策略、不改 RR、不改 DB。

## Owner 問題

Owner 要處理 v20.4.36 06/04 報文手機閱讀一致性，嚴格覆蓋六個 failure specimen：

1. 原因優先級混亂：RR 原因 / 不適用原因 / 證據原因 / 主狀態互相搶主因。
2. 正常資料行刷屏：每卡重複「資料：...已確認...」。
3. 普通歷史行刷屏：多卡重複「前次 observe｜修復中｜連續觀察 1 天｜權重 +1」。
4. 建準可買但回測偏弱並列，缺手機可讀解釋。
5. 首屏裸寫「今日新建倉 3」，與停損 / 減碼並列時容易誤讀成仍積極建倉。
6. 回測單檔契約不得回退，仍需顯示「回測（建準）：...」並與可買解釋一致。

## 使用者可見結果

手機 Telegram 報文應變成：

- 首屏清楚區分：持倉要處理什麼、新倉是否可買、今日已買標的是否已有風控。
- 未持倉卡片的主狀態、RR 不適用原因、證據不適用原因一致。
- 正常來源時不逐卡顯示資料已確認句。
- 普通 cross-day 歷史不逐卡刷屏，只保留高風險或 execution memory 類歷史。
- 建準若仍是可買但回測偏弱，需一句短文案降低誤讀，例如「回測偏弱僅輔助，分批小倉、不追價」。
- 回測單檔格式維持「回測（建準）：...」。

手機示例輸出形狀：

今日已買3｜風控中2｜新倉建議1

🟢 可買｜建準
回測（建準）：...偏弱；回測僅輔助，分批小倉、不追價

👀 等量能｜量能不足
RR -（量能不足）｜不適用（量能不足）｜證據：量能不適用

⛔ 淘汰｜突破失敗
RR -（風控）｜不適用（突破失敗）｜證據：風控不適用

## 非目標

- 不改 RR 公式。
- 不改 strategy decision。
- 不改買賣 / 加減碼 / 停損 / 停利決策。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不改 DB write path。
- 不新增 production backfill / production write。
- 不觸發 live Telegram。
- 不把建準可買改成不可買來消除文案矛盾。
- 不進行全量報文重構、策略重設或 L3 production 驗證。

## 影響模組與直接消費者

影響模組：

- presentation/report.py: 首屏摘要、卡片資料行、歷史行、回測顯示若在此層生成。
- core/generator.py: message list、原因顯示、evidence unavailable reason、funnel / card formatter 若在此層生成。
- tests/test_generator_report.py 或等價新增測試: 06/04 failure specimen 的 official generator / report message-list replay。

直接消費者：

- Owner 手機 Telegram 報文。
- official generator / report runner 產出的 message list。
- QA message-list replay / mobile readability probe。

## 輸出契約

已存在且不得回退的契約：

- 使用者可見版本不得低於 v20.4.36。
- 回測單檔行必須保留「回測（建準）：...」。
- 可買、可準備、僅追蹤、淘汰 / 不可行動仍需分開。
- 無可買時不得使用像推薦的語氣。
- 同一持倉在同一份報文只能有一個主行動。
- 不得用刪除卡片、刪除證據或刪除回測來掩蓋矛盾。

原因優先級：

1. 淘汰 / FAIL / 突破失敗 / 弱勢 / 風控優先，顯示風控或突破失敗，不得被過熱覆蓋。
2. 純過熱 / 等冷卻 / 不可追高且非淘汰時，才顯示過熱不適用。
3. 等量能 / 量能不足且非淘汰時，顯示量能不足或條件未滿不適用，不得寫資料不足。
4. 真缺資料 / source-error / insufficient-data 時，才顯示資料不足。

正常資料行降噪：

- 正常來源時，逐卡不得重複顯示「資料：持倉與現價已確認；風控由持倉成本/停損推算」。
- 正常來源時，逐卡不得重複顯示「資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算」。
- 只在 source missing、source-error、insufficient-data、stale、execution memory conflict、QA/debug 顯示模式時保留。

普通歷史行降噪：

- 普通歷史不得逐卡刷屏「前次 observe｜修復中｜連續觀察 1 天｜權重 +1」。
- 只保留連續失效、高風險歷史、已買 / 已賣 / 已停利 / 已減碼、source conflict、達到策略門檻的歷史提示。

建準可買 + 回測偏弱：

- 若策略仍輸出建準可買，但單檔回測摘要為偏弱 / 無明顯優勢 / 樣本不足，必須在同卡以短句解釋：回測僅輔助、分批、小倉、不追價或等價語意。
- 不得因此改變 strategy decision。

首屏今日新建倉：

- 不得裸寫「今日新建倉 3」。
- 當今日買入標的已有停損 / 減碼 / 硬風控，需改成風險-aware 摘要，例如「今日已買3｜風控中2｜執行動作3（停損/減碼）」。

## 版本契約

- 使用者可見版本維持 v20.4.36。
- 不得回退版本。
- 若 Tech 實際改動 header / VERSION 常量，CHANGELOG 必須明確說明升版理由與新版本。
- 若只改報文文字 / formatter 且不改 VERSION，CHANGELOG 必須寫「版本維持 v20.4.36」。

## 驗收條件

1. official generator / report message-list replay 覆蓋 Owner 06/04 六個 failure specimen。
2. 光寶科「等量能｜量能不足」不再顯示「證據：資料不足」。
3. 群創 / 技嘉「淘汰｜突破失敗」主不適用原因不得顯示為過熱。
4. 正常來源持倉卡不逐卡顯示持倉與現價已確認句。
5. 正常來源未持倉卡不逐卡顯示現價與 OHLCV 已確認句。
6. 普通「前次 observe｜修復中｜連續觀察 1 天｜權重 +1」不逐卡刷屏。
7. 建準可買但回測偏弱時，同卡有分批 / 小倉 / 不追價或回測僅輔助短句。
8. 首屏不再裸寫「今日新建倉 3」；需反映今日已買標的中的風控數量。
9. 回測單檔格式「回測（建準）：...」保留。
10. 不改 RR 公式、strategy decision、DB schema/write、live Telegram。

## 範例或 Fixture

必須以 Owner 06/04 完整報文或等價 replay payload 建立 message-list fixture，最少包含：

- 光寶科：等量能｜量能不足 + 原失敗「證據：資料不足」。
- 群創：淘汰｜突破失敗 + 原失敗「不適用（過熱）｜證據：風控不適用」。
- 技嘉：同類突破失敗淘汰卡，用來反證原因一致性。
- 正常持倉卡：原本會顯示「資料：持倉與現價已確認...」。
- 正常未持倉卡：原本會顯示「資料：現價與 OHLCV 已確認...」。
- 建準：可買 +「回測（建準）：...偏弱」。
- 首屏：原本「執行動作 3（停損/減碼）｜新倉建議 1｜今日新建倉 3」。

## 失敗標本與驗收路由

驗收路由必須打到 official generator / report final message list，例如 formatTelegramMessages、render_telegram_messages 或專案現有等價官方報文入口。

- Tech 不得只測 private helper。
- 若因環境限制只能測 helper 層，CHANGELOG 必須標 partial，列出未覆蓋的 official generator / runner artifact 層。
- QA 必須沿同一 message-list replay 反證，並額外檢查一個手機誤讀路徑或契約風險。

## 明確禁止事項

- 禁止 Architect 或 PM 直接改產品代碼；本卡交給 Tech 實作，QA 驗收。
- 禁止用 helper-only 測試宣稱完成。
- 禁止刪卡片、刪證據、刪回測來掩蓋矛盾。
- 禁止改買賣策略結果來解決文案問題。
- 禁止改 RR 公式。
- 禁止改 DB schema/write 或 live Telegram。
- 禁止擴成全量報文重構、策略回測重設或 production write 任務。

## 阻塞條件

- 拿不到 Owner 06/04 完整報文或等價 replay payload，且無法構造同層 official message-list fixture。
- 修復需要改 strategy decision、RR 公式、DB schema/write、live Telegram。
- 現有 official generator/report 入口無法在測試環境產出 message list，且沒有可接受的 runner artifact。
- 現有版本常量 / header 位置不明，無法確認是否維持 v20.4.36。
- Tech 只能做到 helper 層驗證時，不得宣稱完成；最多標 partial。

## 本輪停止條件

完成定義：

- 六個 06/04 failure specimen 均由 official generator / report message-list replay 覆蓋。
- 驗收條件 1-10 全部通過。
- CHANGELOG 明確列出覆蓋層級為 message-list replay，或若不足則標 partial。
- QA 至少補一個 Tech 未覆蓋的手機誤讀反證或契約風險檢查。

不納入本輪，只記待辦：

- 任何新的策略買賣問題。
- RR 數值合理性或公式調整。
- production DB evidence source 補資料。
- live Telegram 實送。
- 全量報文資訊架構重設。
- 觀察天數跨日持久來源治理。
