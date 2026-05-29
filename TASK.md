# TASK: Evidence Phase 2 Production Read-only Source Mapping And Telegram Wording Cleanup

## 任務狀態

- task_id: evidence_phase2_source_mapping_wording_cleanup_20260529
- 任務類型: normal_patch
- 任務尺寸: normal_patch
- 狀態: todo
- 版本建議: patch
- 版本契約: 本輪若修改 Telegram / CLI 使用者可見報文、evidence wording、source warning、header 或測試期望，升為 v20.4.2；不得回退 v20.4.1。
- QA 分級建議: L2
- QA 升級原因: 本輪不改策略門檻，但會碰 production DB read-only evidence consumption、Telegram summary wording、source boundary 與 fresh runner 可重建性；需驗證不產生 fake confirmed evidence。
- 任務停止條件: 完成 market/theme/strategy evidence 的既有 DB/persistent read-only source mapping、必要的最小 read-only consumption 或 wording cleanup、手機報文 fixture 驗證後停止。若任何所需 table/field/source 不存在
或不可由 fresh runner 讀取，Tech/QA 必須 blocked 並列精確缺口，不得新增 schema 或用 runtime 補值。
- 公開來源: 未使用；本任務依 Owner 指令與已清理專案摘要定義。

## Owner 問題

Owner 延續 v20.4.1 報文問題：production DB 已有資料，但 market/theme evidence 仍顯示 absent/missing-source，strategy evidence v20.0 table 未啟用，導致 Telegram evidence 區塊看起來像「沒有證據」或噪音過多。

本輪要先定義 source mapping 與手機 wording contract，再允許 Tech 在既有 DB table/field 足夠時做 read-only consumption / wording cleanup。若 production DB 現有來源不足，必須阻塞並列出缺什麼，不能建表、遷移、回填或用
runtime fake data 補成 confirmed。

## 使用者可見結果

Owner 在手機 Telegram 報文中應看到：

- Summary 不再被 absent/missing-source、未啟用 table、長 source diagnostic 混雜成噪音。
- 若 DB/persistent source 足夠，evidence wording 能簡短說明「已讀取 production source」與證據狀態，例如支持、混合、不足、過期。
- 若 DB/persistent source 不足，報文只用短句指出「來源不足，不作確認」，不得讓 Owner 誤讀為市場/題材真的不存在。
- Strategy evidence 若 existing DB table/field 足夠，可由 read-only source 啟用顯示；若不足，必須明確列缺口，不得 fallback 成 confirmed。
- 報文仍維持 v20.4.1 source boundary：runtime/local 只能同 run 輔助，不得標成 production confirmed evidence。

手機閱讀路徑：

1. 最後 summary 先回答今天能不能買、持倉先處理什麼、未持倉只是追蹤或不可行動。
2. Evidence wording 只能補充決策可信度，不得搶在行動前面，也不得用長列表干擾主決策。
3. 詳情或證據段再列 source 狀態；source 缺口要可追溯，但不在 summary 重複傾倒。
4. Owner 不需要在手機上分辨 runtime/cache/DB 細節才能避免誤買；文案本身要清楚區分 confirmed、insufficient、missing-source。

## 非目標

- 不新增 DB schema、table、field、index、migration、SQL。
- 不做 production write path、live Supabase write、正式 backfill、live Telegram。
- 不改 BUY / SELL / RR / overheat / trading thresholds。
- 不改 watchlist。
- 不新增外部 provider 或新聞/題材 ingestion。
- 不把 DB history 單獨升級成買賣門檻。
- 不做全量 evidence 架構重寫、全 repo 清理或 performance project。
- 不把 runtime/local/watchlist breadth fallback 標成 confirmed market/theme/strategy evidence。

## 影響模組

- core/market_theme_evidence.py: market/theme evidence source mapping、read-only source 狀態與 wording。
- services/strategy_evidence.py: strategy evidence existing DB read-only mapping；若欄位不足則 blocked。
- core/generator.py: Telegram summary/header/evidence wording 直接消費者；只允許最小同步。
- 相關測試: tests/test_market_theme_evidence.py、tests/test_generator_report.py、tests/test_notifier.py，必要時補 strategy evidence 直接測試。
- 不應影響: services/analysis.py 核心門檻、DB write stores、backfill/replay write path、watchlist、Telegram live delivery。

