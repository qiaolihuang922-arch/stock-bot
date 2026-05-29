# TASK: Integration Audit Before Evidence Chain Development Continues

## 任務狀態

- task_id: evidence_chain_integration_audit_before_resume
- 任務類型：process
- 任務尺寸判斷：process
- 狀態：ready_for_tech_audit
- 版本建議：none，本輪不改使用者可見產品輸出，不升 Telegram 版本
- QA 分級建議：process / audit，若 QA 需要跑局部測試，只能作為佐證，不得擴成產品修復
- 本輪主問題：暫停證據鏈後續開發，先完成全流程 integration audit

## Owner 問題

Owner 要在繼續證據鏈開發前，確認目前系統是否真的符合 production source-of-truth / fail-closed 契約，而不是靠 local、runtime、report-derived、fixture、假資料或未串接 DB 造成假 confirmed、假持倉、假事件或假 evidence。

Owner 要確認三件事：

1. 策略使用的假資料是否已清理；正式 Telegram / GitHub fresh runner 遇到缺 DB、缺價格、缺持倉、缺 events、缺 evidence 時是否 fail closed；任何需抓取資料是否明確來自真實 source，不得 local/runtime/report-derived fake
confirmed。
2. 既有 DB 資料是否都被策略使用，或至少明確標示為 reference-only / unused 並說明理由；需掃描 DB services、core/generator 消費點、strategy_evidence、position_store、cross_day_context、market_theme_evidence_store、
daily_snapshot / signal store，列出 table -> writer -> reader -> strategy/formatter consumer -> current status。
3. 新表 public.market_theme_confirmed_evidence 是否已端到端串接；目前已知 schema 已建、read-only loader 已接 generator，但 writer / ingestion / backfill / RLS / read-only role / actual production data smoke 可能缺，需
列出 source raw data -> writer -> table -> loader -> provider -> Telegram -> strategy influence boundary。

## 使用者可見結果

本輪不改 Telegram 報文、不改策略、不改 DB、不改 runner。Owner 可見結果是三份交付文件中的審計結論：

- TASK.md：本任務卡。
- CHANGELOG.md：Tech 的 integration audit evidence matrix。
- QA_REPORT.md：QA 對 Tech 每個 PASS 的獨立反證結果與最終結論。

Owner 讀完後應能判斷：

- 是否可以繼續證據鏈下一階段開發。
- 哪些鏈路已 PASS。
- 哪些鏈路是 conditional / blocked。
- 哪些資料表已被策略或 formatter 消費。
- 哪些資料表目前只是 reference-only / unused。
- market_theme_confirmed_evidence 端到端缺口在哪裡。

## 非目標

- 不修 product bug。
- 不新增、修改或刪除產品代碼。
- 不新增、修改或刪除測試。
- 不改 SQL、schema、migration、RLS、role、runner、策略門檻、watchlist、Telegram formatter。
- 不做 live Supabase write。
- 不做 backfill。
- 不做 live Telegram delivery。
- 不把 audit 發現的問題順手修掉。
- 不把本輪擴成全量重構、策略重設或證據鏈新階段開發。
- 不要求 QA 做 full pytest，除非 QA 明確指出某個 PASS 結論只能靠指定測試反證，且不得修改任何檔案。

## 影響模組

本輪只讀審計以下範圍，Tech / QA 不得越界修改：

- core/generator.py
- core/market_theme_evidence.py
- services/market_theme_evidence_store.py
- services/position_store.py
- services/cross_day_context.py
- services/strategy_evidence.py
- services/daily_snapshot_store.py
- services/signal_store.py
- DB table / query constants referenced by the above modules
- GitHub fresh runner / scheduled report generation path 的既有入口摘要
- 既有 TASK.md / CHANGELOG.md / QA_REPORT.md 交付文件

## 直接消費者

- Owner：用 audit 結論決定是否繼續證據鏈開發。
- Architect：只依 CHANGELOG.md / QA_REPORT.md 收口，不依賴聊天紀錄。
- 後續 Tech：只能依本輪 evidence matrix 的 gap / next action 開新任務，不得把本輪 audit 當成已修復。
- 後續 QA：依本輪 QA 反證出的 blocked / conditional 項建立驗收邊界。

## 輸出契約

### Tech 輸出契約：CHANGELOG.md

CHANGELOG.md 必須從 # CHANGELOG: 開始，且只能寫審計結果，不得宣稱有產品修復。必須包含 evidence matrix，欄位固定為：

path/table | claim | evidence | current status | risk | next action

每一列要求：

