# TASK: Evidence Chain Pre-Development Closure

## 任務狀態

- task_id: evidence_chain_predev_closure_20260529
- 任務類型：risk_patch
- 任務尺寸判斷：risk_patch
- 狀態：ready_for_tech
- 版本建議：none，本輪不改 Telegram 使用者可見報文內容與 header；若 Tech 實際改到 Telegram formatter / message list / header，必須 blocked 要求 PM 重開版本契約，預設至少 patch
- QA 分級建議：L2+，聚焦 DB 契約、fresh GitHub runner 可重建、非 live writer/dry-run 與直接消費者；不得擴成 full strategy redesign 或正式 backfill
- 本輪主問題：在繼續策略證據鏈判斷前，完成 repo-side 的端到端閉環前置工作

## Owner 問題

Owner 要先統一三件事，避免後續 evidence chain 開發建立在假資料、未消費 DB 或未串接新表上：

1. 清理或阻斷策略路徑中的 fake/default/synthetic/local/runtime 假資料，確保策略需要抓取的資料都來自真實來源；真實來源缺失時 fail closed，不得補成可買、confirmed、持倉、今日交易或正常市場證據。
2. 確保 production DB 相關資料要嘛已被策略 / formatter / evidence flow 消費，要嘛明確列為 reference-only / unused / not-yet-integrated；不得讓文件或程式暗示「已用上」但實際沒有 consumer。
3. 新表 public.market_theme_confirmed_evidence 必須與 GitHub runner -> strategy/generator -> Telegram 報文流程形成可重建鏈路；本輪只做非 live repo-side 閉環補丁，不做正式 production write。

本輪不是重新判斷策略證據鏈強弱，也不是放寬買賣條件。

## 使用者可見結果

Owner 本輪可見結果不是新的 Telegram 實盤報文，而是可交給 Architect 吸收的三份交付：

- TASK.md：本任務卡。
- CHANGELOG.md：Tech 的非 live 閉環補丁摘要、關係圖、DB usage matrix、dry-run / handoff contract。
- QA_REPORT.md：QA 對 fake confirmed、local state、fresh GitHub runner、DB 未接入標記的反證。

Owner 讀完後應能看到：

- 哪些資料來源是正式 source-of-truth。
- 哪些 DB 表已被策略或 formatter 消費。
- 哪些 DB 表只是 reference / audit / unused，且不再被誤稱為已接入策略。
- market_theme_confirmed_evidence 從 payload builder / SQL handoff / table / loader / provider / Telegram evidence 區塊的最小閉環。
- 若需要建表、擴欄、RLS、production 寫入或正式 backfill，Owner 應拿到可手動執行的 SQL 或明確步驟，而不是 agent 直接執行。

## 非目標

- 不繼續做策略 evidence chain 判斷。
- 不改 BUY / SELL / RR / 加減碼 / 停損停利 / 過熱 / 漲停不追門檻。
- 不把 confirmed market/theme evidence 變成買點放寬條件。
- 不做 live Supabase write。
- 不做正式 backfill。
- 不做 live Telegram delivery。
- 不改 production RLS / role / grant。
- 不由 agent 建表、擴欄或修改 production schema。
- 不清理全 repo、不中途重構無關模組。
- 不把所有 DB 表強塞進策略；未達本輪閉環者要明確標記 reference-only / unused / not-yet-integrated。
- 不以 local cache、worktree state、agent 對話、test fixture、runtime dict 當作 GitHub fresh runner 的正式狀態。

## 影響模組

Tech 只允許碰本輪端到端閉環需要的 repo-side 非 live 範圍，實際檔名可依現有結構調整：

