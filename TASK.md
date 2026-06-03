# TASK: 實裝 trend_continuation 買入路徑

## 任務狀態

- task_id: trend_continuation_buy_path_phase2_20260603
- 任務類型: risk_patch
- 狀態: ready_for_tech
- QA 分級建議: L3
- 版本建議: 使用者可見報文新增買入狀態與 funnel 分類，需升版或更新報文版本字串
- 前提證據: Owner 已確認研究 n=232、5 日勝率 55.17%、平均收益 +2.26%、positive、meets_min_sample
- Owner 授權邊界: 僅限 trend_continuation 這一條路徑允許「證據達標可開 BUY」

## Owner 問題

目前系統已有 trend continuation 研究證據，但正式策略仍未開放該 setup 的 BUY 路徑。Owner 要求在不改 RR、DB schema、live Telegram 的前提下，把研究已驗證的 trend continuation 形態接入正式決策、證據 gate、倉位風控、退出邏
輯與報文顯示。

核心問題不是新增通用追高策略，而是只在「趨勢成立 + 回踩 ma5/ma10 + 放量站回」且回測證據達標時，於回踩站回日給出小倉 BUY。

## 使用者可見結果

手機報文中，符合條件的標的會出現在單獨分類，卡片狀態為：

🟢 趨勢延續買入｜小倉
依據：回測 55% 勝 / +2.26%，回踩站回 ma5/ma10 後放量確認
倉位：<=15%
止損：回踩低點下方；形態失效即出
持有：對齊 5 日 edge，5 日內未續漲或跌破回踩低點即了結

funnel 需與既有「可買 / 等冷卻 / 不可追高」並存，新增或呈現為單獨一類，不得混入不可追高或一般突破買入。

## 非目標

- 不改 RR 計算公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 live Telegram delivery。
- 不把其他 setup 放開成「證據可開 BUY」。
- 不新增一套與研究腳本不同的形態判定。
- 不把 extended spike、創新高追價、無回踩情境改成 BUY。
- 不重設整體策略樹或重構全量 condition engine。
- 不改首次突破倉位邏輯，trend_continuation 倉位必須小於首次突破倉。

## 影響模組與直接消費者

影響模組：

- services/analysis.py
- strategy() 決策樹
- 持倉 / 倉位 / 止損 / 退出邏輯
- scripts/research_trend_continuation.py
- 研究命中定義來源；正式策略必須直接復用其判定函數或抽出同源函數後由研究腳本與正式策略共同引用
- core/generator.py
- BUY / WAIT 報文 payload、分類、卡片狀態
- core/condition_engine.py
- trend_continuation 證據 gate 與 setup 判斷
- presentation/report.py
- 手機報文呈現與 funnel 分類
- 相關 tests / fixtures / replay artifact

直接消費者：

- Telegram 手機報文讀者 Owner
- official report generator / runner artifact
- condition engine 的 BUY / WAIT 判斷消費者
- strategy decision payload 消費者
- QA replay / fixture 驗收路由

## 輸出契約

### decision payload

新增 decision_type = "trend_continuation"，僅在以下條件全部成立時允許 BUY：

- 趨勢成立
- 回踩 ma5 或 ma10
- 回踩後放量站回
- 觸發日為「回踩站回日」
- 同源回測證據達標：
- win_rate >= 55%
- avg_5d_return > 0
- evidence source 與階段一研究同源
- 非 extended spike 無回踩
- 非單純創新高追價

若形態成立但證據不足、證據缺失、證據為負，輸出不得為 BUY，應降級為「趨勢觀察」。

### evidence gate

只允許 trend_continuation 使用研究證據打開 BUY。

其他 decision_type 必須維持既有契約：遵守 RESEARCH.md 的「證據不得單獨變 BUY」限制。

### 倉位契約

- trend_continuation 倉位為小倉。
- 上限 <=15%。
- 必須小於首次突破倉。
- 不得因證據達標自動放大倉位。

### 止損契約

- 止損位置為回踩低點下方。
- 跌破回踩低點或形態失效即出。
- 沿用已有「同日入場即錯減碼」規則。

### 退出 / 持有契約

- 持有邏輯對齊 5 日 edge。
- 5 日內未續漲需了結或退出觀察。
- 5 日內跌破回踩低點即了結。
- 不得無限持有或轉成一般長抱。

### 報文契約

新增卡片狀態：

🟢 趨勢延續買入｜小倉

需顯示依據：

回測 55% 勝 / +2.26%

手機閱讀路徑需清楚分辨：

- 可買
- 趨勢延續買入｜小倉
- 等冷卻
- 不可追高
- 趨勢觀察

若無符合 BUY 條件，不得用推薦語氣包裝觀察標的。

## 版本契約

- 使用者可見報文新增狀態與分類，必須同步更新報文版本字串或對應 header 常量。
- 不得回退既有版本字串。
- 若現有版本契約位置不明，Tech 必須先定位並在 CHANGELOG.md 說明；定位失敗則 blocked。

## 已存在且不得回退的契約

- 其他 setup 不得因研究證據單獨轉 BUY。
- extended spike 無回踩仍為 WAIT / 不可追高。
- 無可買標的時不得出現像推薦的文案。
- 分組標題、卡片狀態、漏斗、索引、詳情必須一致。
- 同一持倉在同一份報文只能有一個主行動。
- 今日買入後預設只能新倉風控觀察；若轉弱要賣，必須同行說明跌破警戒、停損或策略失效。
- 空區塊、0-count、無新增下單占位預設不顯示。
- DB schema 與 live Telegram 不得變更。
- RR 計算公式不得變更。

