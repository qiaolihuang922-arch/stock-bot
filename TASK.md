# TASK: v20.4.35-report-semantics

## 任務狀態

- task_id: v20.4.35-report-semantics
- 任務尺寸判斷: risk_patch
- 判斷理由: 本輪雖是四個小型報文語意修正，但會碰 evidence modifier、過熱 blocker、持倉資料行與簡報計數，屬使用者可見決策語意，不可當 tiny_patch。
- 狀態: ready_for_tech
- QA 分級建議: L3
- 版本建議: 維持並核對使用者可見報文版本 v20.4.35；不得回退。若實際 header / constant 尚未是 v20.4.35，Tech 需同步到 v20.4.35；本輪不主動升到其他版本。
- 本輪主問題: v20.4.35 報文語意一致性修正，只處理 Owner 指定四項。

## Owner 問題

Owner 要繼續執行已寫入 TASK.md 的 v20.4.35-report-semantics，完成四項修復並補 probe：

1. 過熱 / 不可追高所有 blocker 均使 evidence modifier = 1.0，且手機報文顯示「過熱不適用」。
2. 低量強度降級不得出現「突破確認 + 裸待確認」的可見衝突。
3. 持倉非加碼資料行仍需保留量比 V。
4. 簡報計數需明確區分「執行動作」與「今日新建倉」。

Owner 的「繼續」只代表啟動 PM -> Tech -> QA 流程，不授權 PM / Architect 跳過 Tech 或 QA，也不授權直接改產品代碼。

## 使用者可見結果

Telegram 手機閱讀路徑中，正式 generator / report text 應呈現：

- 過熱、不可追高、等冷卻、RR 過熱 blocker 成立的標的，不顯示任何 evidence boost；證據欄顯示「過熱不適用」，RR 維持 -（過熱） 或既有等價過熱 blocker 文案。
- 低量降級標的不得同時讓使用者讀到「突破確認」與裸「待確認」；需改成不衝突的形狀，例如 突破確認｜縮量觀察。
- 持倉非加碼資料行仍顯示既有持倉不適用，但保留量比，例如 數據：不適用（既有持倉）｜V 1.2x。
- 簡報計數不得使用裸 交易執行 N｜今日 M；需清楚顯示，例如 執行動作 1（減碼）｜今日新建倉 0。

## 非目標

- 不改 RR 公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 production write path。
- 不做 live Telegram delivery。
- 不改持倉狀態機或買賣策略核心。
- 不重構整份 generator / formatter。
- 不新增 Telegram 區塊。
- 不處理非本輪四項以外的排序、美化、文案降噪或資料品質問題。

## 影響模組

- core/generator.py
- evidence modifier / boost blocker 判定既有路徑
- 過熱 / 不可追高 / RR blocker 可見文案既有路徑
- 低量強度降級與卡片狀態文案既有路徑
- 持倉資料行格式化既有路徑
- 簡報 / summary 計數既有路徑
- 現有 generator / report tests 與 probe

若實際程式位置不同，Tech 只能在既有報文產生鏈內做最小修正，不得藉機搬移架構。

## 直接消費者

- Telegram 手機閱讀報文。
- official report generator 產出的 message list / report text。
- formatTelegramMessages 或等價 official formatter replay。
- 既有 report / generator regression tests。
- QA L3 replay / artifact 驗收。

## 輸出契約

### 過熱 / 不可追高 evidence 契約

任一過熱 blocker 成立時，evidence modifier 必須為 1.0：

- heat_state 為既有過熱 / 不可追高語意值。
- funnel / card 狀態為 等冷卻。
- funnel / card 狀態為 不可追高觀察 或等價不可追高狀態。
- RR 顯示為過熱 blocker。
- 既有 helper 如 should_show_overheat_rr_blocker(result) 回傳 true。

可見輸出必須符合：

- 不得顯示 證據 +8%、+15% 或任何 evidence boost。
- 證據欄顯示 過熱不適用 或既有等價過熱不適用文案。
- RR 維持 -（過熱） 或既有等價過熱 blocker 文案。

### 低量降級契約

- 同一標的同一手機可見區塊不得同時出現 突破確認 與裸 待確認。
- 低量降級需使用明確限定文案，例如 縮量觀察、突破確認｜縮量觀察，不得只追加裸 待確認。

### 持倉資料行契約

- 非加碼持倉可豁免 RR / 綜合 / 技術 / 證據。
- 非加碼持倉不得豁免量比 V。
- 可見形狀需保留：
數據：不適用（既有持倉）｜V {vol}x

### 簡報計數契約

- 簡報計數必須明確區分「執行動作」與「今日新建倉」。
- 示例形狀：
執行動作 N（減碼/停利/停損/加碼...）｜今日新建倉 M
- 今日新建倉 只計今天新建立倉位，不得混入減碼、停利、停損、續抱、觀察等執行動作。

### 已存在且不得回退的契約

- 無可買時不得使用推薦式文案。
- 可買、可準備、僅追蹤、淘汰 / 不可行動維持分開。
- 同一持倉在同一份報文只能有一個主行動。
- 今日買入後若轉弱，同行需說明跌破警戒、停損或策略失效；不得產生跨區塊矛盾。
- RR 公式與既有過熱 RR blocker 不可變更。
- DB payload / schema 不可變更。
- 使用者可見版本不得回退。
- probe 必須打到 official generator / report text 或等價 message-list replay，不得只驗 helper。

