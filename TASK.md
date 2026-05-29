# TASK: Cross-day Context Source Boundary Hardening

## 任務狀態

- task_id: cross_day_context_source_boundary_hardening_20260529
- 任務類型: risk_patch
- 任務尺寸: risk_patch
- 狀態: todo
- 版本建議: patch；若 Tech 修改任何使用者可見 Telegram / CLI 報文、source warning、排序、summary、prepare、dedupe 或 header，升為 v20.4.1；若只補測試且證明程式已符合契約，沿用目前 v20.4.0 並在 CHANGELOG.md 說明不升版理
由。
- 版本契約: 不得回退 v20.4.0；本輪只硬化 source boundary，不新增 Phase 2 schema mapping。
- QA 分級建議: L2
- QA 升級原因: 本輪涉及跨日策略記憶、歷史證據權重、連續觀察天數、前次行動/日期與 execution dedupe；必須驗證 GitHub fresh runner 無本地 runtime state 時仍可重建，且 missing-source/source-error/insufficient-data 會 fail
closed。
- 停止條件: 驗證並必要時修正 services/cross_day_context.py 與直接 generator/tests，使跨日記憶只來自 production DB 或 Owner 明確批准的持久 source；完成 fresh-run、DB missing、DB event、local-only negative 四類驗收後停
止。旁支問題如 schema 不足、Phase 2 欄位 mapping、效能、backfill、watchlist、live delivery 只列阻塞或待辦，不納入本輪實作。

## Owner 問題

正式流程是 git / GitHub runner 啟動後產生 Telegram 報文，runner 必須視為無狀態。任何只存在本機、worktree、暫存檔、runtime dict、cache 或 agent 對話中的狀態，對跨日策略記憶都無效。

Owner 要求硬化 services/cross_day_context.py 的來源邊界：cross-day memory、historical evidence weight、consecutive observe days、previous action/date、execution dedupe 這些必須跨 fresh GitHub runner 存活的判斷，只能來
自 production DB 或 Owner 明確批准的持久 source。runtime/local context 只能作同一次報文內 guard/display，不得被描述或用作跨日記憶。

## 使用者可見結果

Owner 在 Telegram / CLI 報文中應看到：

- 有 production DB 歷史資料時，v20.4.0 既有排序、summary、prepare、dedupe、硬風控優先行為維持有效。
- fresh GitHub runner 沒有任何本地 runtime state 時，只要 DB 有可信資料，仍能重建前次狀態、前次行動/日期、連續觀察天數、歷史權重與同級 execution dedupe。
- DB 缺表、缺欄位、查詢錯誤或資料不足時，不輸出假跨日記憶、假連續天數、假 previous action/date、假已執行事件；必須顯示或內部標記 missing-source / source-error / insufficient-data，並 fail closed。
- runtime/local context 若存在，只能影響同一次 render 的 guard 或顯示，不得讓 summary / 詳情暗示「跨日記憶已確認」。

手機閱讀路徑：

1. Summary 先看持倉是否有已執行 dedupe、硬風控是否優先。
2. 未持倉 summary / 漏斗再看可準備、僅追蹤排序是否因可信 DB history 調整。
3. 個股詳情最後看 previous state/action/date、連續觀察天數、歷史權重與 source 狀態。
4. 若來源不足，手機報文不得讓 Owner 誤以為系統記得前一天狀態或今日已執行事件。

## 非目標

- 不新增 DB schema、migration、table、column、index。
- 不新增 production write path。
- 不做 live Supabase write、正式 backfill、live Telegram delivery。
- 不改 watchlist。
- 不改核心 BUY / SELL / RR / 過熱 / 漲停不追 / 停損停利門檻。
- 不重設策略分類、持倉狀態機或 Phase 2 source precedence。
- 不把 runtime/local fallback 包裝成 production memory。
- 不做 full repo 清理、重構或效能優化。

## 影響模組

