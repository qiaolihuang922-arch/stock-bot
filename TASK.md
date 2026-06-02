# TASK: Phase 0 + B1-B5 前置修復與手機閱讀回歸

## 任務狀態

- task_id: phase0_b1_b5_prereq_rerun_20260602
- 任務類型: risk_patch
- 升級理由: B2 涉及「弱勢 / 遠離突破」與「極強」強弱標籤語意 gate，Phase 0-1 涉及 structure_score/strength 顯示門控，會影響使用者對可行動性的判讀。
- 狀態: ready_for_tech
- 版本建議: 若使用者可見報文版本字串存在，需升版或至少確認不回退；不得低於上一輪 v20.4.28 已修契約。
- QA 分級建議: L3，因本輪同時覆蓋多個手機閱讀語意衝突、formatter contract、持倉排序與漏斗 count 對齊。

## Owner 問題

上一輪 Phase 0 + B1-B5 前置任務被 stale Tech worktree 阻塞，需要重跑並落地已確認範圍：先修報文顯示門控與並行 bug B1-B5 的前置修復 / 回歸，不進入 major 策略證據分數改造，也不做 Phase 3 自動化生產。

本輪核心問題是手機報文中出現互相衝突或誤導的文字，例如：

- 證據不足｜S5/5 並存。
- insufficient/missing 狀態仍輸出「仍支持」。
- 條件：觀察：觀察天數未確認 雙詞拼接。
- 盤面：弱勢｜極強 強弱矛盾。
- 漏斗 count 與卡片分類不一致。
- 已修的持倉風控全列與排序不得回退。

## 使用者可見結果

手機閱讀報文需呈現保守且一致的狀態：

- Phase 0-1: source_status 非 available / derived 時，不得顯示可被理解為滿分強證據的 structure_score/strength，需顯示不可用或證據不足。
- Phase 0-2: status 為 insufficient / missing 時，不得輸出「仍支持」等偏正向表述，需改為保守表述。
- B1: 條件行不得出現 觀察：觀察... 雙詞拼接。
- B2: 趨勢為弱勢或遠離突破時，強度不得顯示 極強；不得出現 弱勢｜極強。
- B3/B4: v20.4.28 已修的持倉風控六檔完整列出與排序一致，不得回退。
- B5: 漏斗細分需與卡片一致，隔日確認 單獨計數，不得併入 等冷卻 或其他桶。

## 非目標

- 不改 RR 計算公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 DB write path、backfill 或 production DML。
- 不 live Telegram delivery。
- 不進入 evidence_score / decision_eligible / final_confidence / funnel evidence modifier major 改造。
- 不做 Phase 3 自動化生產。
- 不重設策略核心、不改交易狀態機。
- 不把本輪擴成全量報文重構或全量資料清理。
- 不新增未經 Owner 確認的策略語意。

## 影響模組與直接消費者

- 影響模組:
- report.py 或等價報文 formatter / Telegram message builder。
- 持倉風控列表與排序 formatter。
- 漏斗統計 formatter / card 分類對齊邏輯。
- 相關 formatter regression probes / tests。
- 直接消費者:
- Owner 手機 Telegram 報文閱讀路徑。
- runner 產出的 message list / report preview。
- QA 手機閱讀反證 probes。
- 不確定但需 Tech 先確認的既有契約:
- 實際版本常量 / header 所在檔案。
- B3/B4 v20.4.28 六檔持倉排序的正式 fixture 名稱。
- Phase 0 source_status 欄位來源與合法值是否已穩定為 available / derived / insufficient / missing。

## 輸出契約

### Phase 0-1 structure_score / strength 顯示門控

- 在輸出 structure_score 或 strength 前必須先檢查 source_status。
- source_status in {"available", "derived"}:
- 可依既有格式顯示分數與強度。
- source_status not in {"available", "derived"}:
- 不得顯示 S5/5、極強 或其他滿分 / 強勢字樣。
- 應顯示不可用或保守狀態，例如：
- 結構：證據不足｜不可用
- 結構：資料不足｜暫不評分
- 手機閱讀禁止形狀:
- 證據不足｜S5/5

### Phase 0-2 insufficient / missing 保守表述

- 當 status 為 insufficient 或 missing:
- 不得輸出 仍支持、支持進場、支持續抱 等偏正向判讀。
- 應輸出保守表述，例如：
- 證據不足，暫不支持行動
- 資料缺失，先保守觀察
- 不得因缺資料而升格成可買、可加碼、可續抱。

### B1 條件行去重

- 條件行若主狀態已是 觀察，原因文字不得再前綴同一個 觀察：。
- 手機閱讀允許形狀:
- 條件：觀察天數未確認
- 條件：觀察｜天數未確認
- 手機閱讀禁止形狀:
- 條件：觀察：觀察天數未確認

### B2 弱勢 / 遠離突破與強度一致

- 當盤面趨勢為 弱勢 或狀態語意為 遠離突破:
- 強度不得顯示 極強。
- 若需要顯示強度，必須降為保守 / 不可用 / 待確認語意。
- 手機閱讀禁止形狀:
- 盤面：弱勢｜極強
- 遠離突破｜極強

### B3/B4 已存在且不得回退的契約

