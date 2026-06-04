# TASK: evidence-chain decision layers

## 任務狀態

- task_id: evidence_chain_decision_layers_v20_4_43
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見報文內容變更，建議升版到 v20.4.43；若實際 core/generator.py VERSION 不是 v20.4.42，Tech 必須先 blocked 回報。
- QA 分級建議: L3
- 任務尺寸判斷: 會影響買 / 準備 / 趨勢延續 / 不可買資格層與決策說明，屬 risk_patch；本輪只接既有 evidence-chain manifest/artifacts，不做策略重設或卡片 redesign。

## Owner 問題

Owner 要延續目前 evidence_chain_decision_layers 任務：保留現有可見卡片樣式，但把既有 evidence-chain manifest/artifacts 接入決策說明與 eligibility states。

核心問題是：每檔股票判斷必須有可回溯 evidence；缺 evidence、證據衝突、source-error 時 fail closed。證據達既有門檻時，要能區分 blocked/non-buy、prepare、trend_continuation、buy，但不得全域放寬 RR不足、過熱、突破失敗、
source-error、hard stop、DB/live restrictions 等硬閘門。

## 使用者可見結果

- 手機 Telegram 報文維持 v20.4.42 現有卡片顯示風格、密度與主要順序。
- 每張股票卡片的主判斷都有 evidence-backed reason。
- 使用者能看出股票目前是：
- blocked / non-buy：不可買，且有明確阻塞 evidence 或硬閘門。
- prepare：證據達準備門檻，但仍不可下單。
- trend_continuation：趨勢延續證據達標，仍只走既有小倉 / 趨勢延續契約。
- buy：必要 evidence 與硬閘門均通過。
- 無可買時仍使用不可買語氣，例如「新倉：無有效進場」，不得像推薦。

## 非目標

- 不重新設計 Telegram 卡片。
- 不全域放寬 hard gates。
- 不新增或修改 DB schema / RLS / grant / policy / role / index / constraint。
- 不做 DB write、backfill、manual DML 或 live Telegram delivery。
- 不新增策略門檻研究；若 threshold 不存在或矛盾，本輪 blocked。
- 不處理 unrelated wording cleanup、排序重構、全量資料治理或卡片美化。

## 影響模組

- 既有 evidence-chain manifest/artifact 載入與解析層。
- eligibility / gating 判斷層。
- decision explanation builder。
- official Telegram generation path：formatTelegramMessages 或等價 full message-list replay。
- 現有 summary / funnel / index / card 狀態一致性輸出。

## 直接消費者

- Owner 手機 Telegram 閱讀路徑。
- official report generator / runner artifact consumer。
- QA replay 驗收路徑。
- 依賴 eligibility state 的 summary、漏斗、索引與卡片 renderer。

## 輸出契約

每個 stock judgment 必須能映射到 evidence-chain 結果，至少包含：

- symbol
- eligibility_state: blocked | non_buy | prepare | trend_continuation | buy
- primary_action: 同一股票同一報文只能一個主行動。
- evidence_status: ok | missing | conflicting | source_error | insufficient
- evidence_refs: manifest/artifact reference id、source key 或等價可追溯欄位。
- blocking_reasons: hard gate / fail-closed 原因。
- progress_reasons: 已達標證據與下一步仍需條件。

Hard gates 不得被 evidence boost 覆蓋：

- unresolved RR不足
- overheat / EXTREME
- failed breakout
- source-error / missing-source / conflicting evidence
- hard stop
- DB / live restrictions

報文契約：

- 保留現有卡片外觀與主要欄位順序。
- 只在既有 status / reason / detail 區域補 evidence-backed 狀態。
- 可買、可準備、僅追蹤、淘汰 / 不可行動語意必須一致。
- 空區塊、0-count、無新增下單占位預設不顯示。

## 版本契約

已存在且不得回退：

