# TASK: funnel 過熱未持倉不得計入可準備

## 任務狀態

- task_id: risk_patch_unheld_funnel_overheat_prepare_fix
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見 Telegram / 報文漏斗語意有變更，需檢查並同步既有報文版本字串；不得回退既有版本。
- QA 分級建議: L2，因影響未持倉漏斗分類與手機決策閱讀，但不改策略 decision、RR 公式、DB 或 live delivery。

## Owner 問題

core/generator.py 的 unheld_funnel_state() 在 market_mode='進攻偏熱' 且 strong_prepare_bucket 回傳 prepare_label 時，會把部分未持倉標的歸入 可準備。但 RR 被 should_show_overheat_rr_blocker(result, holding=False) 抑制、
heat_state 為 HOT / EXTREME、或 strong_prepare_bucket label='過熱降溫' 的標的，實際手機閱讀上應是過熱待冷卻 / 待回測，不能被漏斗算作 可準備 / 不可追高觀察 N（不可買），否則卡片標題、漏斗、summary 自相矛盾。

## 使用者可見結果

- 未持倉過熱標的不再出現在 可準備 計數或「不可追高觀察」類似可準備文案中。
- 這類標的應進入既有「僅追蹤」拆分，例如 等冷卻 / 等回測；優先使用現有分類，不新增大結構。
- 手機閱讀路徑需一致：
- Summary: 新倉不可買時不得暗示可準備。
- 漏斗: 過熱標的計入 等冷卻 / 等回測，不計入 可準備。
- 卡片: 標題如 過熱待回測 時，所屬漏斗分類不得是 可準備。

示例輸出形狀：

Summary:
新倉：無有效進場；過熱標的先等冷卻 / 回測。

未持倉漏斗:
可準備 0
僅追蹤:
- 等冷卻 1
- 等回測 0

卡片:
ABC｜過熱待回測｜僅追蹤：等冷卻

## 非目標

- 不改 strategy decision。
- 不改 RR 公式、RR blocker 判斷本身。
- 不改 DB schema、RLS、grant、policy、role、index / constraint。
- 不改 DB write path、backfill 或 production 資料。
- 不做 live Telegram delivery。
- 不處理其他修復清單項。
- 不重構整個漏斗、summary 或持倉狀態機。

## 影響模組與直接消費者

- 影響模組:
- core/generator.py
- 既有未持倉 funnel / Telegram 報文生成測試或 probe
- 直接消費者:
- Owner 手機閱讀的 Telegram 報文 summary
- 未持倉漏斗分組與 count
- 未持倉標的卡片標題 / 狀態文字
- CI / local 可重跑 probe

## 輸出契約

- unheld_funnel_state() 對未持倉標的分類必須滿足：
- 若 should_show_overheat_rr_blocker(result, holding=False) 為 true，不得回傳或計入 可準備。
- 若 heat_state 為 HOT 或 EXTREME，不得回傳或計入 可準備。
- 若 strong_prepare_bucket label 為 過熱降溫，不得回傳或計入 可準備。
- 上述標的應歸入既有明確不可進場 / 僅追蹤分類，優先為 等冷卻 或 等回測。
- 非過熱、未被 RR blocker 抑制、且符合既有強勢準備條件的未持倉標的，仍維持既有 可準備 行為，不得誤降級。
- 漏斗 count、卡片標題、summary 三者語意必須一致：
- 卡片顯示過熱 / 待回測時，漏斗不得把同一標的算作 可準備。
- Summary 不得把過熱標的寫成可買或可準備。
- 已存在且不得回退的契約:
- 可買、可準備、僅追蹤、淘汰 / 不可行動分組需保持分離。
- 無可買時不得使用像推薦的文案。
- 空區塊、0-count、無新增下單占位預設不顯示，除非既有報文已固定顯示。
- 同一未持倉標的在同一份報文內只能有一個主分類。
- 不改既有 public payload shape，除非 Tech 證明現有分類無法承載且回報 blocked。

## 版本契約

- 若 Telegram 報文 header / version 常量存在，Tech 必須檢查是否需升版並在 CHANGELOG.md 寫明。
- 不得回退既有版本字串。
- 若本修正只改分類邏輯但既有版本規則要求使用者可見報文變更需升版，需同步升版。

## 驗收條件

1. 可重跑 probe 覆蓋過熱待回測未持倉：
- 修復前會落入 可準備 count 的 fixture，修復後不得落入 可準備。
- 修復後應落入 等冷卻 或 等回測 count。
- 卡片標題、漏斗分類、summary 三處語意一致。
2. 可重跑 probe 覆蓋 RR blocker：
- should_show_overheat_rr_blocker(result, holding=False) 為 true 的未持倉標的不得計入 可準備。
3. 可重跑 probe 覆蓋普通強勢準備：
- 非過熱、非 RR blocker、符合既有 strong prepare 條件的未持倉標的仍計入 可準備。
4. QA 需補一個 Tech 未覆蓋的反證路徑：
- 手機閱讀路徑檢查 summary / 漏斗 / 卡片是否出現同一標的一邊過熱待回測、一邊可準備的矛盾。
- 或檢查 heat_state HOT/EXTREME 與 label='過熱降溫' 任一分支不漏判。

## 範例或 Fixture

- fixture A: 未持倉、market_mode='進攻偏熱'、strong_prepare_bucket 原本回傳 prepare label、卡片標題可顯示 過熱待回測、heat_state='HOT'
- expected: 可準備 count 不增加；等冷卻 或 等回測 count 增加；summary 不寫可準備。
- fixture B: 未持倉、RR 被 should_show_overheat_rr_blocker(result, holding=False) 抑制
- expected: 不進 可準備；進既有不可進場 / 僅追蹤分類。
- fixture C: 未持倉、strong_prepare_bucket label='過熱降溫'
- expected: 不進 可準備；優先進 等冷卻。
- fixture D: 未持倉、非過熱、非 RR blocker、普通強勢準備
- expected: 維持既有 可準備 分類。

## 明確禁止事項

- 禁止改 strategy decision 結果。
- 禁止改 RR 計算公式或 blocker 條件定義。
- 禁止新增 / 修改 DB schema、DB write、production DML 或 backfill。
- 禁止 live Telegram delivery。
- 禁止把本輪擴成全漏斗重構、全報文重排或其他清單項修復。
- 禁止用對話記憶或 local cache 當跨日狀態來源。
- 禁止只改文案而不補可重跑 probe。

## 阻塞條件

- 若現有分類沒有任何可承載 等冷卻 / 等回測 / 明確不可進場的既有 bucket，Tech 必須 blocked，回報需要 PM / Architect 決定是否新增分類。
- 若無法構造可重跑 fixture 或 probe 來重現修復前後差異，Tech 不得宣告完成。
- 若版本字串位置不明且報文版本契約無法確認，Tech 需在 CHANGELOG.md 標記 partial 或 blocked，由 Architect 補上下文。
- 若改動需要 DB schema/write 或 live Telegram，立即 blocked，因超出本輪授權。

## 本輪停止條件

- 完成到以下範圍即停止：
- unheld_funnel_state() 對過熱 / RR blocker / 過熱降溫 未持倉不再歸入 可準備。
- 過熱待回測 fixture 的 summary / 漏斗 / 卡片一致。
- 普通非過熱強勢準備 fixture 不被誤降級。
- Tech 提供可重跑命令與結果，QA 提供至少一個額外反證。
- 以下旁支只記待辦，不納入本輪：
- 其他清單項。
- 全量漏斗分類命名優化。
- 策略買賣判斷調整。
- DB 持久化或 production Telegram delivery。
