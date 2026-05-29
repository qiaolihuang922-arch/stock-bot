# TASK: DB Strategy Consumption Phase 1 - Cross-day State And Evidence Weight

## 任務狀態

- task_id: db_strategy_consumption_phase1_cross_day_state_evidence_weight_20260529
- 任務類型: risk_patch
- 任務尺寸: risk_patch
- 狀態: todo
- 版本建議: minor，建議升為 v20.4.0
- 版本契約: 本輪會改變使用者可見 Telegram / CLI 報文中的排序、摘要、狀態說明或證據權重，因此必須同步 core/generator.py 的 VERSION 或等價 header 常量到 v20.4.0，並同步測試期望。
- QA 分級建議: L3-lite
- QA 升級原因: 本輪讀取 DB 歷史資料影響策略記憶、證據權重、持倉去重與使用者可見排序/摘要；需驗證 DB 有資料時有效、DB 缺資料時 fail closed、不回退 v20.3.1 fake-data fail-closed、不改核心可買門檻。
- 停止條件: Phase 1 只完成「讀既有 DB/本地 store path -> 產生跨日狀態與證據權重 -> 影響排序/摘要/去重邊界」；不得擴成 schema 設計、正式 backfill、核心買賣門檻重設、watchlist 改造或完整策略重寫。

## Owner 問題

DB 多表已經有資料，但策略目前缺少跨日記憶與歷史證據權重，導致：

1. 同一檔連續多天一直觀察，沒有因連續修復或連續失效而升級/降級排序。
2. 已停利或已減碼後，下一輪仍可能重複建議同級停利/減碼。
3. 漲很多但長期淘汰的股票沒有進入「準備層」觀察，Owner 看不到它是否正在修復。
4. 今日買入後，下一輪或同日後段又出現反向賣出/減碼建議，形成跨日或同日狀態斷裂。

Owner 已確認開始 Phase 1。目標是讓既有 DB/本地 store path 先負責策略記憶與證據權重，但不直接改核心買賣門檻。

## 使用者可見結果

Owner 在 Telegram / CLI 報文中應看到：

- 同一檔股票能顯示前次狀態與連續觀察脈絡，例如連續觀察、連續修復、連續失效。
- 已停利/已減碼的持倉不再被同級動作重複推送；若仍有更高級風控或硬停損，必須清楚說明觸發條件。
- 長期淘汰但近期快速修復或上漲的股票，可以進入「可準備 / 僅追蹤」排序優先級提升，但仍不得被 DB 權重單獨改成可買。
- 今日買入後，預設主行動是新倉風控觀察；若訊號轉弱，只能升級為風控觀察或有條件停損警戒，不得無脈絡反向賣出。
- DB 缺資料、DB 錯誤、欄位不足或來源不可信時，報文不得補假歷史、假連續天數、假權重或假今日事件；只能降級為無歷史證據或 fail closed。

手機閱讀路徑：

1. Owner 打開 Telegram 先看 summary：今天能不能買、持倉先處理什麼、未持倉哪些只是準備/追蹤、哪些不可行動。
2. 再看執行清單：已停利/減碼不重複，同一檔只有一個主行動。
3. 再看未持倉漏斗：可買 / 可準備 / 僅追蹤 / 淘汰 分層不混桶。
4. 最後看個股詳情：可追溯前次狀態、連續觀察天數、修復/失效、歷史證據權重來源。

## 非目標

- 不新增 DB schema、migration、table、column 或 index。
- 不做 live Supabase write。
- 不做 live Telegram delivery。
- 不做正式 backfill。
- 不改 watchlist。
- 不大改核心買賣門檻、BUY/SELL/RR/停損停利門檻。
- 不把 DB 歷史權重單獨作為「不可買 -> 可買」的決策依據。
- 不把缺失 DB 資料補成 fake/default/synthetic/fallback。
- 不重寫整個 analysis engine、generator 或 store layer。
- 不修本輪以外的報文噪音、外部市場 evidence、RLS、效能或資料建置問題；只可記入殘留風險或後續待辦。

## 影響模組

Tech 可依完整 repo 實際命名定位，但最小影響面應優先限於：

- DB / store read path:
- daily_signal_snapshot
- signal_runs
- signal_items
- signal_outcomes
- strategy_feature_snapshots
- strategy_outcome_metrics
- strategy_classification_audit
- positions
- position_events
- 既有 local store path
- 直接接入模組:
- services/analysis.py
- core/generator.py
- services/position_store.py
- services/signal_store.py
- services/daily_snapshot_store.py
- services/strategy_evidence.py
- core/signal_snapshot.py
- core/signal_validator.py
- 測試:
- 直接 formatter / generator tests
- analysis contract tests
- position/event dedupe tests
- DB missing-source / fail-closed tests

