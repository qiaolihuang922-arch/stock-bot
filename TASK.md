# TASK: market_theme_evidence v20.1.0 confirmed 判斷收斂與 Telegram 弱證據呈現修復

## 任務狀態

- task_id: market_theme_evidence_v20_1_0_confirmed_source_family_fix
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本契約: 保持 v20.1.0，不得升版、不得回退。
- QA 分級建議: L2
- QA 升級原因: 本輪改到 Telegram formatter 可見語意、helper payload contract、notifier 直接消費路徑，且 QA 已以負面案例阻塞 confirmed 判斷過寬問題。

## Owner 問題

上一輪 market_theme_evidence v20.1.0 dry-run provider / payload contract 被 QA 阻塞：build_market_theme_evidence() 把 results_map + watchlist_groups 這類同屬報文衍生來源族群的資料湊成 confirmed｜AI/電子供應鏈偏多。

這違反既有 TASK 核心要求：confirmed 必須由至少兩類獨立、非循環、結構化內部來源支持。缺少 market_state、price_volume、structured_strategy_evidence 等 structured source 時，不得把 theme 字串或 report-derived 輸入包裝成
confirmed bullish market theme。

## 使用者可見結果

Owner 在手機 Telegram 打開報文時，若系統只拿到 results_map、watchlist_groups、formatter report input 這類報文衍生資料，應看到：

- 市場主題狀態為 weak、來源不足 或 只追蹤。
- 不得看到 confirmed。
- 不得看到 AI/電子供應鏈偏多 這種像已確認偏多的結論。
- 若買點未成立，即使主題 confirmed，也必須仍顯示不可買或只追蹤，不得變成買入建議。

## 非目標

- 不重開 market_theme_evidence v20.1.0 需求範圍。
- 不新增資料表。
- 不改策略 decision。
- 不改 DB payload schema 或正式寫庫流程。
- 不改 watchlist 來源、scheduler、live Telegram delivery、live Supabase write。
- 不把既有 strategy_evidence_summary 字串宣稱為已自動接入 structured confirmed。
- 不做正式 backfill。
- 不調整股票買賣策略、停損停利、持倉狀態機。

## 影響模組

- core/market_theme_evidence.py
- 本輪候選 diff 必須納入。
- 收斂 confirmed 判斷、source family 去重、structured source contract 驗證。
- core/generator.py
- formatTelegramSummary 或等價 Telegram summary formatter 必須正確呈現 weak / 來源不足 / 只追蹤。
- 必須核對 VERSION 或等價 header 版本仍為 v20.1.0。
- notifier 相關 Telegram 直接消費路徑
- 驗證 formatter 輸出進入 Telegram message list 後不誤導。
- tests/test_market_theme_evidence.py
- 本輪候選 diff 必須納入。
- 補齊 QA 指出的負面與正面 contract tests。
- 既有 formatter / notifier 測試
- 依本 TASK 直接範圍補測，不做 full repo 擴張。

## 直接消費者

- Telegram summary formatter / formatTelegramSummary
- Telegram message list / notifier dry-run output
- generate_report production 預設路徑
- QA helper tests / formatter tests / notifier smoke tests
- Owner 手機上的 Telegram 報文閱讀路徑

## 輸出契約

### source family contract

results_map、watchlist_groups、formatter report input 彼此視為同一個 report-derived 來源族群：

- source_family: report_derived
- 不得互相湊成 confirmed
- 僅可支撐 weak 或 trackable
- 不得補出 theme_direction: bullish

可支撐 confirmed 的 structured source family 包含但不限於：

- market_state
- price_volume
- structured_strategy_evidence
- watchlist_theme_breadth

### structured source 必備欄位

每個用來支撐 confirmed 的 structured source 必須具備：

- as_of
- freshness
- confidence
- supports_claims
- limitations

缺任一欄位，不得計入 confirmed 的 structured source count。

### confirmed 判斷契約

confirmed 必須同時符合：