- v20.4.28 已修契約需保留:
- 持倉風控六檔完整列出。
- 各區塊排序一致。
- 風控列與詳情卡順序一致。
- 若 Tech 無法確認上一輪正式契約或 fixture，必須 blocked，請 Architect 補充上一輪 CHANGELOG / QA_REPORT 或 fixture，不得自行猜測排序。

### B5 漏斗 count 對齊卡片

- 隔日確認 必須是獨立漏斗 count。
- 隔日確認 卡片不得被 count 到 等冷卻。
- 漏斗 summary 與卡片分組需一致：
- 卡片有 1 檔 隔日確認，漏斗也需顯示 隔日確認 1。
- 卡片無 等冷卻 時，漏斗不得因隔日確認而顯示 等冷卻 1。

## 版本契約

- 使用者可見報文 / Telegram header / CLI preview 若有版本字串:
- 不得回退低於上一輪 v20.4.28。
- 若本輪修正會改使用者可見報文語意，建議升版。
- 若 repo 無集中版本常量，Tech 需在 CHANGELOG 記錄「無版本字串可同步」與查核位置。
- QA 需核對實際 header / 常量與 Tech 聲明一致。

## 驗收條件

- Phase 0-1 probe: fixture 中 source_status=insufficient 或 missing 時，報文不得出現 證據不足｜S5/5。
- Phase 0-2 probe: fixture 中 status 為 insufficient / missing 時，報文不得出現 仍支持。
- B1 probe: 智原條件行不得出現 條件：觀察：觀察天數未確認。
- B2 probe: 智原或等價 fixture 中 弱勢 / 遠離突破 卡片不得出現 弱勢｜極強 或 遠離突破｜極強。
- B3/B4 regression: 持倉風控六檔完整列出，且 summary / 風控區 / 詳情卡排序一致。
- B5 probe: 漏斗 count 中 隔日確認 單獨計數，且 count 與卡片數量一致，不併入 等冷卻。
- QA 必須補一個 Tech 未覆蓋的手機閱讀反證，至少包含：
- 直接讀取產出的手機報文文字或 message list。
- 檢查禁止字串不存在。
- 檢查卡片分組與漏斗 count 一致。
- QA 結論只能是 通過、阻塞、conditional pass；若缺 fixture、缺版本來源、缺可重跑報文 artifact，不得宣告通過。

## 範例或 Fixture

### Phase 0 禁止輸出

結構：證據不足｜S5/5
狀態：資料不足，仍支持

### Phase 0 允許輸出形狀

結構：證據不足｜暫不評分
狀態：資料不足，先保守觀察

### B1 禁止輸出

智原
條件：觀察：觀察天數未確認

### B1 允許輸出形狀

智原
條件：觀察天數未確認

### B2 禁止輸出

智原
盤面：弱勢｜極強

### B2 允許輸出形狀

智原
盤面：弱勢｜待確認

### B5 允許輸出形狀

漏斗：
可買 0
隔日確認 1
等冷卻 0

卡片：
隔日確認
- 智原：等待隔日確認

## 明確禁止事項

- 禁止直接改策略核心分數、RR 公式或進出場判斷。
- 禁止新增 / 修改 DB schema 或 production write。
- 禁止 live Telegram 發送。
- 禁止把 insufficient / missing 補成假分數或假強度。
- 禁止用 local cache、worktree runtime dict 或聊天紀錄當跨日 source-of-truth。
- 禁止刪除或壓掉 B3/B4 已修契約。
- 禁止只改文案但不補可重跑 regression probe。
- 禁止只用 Tech 自檢代替 QA。
- 禁止本輪處理 evidence_score / final_confidence / funnel evidence modifier major 調整。

## 阻塞條件

- 找不到 report.py 或等價 formatter，且無法定位使用者可見報文產生路徑。
- 找不到可重跑的 report preview / message list / formatter test 入口。
- 找不到或無法重建 B3/B4 v20.4.28 六檔持倉排序契約。
- Phase 0 的 source_status / status 欄位來源不明，導致無法判斷 available / derived / insufficient / missing。
- 需要 DB schema、production write、live Telegram 或 major 策略改造才能完成時，必須停止並回 Architect / Owner，不得擅自擴 scope。
- stale worktree 或依賴環境導致 Tech / QA 無法在乾淨狀態重跑時，需標 blocked 並列實際錯誤。

## 本輪停止條件

本輪完成只代表 Phase 0 + B1-B5 前置修復 / 回歸完成，停止於：

- 所有指定禁止字串在可重跑手機報文 / formatter probes 中消失。
- B3/B4 已修六檔持倉契約未回退。
- B5 漏斗 count 與卡片分組一致。
- Tech 更新 CHANGELOG.md，QA 更新 QA_REPORT.md 且 L3 手機閱讀反證通過或明確 conditional / blocked。
- Architect 後續再處理 commit / push gate。

以下旁支問題只記待辦，不納入本輪：

- evidence_score / final_confidence / decision_eligible 的策略重構。
- funnel evidence modifier major 調整。
- Phase 3 自動化 production。
- DB source-of-truth 補強或 schema 變更。
- 新發現但不阻塞本輪驗收的其他報文噪音或排序偏好。