若 repo 中已有等價 helper，Tech 必須優先復用既有 store / provider，不新增平行讀取層。

## 直接消費者

- services/analysis.py: 消費 Phase 1 state/evidence context，用於排序、優先級、狀態降級/升級提示與持倉行動一致性 guard。
- core/generator.py: 消費已計算好的 cross-day context，輸出手機可讀 summary、卡片狀態、詳情追溯與版本 header。
- services/position_store.py: positions / position_events 的 source-of-truth 讀取與 fail-closed metadata。
- services/signal_store.py、services/daily_snapshot_store.py、services/strategy_evidence.py: 既有 DB / local store 資料讀取來源；不得偽造資料。
- Telegram Owner: 最終消費者；看到的是排序、摘要、行動去重與歷史證據說明。
- QA: 驗證 DB 有資料與缺資料兩條路徑、核心可買門檻不變、v20.3.1 fail-closed 不回退。

## 輸出契約

### Phase 1 context contract

Tech 必須提供或接入一個明確的 cross-day context，欄位可用 dict/dataclass/現有 result extension，但必須有等價語意：

- symbol: 股票代號。
- source_status: ready / missing-source / source-error / insufficient-data。
- source_of_truth: 實際使用的 table 或 local store path 名稱列表。
- previous_state: 前次分類或主狀態，例如 buyable / prepare / observe / eliminated / holding / take_profit_observed / reduced_observed / unknown。
- previous_action: 前次主行動，例如 buy / hold / observe / reduce / take_profit / stop_loss / none / unknown。
- previous_action_date: 前次主行動日期；缺資料為 None 或 unknown，不得補今日。
- consecutive_observe_days: 連續觀察天數；只能由可信歷史資料計算，缺資料為 0 或 unknown，不得假設。
- repair_status: repaired / improving / unchanged / deteriorating / failed / unknown。
- failure_status: invalidated / cooling / still_valid / unknown。
- historical_evidence_weight: 有界權重，建議範圍 -2..+2 或等價 enum；缺資料必須為 0 或 unknown。
- weight_reason: 短 reason list，最多 1-3 條，說明權重來源。
- dedupe_guard: same_day_executed / prior_take_profit_completed / prior_reduce_completed / new_position_guard / none / unknown。
- allowed_effects: 本輪允許此 context 影響的面向，例如 sort_priority / summary_wording / prepare_promotion / duplicate_action_suppression / risk_note。
- forbidden_effects: 必須包含 cannot_flip_to_buy_alone；必要時包含 cannot_override_hard_stop / cannot_fake_execution / cannot_confirm_market_evidence。

### 允許影響

DB 歷史與 evidence weight 可以影響：

- 同一分組內排序，例如連續修復優先於普通觀察。
- 淘汰 -> 僅追蹤 或 僅追蹤 -> 可準備 的呈現優先級，但只限已有當日條件支持時。
- summary 中「追蹤最強 / 修復中 / 連續失效 / 停利後觀察」等文案。
- 已停利/已減碼後的同級重複建議抑制。
- 今日買入後的新倉風控觀察 guard。
- 詳情中的歷史證據追溯。

### 禁止影響

DB 歷史與 evidence weight 不得單獨造成：

- 不可買 -> 可買。
- 淘汰 -> 可買。
- 可準備 -> 交易執行清單。
- 放寬 BUY / SELL / RR / 過熱 / 漲停不追 / 停損停利核心門檻。
- 在 DB 缺資料時輸出連續天數、已執行事件、持倉、價格或 confirmed evidence。
- 覆蓋 v20.3.1 的 source warning fail-closed 行為。
- 把 dry-run/backfill fixture 當 production runtime truth。

### Source-of-truth 要求

Tech 必須在 CHANGELOG.md 列出每個來源的 source-of-truth 與 fail-closed 行為：

- positions: production truth 或 Owner-defined holding source；source-error/missing-source 不得回全 watchlist 0 股。
- position_events: execution/history truth；source-error/missing-source 不得回全 0 event summary。
- daily_signal_snapshot: cross-day state candidate；缺失只能代表無 snapshot 證據，不代表狀態不存在。
- signal_runs/signal_items/signal_outcomes: signal history / outcome evidence candidate；缺失只能降級為無 evidence。
- strategy_feature_snapshots: feature history candidate；不得用過期 feature 覆蓋當日硬門檻。
- strategy_outcome_metrics: historical weight candidate；只能調整證據權重/排序，不得單獨改買賣門檻。
- strategy_classification_audit: previous classification source candidate；若缺資料，不得假設前次分類。
- local store path: 只能作為既有契約中的 read fallback；必須標示來源與可信度，不得默默優先於 production DB truth。

