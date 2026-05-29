# TASK: Runtime Market Breadth Evidence Fallback

## 任務狀態

- task_id: v20.3.0-runtime-market-breadth-evidence-fallback
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本契約: 升版到 v20.3.0
- QA 分級建議: L2
- 任務尺寸判斷: normal_patch
- 理由: 本輪改 Telegram 市場/題材 evidence 顯示與 evidence fallback contract，涉及使用者可見報文與直接消費者，但不得改交易策略、DB schema、watchlist universe 或 live path。
- 非 tiny_patch: 不是單一文案修正，需處理 runtime evidence 來源、缺來源標記與 confirmed 禁止條件。
- 非 risk_patch: 不得改 BUY/SELL/RR/過熱/漲停不追/可準備分類，也不得新增進場建議。

## Owner 問題

v20.2.0 已建立 market/theme evidence contract，但 production 尚未有 evidence table/cache 時，Telegram 市場/題材區塊仍顯示「策略證據未啟用 / absent」，導致 Owner 在手機上看不到任何可追溯的市場或題材背景。

Owner 要繼續證據鏈，但本輪必須不建表、不 live write、不 backfill；在缺 DB evidence table/cache 的情況下，先用現有 runtime watchlist breadth / 本次報告已計算的 watchlist signals 生成可驗證的 weak/runtime evidence，讓報
文清楚表示「內部觀察池偏強，但缺大盤/族群指數，未確認」。

## 使用者可見結果

Owner 在 Telegram 手機報文的市場/題材 evidence 區塊會看到：

- 若 DB evidence table/cache 不存在，但 runtime watchlist breadth 足夠且偏支持:
- 不再只顯示 absent 或「策略證據未啟用」。
- 顯示 weak / runtime / missing-source 級別的市場或題材觀察證據。
- 文案必須明確說明這只是內部觀察池廣度支持或偏強，缺大盤/族群指數，因此未確認。
- 若 runtime data 也不足:
- 仍可顯示 absent。
- 但必須說明缺哪類來源，例如缺 watchlist breadth、缺 market_index、缺 sector_index 或缺 runtime signals。
- 交易決策、分類與建議不變:
- 不因 weak runtime evidence 新增可買、可準備、加碼或任何進場暗示。

手機閱讀路徑:

1. Owner 打開 Telegram 先看 summary / 決策區。
2. 市場/題材 evidence 區塊只能補充背景強弱，不能看起來像進場推薦。
3. 文案必須先講 evidence 等級與未確認原因，再講支持內容。
4. 缺資料時要短句說明缺口，不輸出空標題或模糊的 absent。

## 非目標

- 不建立 DB evidence table。
- 不新增 migration。
- 不寫 Supabase。
- 不 live Telegram delivery。
- 不 backfill。
- 不改 market/theme evidence 的長期 DB contract。
- 不改 BUY/SELL/RR/過熱/漲停不追/可準備分類邏輯。
- 不新增進場建議、加碼建議或交易優先級。
- 不重設策略、不重寫 evidence 架構、不做全量清理。
- 不要求 L3 full pytest、replay/backfill dry-run 或 live payload 驗證。

## 影響模組

Tech 應只檢查並修改與下列範圍直接相關的模組:

- market/theme evidence fallback 建構邏輯。
- Telegram formatter 中市場/題材 evidence 區塊。
- 目前報告流程中已存在的 runtime watchlist breadth / watchlist signals 消費點。
- 版本常量或 Telegram header 版本顯示。
- 對應的局部 formatter / evidence contract 測試與 fixtures。

不得擴大到:

- DB schema / migrations。
- Supabase write path。
- watchlist universe 來源或篩選邏輯。
- 策略 decision engine。
- backfill / replay / live delivery entrypoint。

## 直接消費者

- Telegram 報文市場/題材 evidence 區塊。
- Telegram summary 或 header 中顯示版本字串的直接 formatter。
- market/theme evidence message list contract 的直接呼叫方。
- QA 用來產生接近真實 Telegram 長報文的 formatter fixture。

## 輸出契約

### Evidence fallback contract

當 DB evidence table/cache 不存在或不可用時:

