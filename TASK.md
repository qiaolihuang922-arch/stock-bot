# TASK: per-stock evidence scoring, reliability fail-closed, funnel consistency, and Phase 3 alert guard closeout

## 任務狀態

- task_id: evidence-per-stock-reliability-funnel-phase3-closeout-20260602
- 任務類型: major
- 狀態: done
- Owner 優先級: E1 -> E3 -> E2/E4 -> E5 -> D1 -> D2/B5 -> A1
- 版本建議: 使用者可見報文文案 / 分類 / score line 會變更，需升版，不得回退目前 v20.4.30
- QA 分級建議: L3

## Owner 問題

目前 evidence chain 已進入 final_confidence 與漏斗邊界，但仍可能把報表級證據、資料不足證據或單一來源證據錯當成所有股票的可靠加分，造成手機報文出現以下硬風險：

- 不同股票共用同一個 evidence_score / modifier，沒有真正 per-stock。
- 資料依據不足時仍可能得到 confirmed / 滿額 score / +15%。
- 單一來源、supporting label 或 source-error looking payload 仍可能推到 ceiling。
- 卡片標題與未持倉漏斗 state 可能對同一標的不一致。
- Phase 3 前輪已落地，但需確認 scheduled path guard 與連續 N 日 unavailable/stale 告警是否完整；缺口才補，不得重造已完成實作。

## 使用者可見結果

手機 Telegram 報文需呈現更保守且一致的決策語意：

- 同一份報文中，不同題材 / setup 的股票可以有不同 證據 分數、evidence_modifier 與 綜合 分數。
- 資料不足時，不得顯示像 confirmed、強支撐或可加分的語氣。
- reliability 為 資料不足 時，背景說明改為：
- 短期背景資料不足，僅供觀察
- 卡片標題、未持倉漏斗、tracking_only_count、detail / manifest 對同一標的分類一致。
- source-error / missing / insufficient 的 market/theme evidence 不得包裝成 supporting。
- Phase 3 若連續 N 個已確認交易日 evidence unavailable/stale，需在既有報文或日誌路徑發出可追蹤告警；不得 live Telegram delivery。

手機閱讀示例形狀：

分數：綜合 76 / 技術 74 / 證據 82
證據：題材趨勢 confirmed｜同 setup 回測 supporting｜+8%

短期背景資料不足，僅供觀察

未持倉漏斗（非執行）
僅追蹤 3：隔日確認 1、等回測 2

不可出現示例：

資料不足｜仍支持目前背景觀察
source-error｜supporting｜+15%
卡片：隔日確認；漏斗：可準備

## 非目標

- 不改 RR 公式。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不做 live Telegram delivery。
- 不直接手寫 production DML。
- 不重做前輪已完成的 Phase 1/2/2b 或 Phase 3 實作；只能用證據確認已滿足，或補本輪明確缺口。
- 不新增交易策略核心規則或改變 hard blocker 定義。
- 不處理本輪外的文案降噪、全報文清理、資料治理或 mapping 擴表。

## 影響模組與直接消費者

影響模組：

- core/generator.py
- presentation/report.py
- scripts/run_phase3_evidence_automation.py
- .github/workflows/stock-bot.yml
- 相關 tests / probes，優先放在既有 generator report、market/theme evidence、phase3 automation 測試檔

直接消費者：

- Telegram 報文手機閱讀者。
- generate_report() message list / rendered report。
- pick_best_stock、watchlist sort、execution ordering 的 final confidence consumer。
- stock.<name>.risk.value / manifest 中的 score、funnel state、evidence adjustment consumer。
- Phase 3 scheduled evidence runner 與 GitHub Actions daily_evidence workflow。
- QA probe / regression tests。

## 輸出契約

### 1. per-stock evidence score

compute_evidence_score(report_context, name) 必須以 name 取該股自身證據：

- strategy_sample: 取同類 setup / 該股 setup 對應回測，不得用報表級單一值套所有股票。
- market_theme: 取該股所屬題材 / theme 的 trend，不得用報表級單一值套所有股票。
- 同一報表內兩檔不同題材或不同 setup，允許且應能得到不同：
- evidence_score
- evidence_modifier
- final_confidence

### 2. reliability / decision eligibility 門檻

confirmed_trend / decision_eligible 的滿額 score 門檻，必須與 presentation/report.py 目前可靠度門檻同口徑：

- 建議同時要求 observed >= threshold 且 streak 達標。
- 資料不足 / insufficient-data 時，對應 evidence score/status 不得為 confirmed。
- evidence insufficient 時不得產生正向 +15% modifier。