## 驗收條件

1. CHANGELOG.md 必須從 # CHANGELOG: 開始，列出實際修改檔案、source-of-truth、fail-closed 行為、直接消費者同步與自檢命令。
2. 使用者可見版本 header 必須升為 v20.4.0 或等價版本，且測試同步。
3. DB 有可信歷史資料時，至少一個 fixture 能證明 previous_state、consecutive_observe_days、repair_status/failure_status 或 historical_evidence_weight 會影響排序、summary 或詳情追溯。
4. DB 有可信 execution/history 資料時，至少一個 fixture 能證明已停利/已減碼後不重複同級建議。
5. 今日買入後下一輪或同日後段的 fixture 必須顯示 新倉風控觀察 或有條件風控警戒，不得無脈絡反向賣出。
6. 長期淘汰但近期修復/大漲的 fixture 可進入準備或追蹤優先呈現，但不得進入交易執行清單，且必須標示不可買或待觸發。
7. DB missing-source/source-error/insufficient-data 時，不得輸出假前次狀態、假連續天數、假 evidence weight、假今日事件或假持倉；必須 fail closed 或降級為無歷史證據。
8. 核心可買門檻不變：同一當日信號在沒有滿足原本 BUY 條件時，不得因歷史 evidence weight 變成 可買。
9. 不得回退 v20.3.1 fake-data fail-closed：positions / position_events / runtime fallback 不可重新產生 fake/default/synthetic 結論。
10. Telegram 手機閱讀順序必須行動優先：持倉風控與已持倉風險處理優先於新觸發/待觸發事項。
11. 同一檔同一份報文只能有一個主行動；summary、持倉卡、執行清單、詳情不得互相衝突。
12. Forbidden diff 檢查必須確認無 DB schema/migration、無 live Supabase write、無 live Telegram、無正式 backfill、無 watchlist diff。
13. 若 Tech 發現既有 DB 欄位不足以可靠計算某欄位，該欄位必須輸出 unknown 或不顯示，並在殘留風險列待辦；不得補假值。
14. QA 必須補至少三類反證：DB 缺資料、核心可買門檻不變、停利/減碼不重複。

## 範例或 fixture

### Fixture A: 連續觀察修復，只影響排序/摘要

輸入形狀：

symbol: "2330"
today_classification: "observe"
today_buy_gate: false
db_history:
previous_state: "observe"
consecutive_observe_days: 4
repair_status: "improving"
historical_evidence_weight: 1

期望輸出形狀：

Summary:
新倉：無有效進場
追蹤最強：2330 修復中，連續觀察 4 天，不可買，待觸發

未持倉:
可準備 1
- 2330｜修復中｜連續觀察 4 天｜不可買｜待突破/回測確認

不得輸出：

可買：2330
交易執行：買 2330

### Fixture B: 已停利/減碼，不重複同級建議

輸入形狀：

symbol: "2356"
holding: true
today_signal_action: "take_profit"
db_position_events:
previous_action: "take_profit"
previous_action_date: "2026-05-29"
executed_level: "same_level"

期望輸出形狀：

持倉優先:
2356｜停利後觀察｜今日已停利，同級不重複｜剩餘部位續看風控

不得輸出：

2356｜第二次同級停利
2356｜本次建議再賣同級股數

### Fixture C: 今日買入後轉弱，不無脈絡反向賣出

輸入形狀：

symbol: "3017"
today_position_event: "buy"
later_signal_weakened: true
hard_stop_triggered: false

期望輸出形狀：

持倉優先:
3017｜新倉風控觀察｜今日買入後轉弱，不加碼；未跌破停損，先觀察

若硬停損觸發，才可輸出：

3017｜停損警戒｜今日買入後跌破停損條件，依風控處理

### Fixture D: DB 缺資料 fail closed / 無歷史證據

輸入形狀：

symbol: "3661"
db_status: "source-error"
today_signal_action: "observe"

期望輸出形狀：

3661｜僅追蹤｜歷史證據不可用，未納入連續天數/權重

不得輸出：

連續觀察 3 天
歷史勝率支持
今日無交易已確認

## 明確禁止事項

