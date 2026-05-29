# TASK: Evidence Phase 3 Production Confirmed Market Theme Evidence Source Mapping

## 任務狀態

- task_id: evidence_phase3_production_confirmed_source_mapping_20260529
- 任務類型: normal_patch
- 任務尺寸: normal_patch
- 狀態: todo
- 版本建議: patch
- 版本契約: 本輪若新增 read-only loader/mapping 使 market/theme evidence 可從 production/persistent source 變成 confirmed，或修改 Telegram/CLI 使用者可見 wording/header/snapshot，升為 v20.4.3；不得回退 v20.4.2 source-
family gate。
- QA 分級建議: L2
- QA 升級原因: 本輪不改交易策略門檻，但會碰 confirmed evidence source boundary、production read-only mapping、fresh runner 可重建性與手機報文語意；需反證 fake confirmed。
- 任務停止條件: Tech 先只檢查既有 code/schema/docs。若既有 production DB/persistent source contract 足夠，才做最小 read-only loader/mapping 與直接測試；若缺任一 required source/field，立即 blocked 並列精確缺口，不做
schema/write/backfill/provider 擴張。
- 公開來源: 未使用；本任務依 Owner 指令與已清理專案摘要定義。

## Owner 問題

Owner 要在 v20.4.2 之後推進 Evidence Phase 3：確認現有 production DB 或 Owner-approved persistent source 是否已足夠支撐 market/theme evidence 由真實 production source 變成 confirmed。

本輪核心不是重做策略，也不是建資料源；而是定義並驗證「confirmed evidence 所需來源契約」。只有既有 production/persistent source 已提供完整欄位時，才允許 Tech 實作 read-only loader/mapping。若不足，交付 blocked 缺口表，
不得用 runtime/local/cache/report-derived/test fixture 假裝 confirmed。

## 使用者可見結果

Owner 在手機 Telegram 應看到：

- 若 production/persistent source 完整且 fresh，market/theme evidence 可簡短顯示為已確認來源支持、混合或不足。
- 若來源缺欄位、過期、不可追溯或不可由 fresh runner 重建，仍顯示 production 來源不足，不作確認 或等價短句。
- Runtime/local/cache/report-derived 資料只能在 detail 作診斷，不得讓 summary 顯示 confirmed。
- 手機閱讀順序維持行動優先：先看今天能不能買、持倉先處理什麼，再看 evidence 對決策可信度的補充。

## 非目標

- 不新增 DB schema、table、field、index、migration、SQL。
- 不做 live Supabase write、正式 backfill、live Telegram。
- 不改 watchlist。
- 不改 BUY / SELL / RR / overheat / trading thresholds。
- 不新增外部市場、新聞或題材 ingestion provider。
- 不把 market/theme evidence 變成核心買賣門檻。
- 不把 runtime/local/cache/report-derived/test fixture 昇格為 confirmed source。
- 不做全量 evidence 架構重寫、全 repo 清理或 performance project。

## 影響模組

- core/market_theme_evidence.py: confirmed evidence source contract、source-family gate、read-only mapping。
- core/generator.py: Telegram evidence summary/detail 的直接消費者；僅允許必要 wording/header 同步。
- 既有 DB/read-only source helper 或 schema docs: 只讀檢查與必要 mapping。
- 相關測試: tests/test_market_theme_evidence.py、tests/test_generator_report.py、tests/test_notifier.py；若新增 loader helper，補直接單元測試。
- 不應影響: services/analysis.py、watchlist、DB write stores、replay/backfill write path、live Telegram。

## 直接消費者

- Owner 手機 Telegram 報文。
- core/generator.py evidence summary/detail formatter。
- market/theme evidence provider。
- GitHub fresh runner；confirmed evidence 必須可在無 local/runtime/cache/worktree context 下由 production DB 或 Owner-approved persistent source 重建。
- QA；需驗證 no fake confirmed、no schema/write/backfill/watchlist/live changes、mobile wording action-first。

## 已存在且不得回退的契約

- 最新使用者可見版本不得低於 v20.4.2。
- v20.4.2 source-family gate 保持：confirmed/ready 只能來自 production_db 或 owner_approved_persistent。
- runtime_diagnostic、runtime、local、cache、worktree、test fixture、report-derived source 只能作 trace/detail，不得 confirmed/ready，不得污染頂層 source_family。
- missing-source / source-error / insufficient-data / stale 必須 fail closed。
- 市場/題材 evidence 不得放寬個股買點，不得自動產生 BUY。
- Telegram 手機閱讀行動優先；summary 不傾倒長缺口、空區塊、0 計數或 no-op 文案。
- 正式 runner 無狀態；任何 confirmed/cross-day 判斷不得依賴 agent 對話、本機暫存、worktree cache 或同 run runtime fallback。

## 輸出契約

Tech 必須先產出 source mapping 判斷，且每個 candidate source 都要列出：