### 3. 加權合成與 modifier cap

加權合成需 fail closed：

- 單一可用來源不得直接給 ceiling 1.15。
- 使用加權合成，不得以不分來源品質的等權平均推到 ceiling。
- label=supporting 時 modifier 必須封頂於中間檔，例如 <= 1.08。
- 只有 confirmed 且雙源或足夠高可信來源時，才允許到 1.15。
- RR / overheat / chase / LIMIT_LOCK / no setup 等 hard blockers 不得因 evidence modifier 被放寬。

### 4. market/theme evidence payload fail closed

_market_theme_evidence_payload 必須先判斷 source status：

- 若 source_status in {missing-source, source-error, insufficient-data, unresolved-conflict}：
- status = unavailable
- score = None
- 不得再進入 supporting / weak / mixed 判斷

### 5. reliability 資料不足文案

presentation/report.py reliability 為 資料不足 時：

- 不再輸出 仍支持目前背景觀察
- 改輸出 短期背景資料不足，僅供觀察

### 6. 卡片與漏斗分類器一致

同一標的的卡片標題與 unheld_funnel_state 必須同源或等價同口徑：

- 卡片 state = 漏斗 state。
- 漲停反彈 統一為一種口徑：隔日確認 或 等回測，Tech 只能選一個並同步所有 consumer。
- tracking_only_count 必須包含同一口徑下的 隔日確認。
- 漏斗拆分加總 = 僅追蹤 總數 = 卡片實際數。

### 7. Phase 3 缺口收斂

前輪 commit 281be20 已宣告：

- daily_evidence schedule 已存在。
- scheduled path 不送 Telegram。
- trading day + 13:20 後才跑 daily snapshot 與 market/theme approved write CLI。
- unknown calendar / 休市 / source-error fail closed skip。
- stale alert 只按 confirmed trading day 累積。

本輪 Tech 必須先檢查上述是否仍成立：

- 若已滿足，CHANGELOG.md 寫證據與測試，不重複改。
- 若缺少 scheduled path guard、approved write path guard、或連續 N 日 unavailable/stale 報文 / 日誌告警，才補最小缺口。
- 告警只能走既有報文或日誌路徑，不得 live Telegram delivery。

## 版本契約

- 現有使用者可見版本不得低於 v20.4.30。
- 若改動任何 Telegram 報文文案、score line、漏斗分類、卡片標題或 visible alert，必須升 core/generator.py 的 VERSION。
- 若只補非可見 Phase 3 guard 且無報文輸出變更，可不升版，但 CHANGELOG.md 必須明確說明原因。
- 不得把「不要回退版本」解讀為「禁止升版」。

## 已存在且不得回退的契約

- c7dd94b 已落地 evidence score 進 final_confidence、pick/sort/execution ordering，報文分數拆為 綜合 / 技術 / 證據。
- missing evidence modifier = 1.0，不得改成正向加分。
- supporting_trend 只作 supporting score，不作 strong boundary evidence。
- single_day 不得 decision eligible。
- Phase 2b 只能把 near-boundary 調整到 可準備，不得直接變 可買。
- RR / overheat / chase / LIMIT_LOCK hard blockers 不得被 evidence 放寬。
- mixed adjusted + ordinary prepare 在 Summary / 漏斗 / card / detail index / manifest 必須一致。
- 281be20 Phase 3 scheduled path 不送 Telegram、不繞過 approved write CLI、不在交易日未知時寫入。
- v20.4.29 起 隔日確認 已是獨立 bucket；本輪可統一口徑，但不得把它重新混回推薦感 可買 / 可準備。
- 持倉卡、風控檢查、detail index 同序契約不得回退。

## 驗收條件

Tech 必須先補可重跑 probe 復現，再修實作。至少覆蓋：

