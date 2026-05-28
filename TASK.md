# TASK: v20.1.2 Market Theme Evidence Structured Provider 接線

## 任務狀態

- task_id: market_theme_evidence_structured_provider_v20_1_2
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: patch，由 v20.1.1 升至 v20.1.2
- 版本契約: Telegram 報文 header / formatter 可見版本必須顯示 v20.1.2
- QA 分級建議: L2

## Owner 問題

Owner 已確認 v20.1.1 手機報文修復可繼續證據鏈下一步。現在要把 v20.1.0 的 market_theme_evidence dry-run helper 往 production formatter 可用方向推進，但本輪仍不得建表、不得寫庫、不得接外部 provider。

核心問題是：formatter 目前已有 evidence helper contract，但 production 報文不能只靠 helper 或 report-derived 資料自我證明「市場 / 題材 confirmed」。本輪要建立可由 formatter / notifier 直接消費的 structured provider 接
線，且只吃現有 runtime 已能取得的結構化輸入。若 runtime 只有 report-derived family，報文必須維持 weak / track only，不得升成 confirmed。

## 使用者可見結果

Owner 在手機 Telegram 打開報文後應看到：

1. Header 版本為 v20.1.2。
2. 市場 / 題材 evidence 行仍出現在手機 summary 的決策脈絡中，但語意更明確區分：
- confirmed：只有兩類完整 structured source family 同向且新鮮時才可出現。
- weak：只有 report-derived 或單一來源時，只能寫來源不足、僅追蹤。
- absent / stale：不得包裝成市場主線偏多。
3. 即使市場 / 題材 confirmed，個股買點、RR、回測、冷卻與風控沒有成立時，仍顯示不可買 / 無有效進場。
4. Report-derived only 場景不得讓 Owner 誤讀成「AI / 電子供應鏈 confirmed 偏多」或「今天可追主線買進」。

## 非目標

- 不新增 DB table / schema / migration。
- 不新增 evidence cache 或持久化 history。
- 不做 live Supabase write。
- 不做 live Telegram delivery。
- 不做正式 backfill。
- 不新增外部 provider。
- 不接 TWSE / MOPS / FinMind / news / 法人等新資料源。
- 不修改 watchlist。
- 不修改策略 decision、個股買賣、加減碼、停損、停利、RR 或分類邏輯。
- 不讓市場 / 題材 evidence 放寬任何個股買點。
- 不把 report-derived、watchlist_groups、formatter input 互相拆成多個 family 來湊 confirmed。

## 影響模組

- Market theme evidence helper / provider: core/market_theme_evidence.py 或等價模組。
- Telegram formatter / report generator: core/generator.py 或等價 formatter 模組。
- Telegram message list contract: formatter 輸出的連續訊息、summary、header、market theme evidence 行。
- Telegram notifier direct consumer: notifier 需仍能消費 formatter message list。
- 相關 formatter / market theme evidence / notifier tests。

## 直接消費者

- Owner 手機 Telegram 報文。
- formatTelegramMessages() / report formatter 的 message list 輸出。
- Telegram notifier / sender。
- generate_report() 或 production 報文組裝入口。
- QA fixture / snapshot / direct consumer smoke。
- 後續 production evidence provider / DB schema 任務的上游 contract 參考。

## 輸出契約

### Structured Provider Contract

本輪需建立或接線一個 production formatter 可用的 structured provider path。它可以是現有 helper 的 wrapper、adapter 或 provider function，但輸出必須是結構化 evidence object，不得只回傳文字。

建議輸出形狀：

market_theme_evidence:
as_of: "2026-05-28T13:30:00+08:00"
level: confirmed | weak | absent | stale
theme: "AI/electronics_supply_chain" | "market" | "unknown"
market_direction: bullish | neutral | bearish | unknown
execution_implication: no_trade_signal
source_families:
- family: report_derived
status: complete | partial | missing | stale
as_of: "2026-05-28T13:30:00+08:00"
freshness: fresh | stale | unknown
confidence: high | medium | low | unknown
supports_claims:
- "theme_trackable"
limitations:
- "formatter/report-derived only; cannot confirm market theme"
- family: existing_runtime_structured_source
status: complete | partial | missing | stale
as_of: "..."
freshness: fresh | stale | unknown
confidence: high | medium | low | unknown
supports_claims: []
limitations: []
formatter_allowed_phrases:
- "來源不足，僅追蹤"
formatter_forbidden_phrases:
- "AI / 電子供應鏈 confirmed 偏多"
- "今日可追主線買進"