## 驗收條件

1. services/analysis.py strategy() 可產出 decision_type = "trend_continuation"，且只在回踩站回日觸發，不在 spike 創新高日觸發。
2. 正式策略與 scripts/research_trend_continuation.py 使用同一個形態判定函數；同一 fixture 在研究腳本與正式策略中命中結果一致。
3. trend_continuation setup 證據達標時可 BUY：
- win_rate >= 55%
- avg_5d_return > 0
- 本輪基準 fixture 顯示 55.17% / +2.26%
4. trend_continuation setup 證據不足、缺失或為負時不得 BUY，必須降級為「趨勢觀察」。
5. spike 創新高但無回踩不得 BUY，必須維持 WAIT / 不可追高。
6. 倉位輸出為小倉，且 <=15%，不得等於或大於首次突破倉。
7. 止損輸出包含回踩低點下方；跌破回踩低點或形態失效會導向退出。
8. 退出邏輯對齊 5 日 edge：5 日內未續漲或跌破回踩低點即了結，不得無限持有。
9. 報文新增單獨手機可讀分類與卡片狀態：
- 🟢 趨勢延續買入｜小倉
- 顯示 回測 55% 勝 / +2.26%
10. QA 必須驗 official generator 或 runner artifact 層級的報文，不得只驗 helper fixture。
11. QA 必須補至少一個 Tech 未覆蓋的反證案例，覆蓋使用者誤讀、契約風險或負面情境。

## 範例或 Fixture

### 正向 fixture

條件：

- 趨勢成立
- 價格回踩 ma5 或 ma10
- 回踩後放量站回
- 觸發日為回踩站回日
- evidence:
- sample_n = 232
- win_rate_5d = 55.17%
- avg_return_5d = +2.26%
- polarity = positive
- meets_min_sample = true

期望：

decision_type: trend_continuation
action: BUY
position_size: <=15%
card_status: 🟢 趨勢延續買入｜小倉
evidence_text: 回測 55% 勝 / +2.26%
stop: 回踩低點下方
exit_horizon: 5 日

### spike 無回踩 fixture

條件：

- 創新高或 extended spike
- 無回踩 ma5/ma10
- 無回踩站回日

期望：

action: WAIT
decision_type: 不得為 trend_continuation BUY
classification: 不可追高 或 等冷卻

### 證據為負 fixture

條件：

- 形態近似成立
- evidence win_rate <55% 或 avg_return_5d <=0

期望：

action: WAIT
classification: 趨勢觀察
reason: 證據不足或為負，不開 BUY

### 同源判定 fixture

同一批 OHLCV fixture 同時餵給：

- scripts/research_trend_continuation.py 命中判定
- production strategy / condition engine 判定

期望：

research_match == production_match
trigger_date == pullback_reclaim_date

## 失敗標本與驗收路由

失敗標本：

- spike 創新高無回踩被錯誤 BUY
- 回測證據為負或不足仍被 BUY
- 正式策略另寫判定導致研究命中與實盤判定漂移
- 觸發點落在 spike 創新高日，而不是回踩站回日
- trend_continuation 變成無腦追高或一般突破倉

驗收路由：

1. 研究判定函數同源檢查
2. condition engine setup 判定
3. strategy decision payload
4. generator message list / classification
5. presentation report 手機報文
6. official generator 或 runner artifact replay

## 明確禁止事項

- 禁止另寫一套 trend_continuation 判定邏輯。
- 禁止把 extended spike 無回踩放開 BUY。
- 禁止把其他 decision_type 放開為證據可 BUY。
- 禁止改 RR 計算公式。
- 禁止改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止 live Telegram delivery。
- 禁止將 local cache、runtime dict 或 agent 對話當跨日 source-of-truth。
- 禁止用 synthetic helper 測試取代 official generator / runner artifact 驗收。
- 禁止把本輪擴成全策略重構或清理工程。

## 阻塞條件

- 找不到階段一同源回測證據或 evidence contract 無法讀取。
- scripts/research_trend_continuation.py 沒有可復用判定函數，且無法安全抽出成共同函數。
- 無法產生同一 fixture 的研究 / production 一致性驗證。
- 無法定位報文版本字串或 header 常量。
- 需要 DB schema 變更才能完成。
- 需要 live Telegram 才能驗收。
- 測試環境缺依賴且無法補齊。
- official generator / runner artifact 無法產生，且任務目標仍是使用者可見報文。

## 本輪停止條件

本輪完成只以以下範圍為準：

- trend_continuation 單一路徑完成 BUY / WAIT 判定、證據 gate、倉位、止損、5 日退出、報文顯示。
- 研究腳本與 production 使用同源形態判定，fixture 結果一致。
- QA L3 反證覆蓋 spike 無回踩、負證據、同源判定、倉位止損退出、official report 手機閱讀。
- 不要求 live Telegram、不要求 production DB 寫入、不要求長期實盤監控已產生歷史資料。

旁支問題只記待辦，不納入本輪：

- 其他 setup 的證據 gate 政策。
- 全策略 RR 或倉位模型重構。
- DB schema / production persistence 設計。
- 長期實盤 vs 回測勝率監控的完整儀表板；本輪只需保留監控 hook / TODO / artifact contract，偏離預警可作 follow-up，除非現有系統已有監控接口可低風險接入。
