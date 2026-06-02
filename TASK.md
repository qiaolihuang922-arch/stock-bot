# TASK: 顯示門控修復：S 分數 / 強弱補源證據不足時不得顯示高信心數值

## 任務狀態

- task_id: risk_patch_score_source_status_display_gate_20260602
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見報文文字契約有變更，需同步檢查既有 report/version/header 常量；若現有版本契約要求報文變更升版，需升版，不得回退版本字串。
- QA 分級建議: L2，需補至少一個直接消費者 probe 與一個正常資料反證案例；不要求 L3，因本輪不改策略 decision、DB、live delivery。

## Owner 問題

presentation/report.py 的持倉卡與未持倉卡目前可能在 stock.<name>.score.source_status 非 available / derived 時，仍顯示 S 5/5、S 4/5 或「極強 / 突破確認」等高置信強弱文字，造成手機報文上「分數不可用」與「強信號結論」並
存的誤讀。

本輪只修復顯示門控類第 1 項：S 分數與依賴 score/strength 的強弱文字，必須受 evidence_manifest 的 score source status 控制。

## 使用者可見結果

手機閱讀報文路徑：

1. 使用者打開 Telegram/report。
2. 查看「持倉卡」或「未持倉卡」。
3. 若該股票 score.source_status 是 insufficient-data、source-error、缺失或其他非 available / derived 狀態：
- 卡片不得顯示 S 5/5、S 4/5 等 S 數值。
- 卡片資料行顯示 S 不可用 或 S 證據不足。
- 若盤面強弱文字依賴 score/strength，需降級為 強弱證據不足、待確認 或等價低置信文字。
- 不得同卡同時出現 S 證據不足 與 極強 / 突破確認。

示例輸出形狀：

持倉｜2330 台積電
S 證據不足｜RR 2.1｜價格資料可用
強弱：待確認（score 證據不足）

未持倉｜NVDA
S 不可用｜RR 1.8｜價格資料可用
強弱：證據不足

正常資料不得被降級：

未持倉｜AAPL
S 5/5｜RR 2.0｜價格資料可用
強弱：極強

## 非目標

- 不修改 strategy decision、買賣 / 加減碼 / 停損停利判斷。
- 不修改 RR 公式、structure_score 計算公式或 score 來源生成邏輯。
- 不修改 DB schema、RLS、grant、policy、role、index、constraint。
- 不新增 production write / backfill / live Telegram delivery。
- 不處理顯示門控清單其他項。
- 不做全量報文重構、全量文案清理或策略語意重設。

## 影響模組與直接消費者

影響模組：

- presentation/report.py
- 既有 report probe / test fixture 檔案，僅限補本輪可重跑驗收所需。

直接消費者：

- Telegram/report 手機閱讀者。
- 產生持倉卡與未持倉卡的 report rendering path。
- QA probe / regression test，用來驗證 source status 與卡片文字一致。

## 輸出契約

資料讀取契約：

- 顯示 S 分數、structure_score 或依賴 score/strength 的高置信強弱文字前，必須讀取：
- report_context.evidence_manifest["stock.<name>.score"].source_status
- 或透過既有 _stock_field(report_context, name, "score")
- 或等價既有結構化 helper。
- source_status in {"available", "derived"} 才可顯示 S 數值與依賴 score/strength 的高置信強弱文字。
- source_status 非上述值、缺失或讀取失敗時，顯示層必須 fail closed。

卡片文字契約：

- score 可用：
- 可顯示既有 S n/5、structure_score、強弱高置信文案。
- 不得因本修復降級。
- score 不可用：
- 不得顯示 S 1/5 到 S 5/5 的任何數值型 S 文案。
- S 資料行需顯示 S 不可用 或 S 證據不足。
- 若強弱文案依賴 score/strength，需顯示證據不足 / 待確認。
- price / OHLCV / RR 可用時，仍可正常顯示 price / OHLCV / RR，不得因 score 不可用整卡消失。

已存在且不得回退的契約：

- 持倉卡與未持倉卡仍需保留既有主要欄位順序與行動語意。
- RR、價格、OHLCV 可用時的顯示不應被 score source status 牽連降級。
- available / derived 的完整證據案例仍顯示原有 S 數值與強弱結論。
- 不得更改下游 message list 結構，除非現有 report rendering contract 已要求同一欄位以文字降級。