## 版本契約

- 本輪以 v20.4.35 為使用者可見版本契約。
- 若 code 已是 v20.4.35，保持不變並補驗 header / constant。
- 若 code 低於 v20.4.35，同步到 v20.4.35。
- 不得自行升到 v20.4.36+，除非 Architect 另行確認。
- QA 必須核對實際報文 header / version constant 與本 TASK 一致。

## 驗收條件

- 過熱 / 漲停鎖價 replay：
- 條件包含漲幅約 +9.89%、不可追高或 RR 過熱 blocker 成立。
- 預期 evidence modifier = 1.0。
- 報文顯示 證據：過熱不適用。
- 報文不得出現 證據 +8% 或任何 boost。
- RR 顯示 -（過熱） 或等價過熱 blocker。
- 不可追高 / 等冷卻 replay：
- 即使 heat_state 不是 EXTREME，只要可見狀態屬不可追高 / 等冷卻 / RR 過熱 blocker，就不得取得 evidence boost。
- 預期同樣顯示 過熱不適用 且 modifier = 1.0。
- 低量強度降級 replay：
- 原會出現 突破確認 + 待確認 的建準等價案例，修後同一標的同一區塊不得再出現裸 待確認。
- 可接受形狀如 突破確認｜縮量觀察。
- 持倉非加碼 replay：
- 旺宏 / 建準等價既有持倉、非加碼案例。
- 預期資料行包含 不適用（既有持倉）。
- 同一行仍包含 V {vol}x。
- 簡報計數 replay：
- 有減碼 / 停利 / 停損等執行動作且今日新建倉為 0。
- 預期顯示 執行動作 1（減碼）｜今日新建倉 0 或等價清楚形狀。
- 不得讓 今日 裸字被誤讀為今日所有交易動作。
- QA 必須至少補一個 Tech 未覆蓋的使用者誤讀、負面案例或契約風險。
- QA 不得只重跑 Tech 命令後宣告通過。

## 範例或 Fixture

- 光寶科過熱：
- 條件：漲停鎖價、漲幅約 +9.89%、RR 過熱 blocker 成立。
- 預期：RR：-（過熱）、證據：過熱不適用、modifier = 1.0。
- 建準低量降級：
- 條件：原本同時出現 突破確認 與裸 待確認。
- 預期：只保留不衝突文案，例如 突破確認｜縮量觀察。
- 旺宏 / 建準持倉非加碼：
- 條件：既有持倉、非加碼。
- 預期：數據：不適用（既有持倉）｜V 1.2x 類似形狀。
- 簡報計數：
- 條件：有一個減碼執行動作、今日新建倉為 0。
- 預期：執行動作 1（減碼）｜今日新建倉 0。

## 失敗標本與驗收路由

- Owner 指定四項即為本輪 failure specimen。
- 驗收路由需覆蓋：
- helper / modifier 層：確認過熱 blocker 導致 modifier = 1.0。
- formatter 層：確認可見文案為 過熱不適用、不出現裸 待確認、持倉保留 V、簡報計數去歧義。
- official generator / message-list replay 層：確認手機報文最終文字符合契約。
- 若 Tech 只能覆蓋 helper 或 formatter，CHANGELOG.md 必須標 partial 並列未覆蓋的 official generator / report text 層。
- 若 QA 拿不到等價 replay artifact，結論最多只能是 conditional pass。

## 明確禁止事項

- 禁止改 RR 公式。
- 禁止改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止改 production write path。
- 禁止 live Telegram delivery。
- 禁止把本輪擴成策略重設、全量清理、全量報文重構。
- 禁止用 synthetic helper fixture 取代 official generator / report text 驗收。
- 禁止讓過熱 / 不可追高 / 等冷卻標的顯示任何 evidence boost。
- 禁止讓同一標的手機可見文字同時表達 突破確認 與裸 待確認。
- 禁止讓非加碼持倉資料行遺失 V。
- 禁止把減碼 / 停利 / 停損等執行動作計入 今日新建倉。

## 阻塞條件

- 找不到 official generator / report replay 路徑可產出等價手機報文時，Tech 必須標 partial，QA 最多 conditional pass。
- 無法建立光寶科、建準、旺宏等價 fixture / replay 時，不得宣告完整完成。
- 若實際程式不存在 Owner 指定語意欄位或 helper，Tech 不可自行改策略，需回報 Architect 釐清。
- 若修正需要 RR 公式、DB schema、production write path 或 live delivery 變更，立即 blocked。
- 若版本 header / constant 無法核對，QA 不得給 通過。

## 本輪停止條件

驗到以下四項在 official generator / report text 或等價 replay artifact 中成立，即本輪可停止：

1. 過熱 / 不可追高 / 等冷卻 blocker 使 evidence modifier = 1.0，且顯示 過熱不適用。
2. 低量降級不再出現 突破確認 + 裸待確認。
3. 非加碼持倉資料行保留 V {vol}x。
4. 簡報計數明確區分 執行動作 與 今日新建倉。

以下旁支只記待辦，不納入本輪：

- 其他標的分數爭議。
- 其他報文排序或美化。
- 其他 evidence 資料品質問題。
- 新增 Telegram 區塊。
- formatter 架構清理。
- production DB 補資料、回寫或 backfill。