- services/cross_day_context.py: 本輪主檢查與必要修正目標。
- core/generator.py: 直接注入 / 消費 cross-day context 的使用者可見報文入口；只允許最小同步。
- 直接測試: tests/test_cross_day_context.py、與 generator / notifier / market evidence 中直接受 cross-day context 影響的測試。
- 可能直接消費者: strategy result sorting、Telegram summary、prepare layer、holding action dedupe、detail trace。

## 直接消費者

- core/generator.py: 消費 cross-day context，輸出 Telegram header、summary、持倉卡、未持倉漏斗、個股詳情。
- Telegram Owner: 最終消費者；依報文判斷是否買、是否持倉風控、是否只是追蹤。
- QA: 驗證 fresh-run、DB missing、DB event、local-only negative 四類風險。
- GitHub runner: 正式執行環境；不得依賴本機 runtime 或 worktree 暫存狀態。

## Source-of-truth 契約

允許作為跨日 source-of-truth 的來源：

- production DB positions
- production DB position_events
- production DB daily_signal_snapshot
- production DB signal_runs
- production DB signal_items
- production DB signal_outcomes
- production DB strategy_feature_snapshots
- production DB strategy_outcome_metrics
- production DB strategy_classification_audit
- Owner 明確批准且 GitHub runner 可讀取、可重建的持久 source

不得作為跨日 source-of-truth 的來源：

- 同 run runtime dict / in-memory object
- local temp file / cache / worktree artifact
- agent 對話摘要
- test fixture default
- dry-run/backfill 中間產物
- 缺 production DB 時的 synthetic/default/fallback data

runtime/local context 允許用途：

- 同一次報文內防止重複顯示。
- 同一次 render 的輔助顯示。
- 測試 fixture 內明確標記為 non-persistent 的 guard。

runtime/local context 禁止用途：

- 計算跨日連續觀察天數。
- 宣告 previous action/date。
- 產生 historical evidence weight。
- 驅動 fresh GitHub runner 的 execution dedupe。
- 在報文中描述成「歷史 / 前次 / 連續 / 已執行」記憶。

## 輸出契約

cross_day_context 或等價結構必須維持下列語意：

- source_status: ready / missing-source / source-error / insufficient-data
- source_of_truth: 實際使用的 production DB table 或 Owner-approved persistent source
- previous_state: 只能由可信持久來源重建；不足時 unknown
- previous_action: 只能由可信持久來源重建；不足時 unknown / none
- previous_action_date: 只能由可信持久來源重建；不得補今日或 runtime date
- consecutive_observe_days: 只能由可信持久來源計算；不足時 unknown 或不顯示，不得假設
- historical_evidence_weight: 只能由可信持久來源計算；不足時中性或 unknown
- dedupe_guard: execution dedupe 必須來自 production DB / persistent source；同 run guard 必須標示為 same-run only
- allowed_effects: 可影響排序、summary、prepare 呈現、同級 dedupe、detail trace
- forbidden_effects: 必須包含不得單獨變可買、不得覆蓋硬風控、不得偽造 execution、不得用 local-only memory

已存在且不得回退的契約：

- v20.4.0 valid DB data 可影響 sorting / summary / prepare / dedupe。
- DB / cross-day history 只能壓制同級重複行動；不得覆蓋硬風控、停損、REDUCE_50、STOP_100 或風控升級。
- DB / cross-day history 不得單獨把不可買變可買，不得讓可準備進交易執行清單。
- positions / position_events missing-source 或 source-error 不得回全 watchlist 0 股或全 0 event summary。
- Runtime watchlist breadth fallback 不得變成 confirmed market evidence。
- Telegram 手機閱讀必須行動優先，同一檔同一份報文只能有一個主行動。

## 驗收條件