- source_family: production_db 或 owner_approved_persistent
- source_name: table/view/provider/helper 名稱
- market_index: 是否可辨識大盤或市場指標
- sector_theme_key: 是否可辨識 sector/theme key，且可映射到 watchlist 股票
- watchlist_breadth: 是否有觀察池廣度或可由 production source read-only 計算
- as_of / freshness: 是否有可驗證日期、交易日或更新時間
- evidence_value: 支持/不支持/混合/分數/分類等可判斷值
- support_level: confirmed/weak/mixed/absent 的依據
- lineage: run id、snapshot id、symbol/theme key 或等價追溯欄位
- allowed_effects: Telegram wording、detail trace、排序提示；不得改交易門檻
- forbidden_effects: 不得變 BUY、不得覆蓋風控、不得 fake confirmed

Confirmed 條件必須同時滿足：

- source family 合法。
- market_index 或等價市場指標存在。
- sector_theme_key 或等價 theme/sector 映射存在。
- watchlist_breadth 存在或可由 production source read-only 重建。
- as_of/freshness 可判斷且未過期。
- evidence_value/support_level 可由 production source 直接讀取或可追溯計算。
- fresh runner 不依賴 runtime/local/cache/report-derived/test fixture 即可重建。

## 驗收條件

1. Tech 先檢查 existing code/schema/docs，列出每個 market/theme candidate source 的 table/view/helper/field 對照。
2. 若任一 confirmed 必要欄位不存在或不可追溯，Tech 必須 blocked，列精確 required table/view/field/source；不得寫 loader 假補。
3. 若既有 production/persistent source 足夠，read-only loader/mapping 只能讀取既有來源，不新增 schema/write/backfill/live path。
4. confirmed/ready 僅能由 production_db 或 owner_approved_persistent 且 required fields/freshness 完整時成立。
5. runtime/local/cache/report-derived/test fixture 即使內容 supportive，也不得產生 confirmed/ready。
6. Telegram summary 維持短句、行動優先；來源不足時不得輸出像推薦或確認支持的文案。
7. 若使用者可見 wording/header 變更，版本升為 v20.4.3 並同步測試；未變更報文時需在 CHANGELOG.md 說明不升版理由。
8. QA 必須反證 fresh runner source boundary：清空 local/runtime/cache/worktree context 後，只有 production/persistent source 能 confirmed。
9. QA 必須掃描 forbidden diff：無 schema/migration/SQL、無 DB write、無 backfill、無 watchlist、無 live Telegram、無策略門檻變更。
10. 旁支問題如缺外部 provider、production schema 不足、歷史資料品質或效能慢，只列 blocked 缺口或後續待辦，不納入本輪擴張。

## 範例或 fixture

### Fixture A: production source complete

輸入形狀：

source_family = production_db
source_name = existing_market_theme_view
market_index = TAIEX
sector_theme_key = AI_SERVER
watchlist_breadth = supportive
as_of = current_trade_date
freshness = fresh
evidence_value = supportive
support_level = confirmed

期望手機輸出形狀：

結論：新倉無有效進場；持倉先看風控。
證據：市場/題材 production 來源支持。

不得輸出：

missing-source
runtime confirmed
report-derived confirmed

### Fixture B: missing sector/theme key

輸入形狀：

source_family = production_db
market_index = TAIEX
watchlist_breadth = supportive
as_of = current_trade_date
sector_theme_key = missing

期望輸出形狀：

證據：production 來源不足，不作確認。
詳情：缺 sector/theme key，無法 confirmed。

### Fixture C: runtime supportive only

輸入形狀：

runtime_watchlist_breadth = supportive
report_theme_text = supportive
production_market_source = missing-source
production_theme_source = missing-source

期望輸出形狀：

證據：production 來源不足，不作確認。
詳情：runtime/report-derived 僅供診斷，非確認來源。

不得輸出：

市場 confirmed
題材 confirmed
production 已確認支持

## 明確禁止事項

- 禁止新增 schema/table/field/index/migration/SQL。
- 禁止 live Supabase write、正式 backfill、live Telegram。
- 禁止改 watchlist。
- 禁止改 BUY/SELL/RR/overheat/trading thresholds。
- 禁止用 runtime/local/cache/worktree/report-derived/test fixture 補成 production confirmed evidence。
- 禁止把 missing-source/source-error/insufficient-data/stale 顯示成 confirmed。
- 禁止回退 v20.4.2 source-family gate。
- 禁止用「DB 有資料」泛稱通過；必須列實際 table/view/field/source 與 freshness/as_of。
- 禁止把本輪擴成外部 provider、schema design、backfill 或策略重設。

## 阻塞條件

- 找不到可由 GitHub fresh runner read-only 存取的 production DB/persistent source。
- 缺 market_index 或等價市場指標。
- 缺 sector/theme key 或無法映射到 watchlist 股票。
- 缺 watchlist_breadth 或不可由 production source read-only 重建。
- 缺 as_of/freshness，無法判斷是否 fresh。
- 缺 evidence_value/support_level，無法判斷 supportive/mixed/weak/absent。
- 缺 source family 或 lineage，無法證明來源是 production/persistent。
- 只有 runtime/local/cache/report-derived/test fixture 才能產生 evidence。
- 需要新增 schema/table/field、migration、write path、backfill 或 external provider 才能達成 confirmed。
- 任何實作需要放寬 v20.4.2 source-family gate 或改交易門檻。