1. per-stock evidence:
- 同一報表兩檔不同題材 / setup。
- 兩檔得到不同 evidence_score、evidence_modifier、final_confidence。
- 不得共享同一 report-level market/theme 或 strategy sample 值。
2. reliability insufficient:
- 資料依據不足時 score/status 不得 confirmed。
- 不得產生 +15%。
- confirmed_trend / decision_eligible 門檻與 report reliability threshold 一致。
3. weighted modifier:
- only one source available 不到 ceiling。
- label=supporting modifier <= 中間檔。
- confirmed 雙源可到 ceiling。
- hard blockers 仍阻擋可買 / 可準備升級。
4. market/theme fail closed:
- source-error 搭配 supporting-looking payload 時仍輸出 unavailable / score=None。
5. 手機閱讀文案:
- reliability 資料不足 時 rendered message 含 短期背景資料不足，僅供觀察。
- rendered message 不含 仍支持目前背景觀察。
6. 卡片 / 漏斗一致:
- 同一標的 card state = unheld_funnel_state。
- 隔日確認 / tracking_only_count 加總一致。
- 漏斗拆分之和 = 僅追蹤 總數 = 卡片實際。
7. Phase 3:
- 若前輪已滿足，測試證明 schedule guard / approved write path / no live Telegram 仍成立。
- 若補缺口，需測連續 N 個 confirmed trading days unavailable/stale 觸發報文或日誌告警。
- unknown calendar / source-error / 非交易日不得累積 stale 或寫入。

QA L3 必須至少補 Tech 未覆蓋的一條負面路徑，建議優先：

- source-error + supporting-looking market/theme payload。
- two stocks same report 不同 theme/setup。
- insufficient evidence 不得 +15%。
- card/funnel/tracking count 手機閱讀完整 rendered message。

最終 Architect 收口需在主 repo 跑相關 tests、commit、push、completion gate；PM 不批准跳過 Tech / QA。

## 範例或 Fixture

Tech 可用最小 fixture，不需接 production：

stock_a = {
"name": "A",
"setup": "breakout_pullback",
"theme": "ai_server",
"market_theme": {"source_status": "available", "label": "confirmed", "observed": 3, "streak": 3},
"strategy_sample": {"source_status": "available", "setup": "breakout_pullback", "label": "confirmed"},
}

stock_b = {
"name": "B",
"setup": "limit_rebound",
"theme": "shipping",
"market_theme": {"source_status": "insufficient-data", "label": "supporting", "observed": 1, "streak": 0},
"strategy_sample": {"source_status": "available", "setup": "limit_rebound", "label": "supporting"},
}

預期：

- A 可高於 B，但仍受 hard blockers 限制。
- B 不得 confirmed，不得 +15%。
- 若 B card 為 隔日確認，漏斗與 tracking count 也必須以 隔日確認 計。

source-error fixture：

payload = {
"source_status": "source-error",
"trend": "up",
"label": "supporting",
"observed": 5,
"streak": 5,
}

預期：

{"status": "unavailable", "score": None}

## 明確禁止事項

- 禁止改 RR 公式或 hard blocker 定義。
- 禁止改 DB schema / RLS / grant / policy / role。
- 禁止 live Telegram delivery。
- 禁止手寫 production DML 或繞過 approved write path。
- 禁止把 local cache / runtime dict / agent 對話當跨日 evidence source。
- 禁止用報表級 evidence 值套所有股票。
- 禁止資料不足時輸出 confirmed、滿額 score 或 +15%。
- 禁止卡片、漏斗、summary、detail、manifest 對同一標的分類不一致。
- 禁止重造前輪已完成 Phase 3；先用證據判斷缺口。

## 阻塞條件

若出現以下任一情況，Tech / QA 必須 blocked，不得宣告通過：

- 找不到現有 compute_evidence_score、_market_theme_evidence_payload、unheld_funnel_state 或 Phase 3 runner 入口，且無法確認直接 consumer。
- 無法建立同一報表兩檔不同 theme/setup 的可重跑 probe。
- reliability 門檻來源不明，無法判定 report.py:565 同口徑 threshold。
- Phase 3 scheduled write path guard 或 approved write CLI contract 無法讀取確認。
- 測試環境缺 pytest / dependency 且無法補環境。
- 任一 source-error / insufficient-data path 仍可得到 confirmed 或正向 ceiling。
- 需要 DB schema 變更或 live Telegram 才能完成。

## 本輪停止條件

完成範圍到以下為止：

- E1/E3/E2/E4/E5/D1/D2/B5/A1 缺口均有 probe 與實作證據，或前輪已滿足且有可重跑證據。
- 使用者可見報文版本契約處理完成。
- QA L3 通過，且 QA 至少新增 Tech 未覆蓋的負面反證。
- 主 repo related tests 通過。
- commit、push、git completion gate 完成。

以下旁支只記待辦，不納入本輪：

- 擴充 production theme membership mapping。
- 改交易策略核心或 RR。
- 新增 DB schema / backfill historical source-of-truth。
- 全報文文案清理。
- Telegram delivery 行為調整。
- 觀察第 N 天、持倉 execution memory 或其他跨日資料治理。