不確定項：

- 若現有版本字串 / header 升版規則無法從 repo 判定，Tech 需標記 blocked 交 Architect 補充，不得自行假設「不用升版」。

## 版本契約

- 本輪屬使用者可見報文文案與顯示門控修復。
- Tech 必須檢查現有 report 版本字串 / header / 常量。
- 若 repo 已有「報文可見文字變更需升版」規則，需同步升版。
- 不得回退既有版本字串。

## 驗收條件

1. 持倉卡 negative probe：
- fixture 建立持倉卡，price / OHLCV / RR 可用。
- stock.<name>.score.source_status = "insufficient-data" 或 "source-error"。
- 修復後輸出不包含 S 5/5、S 4/5 或任一 S n/5。
- 輸出包含 S 不可用 或 S 證據不足。
- 若原本會顯示 極強 / 突破確認，修復後需降級為證據不足 / 待確認。
2. 未持倉卡 negative probe：
- fixture 建立未持倉卡，price / OHLCV / RR 可用。
- stock.<name>.score.source_status = "insufficient-data" 或 "source-error"。
- 修復後不得顯示數值型 S 分數。
- 不得同時出現 S 證據不足 與高置信強弱文案。
3. 正常案例 regression：
- stock.<name>.score.source_status = "available" 或 "derived"。
- 既有 S 數值與強弱文案正常保留。
- price / OHLCV / RR 顯示不被改壞。
4. 可重跑證據：
- Tech 需提供 probe/test 命令與結果。
- QA 需補一個 Tech 未覆蓋的反證路徑，例如 missing score source status 或 source-error 與 RR 可用並存案例。

## 範例或 Fixture

最小 fixture 形狀：

report_context.evidence_manifest = {
"stock.TEST.score": {
"source_status": "insufficient-data"
},
"stock.TEST.price": {
"source_status": "available"
},
"stock.TEST.ohlcv": {
"source_status": "available"
},
"stock.TEST.rr": {
"source_status": "available"
},
}

修復前風險輸出示例：

TEST
S 5/5｜RR 2.0
強弱：極強 / 突破確認

修復後期望輸出示例：

TEST
S 證據不足｜RR 2.0
強弱：待確認

正常 fixture：

report_context.evidence_manifest = {
"stock.TEST.score": {
"source_status": "available"
}
}

正常期望：

TEST
S 5/5
強弱：極強

## 明確禁止事項

- 禁止修改策略 decision 或交易建議結果。
- 禁止修改 RR 公式。
- 禁止修改 DB schema/write path。
- 禁止 live Telegram 發送。
- 禁止直接手寫 production DML。
- 禁止把 score 不可用擴大成整卡不可顯示。
- 禁止處理本輪以外的顯示門控清單項。
- 禁止只改文案、不補可重跑 probe。
- 禁止在 score source status 非 available / derived 時顯示任何 S n/5 數值。

## 阻塞條件

- 找不到 report_context.evidence_manifest 或既有 _stock_field(report_context, name, "score") / 等價結構化 helper，且無法可靠判定 score source status。
- 現有 fixture/test infrastructure 無法構造持倉與未持倉 report card，且 Tech 無法提供可重跑替代 probe。
- 現有版本契約無法判定是否需升版。
- 修復必須改 strategy decision、DB schema/write 或 live delivery 才能達成時，本輪 blocked。

## 本輪停止條件

完成定義：

- 僅 presentation/report.py 顯示門控與必要 probe/test 完成。
- 持倉與未持倉 negative probe 均證明 score 不可用時不顯示 S 數值，也不顯示依賴 score/strength 的高置信強弱文字。
- available/derived 正常案例未被降級。
- QA 完成 L2 驗收並提供至少一個額外反證。
- 若需 repo 落地，後續由 Architect 依 git completion gate 收口；PM 不宣告完成、不 commit、不 push。

旁支問題處理：

- 其他 evidence gate 缺口、其他報文重複噪音、策略分數來源品質、DB source-of-truth 問題，若不阻塞上述驗收，只記待辦，不納入本輪。