- path/table：具體檔案、函式、table、query、consumer 或 runner path。
- claim：Tech 對該項的可核驗主張，例如 PASS fail-closed、BLOCKED fake fallback remains possible、REFERENCE_ONLY、UNUSED_NO_CONSUMER、READ_ONLY_ONLY。
- evidence：必須是可重查證據，例如檔案路徑、函式名、query 條件、status mapping、call chain、測試名稱或缺口證據；不得只寫「看起來」。
- current status：只能用明確狀態，建議值：
- PASS
- BLOCKED
- CONDITIONAL
- REFERENCE_ONLY
- UNUSED_NO_CONSUMER
- READ_ONLY_ONLY
- UNKNOWN_NEEDS_ARCHITECT_OR_OWNER_INPUT
- risk：若判斷錯，Owner 會看到或策略會受到什麼影響。
- next action：後續若要修，應另開哪類任務；本輪不得實作。

### QA 輸出契約：QA_REPORT.md

QA_REPORT.md 必須從 # QA_REPORT: 開始。QA 必須獨立反證 Tech 的每個 PASS，尤其檢查：

- 是否仍有 fake fallback。
- 是否有 DB table 無 writer / 無 reader / 無 strategy 或 formatter consumer。
- market_theme_confirmed_evidence 是否只有 read 沒有 writer，導致流程端到端斷點。
- GitHub fresh runner 清空 local/runtime/report-derived context 後，Tech 的 PASS 是否仍成立。

QA 結論只能是：

- 通過
- 阻塞
- conditional pass

### 必列 Audit Matrix 範圍

Tech 至少要列出以下鏈路；若實際 table / function 名稱不同，以程式實際名稱為準，但不得省略說明：

- public.market_theme_confirmed_evidence
- services/market_theme_evidence_store.py
- core/market_theme_evidence.py
- core/generator.py
- services/position_store.py
- positions table / position events table 或等價來源
- services/cross_day_context.py
- cross-day context 讀取的 DB tables / event sources
- services/strategy_evidence.py
- strategy evidence / outcome / classification audit 相關 tables
- services/daily_snapshot_store.py
- daily snapshot / signal snapshot tables
- services/signal_store.py
- price / market data source 或 table，例如 daily price / market bars，若存在
- GitHub fresh runner / scheduled report generation 如何取得 DB env、價格、持倉、events、evidence

## 已存在且不得回退的契約

以下契約來自目前專案摘要，Tech / QA 必須把它們當成 audit baseline，不得降級：

- 正式 TG 報文由 git / runner 啟動生成，runner 必須視為無狀態。
- 跨日策略記憶、歷史證據、已執行事件必須來自 production DB 或 Owner 指定持久來源。
- Runtime / local context 只能作為同一次報文內輔助 guard 或顯示材料，不得作為下一次 GitHub runner 的跨日判斷依據。
- DB / 真實來源不可用時，production runtime 不得用 fake/default/synthetic/fallback 補成可買、confirmed、持倉、今日交易、價格或 Telegram 結論。
- positions 不可回全 watchlist 0 股。
- position_events source-error 不可回全 0 event summary，避免誤讀為今日無交易。
- Market/theme evidence 的 confirmed / ready 必須同時滿足 production / Owner-approved persistent source family、required fields 與 freshness。
- report-derived / runtime diagnostic 只能作 trace，不得污染頂層 source_family 或 confirmed 判斷。
- public.market_theme_confirmed_evidence 的 confirmed 條件固定為 support_level in ('confirmed','supporting')、evidence_status='confirmed'、freshness='fresh'。
- support_level=strong 不得被接受或轉成 confirmed。
- confirmed market/theme evidence 不得放寬 BUY / SELL / RR / 加減碼 / 過熱 / 漲停不追門檻。
- 最新使用者可見 Telegram 版本是 v20.4.3；本輪 audit 不升版。

若 Tech 發現上述契約與實際程式不一致，必須標記 BLOCKED 或 CONDITIONAL，不得自行改碼修正。

## 驗收條件

1. Tech 的 CHANGELOG.md 有完整 evidence matrix，且覆蓋 Owner 指定三大問題。
2. 每個 PASS 都有具體 path / table / function / query / call chain 證據。
3. Tech 明確列出 DB table -> writer -> reader -> strategy/formatter consumer -> current status。
4. Tech 明確列出 market_theme_confirmed_evidence 的端到端鏈路：
source raw data -> writer -> table -> loader -> provider -> Telegram -> strategy influence boundary。
5. Tech 對缺 DB、缺價格、缺持倉、缺 events、缺 evidence 的 fail-closed 行為逐項下結論，不得合併成一句「都有處理」。
6. Tech 對 fake/default/synthetic/fallback/local/runtime/report-derived confirmed 做關鍵字與 call chain 掃描，並列出是否仍可能影響策略或 formatter。
7. QA 不只重讀 Tech 結論；必須對每個 PASS 做獨立反證。
8. QA 必須特別反證：
- fake fallback 是否仍存在。
- DB table 是否無人消費。
- market_theme_confirmed_evidence 是否只有 reader / loader，沒有 writer / ingestion / backfill / production data smoke。
- fresh runner 無本地狀態時是否仍能成立。
9. 若任何關鍵鏈路無法證明，結論必須是 阻塞 或 conditional pass，不得寫 通過。
10. 本輪不得產生任何產品代碼、測試、SQL、schema、runner 或策略 diff。