- 目前可見報文版本為 v20.4.42。
- v20.4.42 未持倉非可買卡片兩行 attribution：卡關主因 / 量化差距 不得退回單行難讀格式。
- 真正可買與 trend_continuation 小倉 BUY 不顯示卡關兩行。
- 盤後 ordinary prepare 不得寫成可買或新倉建議。
- trend_continuation BUY 仍限既有小倉契約，不得變成一般 BUY。
- source-error / missing-source / insufficient-data fail closed。
- official Telegram path 優先於 helper-only fixture。

## 驗收條件

- 用 official formatTelegramMessages 或等價 full message-list replay 驗證完整手機閱讀路徑。
- replay 中每張股票卡片都有 evidence-backed reason 或 fail-closed reason。
- manifest missing、artifact source-error、conflicting evidence 至少各有一個反證案例，且不得輸出 buy / 推薦式文案。
- prepare 案例顯示已達準備門檻與仍未過阻塞，不得讓手機讀者誤認可下單。
- trend_continuation 案例在 evidence 達標時可顯示趨勢延續，但遇 RR不足 / overheat / failed breakout / source-error / hard stop 任一未解時 fail closed。
- buy 案例必須證明必要 evidence 與 hard gates 均通過。
- QA 必須補一個 Tech 未覆蓋的反證路徑，不得只重跑 Tech 命令。

## 範例或 Fixture

手機輸出形狀示例，實際文案可沿用現有卡片風格：

【2330】準備｜不可買
主因：趨勢證據達準備門檻，仍待 RR 修復
證據：trend ok；breakout ok；rr insufficient
阻塞：RR不足 unresolved
行動：不新倉，等待 RR 修復

【2317】不可買
主因：突破失敗，且 evidence-chain 來源衝突
證據：breakout conflicting
阻塞：failed breakout；source-error
行動：不可行動

【2454】可買
主因：趨勢、突破、RR、風控證據均達標
證據：trend ok；rr ok；risk ok
阻塞：無
行動：依現有新倉規則

失敗標本與驗收路由：

- 優先使用最近 Owner 完整 Telegram 報文 specimen。
- 若 specimen 不在可讀上下文，Tech 必須產生等價 official full message-list replay artifact。
- 驗收路由必須覆蓋：production-like payload -> evidence-chain manifest/artifacts -> eligibility -> official Telegram message list。

## 明確禁止事項

- 禁止 live Telegram。
- 禁止 DB schema/write/backfill/manual DML。
- 禁止卡片 redesign。
- 禁止只驗 helper / formatter 就宣稱使用者可見完成。
- 禁止把缺證據、證據衝突或 source-error 顯示成可買。
- 禁止把 prepare 寫成推薦買入。
- 禁止全域放寬 RR、overheat、failed breakout、source-error、hard stop。
- 禁止 Tech 自行發明未存在的 evidence thresholds。

## 阻塞條件

- 找不到既有 evidence-chain manifest/artifacts。
- manifest/artifact 欄位不足以支援每檔 decision explanation。
- prepare / trend_continuation / buy thresholds 未定義或互相矛盾。
- 找不到 Owner specimen，且無法產生等價 official full message-list replay。
- 實際 VERSION/header 與 v20.4.42 基準不明。
- 必須 DB write、schema change 或 live delivery 才能驗收。

## 本輪停止條件

完成到 official Telegram replay 層即停止。完成定義：

- 至少一份完整 replay 報文證明每張卡片 judgment evidence-backed。
- missing / conflicting / source-error fail closed。
- hard gates 未被放寬。
- blocked/non-buy、prepare、trend_continuation、buy 在現有卡片格式中可被手機讀者區分。
- QA 結論為 通過，或明確 conditional pass / 阻塞 並列出缺口。

旁支只記待辦，不納入本輪：

- 新策略門檻研究。
- 卡片視覺 redesign。
- DB 持久化治理。
- live 發送。
- unrelated wording cleanup。
- 全市場資料品質治理。
