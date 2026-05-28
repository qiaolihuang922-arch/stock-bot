# TASK: Market Theme Evidence Production Confirmed

## 任務狀態

- task_id: market-theme-evidence-production-pm-20260528
- 任務類型: feature
- 狀態: ready_for_tech
- 版本建議: minor
- QA 分級建議: L3
- 建議使用者可見版本: v20.2.0
- 任務目標: 定義「市場 / 題材證據鏈 production confirmed」的產品需求、輸出契約與安全邊界；本輪只允許 dry-run / runtime evidence 接入與報文呈現，不要求建表、不做 live write。

## Owner 問題

Owner 要解決的是：目前 v20.1.x 已有 dry-run helper 與 structured provider adapter，但還不能真正稱為 production confirmed，因為缺少第二類 production runtime source 來佐證市場 / 題材判斷。

本輪要讓 Telegram 報文可以在有足夠 runtime evidence 時顯示「confirmed」等級，並在證據不足、過期、混雜或來源缺失時自動降級，避免無證據寫出市場主線、AI / 電子供應鏈偏多、或類似可買暗示。

## 使用者可見結果

Owner 在 Telegram 報文手機第一屏或接近第一屏位置，應看到一段短而可追溯的市場 / 題材證據區塊：

- 明確顯示 evidence 等級：confirmed / weak / mixed / stale / absent。
- 明確顯示 runtime source freshness：例如 watchlist breadth: T+0、sector index: T+0、flow: unavailable。
- 明確顯示行動限制：市場 / 題材 confirmed 只代表可追蹤背景，不代表個股可買。
- 若買點、RR、冷卻、回測或風控未成立，仍需顯示 新倉：無有效進場 或等價不可買文案。
- 缺證據時，不得出現 AI / 電子供應鏈仍偏多、市場主線仍在、不代表看空產業 等高風險句。

## 非目標

- 不改策略 decision。
- 不放寬買點、RR、冷卻、回測、量能或風控條件。
- 不新增 DB schema。
- 不建 Supabase table。
- 不做 live Supabase write。
- 不做正式 backfill。
- 不做 live Telegram delivery。
- 不接未經 Owner approval 的外部付費 provider、news provider、browser scraping 或長期 scheduler。
- 不把外部產業新聞單獨轉成個股交易建議。
- 不重構 unrelated formatter、watchlist、position、snapshot 或策略模組。

## 影響模組

- 直接模組:
- core/market_theme_evidence.py
- core/generator.py
- 既有 market theme evidence provider / formatter path
- 可能讀取但不得改變策略語意的來源:
- core/watchlist.py
- services/analysis.py
- services/stock_api.py
- snapshot / strategy evidence 相關既有 dry-run 資料
- 測試影響:
- market theme evidence tests
- generator / Telegram formatter snapshot tests
- notifier payload smoke tests
- strategy invariance tests

## 直接消費者

- Owner 手機 Telegram 報文。
- core/generator.py 報文組裝與 header version。
- Telegram notifier message list / payload contract。
- QA snapshot / formatter tests。
- 後續可能接 DB 或 cache 的 Architect / Tech 規劃，但本輪不得直接落地 DB 或 live write。

## 輸出契約

### Evidence Object Contract

market_theme_evidence 必須維持或擴充為結構化 payload，至少包含：

as_of: "2026-05-28"
level: "confirmed | weak | mixed | stale | absent"
theme: "AI / electronics / semiconductor / broad_market / unknown"
market_direction: "supportive | neutral | weak | mixed | unknown"
execution_implication: "track_only | no_valid_entry | risk_first | unavailable"
sources:
- source_type: "watchlist_breadth | market_index | sector_index | flow | official | external_context"
source_name: "watchlist_strategy_snapshot | TAIEX | electronics_index | ..."
as_of: "2026-05-28"
freshness: "fresh | stale | unavailable"
freshness_reason: "same_trade_date | previous_trade_date_allowed | older_than_threshold | missing"
level: "supportive | neutral | weak | mixed | unavailable"
limitations:
- "只佐證題材背景，不改變個股買點"
supports_claims:
- "市場偏多但買點未成立"
limitations:
- "confirmed 不代表可買"
formatter_allowed_phrases:
- "市場 / 題材證據 confirmed，但新倉仍需個股買點成立"
formatter_forbidden_phrases:
- "AI / 電子供應鏈仍偏多"