- 禁止新增或修改 DB schema、migration、table、column、index。
- 禁止 live Supabase write。
- 禁止 live Telegram delivery。
- 禁止正式 backfill。
- 禁止修改 watchlist。
- 禁止改核心 BUY/SELL/RR/停損停利/過熱/漲停不追門檻。
- 禁止 DB 缺資料時補 fake/default/synthetic/fallback 值。
- 禁止把 dry-run、fixture、runtime fallback 當 production DB truth。
- 禁止把 historical_evidence_weight 單獨作為可買條件。
- 禁止回退 v20.3.1 positions / position_events / fake-data fail-closed 契約。
- 禁止回退 v20.2.4 可準備層不可買契約。
- 禁止回退既有手機報文噪音規則：空區塊、0 計數、無行動占位不得重新出現。
- 禁止同一檔股票在 summary、持倉卡、執行清單、詳情出現互相衝突主行動。
- 禁止 Tech 擴大成全 DB audit 或策略重設；若發現新斷鏈，記入殘留風險或後續任務。

## 已存在且不得回退的契約

- 最新使用者可見 Telegram 版本下限為 v20.3.1，本輪若實作需升為 v20.4.0，不得降版。
- v20.3.1 Data Authenticity Fail-closed:
- DB / 真實來源不可用時 production runtime 不得用 fake/default/synthetic/fallback 補成可買、confirmed、持倉、今日交易、價格或 Telegram 結論。
- positions missing-source/source-error/0 rows 不得回全 watchlist 0 股 fallback。
- position_events source-error/missing-source 不得回全 0 event summary；只有 DB query 成功且空資料才代表真實無事件。
- runtime watchlist breadth fallback 不得稱市場證據、不得 weak/runtime、不得 confirmed。
- v20.2.4 R3 強勢準備層:
- 可準備 是不可買準備層，不得進交易執行清單。
- 強勢偏熱不可因市場熱度或歷史權重直接變可買。
- v20.2.3 / v20.2.2 停利去重:
- 同日已執行同級停利後主行動轉觀察。
- 第二段停利 completed 轉觀察，partial 只顯示剩餘，unexecuted 才顯示完整第二段建議。
- 持倉卡、summary、風控檢查的今日已賣、剩餘、建議股數必須一致。
- 持倉行動一致性:
- 同一檔同一份報文只能有一個主行動。
- 今日買入後預設 新倉風控觀察；若要賣/減碼/停損，必須說明明確觸發條件。
- 風控優先於高分、最強、待觸發加碼。
- Telegram 手機閱讀:
- Summary 行動優先。
- 未持倉漏斗母集合固定為 可買 / 可準備 / 僅追蹤 / 淘汰。
- 僅追蹤 0 不得輸出零計數拆分。
- 空區塊、0-count、無行動占位預設不顯示。

## 阻塞條件

Tech 必須 blocked，不得自行決策的情況：

- 找不到既有 DB/local store read path，且無法用現有 helper 可靠讀取 Owner 指定資料。
- 需要新增 schema、column、migration 或正式 backfill 才能完成 Phase 1。
- 既有資料無日期、symbol、classification/action 或 outcome 欄位，無法可靠計算前次狀態、連續天數或 evidence weight。
- DB source-error/missing-source 與「真實空資料」無法區分。
- 要達成需求必須改核心可買門檻或持倉狀態機，而不是只做排序/摘要/去重邊界。
- TASK.md 與既有 v20.3.1 fail-closed 契約衝突。
- 測試環境缺依賴且 runner 無法補齊，導致 L3-lite 驗證不可執行。
- Owner 指定的表實際不存在或名稱不符，且 repo 中沒有等價 artifact 可證明。

## L3-lite QA 要求

QA 必須驗證：

- DB 有資料時，cross-day state / evidence weight 能影響連續狀態、排序、摘要或去重。
- DB 缺資料、source-error、欄位不足時，不產生假結論。
- 核心可買門檻不變：不可買不得因歷史權重單獨變可買。
- 不回退 v20.3.1 fake-data fail-closed。
- 不重複停利/減碼。
- 今日買入後不無脈絡反向賣出。
- Telegram 手機閱讀順序與行動一致性不破。
- Forbidden diff 無 schema、watchlist、live write、live Telegram、正式 backfill。

QA 停止條件：

- 完成上述 fixture / regression / direct consumer smoke 後即可收口。
- 不要求 full production backfill、live Supabase、live Telegram、RLS 審計、效能壓測或完整 DB end-to-end audit。
- 發現非阻塞旁支問題只記入 QA_REPORT.md 殘留風險或後續建議，不擴大本輪範圍。