- services/market_theme_evidence_store.py
- core/market_theme_evidence.py
- core/generator.py
- services/position_store.py
- services/cross_day_context.py
- services/strategy_evidence.py
- services/daily_snapshot_store.py
- services/signal_store.py
- services/stock_api.py
- GitHub scheduled report / generator entrypoint 的 env 與 fail-closed guard
- 非 live handoff SQL / docs，例如 docs/handoff/* 或 db/sql/*
- 對應局部測試 / fixture

不得修改 watchlist、正式 runner secret、production DB、live Telegram 發送流程。

## 直接消費者

- GitHub fresh runner / scheduled report：必須能在無本地狀態下重建 DB read path 與 fail-closed 狀態。
- core/generator.py：消費 positions、position events、cross-day context、market/theme evidence，產出 Telegram message list。
- core/market_theme_evidence.py：消費 confirmed evidence loader/provider 結果，保留策略影響邊界。
- Telegram formatter / Owner 手機報文：本輪預期不改文案；若缺 source，仍只能顯示來源不足或不作確認，不得 fake confirmed。
- Architect：依 CHANGELOG.md / QA_REPORT.md 吸收，不依賴聊天紀錄。
- 後續 Tech / QA：依本輪關係圖與 DB usage matrix 接續，不重新猜測目前鏈路。

## Source-of-Truth 契約

- 持倉：production positions 或 Owner 明確指定的持久來源。
- 今日 / 歷史交易事件：production position_events 或等價持久事件表。
- 跨日策略記憶、去重、歷史行動：production DB 或 Owner 明確指定持久來源；local/runtime 只能作同 run guard。
- market/theme confirmed evidence：production public.market_theme_confirmed_evidence。
- confirmed 條件：support_level in ('confirmed','supporting')、evidence_status='confirmed'、freshness='fresh'。
- raw market/theme evidence payload：只能來自真實行情、真實廣度、Owner-approved persistent source 或可手動審核的 non-live handoff；不得從 Telegram 報文、runtime diagnosis、fixture、local cache 反推 confirmed。
- DB env / permissions：GitHub runner 必須從 production secrets / env 取得；缺 env、缺權限、DB error、0 rows、資料不足時 fail closed。
- 未接入 DB 表：必須在 matrix 標成 reference-only、write-only、unused 或 not-yet-integrated，不得假裝已影響策略。

## 輸出契約

### Tech 必須輸出到 CHANGELOG.md

CHANGELOG.md 必須從 # CHANGELOG: 開始，包含：

- 修改內容：只列本輪非 live repo-side 閉環補丁。
- 修改檔案：逐一列出。
- 契約影響：說明是否新增 / 修改 writer payload builder、dry-run SQL handoff、loader contract、fresh-run guard、文檔狀態圖；明確說明未 live write。
- 版本同步：本輪不改 Telegram 版本；若實際改 Telegram 輸出，必須 blocked。
- 直接消費者同步：列出 generator、market_theme provider、GitHub runner smoke、handoff docs 是否同步。
- DB usage matrix，固定欄位：
table/source | writer | reader | strategy consumer | formatter/report consumer | current status | source-of-truth | next action
- market/theme evidence 關係圖，至少包含：
raw true source -> payload builder/dry-run -> SQL handoff/manual step -> public.market_theme_confirmed_evidence -> read-only loader -> provider -> generator -> Telegram evidence block -> strategy influence boundary
- fresh GitHub runner guard 說明：
no env / DB error / 0 rows / insufficient rows / unsupported support_level / stale freshness / local-only state 各自如何 fail closed。
- 自檢命令：實際跑過的局部測試或 smoke，不能用「QA 會驗」代替。
- 殘留風險：若仍需 Owner 建表、擴欄、RLS、production write、正式 backfill、production data smoke，必須列為手動步驟或 blocked 條件。

### QA 必須輸出到 QA_REPORT.md

QA_REPORT.md 必須從 # QA_REPORT: 開始。QA 必須反證：

- 沒有 fake confirmed：fixture、runtime、report-derived、local cache、missing source 不會變成 confirmed。
- 沒有把本地狀態當正式狀態：清空 local/worktree/runtime context 後，fresh GitHub runner 仍只能依 production DB 或 fail closed。
- public.market_theme_confirmed_evidence 的讀 / 寫契約可由 repo-side artifact 重建；若缺 production write/RLS/backfill，必須標成 conditional 或 blocked，不得通過成已上線。
- 未接入 DB 表有明確標記，不得在報文、文件或 matrix 中暗示已被策略使用。
- Telegram 手機閱讀路徑沒有新增誤導：缺 source 時不得像推薦或 confirmed。

QA 結論只能是：通過、阻塞、conditional pass。

## 驗收條件

1. Tech 交付至少一個非 live repo-side 閉環補丁：writer/upsert payload builder、dry-run SQL handoff、read-only smoke、fresh-run guard、或流程文檔 / 狀態圖；不得只做口頭 audit。
2. market_theme_confirmed_evidence 關係圖完整列出從 raw true source 到 Telegram evidence block 的每一段，且每段標明 implemented / handoff-only / blocked / manual-owner-step。
3. DB usage matrix 覆蓋目前摘要中已知表或來源：positions、position_events、market_theme_confirmed_evidence、daily_signal_snapshot、signal_runs、signal_items、signal_outcomes、strategy_feature_snapshots、
strategy_outcome_metrics、strategy_classification_audit、market_daily_bars 或實際等價名稱。
4. 未被策略消費的 DB 表必須明確標記，不得用「已接入 DB」籠統帶過。
5. 缺 DB env、DB read error、0 rows、資料不足、unsupported support_level、stale freshness、local-only source 都有 fail-closed 測試或 smoke 證據。
6. Tech 不得產生 live Supabase write、正式 backfill、live Telegram、production RLS / grant 變更。
7. 若需要建表、擴欄、RLS、production 寫入或正式 backfill，Tech 必須停止該部分並輸出 Owner 可手動執行 SQL 或明確手動步驟。
8. QA 必須補至少四類反證：fake confirmed、local state、fresh runner reconstructability、unused DB table labeling。
9. QA 必須檢查 Owner 手機 Telegram 閱讀路徑：本輪若沒有改報文，確認既有缺 source 文案不被新補丁改成 confirmed；若有改報文，必須 blocked 回 PM 補版本契約。
10. 本輪完成後，Architect 能只靠 TASK.md、CHANGELOG.md、QA_REPORT.md 判斷是否可進入下一個 evidence chain 開發任務。

## 範例或 Fixture

### 關係圖輸出形狀

market/theme confirmed evidence closure
raw true source:
status: handoff-only
allowed: production DB / Owner-approved persistent source / real market data
forbidden: runtime diagnosis / Telegram report text / local fixture
payload builder:
status: implemented
output: rows for public.market_theme_confirmed_evidence
SQL handoff:
status: manual-owner-step
live write: forbidden
table:
status: production schema exists
loader:
status: read-only implemented
provider:
status: implemented; fail closed on insufficient data
generator:
status: consumes provider
Telegram:
status: evidence background only; no buy/sell threshold change

### DB Usage Matrix 輸出形狀

table/source | writer | reader | strategy consumer | formatter/report consumer | current status | source-of-truth | next action
positions | existing | position_store | generator fail-closed holding path | Telegram holdings | consumed | production DB | keep
market_theme_confirmed_evidence | handoff-only/non-live builder | market_theme_evidence_store | none for buy threshold | evidence block | read path implemented, write path non-live only | production DB | Owner manual
write/backfill needed
market_daily_bars | existing/unknown | unknown | none | reference only | write-only/reference-only | production DB if populated | follow-up if strategy should consume

### 手機閱讀路徑

本輪預期不新增 Telegram 文案。若 Tech 觸碰 evidence block，手機上只允許類似形狀：

證據：production 來源不足，不作確認。

不得輸出：

證據：題材 confirmed
新倉：可買

除非該 confirmed 來自 public.market_theme_confirmed_evidence fresh rows 且仍不放寬個股買點。

## 已存在且不得回退的契約

- 最新使用者可見 Telegram 版本是 v20.4.3。
- 正式 TG 報文由 git / runner 啟動生成，runner 必須視為無狀態。
- 跨日策略記憶、歷史證據、已執行事件必須來自 production DB 或 Owner 指定持久來源。
- Runtime / local context 只能作同 run 輔助 guard 或顯示材料，不得作下一次 GitHub runner 的跨日判斷依據。
- positions 缺來源不得 fallback 成全 watchlist 0 股。
- position_events source-error / missing-source 不得 fallback 成全 0 event summary。
- market/theme evidence confirmed / ready 必須滿足 production / Owner-approved persistent source family、required fields 與 freshness。
- support_level=strong 不得 accepted 或轉成 confirmed。
- report-derived / runtime diagnostic 只能作 trace，不得污染頂層 source_family。
- confirmed market/theme evidence 不得放寬 BUY / SELL / RR / 加減碼 / 過熱 / 漲停不追門檻。
- 空 source / source-error / insufficient-data 必須 fail closed，不得補成正常候選或 confirmed。

若 Tech 發現上述契約與實際程式不一致，必須修本輪直接相關的 fail-closed guard；若超出本輪最小閉環，標記 blocked 或 follow-up，不得默默回退契約。

## 明確禁止事項

- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止 live Telegram delivery。
- 禁止 production RLS / role / grant 變更。
- 禁止 agent 直接執行 production SQL。
- 禁止新增假資料、synthetic confirmed、fixture-derived confirmed。
- 禁止把 local/runtime/cache/worktree/agent context 當正式 source-of-truth。
- 禁止改策略核心門檻或 watchlist。
- 禁止把未接入 DB 表描述成已被策略使用。
- 禁止為了通過測試而修改 fixture 使 fake source 看起來合法。
- 禁止在本輪做全量重構、全 repo 清理或無關 formatter 改版。

## 阻塞條件

遇到以下任一情況，Tech 或 QA 必須標記 blocked 或 conditional pass，不得宣告完成：

- 需要 production DB connection、secret、RLS 權限或 live write 才能繼續驗證。
- 需要建表、擴欄、改 constraint、改 RLS、grant role。
- 無法證明 fresh GitHub runner 在無 local state 下可重建同樣判斷。
- 找到 fake/default/synthetic/local/runtime source 仍可進 confirmed 或策略決策。
- DB usage matrix 無法判定某表是否有 consumer。
- market_theme_confirmed_evidence 只有 read path，沒有非 live writer/handoff 或明確 Owner manual step。
- Tech 實際改到 Telegram 使用者可見輸出但沒有 PM 版本契約。
- 任一交付文件缺標題、缺直接消費者、缺驗收證據，或混入終端流水。

## 本輪停止條件

做到以下即停止，不再擴張：

- 非 live repo-side 閉環補丁已完成。
- DB usage matrix 已標明 consumed / reference-only / unused / blocked。
- market/theme evidence 關係圖已輸出。
- fresh-run fail-closed guard 有局部測試或 smoke 證據。
- QA 已完成四類反證並給出 通過 / conditional pass / 阻塞。

以下旁支只記為後續待辦，不納入本輪：

- 正式 production backfill。
- live Supabase write。
- production RLS / read-only role 實測。
- 新外部新聞 / 題材 ingestion。
- 讓更多 DB 表影響 BUY / SELL 核心門檻。
- Telegram 文案改版或版本升級。
- performance tuning。