### Runtime Source 類型

本輪 confirmed 至少需要兩類 independent runtime source 同向，且不得只靠 report-derived 文字：

- 必要 source 1: watchlist_breadth
- 來源: 既有 watchlist / strategy snapshot / strategy evidence runtime 結果。
- 用途: 判斷題材內標的是否多數維持強勢、分類未惡化、量能或策略條件是否支持追蹤。
- 必要 source 2: market_index 或 sector_index
- 來源: production runtime 可取得的 TAIEX、電子類、半導體 / 科技相關 index 或可替代的市場層行情資料。
- 用途: 佐證市場層是否 supportive。
- 可選 source:
- flow: 法人買賣超、外資持股或產業持股比。
- official: TWSE、MOPS、MOEA、MOF、公司 IR。
- external_context: 外部產業背景，只能輔助，不得單獨 confirmed。

若本輪實作找不到第二類可用 runtime source，必須降級為 weak / absent，不得硬湊 confirmed。

### Source Freshness

Tech 必須讓每個 source 明確標示 freshness，不得只有來源名稱。

- watchlist_breadth: 必須是本次報文同一交易日或同一 run 的 strategy snapshot；缺失則 unavailable。
- market_index / sector_index: 預設需同一交易日收盤或最新可得交易日；若遇假日或資料延遲，最多允許上一個有效交易日，但必須標示 previous_trade_date_allowed。
- flow: 若使用，最多允許上一個官方公布交易日；超過則 stale。
- official / external_context: 若使用，只能做背景；超過 PM/Tech 定義 freshness threshold 時不得支撐 confirmed。
- 任一 required source stale / unavailable 時，不得輸出 confirmed。
- 任一 source 無 as_of 時，視為 unavailable。

### Cache / Schema 邊界

- 本輪不得新增 Supabase schema、table、migration、RLS policy、index 或 rollback。
- 本輪不得寫 Supabase cache。
- 本輪不得新增長期 disk cache 或排程 cache。
- 允許使用既有 runtime memory、既有 dry-run fixture、既有 provider adapter、或單次 report generation 內的 ephemeral cache。
- 若 Tech 判斷沒有 cache 就無法穩定 production confirmed，必須 blocked，回報需要 Owner approval，不能自行建 cache。
- 若需要新增欄位到持久層、snapshot DB、signal table 或 daily snapshot payload，必須先通知 Owner，不能在本輪直接做。

### Telegram Message Contract

- Evidence 區塊需短句、短行，手機優先。
- Evidence 區塊必須先給結論與限制，再列來源摘要。
- 市場 / 題材證據只影響 Telegram 文案與 evidence 區塊。
- 不得改變策略分類、買賣建議、持倉主行動或下單清單。
- confirmed 也不得讓 新倉 從不可買變可買。
- 若 evidence 與策略買點衝突，策略買點與風控優先，文案應寫 題材可追蹤，買點未成立。

## 版本契約

- 本輪是使用者可見 Telegram 報文能力新增，建議升版到 v20.2.0。
- Tech 必須同步 core/generator.py 的 VERSION 或等價 Telegram header 常量。
- QA 必須核對實際輸出 header 顯示 v20.2.0。
- 若 Tech 判斷本輪只完成 blocked / dry-run 無使用者可見變更，必須在 CHANGELOG.md 說明為何不升版，並由 Architect / Owner 決定是否接受。

## 驗收條件