## 直接消費者

- Owner 手機 Telegram 報文。
- core/generator.py evidence summary/header/detail formatter。
- market/theme evidence provider。
- strategy evidence provider / loader。
- GitHub fresh runner；必須只靠 production DB 或 Owner-approved persistent source 重建 evidence 狀態。
- QA；需驗證 no fake data、no schema/write/backfill/watchlist change、mobile reading order。

## 已存在且不得回退的契約

- 最新使用者可見版本不得低於 v20.4.1。
- 正式 runner 無狀態；跨日或 confirmed evidence 必須來自 production DB 或 Owner 明確批准的持久 source。
- Runtime/local/cache/worktree/agent context 不得作為 confirmed evidence、source-of-truth、跨日記憶或 fresh runner 判斷依據。
- missing-source / source-error / insufficient-data 必須 fail closed，不得用 fallback 補成 confirmed。
- Runtime watchlist breadth fallback 只能作非交易診斷或缺來源說明，不得稱市場證據、不得 confirmed。
- 市場/題材/策略 evidence 不得放寬個股 BUY/SELL/RR/overheat/trading thresholds。
- DB/cross-day history 不得單獨把不可買變可買，不得讓可準備進交易執行清單。
- Telegram 手機閱讀行動優先；空區塊、0 計數、重複 source 噪音預設不顯示。
- evidence absent 只能表示內部結構化來源未啟用/不足，不代表外部市場不強。

## 輸出契約

Tech 必須先產出並實作最小 source mapping，至少覆蓋三類 evidence：

- market_evidence: 可用來源只能是 existing production DB/persistent market source；候選來源包含摘要中已存在的 market_daily_bars 或其他現有 read-only DB source。若缺 required fields，blocked。
- theme_evidence: 可用來源只能是 existing production DB/persistent sector/theme/source；候選來源包含 daily_signal_snapshot、signal_runs、signal_items 或其他現有 read-only DB source。若無法可靠映射 theme/sector，
blocked。
- strategy_evidence: 可用來源只能是 existing strategy evidence DB/audit source；候選來源包含 strategy_feature_snapshots、strategy_outcome_metrics、strategy_classification_audit 或目前程式既有 strategy evidence table。
若 v20.0 table/fields 不存在或未能由 runner 讀取，blocked。

每類 evidence 結構需維持下列語意，不要求新增 DB 欄位：

- source_status: ready / missing-source / source-error / insufficient-data / stale
- source_family: production_db / owner_approved_persistent / runtime_diagnostic
- source_name: 實際 table/view/provider 名稱；不足時列缺口
- freshness: 可判斷時顯示 fresh/stale；不可判斷時不得 confirmed
- confidence: confirmed / weak / mixed / absent 只能在 source boundary 合法時輸出
- allowed_effects: wording、排序提示、detail trace；不得改核心交易門檻
- forbidden_effects: 不得變 BUY、不得覆蓋風控、不得 fake confirmed、不得用 runtime 補 DB

Telegram wording contract：

- Summary 最多一行 evidence 總結；只寫對決策有幫助的狀態。
- 來源不足時使用短句，例如 證據來源不足，不作確認；不要重複 absent/missing-source 長清單。
- confirmed 只能在 production/persistent source、freshness、required fields 都滿足時出現。
- runtime diagnostic 可在 detail 顯示，但必須標示 非確認來源 或等價語意，不得放進 confirmed summary。
- 若沒有可追溯價值，不輸出空 evidence 區塊、0 計數或 no-op 文案。

## 驗收條件

