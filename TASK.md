# TASK: A1+B1-B4+C 報文與 evidence 修正；D1 僅 PM 判定

## 任務狀態

- task_id: 20260603_strategy_evidence_report_risk_patch
- 任務類型: risk_patch
- 狀態: done / QA passed
- 版本建議: 使用者可見 Telegram / 報文內容有變更，需升版或同步既有報文版本字串，不得回退版本。
- QA 分級建議: L3
- 本輪範圍: A1 + B1 + B2 + B3 + B4 + C 納入實作與 QA；D1 僅做 PM 判定並 deferred。

## Owner 問題

Owner 已確認按上一份 Codex 修復指令執行，但需要重新生成正式 TASK，讓 Tech/QA 依本輪契約處理：

- A1: strategy evidence 歷史取樣被 version filter 限制，導致樣本不足、modifier 不生效、可買標的顯示不適用。
- B1-B4: Telegram / 報文在交易執行、原因/風險、未持倉回測行、partial modifier 顯示上造成手機閱讀誤讀與噪音。
- C: 同日建倉後 hard_stop / 快速止損 / 只破警戒的處理不完整，導致聯電 -3.86% + 突破失敗可能被「剛買入」豁免。
- D1: 光寶科同日淘汰 -> 可買翻轉是否為真問題未足以安全納入本輪，先 PM 判定為 deferred。

## 使用者可見結果

手機閱讀 Telegram / 報文時應看到：

- 「交易執行」只列已執行或持倉處理動作，不混入未持倉可買。
- 未持倉可買標的進入「新倉建議」，並明確標示尚未買入 / 建議分批。
- 原因與風險依對象拆分，避免持倉與未持倉原因混在一起。
- 未持倉回測行降噪，盤中/盤後呈現一致。
- partial evidence modifier 等於 1.0 時顯示「僅輔助參考」，不顯示「+0%」。
- 同日建倉若跌破 hard_stop 或快速止損條件，不能被剛買入豁免；若只破警戒但未達 hard_stop / 快速止損，降級為當日觀察。
- 聯電 fixture: 同日建倉後 -3.86% + 突破失敗，應進入「當日減碼」而不是「剛買入豁免」。

手機閱讀示例形狀：

交易執行
- 已持倉：聯電｜當日減碼｜同日建倉後跌破快速止損 / 突破失敗

新倉建議
- XXX｜尚未買入｜建議分批｜evidence: ready/effective，僅輔助參考

原因
- 聯電：同日建倉後轉弱，觸發快速止損條件
- XXX：未持倉可買，等待分批進場

風險
- 聯電：hard_stop 永不豁免
- XXX：尚未買入，不列入交易執行

## 非目標

- 不改 RR 公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不新增或改 production DB write path。
- 不做 live Telegram delivery。
- 不重設策略核心、不改整體買賣評分模型。
- 不把 D1 光寶科翻轉納入本輪實作；只記 deferred 判定。
- 不做全量報文重構或文案大改，只修正本輪指定誤讀與契約。

## 影響模組與直接消費者

影響模組：

- services/strategy_evidence.py
- load_strategy_evidence_summary 或其直接 evidence summary 載入路徑。
- Telegram / 報文 formatter 相關模組
- 交易執行區塊。
- 新倉建議區塊。
- 原因 / 風險區塊。
- 未持倉回測顯示。
- evidence modifier 顯示。
- 同日建倉風控判斷相關模組
- hard_stop。
- 快速止損。
- 警戒緩衝。
- 當日減碼分類。
- 盤中 / 盤後共用降噪與計數 helper。

直接消費者：

- Owner 手機端 Telegram 報文。
- 盤中報文產生流程。
- 盤後報文產生流程。
- strategy evidence summary 下游使用者。
- QA probes / regression tests。
- Architect closeout 讀取的 TASK.md -> CHANGELOG.md -> QA_REPORT.md 交付鏈。

## 輸出契約

A1 strategy evidence summary:

- services/strategy_evidence.py load_strategy_evidence_summary 必須刪除 version filter。
- 取樣口徑改為依 trade_date 近 N=60 個交易日跨版本歷史取樣。
- ready/effective samples 必須以跨版本歷史計算。
- 當樣本足夠且 evidence 有效時，至少部分標的的 evidence_modifier != 1.0。
- 可買標的不應因 version filter 導致顯示「不適用」。
- 缺樣本、source-error、欄位不足或可信度不足時必須 fail closed，不得假裝可用。

B1 交易執行 / 新倉建議:

- 「交易執行」只放：
- 已執行動作。
- 已持倉處理動作。
- 未持倉可買不得出現在「交易執行」。
- 未持倉可買必須進「新倉建議」。
- 新倉建議需標示：
- 尚未買入。
- 建議分批。

B2 原因 / 風險:

- 原因與風險必須按對象拆分。
- 持倉與未持倉不得共用一段容易誤讀的原因 / 風險長句。
- 同一標的的原因、風險、主行動需一致。

B3 未持倉回測行:

- 未持倉回測行需一致降噪。
- 盤中 / 盤後必須共用降噪與計數函式或等價單一契約，避免兩套輸出漂移。
- 空區塊、0-count、無新增下單占位預設不顯示。

B4 partial modifier 顯示:

- partial evidence modifier = 1.0 時，顯示「僅輔助參考」。
- 不得顯示「+0%」。
- 非 1.0 modifier 的既有顯示不得回退。

C 同日建倉硬風控:

- hard_stop 永不豁免。
- 同日建倉快速止損預設條件：
- 跌破入場價 3%；或
- 跌破入場 K 棒低點。
- 僅破警戒、未達 hard_stop / 快速止損時，當日降級觀察。
- 同日建倉且入場即錯，觸發當日減碼。
- 聯電 -3.86% + 突破失敗 fixture 必須落入當日減碼，不得被剛買入豁免。

D1 PM 判定:

- 光寶科同日淘汰 -> 可買翻轉本輪判定為 deferred。
- 原因: 此問題可能涉及策略翻轉、狀態記憶或跨區塊候選排序，超出本輪 A/B/C 的收斂修正；若未有獨立 fixture 與 Owner 確認，不得在本輪順手修。
- 後續需另開任務，先確認是否為真 bug、資料來源與使用者可見誤讀。

## 版本契約

- Telegram / 報文使用者可見內容改動需同步版本字串或 header 常量。
- 不得回退既有版本。
- 若現有版本契約位置不明，Tech 必須 blocked 並要求 Architect 補充，不得自行假設無需升版。
- CHANGELOG 必須列明版本同步位置與結果。
- QA 必須核對實際輸出 header / 常量與 CHANGELOG 一致。

## 已存在且不得回退的契約

- Summary 只回答決策：今天能不能買、持倉先處理什麼、未持倉哪些只是追蹤、哪些不可行動。
- 可買、可準備、僅追蹤、淘汰 / 不可行動必須分開。
- 無可買時不得使用像推薦的文案；只能寫「新倉：無有效進場」或等價不可買表述。
- 分組標題、卡片狀態、漏斗、索引、詳情必須一致。
- 同一持倉在同一份報文只能有一個主行動：加碼 / 續抱 / 觀察 / 減碼 / 停損 / 停利 / 不動作。
- 今日買入後預設只能新倉風控觀察；若轉弱要賣，必須同行說明跌破警戒、停損或策略失效。
- 同一行動不得在多個區塊重複長句。
- 空區塊、0-count、無新增下單占位預設不顯示。
- hard_stop 永不豁免。
- 缺樣本 / source-error / insufficient-data 必須 fail closed。
- local cache、runtime dict、agent 對話不得作為跨日記憶 source-of-truth。
- live Telegram delivery 需 Owner 單獨批准。

## 驗收條件

Tech 必須先補可重跑 probe，再修實作；每項至少有對應 regression。

A1:

- 有 probe 證明 load_strategy_evidence_summary 不再套 version filter。
- 有 fixture 或測試資料覆蓋近 60 個交易日跨版本取樣。
- ready/effective samples 可被計算。
- 至少部分 evidence_modifier 不等於 1.0。
- 可買標的不再因 version filter 顯示不適用。
- 缺樣本 / source-error 時 fail closed。

B1:

- 未持倉可買不出現在「交易執行」。
- 未持倉可買出現在「新倉建議」。
- 新倉建議含尚未買入 / 建議分批。
- 已執行或持倉處理仍保留在「交易執行」。

B2:

- 原因 / 風險按標的或對象拆分。
- 持倉與未持倉不共用造成誤讀的同一段原因 / 風險。
- 報文中同一標的主行動、原因、風險一致。

B3:

- 盤中與盤後未持倉回測行使用共用降噪與計數契約。
- 空區塊、0-count、無新增下單占位不顯示。
- 未持倉回測行不重複長句，不干擾主要決策。

B4:

- partial modifier = 1.0 顯示「僅輔助參考」。
- partial modifier = 1.0 不顯示「+0%」。
- 非 1.0 modifier 的顯示仍保留原有語意。