### Source Family Rules

- confirmed 必須同時符合：
- 至少兩類不同 structured source family。
- 每類都具備 as_of、freshness、confidence、supports_claims、limitations。
- 兩類來源同向支持同一個市場 / 題材 claim。
- 無 stale 或 missing 的必要欄位。
- report_derived family 包含：
- results_map
- watchlist_groups
- formatter report input
- formatter 已推導 summary / market_summary
- 上述 report-derived 資料即使來自多個欄位，也只能算同一個 source family。
- Report-derived only 永遠不得輸出 confirmed，只能是 weak、absent 或 stale。
- 若現有 runtime 無第二類完整 structured source family，本輪仍應完成 provider 接線，但實際 formatter 輸出只能 weak / track only。

### Formatter Contract

手機 summary 中市場 / 題材 evidence 行需遵守：

- confirmed 可用短句：
- 市場題材：AI / 電子供應鏈證據偏多，但買點仍看個股條件
- weak 必須用短句：
- 市場題材：來源不足，僅追蹤
- 市場題材：report-derived only，僅追蹤
- absent 必須用短句：
- 市場題材：無可用結構化證據
- stale 必須用短句：
- 市場題材：證據過期，僅追蹤

禁止 formatter 因 market theme evidence 輸出以下語意：

- 今日可追主線買進
- AI / 電子供應鏈 confirmed 偏多，除非 confirmed 條件完整成立。
- 市場偏多，所以放寬買點
- 題材偏多，所以 RR / 回測 / 冷卻可忽略

### 手機閱讀路徑

Owner 手機第一屏閱讀順序應為：

1. Header：確認 v20.1.2。
2. 今日新倉：先回答能不能買。
3. 持倉：先回答是否風控 / 續抱 / 不加碼。
4. 市場題材 evidence：只作背景與追蹤，不蓋過個股買點。
5. 未持倉：分清可買、準備、僅追蹤、不可行動。
6. 詳情：需要追溯時再看 source family / limitations。

## 驗收條件

1. Telegram header / formatter 可見版本為 v20.1.2，不得仍顯示 v20.1.1。
2. Production formatter path 會呼叫 structured market theme evidence provider / adapter，而不是只在 dry-run helper 測試中存在。
3. Provider output 是結構化 object，至少包含 level、as_of、source_families、supports_claims、limitations。
4. results_map、watchlist_groups、formatter report input、market_summary 等 report-derived 欄位只能算同一個 source family。
5. Report-derived only fixture 輸出必須是 weak 或更低，且 Telegram 只能顯示 來源不足 / 僅追蹤，不得顯示 confirmed。
6. Missing second structured source family fixture 不得 confirmed。
7. Stale source fixture 不得 confirmed，需降級 stale 或 weak，並在手機文字上標示證據過期或僅追蹤。
8. Two complete structured source families fixture 可輸出 confirmed，但仍必須顯示「買點仍看個股條件」或等價 guard。
9. Confirmed market theme fixture 不得讓原本不可買的個股變成可買；策略 decision、position action、entry sizing、RR、cooldown 結果需保持不變。
10. Non-AI / unknown theme fixture 不得輸出 AI / 電子供應鏈主線文案。
11. Telegram message list contract 不得破壞；notifier direct consumer smoke 必須能消費 formatter output。
12. 手機 summary 不得把 market theme evidence 放在比「今日能不能買」更容易誤讀的位置，且不得使用像推薦買進的文案。
13. 不得新增 DB schema / table / cache，不得新增外部 provider，不得 live Telegram，不得 Supabase write，不得 backfill。
14. 相關 market theme evidence、formatter、notifier 測試通過。

## 範例或 fixture

### Fixture A: report-derived only

Input shape:

results_map:
2330:
category: track
reason: "題材仍可追蹤"
watchlist_groups:
ai_supply_chain:
- 2330
market_summary: "AI / 電子供應鏈仍偏多"
external_or_independent_sources: []

Expected evidence:

level: weak
source_families:
- family: report_derived
status: complete
supports_claims:
- theme_trackable
limitations:
- cannot_confirm_market_theme_without_second_structured_family
formatter_text: "市場題材：來源不足，僅追蹤"

不得出現：

AI / 電子供應鏈 confirmed 偏多
今日可追主線買進

### Fixture B: two complete structured source families

Input shape:

source_families:
- family: report_derived
status: complete
as_of: "2026-05-28T13:30:00+08:00"
freshness: fresh
confidence: medium
supports_claims:
- ai_supply_chain_trackable
limitations:
- report-derived; not trade signal
- family: existing_runtime_structured_source
status: complete
as_of: "2026-05-28T13:30:00+08:00"
freshness: fresh
confidence: medium
supports_claims:
- ai_supply_chain_trackable
limitations:
- market/theme only; individual entries unchanged
stock_entry_signal:
2330: false

Expected Telegram shape:

【05/28 盤後｜v20.1.2】

今日新倉：無有效進場。
市場題材：AI / 電子供應鏈證據偏多，但買點仍看個股條件。
未持倉：僅追蹤，等回測 / RR / 冷卻條件。

不得出現：

今日可追主線買進
2330｜可買

除非原策略買點已成立。

### Fixture C: stale source

Expected Telegram shape:

市場題材：證據過期，僅追蹤。
新倉：無有效進場。

### Fixture D: non-AI theme

Expected Telegram shape:

市場題材：來源不足，僅追蹤。

不得出現：

AI / 電子供應鏈仍偏多
AI 主線

## 明確禁止事項

- 禁止新增 DB table / schema / migration。
- 禁止新增 cache / persistent evidence history。
- 禁止正式 Supabase write。
- 禁止 live Telegram delivery。
- 禁止正式 backfill。
- 禁止新增外部 provider 或外部 API 接線。
- 禁止用 report-derived 欄位互相湊成兩類 source family。
- 禁止把 market/theme evidence 接入策略 decision 或個股買點放寬。
- 禁止讓 confirmed market theme 改變任何個股 action、position sizing、RR、cooldown、停損停利。
- 禁止在來源不足時輸出 confirmed、偏多主線或可買語意。
- 禁止把 TASK.md 未定義的新資料源、新 schema 或新 side effect 視為可自行實作範圍。
- 禁止刪除固定 8 份 Markdown。
- 禁止修改 unrelated cleanup / refactor。

## 阻塞條件

Tech 必須 blocked，若遇到以下任一情況：

- 要達成 production formatter 接線必須新增 DB table / schema / migration。
- 要達成 confirmed 必須新增 cache、正式 Supabase write、backfill 或外部 provider。
- 現有 runtime 無法取得任何結構化輸入，只能靠自由文字或 formatter 文案推論 evidence。
- 無法區分 report-derived family 與其他 independent structured source family。
- Formatter / notifier direct consumer contract 不清楚，無法保證 message list 不破壞。
- 需求需要改策略 decision、買點、RR、cooldown、停損停利或 watchlist。
- 若本輪只能靠新增外部資料源才有產品價值，必須標記 blocked，並寫明需要 Architect 通知 Owner 決定是否批准 schema / provider / cache / write path。

## QA 分級建議

QA 分級: L2

QA 至少需驗證：

- Formatter 實際輸出 header 為 v20.1.2。
- Production formatter path 確實消費 structured provider output。
- Notifier direct consumer smoke 不破壞 message list。
- Report-derived only 負面案例只能 weak / track only。
- Missing second family、stale family、non-AI theme 負面案例不得 confirmed。
- Two complete structured family 正向案例可 confirmed，但不可放寬個股買點。
- 手機閱讀路徑中，市場題材 evidence 不得蓋過「今日能不能買」。
- 使用者不會把 來源不足 / 僅追蹤 誤讀成可買。
- 策略 decision、DB schema、watchlist、live Telegram、Supabase write、backfill 均未被修改或觸發。