1. Tech 必須列出 market/theme/strategy evidence 分別使用哪個 existing table/provider/field；若不足，blocked 並列精確缺少的 table/field/source。
2. 不得新增或修改 schema/migration/SQL/table/field；不得新增 write/backfill/live Telegram path。
3. 若 existing DB/persistent source 足夠，evidence read-only consumption 能讓 fresh runner 從 DB 重建 ready/confirmed/weak/mixed/stale/insufficient 狀態。
4. 若 DB source 缺失、欄位不足、freshness 不可判斷或讀取錯誤，輸出 missing-source/source-error/insufficient-data/stale，不得 confirmed。
5. Telegram summary 壓縮 evidence 噪音：不得在 summary 重複長 source diagnostic，不得讓 absent 被誤讀為外部市場不強。
6. Strategy evidence v20.0 table 若 existing DB 足夠，應啟用 read-only 顯示；若不足，必須 blocked，不得用 runtime/test fixture 補成 enabled。
7. Header / VERSION / snapshot 測試若報文 wording 有變，升到 v20.4.2 並同步測試；不得回退 v20.4.1。
8. QA 必須檢查接近真實手機長報文的閱讀順序：先行動、再 evidence、最後 detail，不得出現 summary 噪音或 fake confirmed。
9. QA 必須反證 fresh runner：清空 local/runtime/cache/worktree context 後，只有 DB/persistent source 可重建 confirmed evidence。
10. QA 必須掃描 forbidden diff：無 schema/migration/SQL、無 DB write、無 backfill、無 watchlist、無 live Telegram、無策略門檻變更。
11. 若發現旁支問題，例如 external provider 不足、歷史資料品質差、效能慢、schema 需新增欄位，只記為 blocked 缺口或後續待辦，不納入本輪擴張。

## 範例或 fixture

### Fixture A: DB source sufficient

輸入形狀：

market_evidence.source_family = production_db
market_evidence.source_name = market_daily_bars
market_evidence.required_fields_present = true
market_evidence.freshness = fresh

theme_evidence.source_family = production_db
theme_evidence.source_name = signal_items 或 daily_signal_snapshot
theme_evidence.required_fields_present = true
theme_evidence.freshness = fresh

strategy_evidence.source_family = production_db
strategy_evidence.source_name = strategy_classification_audit 或 strategy_feature_snapshots
strategy_evidence.required_fields_present = true

期望手機輸出形狀：

結論：新倉無有效進場；持倉先看風控。
證據：市場/題材為結構化來源支持；策略證據已讀取。

不得輸出：

market evidence absent / missing-source
strategy evidence v20.0 table not enabled

### Fixture B: DB has partial source, freshness missing

輸入形狀：

market_evidence.source_family = production_db
required_fields_present = true
freshness = unknown
theme_evidence.source_family = runtime_diagnostic
strategy_evidence.source_status = missing-source

期望手機輸出形狀：

結論：新倉無有效進場；不可因證據不足放寬。
證據：來源不足，不作確認；詳情列缺 market freshness、theme persistent source、strategy source。

不得輸出：

confirmed market/theme
策略證據已啟用
runtime 題材支持

### Fixture C: Runtime data looks supportive but DB source absent

輸入形狀：

runtime_watchlist_breadth = supportive
db_market_source = missing-source
db_theme_source = missing-source
db_strategy_source = missing-source

期望輸出形狀：

證據：production 來源不足，不作確認。
詳情：runtime 觀察僅供診斷，非確認來源。

不得輸出：

市場證據 confirmed
題材證據 confirmed
DB 已確認支持

## 明確禁止事項

- 禁止新增 schema/table/field/index/migration/SQL。
- 禁止 live Supabase write、正式 backfill、live Telegram。
- 禁止改 BUY/SELL/RR/overheat/trading thresholds。
- 禁止改 watchlist。
- 禁止用 runtime/local/cache/worktree/test fixture 補成 production confirmed evidence。
- 禁止把 missing-source/source-error/insufficient-data/stale 顯示成 confirmed。
- 禁止把 wording cleanup 擴成 strategy redesign。
- 禁止回退 v20.4.1 source boundary、data authenticity fail-closed、手機報文噪音規則。
- 禁止用「DB 有資料」泛稱通過；必須列實際 table/field/source 與 freshness 判斷。
- 禁止在 summary 傾倒長缺口列表；長缺口只能進 detail 或 CHANGELOG/QA_REPORT。

## 阻塞條件

- 找不到可由 GitHub fresh runner read-only 存取的 production DB/persistent source。
- existing table 缺少判斷 confirmed 所需欄位，例如日期/freshness、symbol/market/theme key、evidence value、classification、run id 或 outcome link。
- Strategy evidence v20.0 table/provider 在現有 DB 或程式路徑中不存在、未配置、或欄位不足。
- 只能靠 runtime/local/cache/test fixture 才能產生 evidence。
- 需要新增 schema/table/field、migration、backfill、write path、external provider 才能達成 Owner 目標。
- TASK 與既有 v20.4.1 source boundary 契約衝突時，Tech/QA 必須 blocked，交回 Architect/Owner 決策。