1. confirmed 只能在至少兩類 runtime source 同向且 fresh 時出現，其中一類必須是 watchlist_breadth，另一類必須是 market_index 或 sector_index。
2. 只有 report-derived、單一 source、缺 as_of、source stale、source unavailable 時，不得輸出 confirmed。
3. mixed 場景：外部或官方背景偏強，但 watchlist breadth 或策略分類不支持時，只能 mixed / weak，不得 confirmed。
4. stale 場景：任一 required source 過期時，Telegram 必須標示 stale 並降級，不得使用主線偏多文案。
5. absent 場景：無足夠 evidence 時，Telegram 必須寫 市場證據不足，僅依策略分類追蹤 或等價短句。
6. confirmed 場景：Telegram 可以寫 市場 / 題材證據 confirmed，但同屏必須寫 不代表可買 或 買點仍需個股條件成立。
7. 證據鏈不得改變任何 strategy decision、個股買點、持倉主行動、watchlist 成員、DB write path 或 Telegram delivery 行為。
8. 報文不得新增空區塊、0-count 占位、或重複長句。
9. Telegram message list / notifier payload shape 不得破壞既有直接消費者。
10. QA 需執行 L3，但停止條件如下：
- 已覆蓋 confirmed / weak / mixed / stale / absent 五類 fixture。
- 已驗證 strategy decision before/after 不變。
- 已驗證 formatter header version。
- 已驗證 notifier payload smoke。
- 已完成 replay/backfill dry-run 或等價 no-live-write path 檢查，且確認沒有 Supabase live write、正式 backfill、live Telegram。
- 不要求正式 live delivery、不要求 production Supabase write、不要求真實 backfill 寫庫。

## 範例或 fixture

### Fixture A: confirmed 但不可買

市場 / 題材證據：confirmed
限制：題材可追蹤，不代表可買
來源：watchlist breadth fresh；電子類指數 fresh
新倉：無有效進場
原因：個股買點 / RR / 冷卻仍未全部成立

期望：

- 可出現 confirmed。
- 不得出現 今日可買，除非原策略買點成立。
- 不得把 confirmed 轉成 BUY。

### Fixture B: stale 降級

市場 / 題材證據：stale
限制：市場資料過期，本輪不判斷主線
來源：watchlist breadth fresh；sector index stale
新倉：無有效進場

期望：

- 不得出現 AI / 電子供應鏈仍偏多。
- 不得出現 市場主線仍在。
- 不得 confirmed。

### Fixture C: mixed 背景強但 watchlist 弱

市場 / 題材證據：mixed
限制：外部背景偏強，但 watchlist 未支持
來源：official context fresh；watchlist breadth weak
新倉：無有效進場

期望：

- 只能寫背景或追蹤。
- 不得寫 confirmed。
- 不得放寬買點。

### Fixture D: absent

市場 / 題材證據：absent
限制：市場證據不足，僅依策略分類追蹤
新倉：無有效進場

期望：

- 不得輸出主線、偏多、供應鏈仍強等文案。
- 不得新增空來源清單。

## 禁止事項

- 禁止改策略 decision。
- 禁止放寬買點。
- 禁止新增 Supabase schema / table / migration。
- 禁止 live Supabase write。
- 禁止正式 backfill。
- 禁止 live Telegram。
- 禁止自行接 external provider、news scraping、付費 API 或長期 scheduler。
- 禁止用 stale / missing source 推出 confirmed。
- 禁止用外部產業背景單獨推出今日可買。
- 禁止將 evidence 寫入持久 DB。
- 禁止刪除固定 8 份 Markdown。
- 禁止順手重構 unrelated module。

## 需要先通知 Owner 的 Approval Gates

Tech 遇到以下任一情況必須 blocked，回報 Architect / Owner，不得自行實作：

- 需要新增 DB table、schema、migration、RLS、index 或 rollback。
- 需要寫 Supabase cache 或任何持久 cache。
- 需要正式 backfill 或 production data migration。
- 需要 live Supabase write。
- 需要 live Telegram delivery。
- 需要新增 external provider、付費 API、browser scraping、新聞 ingestion 或 scheduler。
- 需要擴大 watchlist 或改股票清單來源。
- 需要讓 evidence 參與 strategy decision、買點、持倉行動或下單清單。
- 無法取得第二類 runtime source，但仍想顯示 confirmed。
- freshness threshold 需要改成超過上一個有效交易日。

## 阻塞條件

- 找不到可用第二類 production runtime source，且只能依 report-derived 或單一 source 判斷。
- 現有 runtime source 無 as_of，導致 freshness 無法判斷。
- 需要建表、cache、external provider、正式 backfill 或 live write 才能達成本輪目標。
- 無法在測試中證明 strategy decision before/after 不變。
- 無法在測試中證明 Telegram header version 與 VERSION 常量同步。
- 無法提供 confirmed / weak / mixed / stale / absent 五類 fixture 驗證。
- 任一實作會讓 evidence 影響可買、加碼、減碼、停損、停利或持倉主行動。
