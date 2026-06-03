# TASK: 06/03 v20.4.32 報文策略與降噪修復

## 任務狀態

- task_id：task_20260603_report_strategy_noise_fix
- 任務類型：risk_patch（含 normal_patch 子項）
- 狀態：ready_for_tech
- 版本建議：使用者可見報文需升版，不得回退 v20.4.32；實際版本字串由 Tech 依既有版本機制同步。
- QA 分級建議：L3
- 落地順序：1、2 -> 3 -> 4、5、6、7
- 本輪主目標：修正 Owner 06/03 v20.4.32 完整報文中的 7 項使用者可見錯誤，不做策略重設或 DB 變更。

## Owner 問題

Owner 已提供 2026-06-03 v20.4.32 完整報文作為 failure specimen。該報文在手機閱讀時同時出現策略判斷錯誤、分組顯示不一致與重複噪音：

- 聯電 2303：avg 138.08 / price 132.75 / -3.86% / 今日買 50股 / 盤面突破失敗弱勢，仍輸出「新倉風控觀察」與「原始減碼訊號未達硬風控覆蓋條件」。修後必須輸出「減碼」。
- 技嘉 2376：等冷卻 / 過熱觀察狀態仍顯示 RR 0.21。修後應顯示 -（過熱）。
- 簡報原因行：目前逐檔串接「旺宏：...；建準：...；智原：...；聯電：...」。修後只保留主線一句。
- 未持倉回測行：同區塊部分卡片有回測、部分沒有。修後同區塊口徑一致，樣本不足 / 不可用不逐卡印，歸資料依據一次。
- 光寶科在可買與淘汰之間同日抖動，單次評估不應直接翻成可買。
- 解鎖證據因 strategy_sample version 過濾導致真實報文 evidence partial / 資料不足；修後必須用同層 replay/artifact 驗證，不得只驗 loader helper。
- 盤中與盤後卡片降噪邏輯不可只改單邊，需共用。

## 使用者可見結果

手機閱讀 06/03 等價 replay 報文時，Owner 應看到：

- 聯電 2303 同日建倉若跌幅達 -3% 且盤面突破失敗 / 結構轉弱，主行動為「減碼」；若觸及 hard stop，主行動為「止損 / 立即減碼」。
- 同日建倉只跌破警戒但未達快速止損條件時，仍保留「新倉風控觀察」緩衝。
- 光寶科若上一狀態為淘汰 / FAIL / 結構弱，單次買點成立不得直接跳可買；同盤中翻轉需標記 unstable 並維持保守側。
- 可買標的的策略證據不再因版本過濾長期顯示「不適用 / 資料不足」。
- 等冷卻 / 過熱 / 過熱觀察卡片 RR 欄一律顯示 -（過熱）。
- 簡報原因行只是一句主線，例如：原因：持倉多數縮量/轉弱，新倉無有效進場。
- 未持倉同一區塊內，回測行要麼全顯示，要麼全不顯示；樣本不足 / 不可用集中到資料依據，不逐卡輸出。
- 盤中與盤後報文都套用相同逐卡降噪、歷史行 token 去重與簡報壓縮。

## 非目標

- 不重設 RR 計算公式。
- 不新增或修改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 production DB write path。
- 不執行 live Telegram delivery。
- 不重寫整體策略框架、持倉狀態機或回測模型。
- 不把本輪擴大成全報文文案重設、全量清理或 UI 重設。
- 不用 synthetic helper fixture 取代 Owner 06/03 v20.4.32 完整報文等價 replay/artifact 驗收。
- 不修本輪以外的新問題；若發現旁支，只記待辦。

## 影響模組與直接消費者

影響模組：