C:

- hard_stop probe: 同日建倉跌破 hard_stop，不能豁免。
- 快速止損 probe: 同日建倉跌破入場價 3%，觸發當日減碼。
- 快速止損 probe: 同日建倉跌破入場 K 棒低點，觸發當日減碼。
- 警戒緩衝 probe: 僅破警戒、未達 hard_stop / 快速止損，當日降級觀察。
- 聯電 fixture: -3.86% + 突破失敗，落入當日減碼，不是剛買入豁免。

QA L3:

- QA 不只重跑 Tech 命令；至少補一個 Tech 未覆蓋的直接消費者、負面案例、手機閱讀誤讀路徑或契約風險。
- QA 必須覆蓋盤中與盤後報文路徑。
- QA 必須檢查版本字串 / header 常量。
- QA 必須反證 D1 未被實作或誤納入本輪。

## 範例或 Fixture

A1 fixture:

trade_date: 最近 60 個交易日
versions: vA, vB, vC
symbol: 可買標的
expected:
- 跨版本樣本納入 ready/effective samples
- evidence_modifier 至少部分不等於 1.0
- 不顯示 evidence 不適用

A1 fail-closed fixture:

source: strategy evidence summary
condition: 無樣本或 source-error
expected:
- status: missing-source / source-error / insufficient-data
- 不產生假 modifier
- 不把標的升格為 evidence 可用

B1 mobile fixture:

input:
- A: 未持倉，可買
- B: 已持倉，續抱
expected:
交易執行:
- B 續抱
新倉建議:
- A 尚未買入，建議分批
not expected:
- A 出現在交易執行

B4 fixture:

input:
- evidence_state: partial
- evidence_modifier: 1.0
expected:
- 顯示「僅輔助參考」
not expected:
- 顯示「+0%」

C 聯電 fixture:

symbol: 聯電
position_state: 同日建倉
move: -3.86%
signal: 突破失敗
expected:
- 主行動: 當日減碼
- 原因: 同日建倉後觸發快速止損 / 入場即錯
not expected:
- 剛買入豁免

C 警戒 fixture:

position_state: 同日建倉
condition:
- 只破警戒
- 未跌破 hard_stop
- 未跌破入場價 3%
- 未跌破入場 K 棒低點
expected:
- 當日降級觀察
not expected:
- 當日減碼
- 剛買入豁免

## 明確禁止事項

- 禁止改 RR 公式。
- 禁止改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止新增或改 production DB write。
- 禁止 live Telegram delivery。
- 禁止直接手寫 production DML。
- 禁止把 local cache、worktree、runtime dict 或 agent 對話當跨日記憶。
- 禁止把 D1 光寶科翻轉順手修進本輪。
- 禁止只改文案不補 probe。
- 禁止只驗單一路徑後宣告盤中 / 盤後都通過。
- 禁止 source-error、缺樣本、insufficient-data 時仍宣告 ready / effective。
- 禁止讓未持倉可買出現在交易執行。
- 禁止 hard_stop 被任何「同日建倉 / 剛買入」邏輯豁免。

## 阻塞條件

- 找不到 load_strategy_evidence_summary 或其實際 evidence summary 載入路徑。
- 無法建立跨版本近 60 交易日取樣 fixture 或 probe。
- 報文版本字串 / header 常量位置不明且無法安全確認。
- 盤中 / 盤後報文路徑無法重跑。
- 缺測試環境且補環境後仍無法跑 regression。
- 同日建倉入場價、入場 K 棒低點、hard_stop 任一必要欄位缺失且無可靠 source。
- 任何修正需要 DB schema/write 或 live Telegram 才能完成。
- D1 若被證明會阻塞 A/B/C 驗收，需停下交回 Architect，不得擅自擴大本輪。

## 本輪停止條件

完成定義：

- A1、B1、B2、B3、B4、C 均有可重跑 probe。
- Tech CHANGELOG 交代修改檔案、契約影響、版本同步、直接消費者、自檢命令與結果。
- QA L3 通過，且包含盤中 / 盤後、手機閱讀誤讀路徑、版本核對、D1 deferred 反證。
- Architect 後續完成 commit / push / gates 後，本輪才可被收口為完成。

本輪不處理：

- D1 光寶科同日淘汰 -> 可買翻轉，只記 deferred。
- 其他策略翻轉、候選排序、RR 公式、DB 持久化、live delivery 問題。
- 任何新發現但不阻塞 A/B/C 驗收的旁支問題，記入後續待辦，不納入本輪。