1. Tech 必須先檢查 services/cross_day_context.py 是否存在 local/runtime-only source 被用作跨日 memory；若有，最小 diff 修正。
2. GitHub fresh-run acceptance: 測試必須模擬無 local runtime/cache/worktree state，僅給 production DB/persistent source fixture；previous state/action/date、consecutive observe days、historical weight、dedupe 仍可由 DB
重建。
3. DB missing acceptance: DB source 缺失、錯誤或欄位不足時，輸出 missing-source / source-error / insufficient-data，不得產生假 previous action/date、假連續天數、假 historical weight 或假 execution dedupe。
4. DB event acceptance: production DB event 顯示同級停利/減碼已執行時，報文維持 v20.4.0 同級 dedupe；若當日硬風控更高級，硬風控優先。
5. Local-only negative acceptance: 僅提供 runtime/local context、沒有 DB/persistent source 時，不得輸出跨日記憶，不得讓 sorting/summary/prepare/dedupe 表現成跨日 confirmed。
6. 使用者可見 header: 若本輪改變任何報文輸出或 source warning，header / VERSION / 測試期望升到 v20.4.1；若不改輸出，明確保留 v20.4.0。
7. Forbidden diff 掃描確認無 schema/migration、無 DB write path、無 live Supabase、無 backfill、無 watchlist、無 live Telegram。
8. CHANGELOG.md 必須列出 source-of-truth 邊界、修改檔案、直接消費者同步、自檢命令與殘留風險。
9. 若 production DB schema/fields 不足以完成任何必需判斷，Tech 必須 blocked，精確列出缺哪個 table/field/relationship；不得新增 schema 或用 fallback 補值。
10. QA 必須檢查一段接近真實手機報文，確認 source 不足時不會誤導 Owner 以為有跨日記憶。

## 範例或 fixture

### Fixture A: Fresh GitHub runner only DB data

輸入形狀：

local_runtime_state: empty
db.position_events:
symbol: 2356
action: take_profit
action_date: 2026-05-28
level: same_level
today_signal_action: take_profit
hard_risk_action: none

期望輸出形狀：

持倉優先:
2356｜停利後觀察｜前次停利 2026-05-28，同級不重複

不得輸出：

2356｜本次再次同級停利
source_of_truth: runtime/local

### Fixture B: DB missing, local runtime has tempting data

輸入形狀：

db_status: missing-source
local_runtime_context:
previous_action: reduce
previous_action_date: 2026-05-28
consecutive_observe_days: 5

期望輸出形狀：

source_status: missing-source
previous_action: unknown
consecutive_observe_days: unknown 或不顯示
historical_evidence_weight: neutral/unknown

不得輸出：

連續觀察 5 天
前次減碼 2026-05-28
同級已執行不重複

### Fixture C: DB event plus higher-priority hard risk

輸入形狀：

db.position_events:
symbol: 3017
action: reduce
action_date: 2026-05-28
level: same_level
today_signal_action: reduce
hard_risk_action: STOP_100

期望輸出形狀：

持倉優先:
3017｜停損 / 硬風控優先｜歷史同級減碼不覆蓋今日停損

不得輸出：

3017｜減碼後觀察

## 明確禁止事項

- 禁止新增或修改 DB schema / migration / SQL。
- 禁止新增 live Supabase write、正式 backfill、live Telegram delivery。
- 禁止改 watchlist。
- 禁止用 runtime/local/cache/worktree 狀態作為跨日記憶。
- 禁止用本地 fallback 補 production DB 缺失。
- 禁止回退 v20.4.0 DB valid-data 行為。
- 禁止讓歷史記憶覆蓋硬風控、停損、REDUCE_50、STOP_100。
- 禁止把不可買單靠歷史權重變可買。
- 禁止把本輪擴成 Phase 2 source precedence、schema mapping 或資料建置工程。

## 阻塞條件

- 無法識別 production DB / persistent source 是否包含必要欄位。
- 現有 DB schema 無法可靠提供 previous action/date、consecutive observe days、historical evidence weight 或 execution dedupe 所需資料。
- fresh GitHub runner 無法讀取相同 source-of-truth。
- 需要新增 schema、migration、write path、backfill、watchlist 或 live delivery 才能完成驗收。
- TASK 與現有 v20.4.0 契約衝突，且無法用最小 diff 保留既有行為。