- core/condition_engine.py
- 同日建倉風控減碼抑制邏輯。
- 可買 / 淘汰 / FAIL / 結構弱分類切換與 hysteresis。
- services/analysis.py
- 分類狀態切換、cross_day_context.previous_state 或等價上下文使用。
- services/strategy_evidence.py
- load_strategy_evidence_summary 載入 daily_signal_snapshot 的版本過濾。
- core/generator.py
- rr_display_text / should_show_overheat_rr_blocker 或等價 RR 顯示。
- 簡報原因行生成。
- render_backtest_context 在未持倉卡片的呼叫與區塊一致性。
- presentation/report.py
- 盤中、盤後卡片渲染降噪共用函式。

直接消費者：

- Telegram / 報文手機閱讀者 Owner。
- official report generator 產出的盤中 / 盤後 message list。
- runner artifact / replay artifact 中的 06/03 v20.4.32 等價報文。
- QA replay/probe 與既有報文測試。
- 下游使用報文卡片欄位的 presentation layer。

## 輸出契約

### 報文層契約

- 同一持倉在同一份報文只能有一個主行動：加碼 / 續抱 / 觀察 / 減碼 / 停損 / 停利 / 不動作。
- 今日買入後預設可保留新倉風控觀察，但若符合以下任一條件，需覆蓋為減碼 / 止損：
- price <= hard_stop_price：立即減碼 / 止損。
- price <= avg_price * (1 - SAME_DAY_FAIL_DROP_PCT)，其中 SAME_DAY_FAIL_DROP_PCT = 0.03。
- 當日盤面為突破失敗 / 結構轉弱。
- 若只跌破警戒價但未達 hard stop、未達 -3%、未有突破失敗 / 結構轉弱，維持新倉風控觀察緩衝。
- 等冷卻 / 過熱 / 過熱觀察 funnel 分類，RR 顯示欄一律為 -（過熱），不可顯示數值。
- 簡報原因行只輸出主線一句，不逐檔串接原因；逐檔原因留在持倉卡片內。
- 未持倉同一區塊內回測行顯示口徑一致：
- 若區塊決定顯示回測，該區塊卡片均顯示同形狀回測行。
- 若樣本不足 / 不可用，卡片內不逐檔印，改由資料依據集中說明。
- 盤中與盤後報文都必須使用同一套降噪函式：逐卡重複句刪除、歷史行 token 去重、簡報壓縮。

### 分類狀態契約

- 從淘汰 / FAIL / 結構弱切到可買，需符合：
- 連續 >= 2 次評估買點成立，或盤中連續 N 分鐘維持買點成立；N 由 Tech 沿既有評估節奏選擇最小可驗證常量或既有設定。
- breakout_distance <= 1%。
- 若存在 cross_day_context.previous_state 且同盤中狀態翻轉，需標記 unstable 並維持保守側：淘汰 / 不可買。
- 單次評估不得直接由淘汰翻可買。

### 策略證據契約

- load_strategy_evidence_summary 不再以 .eq("version", version) 過濾 daily_signal_snapshot。
- 查詢按 trade_date 倒序取近 60 個交易日全部版本資料。
- 其餘分類回測、outcome 統計、modifier 計算邏輯不變。
- 當 60 日歷史含成熟 outcomes，應產生：
- 有效樣本 > 0
- status = ready
- modifier != 1.0
- 不得因版本不一致導致可買標的證據恒為「不適用」。

## 版本契約

- 使用者可見報文版本必須升版，且不可回退 v20.4.32。
- 若 repo 有 header 常量、CLI version、message metadata 或 report title version，需同步更新。
- CHANGELOG 必須列出實際版本字串與同步位置。
- QA 必須檢查 replay/artifact 中實際 header / 常量與 CHANGELOG 一致。

## 驗收條件

### 必要前置

- Tech 每項修復先補可重跑 probe，再改實作。
- Tech 自檢必須至少覆蓋 helper / formatter / official generator / replay artifact 層級中 PM 指定的路由。
- QA 必須覆蓋 Owner 06/03 v20.4.32 完整報文的同層 replay 或等價 artifact；若無法取得等價路徑，QA 結論只能是 conditional pass 或 阻塞，不得寫 通過。