- 至少兩個不同 source_family
- 每個 source 都是 structured source
- 每個 source 都具備必備欄位
- 來源不可循環、不可同族重複湊數
- 至少一個 source family 不是 report_derived
- 若沒有 market_state 或 structured_strategy_evidence，不得補 theme_direction: bullish
- 僅有 theme 字串時，只能輸出 theme_trackable 或 weak

### Telegram summary contract

若 formatter 只得到 results_map / watchlist_groups / formatter report input：

- 顯示 weak
- 顯示 來源不足
- 顯示 只追蹤 或等價不可行動語意
- 不得顯示 confirmed
- 不得顯示 AI/電子供應鏈偏多
- 不得把未成立買點包裝成可買

若 market theme 已 confirmed，但個股買點未成立：

- market theme 可顯示 confirmed
- 個股交易行動仍必須是不可買 / 等待 / 只追蹤
- summary 不得把 confirmed 主題誤導成今日可買

### CHANGELOG 契約

Tech 必須在 CHANGELOG.md 如實說明：

- core/market_theme_evidence.py 是否新增或修改。
- tests/test_market_theme_evidence.py 是否新增或修改。
- production generate_report 預設路徑目前是否只會產生 weak / absent。
- 不得宣稱既有 strategy_evidence_summary 字串已自動接入 structured confirmed，除非本輪真的有 structured source contract 接線且有測試證明。
- 版本仍為 v20.1.0，並說明 formatter header / 常量是否已核對。

## 驗收條件

1. results_map + watchlist_groups only 不得輸出 confirmed。
2. results_map + watchlist_groups only 不得輸出 theme_direction: bullish。
3. 只有 theme 字串時，只能輸出 theme_trackable 或 weak，不得輸出 AI/電子供應鏈偏多。
4. 缺少 as_of、freshness、confidence、supports_claims、limitations 任一欄位的 source 不得計入 confirmed。
5. 同一個 source_family 兩筆 structured source 不得湊成 confirmed。
6. structured market_state + structured_strategy_evidence 且欄位完整時，才可輸出 confirmed。
7. confirmed market theme 但個股買點未成立時，Telegram summary 仍必須顯示不可買 / 等待 / 只追蹤，不得輸出買入建議。
8. formatTelegramSummary 若只得到 report-derived inputs，手機閱讀第一屏必須看到 weak / 來源不足 / 只追蹤，不得看到 confirmed。
9. generate_report production 預設路徑若尚未接 structured source，Tech 必須在 CHANGELOG 說明目前只能產生 weak / absent。
10. header / version 常量仍為 v20.1.0，不得回退。
11. 不得改 DB、watchlist、scheduler、live delivery、策略 decision。
12. QA 必須重跑 helper / formatter / notifier 相關驗證，並補手機閱讀反證。

## 範例或 fixture

### Fixture A: report-derived only，不得 confirmed

Input shape:

{
"results_map": {
"2330": {"theme": "AI/電子供應鏈", "score": 82}
},
"watchlist_groups": {
"AI/電子供應鏈": ["2330", "2382"]
},
"market_state": None,
"price_volume": None,
"structured_strategy_evidence": None
}

Expected evidence shape:

{
"theme_status": "weak",
"theme_direction": None,
"theme_label": "AI/電子供應鏈",
"actionability": "track_only",
"source_families": ["report_derived"],
"limitations": ["來源不足，僅來自報文衍生資料"],
"confirmed": False
}

手機 Telegram 示例輸出形狀:

市場主題：AI/電子供應鏈
狀態：weak｜來源不足｜只追蹤
行動：不可買，等 structured evidence 補強

不得出現:

confirmed｜AI/電子供應鏈偏多

### Fixture B: 缺 structured 欄位，不得 confirmed

Input shape:

{
"market_state": {
"source_family": "market_state",
"as_of": "2026-05-28",
"confidence": 0.8,
"supports_claims": ["risk_on"]
},
"structured_strategy_evidence": {
"source_family": "structured_strategy_evidence",
"as_of": "2026-05-28",
"freshness": "same_day",
"confidence": 0.7,
"supports_claims": ["AI breadth improving"],
"limitations": ["sample limited"]
}
}