- 可使用本次 runtime 已計算的 watchlist breadth / watchlist signals 產生 fallback evidence。
- fallback evidence 最高只能是:
- weak
- runtime
- missing-source
- 若缺 market_index 或 sector_index，不得輸出 confirmed。
- fallback evidence 必須帶出缺來源原因，至少能區分:
- 缺 DB evidence table/cache。
- 缺 market_index。
- 缺 sector_index。
- 缺 runtime watchlist breadth / watchlist signals。
- runtime breadth 支持時，文案語意必須是「偏支持 / 偏強但未確認」，不得是「確認轉強」「可買」「進場」。

### Telegram 文案 contract

可接受語意示例:

市場證據：weak/runtime
內部觀察池廣度偏強；缺大盤指數 evidence，未確認。

題材證據：weak/runtime
觀察池同題材訊號偏支持；缺族群指數 evidence，未確認。

runtime data 不足時示例:

市場證據：absent/missing-source
缺 runtime watchlist breadth，且無 DB evidence table/cache；本輪不確認市場證據。

題材證據：absent/missing-source
缺 sector_index 與可用觀察池題材廣度；本輪不確認題材證據。

禁止文案語意:

市場確認轉強，可進場

題材 confirmed

觀察池偏強，新增可買

### 版本契約

- Telegram 使用者可見版本必須顯示 v20.3.0。
- Tech 必須同步實際版本常量 / header / 測試期望。
- 不得只在文件寫 v20.3.0，實際 Telegram header 仍停在舊版。

## 已存在且不得回退的契約

- v20.2.0 已建立的 market/theme evidence contract 不得移除或改成只剩文案。
- 缺 DB evidence table/cache 時不得假裝已 confirmed。
- evidence 不得改變交易決策。
- Telegram 報文必須手機優先，summary / 市場題材 / 詳情的語意不得互相矛盾。
- 無可買時不得使用像推薦的文案。
- 可買、準備、僅追蹤、不可行動 必須分開。
- 空區塊與 0-count no-op 文案不得為了占位輸出。
- 不得回退既有版本契約；本輪應升到 v20.3.0。

若 Tech 發現 v20.2.0 evidence contract 的實際欄位名稱、等級枚舉或直接消費者與本 TASK 描述不一致，必須 blocked 回報 Architect，不得自行重定義 contract。

## 驗收條件

1. 無 DB evidence table/cache，但 watchlist breadth supportive 且缺 market/sector index 時:
- Telegram 市場/題材區塊顯示 weak/runtime evidence。
- 文案清楚說明內部觀察池廣度支持或偏強。
- 文案清楚說明缺大盤/族群指數，未確認。
- 不出現 confirmed。
2. runtime breadth / watchlist signals 不足時:
- 仍可顯示 absent。
- 必須標示 missing-source 或等價缺來源訊息。
- 必須指出缺哪類來源。
3. 交易決策不變:
- BUY/SELL/RR/過熱/漲停不追/可準備分類不得因 fallback evidence 改變。
- 不新增任何進場、加碼或可準備建議。
4. 版本顯示:
- Telegram header 或等價使用者可見版本顯示 v20.3.0。
5. 無 forbidden diff:
- 無 DB schema / migration diff。
- 無 Supabase write path diff。
- 無 watchlist universe 或 watchlist source diff。
- 無 live Telegram delivery diff。
- 無 replay/backfill 行為 diff。
6. 手機閱讀:
- 接近真實長報文中，Owner 能在市場/題材 evidence 區塊直接看出「runtime weak、缺來源、未確認」。
- weak runtime evidence 不得在 summary 或執行清單中被包裝成買入理由。

## 範例或 fixture

### Fixture A: no evidence table + supportive runtime breadth + missing indexes

輸入形狀:

db_evidence_table: missing
evidence_cache: missing
runtime_watchlist_breadth:
available: true
supportive: true
signal_count: 8
total_count: 12
market_index: missing
sector_index: missing
pre_existing_decisions:
buy: []
prepare: ["2330"]
tracking_only: ["2317", "2454"]
not_actionable: ["9999"]

期望輸出形狀:

市場證據：weak/runtime
內部觀察池廣度偏強；缺大盤指數 evidence，未確認。

題材證據：weak/runtime
觀察池同題材訊號偏支持；缺族群指數 evidence，未確認。

期望不變:

buy: []
prepare: ["2330"]
tracking_only: ["2317", "2454"]
not_actionable: ["9999"]
confirmed_present: false

### Fixture B: no evidence table + missing runtime breadth

輸入形狀:

db_evidence_table: missing
evidence_cache: missing
runtime_watchlist_breadth:
available: false
market_index: missing
sector_index: missing
pre_existing_decisions:
buy: []
prepare: []
tracking_only: ["2330"]
not_actionable: ["9999"]

期望輸出形狀:

市場證據：absent/missing-source
缺 runtime watchlist breadth，且無 DB evidence table/cache；本輪不確認市場證據。

題材證據：absent/missing-source
缺 sector_index 與可用觀察池題材廣度；本輪不確認題材證據。

期望不變:

buy: []
prepare: []
tracking_only: ["2330"]
not_actionable: ["9999"]
confirmed_present: false

## 明確禁止事項

- 禁止建立 DB table。
- 禁止新增 migration。
- 禁止寫 Supabase。
- 禁止 live Telegram delivery。
- 禁止 backfill。
- 禁止修改 watchlist universe 或 watchlist source。
- 禁止修改 BUY/SELL/RR/過熱/漲停不追/可準備分類。
- 禁止因 weak/runtime evidence 新增進場建議。
- 禁止在缺 market_index 或 sector_index 時輸出 confirmed。
- 禁止把 absent 寫成沒有原因的空泛文案。
- 禁止為了本輪修正做全量重構、全 repo 清理或 L3 驗證擴張。
- 禁止回退 v20.2.0 已建立的 market/theme evidence contract。

## 阻塞條件

Tech 必須 blocked，而不是自行決策，若遇到以下情況:

- 找不到 v20.2.0 market/theme evidence contract 的實際欄位、等級或直接消費者。
- runtime watchlist breadth / watchlist signals 在目前報告流程中不存在或無法安全取得。
- 現有 formatter 無法區分 weak/runtime/missing-source/confirmed，且需要重定義 public contract。
- 升版到 v20.3.0 會牽涉不明版本來源或多處 header 不一致。
- 要達成需求必須建立 DB table、migration、Supabase write、backfill 或改 live delivery。
- 發現 weak runtime evidence 目前會被策略 engine 消費並影響交易分類。

## QA 分級建議

- QA 等級: L2
- 驗證範圍:
- formatter / evidence contract 局部測試。
- 直接消費者測試。
- 策略不變性 smoke。
- 接近真實 Telegram 長報文手機閱讀檢查。
- forbidden diff 檢查。
- 不做:
- full pytest。
- replay/backfill dry-run。
- live Telegram。
- live Supabase write。
- production DB schema 驗證。

QA 必須補 Tech 自檢以外的反證:

- 用 Fixture A 驗證 weak runtime evidence 顯示且 confirmed 不出現。
- 用 Fixture B 驗證 absent/missing-source 並指出缺來源。
- 比對 fallback 前後交易分類完全不變。
- 檢查 diff 中沒有 DB/schema/watchlist/live/backfill 相關修改。
- 從 Owner 手機閱讀順序確認文案不會被誤讀為買入或確認訊號。

## 本輪停止條件

完成以下項目即停止，不納入旁支擴張:

- Telegram 市場/題材區塊可在無 DB evidence table/cache 時顯示 weak/runtime fallback。
- runtime data 不足時可顯示 absent/missing-source 並說明缺來源。
- confirmed 在缺 market/sector index 時不出現。
- 交易分類不變。
- 使用者可見版本為 v20.3.0。
- L2 驗證通過 forbidden diff 與手機閱讀檢查。

旁支只記待辦，不納入本輪:

- 正式 evidence table 建表與 migration。
- Supabase evidence write。
- evidence backfill。
- market_index / sector_index 外部資料接入。
- 長期 market/theme evidence scoring 改版。
- watchlist breadth 指標重設。