### 1. 同日建倉快速止損

- Probe A：聯電等價資料 avg=138.08 / price=132.75 / return=-3.86% / today_bought=50 / breakout_failed=true，輸出主行動為「減碼」，不可再輸出「新倉風控觀察」作為主行動。
- Probe B：同日建倉 return=-1% 且未 hard stop、未突破失敗、未結構轉弱，輸出仍為「新倉風控觀察」。
- Probe C：同日建倉觸及 hard_stop_price，輸出「止損 / 立即減碼」。
- Official generator / replay artifact 中聯電卡片主行動與 summary / 漏斗 / 詳情一致，不可跨區塊衝突。

### 2. 光寶科可買淘汰防抖

- Probe A：同一標的前一狀態為淘汰 / FAIL / 結構弱，單次評估買點成立，不得輸出可買，需維持保守側並標記 unstable 或等價狀態。
- Probe B：連續兩次以上評估成立且 breakout_distance <= 1%，才允許切到可買。
- Probe C：price 無顯著變化時，狀態保持，不可在可買 / 淘汰間抖動。
- Replay/artifact 不得出現光寶科同日單次翻可買造成手機閱讀誤導。

### 3. 解鎖證據加權

- Loader probe：60 日歷史含跨版本成熟 outcomes，載入後有效樣本 >0、status=ready、modifier != 1.0。
- Report replay/artifact：至少一個原本 evidence partial / 資料不足的可買標的，在 official generator 輸出中不再因版本過濾顯示「不適用」。
- 驗收不能只停在 load_strategy_evidence_summary helper；需證明報文層已消費修後證據。

### 4. 過熱 RR 隱藏

- 技嘉 2376 過熱觀察 / 等冷卻等價卡片 RR 顯示為 -（過熱）。
- 任何 funnel 分類為等冷卻 / 過熱 / 過熱觀察的卡片，不顯示 RR 數值。
- 非過熱類卡片 RR 顯示既有行為不回退。

### 5. 簡報原因行精簡

- 簡報原因行 <= 1 句。
- 不再出現「旺宏：...；建準：...；智原：...；聯電：...」這類逐檔串接。
- 逐檔原因仍保留在各自持倉卡片，不丟失必要決策依據。

### 6. 回測行卡間一致

- 未持倉 8 檔等價區塊中，回測行口徑一致，不可部分卡有、部分卡無。
- 樣本不足 / 不可用不逐卡輸出；集中到資料依據一次。
- 若同區塊決定全不顯示回測行，手機閱讀不可留下像缺漏的混排痕跡。

### 7. 盤中 / 盤後共用降噪

- 盤中與盤後兩條報文分支都呼叫同一共用降噪函式或同一公共 pipeline。
- 逐卡重複句刪除、歷史行 token 去重、簡報壓縮在盤中 / 盤後均生效。
- 不得只修一邊導致另一邊仍有重複句或逐檔簡報串接。

## 範例或 Fixture

### Failure specimen

Owner 06/03 v20.4.32 完整報文為本輪 failure specimen。Tech / QA 應建立或使用等價 replay artifact，至少保留以下關鍵可見資料：

- 聯電 2303：
- avg 138.08
- price 132.75
- -3.86%
- 今日買 50股
- 盤面突破失敗弱勢
- 修前錯誤主行動：新倉風控觀察
- 修後期待主行動：減碼
- 技嘉 2376：
- funnel：等冷卻 / 過熱觀察
- 修前錯誤：RR 0.21
- 修後期待：RR -（過熱）
- 簡報原因行：
- 修前錯誤形狀：原因：旺宏：...；建準：...；智原：...；聯電：...
- 修後期待形狀：原因：持倉多數縮量/轉弱，新倉無有效進場。
- 未持倉回測：
- 修前錯誤：同一區塊部分卡有回測、部分卡無。
- 修後期待：同區塊全顯示或全不顯示；樣本不足集中資料依據。

### 手機閱讀示例輸出形狀