Expected:

{
"confirmed": False,
"theme_status": "weak",
"limitations": ["market_state 缺 freshness 或 limitations，不可計入 confirmed"]
}

### Fixture C: 同 family 兩筆，不得 confirmed

Input shape:

{
"sources": [
{
"source_family": "market_state",
"as_of": "2026-05-28",
"freshness": "same_day",
"confidence": 0.8,
"supports_claims": ["risk_on"],
"limitations": ["index only"]
},
{
"source_family": "market_state",
"as_of": "2026-05-28",
"freshness": "same_day",
"confidence": 0.7,
"supports_claims": ["sector strength"],
"limitations": ["same family"]
}
]
}

Expected:

{
"confirmed": False,
"theme_status": "weak",
"source_family_count_for_confirmed": 1
}

### Fixture D: structured market_state + structured_strategy_evidence，可 confirmed

Input shape:

{
"market_state": {
"source_family": "market_state",
"as_of": "2026-05-28",
"freshness": "same_day",
"confidence": 0.82,
"supports_claims": ["risk_on", "electronics sector breadth"],
"limitations": ["intraday may change"]
},
"structured_strategy_evidence": {
"source_family": "structured_strategy_evidence",
"as_of": "2026-05-28",
"freshness": "same_day",
"confidence": 0.76,
"supports_claims": ["AI supply chain setup count rising"],
"limitations": ["buy point still requires individual trigger"]
}
}

Expected:

{
"confirmed": True,
"theme_status": "confirmed",
"theme_direction": "bullish",
"source_families": ["market_state", "structured_strategy_evidence"]
}

### Fixture E: confirmed 但買點未成立，仍不可買

手機 Telegram 示例輸出形狀:

市場主題：AI/電子供應鏈偏多
狀態：confirmed｜2 類 structured sources

新倉：無有效進場
追蹤最強：2330、2382
行動：不可買，等個股買點成立

不得出現:

今日可買：2330

除非個股買點 contract 另有證據成立。

## 明確禁止事項

- 禁止用 results_map、watchlist_groups、formatter report input 互相湊成 confirmed。
- 禁止把 report-derived family 當成多個獨立來源。
- 禁止缺 structured 欄位仍 confirmed。
- 禁止同 family 多筆湊 confirmed。
- 禁止沒有 market_state 或 structured_strategy_evidence 時補 theme_direction: bullish。
- 禁止只因 theme 字串存在就輸出 AI/電子供應鏈偏多。
- 禁止改策略 decision。
- 禁止新增 DB table / migration。
- 禁止改 DB write path、watchlist、scheduler、live Telegram、live Supabase。
- 禁止正式 backfill。
- 禁止把 strategy_evidence_summary 字串宣稱成 structured confirmed。
- 禁止刪除固定 8 份 Markdown。
- 禁止擴大為 full product refactor。

## 阻塞條件

Tech 必須 blocked，若發現：

- 既有 TASK.md / CHANGELOG.md 與本 TASK 的 confirmed contract 矛盾且無法局部修正。
- 無法定位 build_market_theme_evidence() 或等價 helper。
- 無法確認 formatTelegramSummary 或 Telegram summary 直接消費路徑。
- 無法核對 VERSION / formatter header 是否為 v20.1.0。
- 測試環境缺 pytest 或必要依賴，runner 補環境後仍無法執行。
- 需要新增 DB schema、改策略 decision、改 live delivery 才能完成本 TASK。
- production generate_report 預設路徑是否只產生 weak / absent 無法判定。

QA 必須 blocked 或 conditional pass，若發現：

- helper 測試通過但 Telegram 手機閱讀仍可能把 weak 誤讀成 confirmed。
- confirmed 主題被誤導成個股可買。
- CHANGELOG.md 宣稱 structured confirmed 已接線，但測試或程式證據不足。
- header 版本不是 v20.1.0。
- 新檔 core/market_theme_evidence.py 或 tests/test_market_theme_evidence.py 未被納入候選 diff 說明。