簡報
原因：持倉多數縮量/轉弱，新倉無有效進場。

持倉
2303 聯電｜減碼
現價 132.75｜均價 138.08｜-3.86%
今日買入 50股；盤面突破失敗/結構轉弱，觸發同日入場即錯減碼。

2376 技嘉｜過熱觀察
RR：-（過熱）

未持倉觀察
資料依據：部分標的樣本不足或回測不可用，本區塊不逐卡列回測。

## 明確禁止事項

- 禁止 Architect 或 PM 直接改產品代碼、測試或報文實作。
- 禁止跳過 Tech / QA。
- 禁止 live Telegram delivery。
- 禁止 DB schema / RLS / grant / policy / role / index / constraint 變更。
- 禁止改 RR 計算公式。
- 禁止手寫 production DML 或繞過既有 repo script / approved service API。
- 禁止只用 helper fixture 宣告 Owner 報文問題通過。
- 禁止把「新倉風控觀察」與「減碼 / 止損」作為同一持倉的並列主行動。
- 禁止過熱 / 等冷卻類卡片顯示 RR 數值。
- 禁止簡報原因行逐檔串接。
- 禁止同一未持倉區塊卡片回測顯示口徑混用。
- 禁止只修盤中或只修盤後降噪。
- 禁止把旁支問題納入本輪擴張實作。

## 阻塞條件

- 無法取得 Owner 06/03 v20.4.32 完整報文或等價 replay artifact。
- replay artifact 無法覆蓋 official generator / runner 報文層，只能覆蓋 helper。
- 現有資料無法表示 today bought、avg_price、hard_stop_price、盤面突破失敗 / 結構轉弱、previous_state 或 evidence outcomes。
- 需要 DB schema 或 production write path 變更才能完成。
- 無法判定現有版本字串位置，且會造成使用者可見版本不同步。
- 測試環境缺依賴且無法補齊，導致 L3 replay/probe 無法執行。
- 若 Tech 發現 7 項中任一項必須改變已存在契約，需停止並回報，不得自行擴權。

## 已存在且不得回退的契約

- 無可買時，Summary 不得使用像推薦的文案，只能寫「新倉：無有效進場」或等價不可買表述。
- 可買、可準備、僅追蹤、淘汰 / 不可行動必須分開。
- 分組標題、卡片狀態、漏斗、索引、詳情必須一致。
- 同一持倉在同一份報文只能有一個主行動。
- 今日買入後預設是新倉風控觀察；本輪只新增「入場即錯」與 hard stop 優先覆蓋，不取消一般緩衝。
- 逐檔原因應留在持倉卡片，不能從報文完全消失。
- strategy evidence 既有分類回測邏輯不變；本輪只移除 version 過濾並驗證報文層消費。
- runner 視為無狀態；跨日記憶必須來自 production DB 或 Owner 指定 source-of-truth。
- 使用者可見報文變更需核對版本字串。

## 本輪停止條件

完成定義：

- 7 項修復均有可重跑 probe。
- 06/03 v20.4.32 failure specimen 的同層 replay 或等價 artifact 能產生修後報文。
- replay/artifact 證明：
- 聯電主行動為減碼。
- 技嘉 RR 為 -（過熱）。
- 簡報原因行 <= 1 句且不逐檔串接。
- 未持倉回測行同區塊一致。
- 光寶科不再單次從淘汰翻可買。
- 可買標的 evidence 不再因 version 過濾恒為不適用。
- 盤中 / 盤後都套用降噪。
- QA 依上述 replay/artifact 補充至少一個 Tech 未覆蓋的反證路徑，並只能在同層驗收成立時寫 通過。

不納入本輪：

- 其他股票的新策略調參。
- 其他日期歷史報文全面重算。
- Telegram live 發送。
- DB schema / write path 調整。
- 全量文案風格重設。
- 未由 Owner 06/03 specimen 或上述 7 項直接導出的旁支問題；只記待辦。
