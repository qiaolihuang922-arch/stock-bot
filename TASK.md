# TASK: evidence_score_effective_and_market_daily_freshness_v20_4_34

## 任務狀態

- task_id：20260603_evidence_score_effective_market_freshness_v20_4_34
- 任務類型：risk_patch
- 狀態：ready_for_tech
- 任務尺寸判定：本輪不是 tiny_patch；主 bug 是「證據已顯示但沒有真正進分數」。market daily freshness 是同一證據鏈的 production source 前置條件；RR 隱藏、簡報計數、防抖只納入 Owner 指定的最小報文一致性修補，不擴成策略重
設。
- QA 分級建議：L3
- 落地順序：二 market daily freshness -> 一 per-stock strategy sample -> 三 evidence_modifier 生效與護欄 -> 四/五報文一致性 -> 六光寶科防抖

## Owner 問題

Owner 要修復 v20.4.34 證據鏈兩個死因：

1. strategy 评分读错来源：compute_evidence_score 用全局 report_from_rows classification / structured_status 判斷 ready，因 REPORT_CATEGORIES=[淘汰, 等回測, RR不足] 每組幾乎不足 10，導致 strategy 長期 partial(0.5)、
modifier 1.0；但卡片顯示的回測樣本來自 per-stock data[backtest_context]，兩邊不同源。
2. market confirmed_evidence 沒有每日保鮮：market_theme_confirmed_evidence 停在 2026-05-29；到 2026-06-03 gap=5，大於 MAX_PREVIOUS_TRADE_DATE_GAP_DAYS=4，報文出現資料不足。每日 cron / Phase 3 evidence automation 必須在
收盤後寫入當日 confirmed evidence，不能因 secret 缺失靜默跳過。

附帶修補 Owner 指定的三個使用者可見一致性問題：evidence modifier 必須真的改綜合分且弱勢股不被抬分、過熱/等冷卻 RR 一律隱藏、簡報計數口徑消除歧義、光寶科可買/淘汰抖動加防抖。

## 使用者可見結果

手機閱讀路徑：Telegram 報文首屏 summary -> 市場背景 / 今日交易執行 -> 持倉與未持倉卡片 -> 詳情。

期望形狀：

市場背景：confirmed_trend（2026-06-03）
今日交易執行：執行動作 2 檔
今日新倉建議：新建倉 3 檔

緯創
綜合 90｜技術 78｜證據 +15%（confirmed）
回測樣本 36｜參考度高
狀態：可買 / 可準備 / 僅追蹤 中之一

技嘉
RR -（過熱）
狀態：過熱觀察

旺宏 / 聯電
綜合 <= 技術 或 modifier <= 1.0
狀態：減碼 / 失敗 / 弱勢時不得被背景證據抬分

不可再出現：

回測樣本 36 / 38，但 strategy evidence 仍 partial +0%
confirmed_evidence 已有當日資料，但 market 背景仍資料不足
交易執行 2 與 今日交易已建立新倉 3 檔 使用同一語境造成歧義
技嘉 過熱觀察 RR 0.21
同一標的盤中在 可買 / 淘汰 間來回翻

## 非目標

- 不改 RR 公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不做 live Telegram delivery。
- 不手寫 production DML；資料寫入只能走既有 repo script / approved service API。
- 不把 local cache、runtime dict、agent 對話當跨日 evidence source。
- 不重設整體策略、買賣規則、持倉狀態機或 ranking 公式，只修 Owner 指定的 evidence source / modifier / 報文一致性。
- 不把 missing secret 或 production source-error 包裝成 pass。

## 影響模組與直接消費者

影響模組：

- core/generator.py
- compute_evidence_score(report_context, name)
- _strategy_sample_evidence_payload
- evidence_modifier_for_score
- apply_evidence_confidence
- rr_display_text
- should_show_overheat_rr_blocker
- 簡報 / Telegram 報文 summary 行與卡片分數行
- .github/workflows/stock-bot.yml
- daily evidence cron 時間
- scripts/run_phase3_evidence_automation.py
- approved payload secret 缺失 fail closed
- 當日 trade_date 寫入與 read-after-write smoke
- scripts/backfill_market_theme_sources.py
- 僅限確認不破壞 official market/theme evidence 路徑；若需補當日路徑，必須走既有接口
- services/analysis.py / core/condition_engine.py
- 光寶科類「淘汰 -> 可買」防抖最小修補

直接消費者：

- Telegram 手機報文讀者。
- official report/message-list generator。
- GitHub Actions RUN_MODE=daily_evidence。
- Phase 3 evidence automation。
- QA replay / probes。
- 後續排序、funnel、卡片狀態使用的 final confidence / evidence modifier。

## 輸出契約

strategy evidence 契約：

- compute_evidence_score(report_context, name) 的 strategy 分量必須用該股 data[backtest_context]，不得用全局 classification ready_count 作主要 ready 判斷。
- name 必須選到各股自身 backtest context，達成 per-stock 生效。
- sample >= STRATEGY_SAMPLE_MIN_ROWS(10) 且 reference 高：
- status=ready
- score=1.0
- strategy modifier 可高於 1.0，仍受 cap 約束
- sample 不足：
- status=partial
- score=0.5
- modifier 不得產生正向 boost
- 無 backtest context：
- strategy 分量為 None 或等價 fail-closed，不得假造 ready

market evidence 契約：

- daily evidence 收盤後執行，cron 從 25 5 * * 1-5 調整為收盤後，例如 0 6 * * 1-5。
- MARKET_THEME_APPROVED_PAYLOAD secret 未配置時，run_phase3_evidence_automation.py 必須報錯並讓 job fail，不得靜默 skip。
- 當日路徑必須使用最新 TWSE trading day 的 --trade-date。
- run_market_theme_confirmed_evidence(trading_day) 寫入後必須 read-after-write smoke，確認 market_theme_confirmed_evidence.trade_date == trading_day 有行；失敗則 job fail。
- secret / credential 不得輸出到 log。

modifier 契約：

- strategy=ready(1.0) 或 market=confirmed(1.0) 時，合格股票 modifier 必須在 (1.0, 1.15]。
- final = technical * modifier 或既有等價公式必須讓至少一卡 綜合 != 技術。
- 弱勢 / 失敗 / 過熱股不得被背景抬分：
- decision=FAIL
- structure_phase in {FAILED_BREAKOUT, WEAK, DISTRIBUTION}
- heat=EXTREME
- 上述情境 modifier 必須 <= 1.0

RR 顯示契約：

- funnel 為 等冷卻、過熱*、過熱觀察 時，RR 一律顯示 -（過熱）。
- 不改 RR 公式，只改顯示與 blocker 顯示口徑。

簡報計數契約：

- 交易執行 N 與 今日交易已建立新倉 M 檔 必須同一定義，或改成明確不同標籤：
- 交易執行：執行動作 N 檔
- 今日新倉建議 / 已建立新倉：M 檔
- 不得讓手機首屏誤讀成同一件事有兩個數字。

防抖契約：

- 淘汰 / failed / weak 翻可買需連續 >=2 次評估維持買點，且 breakout_distance <= 1%。
- 同盤中翻轉標記 unstable，維持保守側。
- 不得讓同一標的同盤中在 可買 / 淘汰 間反覆跳。

## 版本契約

- 使用者可見報文版本不得低於 v20.4.34。
- 若本輪有報文 header / 手機可見格式變更，Tech 必須明確說明維持 v20.4.34 或升版；不得回退版本。
- CHANGELOG 必須列出實際 core/generator.py VERSION 掃描結果。
- 若不升版，需說明理由：本輪是 v20.4.34 修復同版契約，而非新能力。

## 驗收條件

必須全部滿足，否則 QA 結論不得為 通過：

1. per-stock strategy evidence：
- 緯創 backtest sample 36、reference 高時：strategy ready / 1.0。
- 華邦 backtest sample 38、reference 高時：strategy ready / 1.0。
- 兩股卡片 綜合 != 技術，顯示 證據 +X%，不得是 partial +0%。
- 至少兩檔不同股票 modifier 不同，證明 per-stock 生效。
2. market daily freshness：
- 收盤後手動跑 RUN_MODE=daily_evidence，使用 2026-06-03 或最新 TWSE trading day。
- market_theme_confirmed_evidence 出現當日 trade_date 行。
- read-after-write smoke 可重跑，且失敗時 job 非 0 exit。
- official report 背景顯示 confirmed_trend，不得顯示 資料不足。
3. evidence modifier：
- 至少一張 official message-list / report 卡片 綜合 != 技術。
- 當日有 confirmed market evidence 時，market 分量進入分數，不只是顯示文案。
- 旺宏 / 聯電等減碼、失敗、弱勢案例 modifier <=1.0。
4. RR 過熱顯示：
- 技嘉 過熱觀察 原 RR 0.21 改為 -（過熱）。
- 等冷卻 / 過熱* / 過熱觀察 全部同口徑。
5. 簡報計數：
- 首屏不再出現 交易執行2 / 新倉3 這種未定義歧義。
- 若保留兩個數字，標籤必須明確區分「執行動作數」與「新建倉 / 新倉建議數」。
6. 光寶科防抖：
- 同一標的盤中不在 可買 / 淘汰 間來回翻。
- 前態淘汰 / failed / weak 單次 BUY 不直接翻可買。
- 連續 >=2 次且 breakout_distance <=1% 才允許翻可買；否則維持保守側並可標記 unstable。
7. 回歸護欄：
- RR 公式未改。
- DB schema 未改。
- 無 live Telegram delivery。
- secret / credential 未出現在 log。
- Tech probe 覆蓋 helper / formatter / official generator / runner artifact；production source 若無權限，必須產出 read-only artifact 或標 partial。

## 範例或 Fixture

最小 fixture / replay 必須包含：

- 緯創：backtest_context.sample=36、reference 高、technical score 與 final score 可比較。
- 華邦：backtest_context.sample=38、reference 高、technical score 與 final score可比較。
- 一檔 sample < 10：strategy partial / 0.5，modifier 不正向 boost。
- 一檔無 backtest context：strategy fail closed。
- market/theme：2026-05-29 舊資料 + 2026-06-03 當日資料，驗證舊資料 gap=5 會 insufficient，當日資料會 confirmed。
- 旺宏 / 聯電：decision=FAIL 或 structure_phase=FAILED_BREAKOUT / WEAK / DISTRIBUTION，驗證 modifier <=1.0。
- 技嘉：funnel 過熱觀察 且原 RR 0.21，驗證顯示 -（過熱）。
- 光寶科：同盤中第一次從淘汰翻 BUY、第二次連續確認、breakout_distance 分別 <=1% 與 >1% 的防抖案例。

## 失敗標本與驗收路由

Owner 失敗標本為本次完整指令描述的 v20.4.34 報文問題與具名股票：

- 緯創 / 華邦：卡片有回測樣本 36 / 38 且參考度高，但 strategy 分數仍 partial / +0%。
- market/theme：2026-06-03 報文因 confirmed_evidence 停在 2026-05-29 而資料不足。
- 旺宏 / 聯電：弱勢 / 失敗 / 減碼股不得被 evidence 背景抬分。
- 技嘉：過熱觀察仍顯示 RR 0.21。
- 光寶科：盤中可買 / 淘汰抖動。

驗收路由：

1. helper 層：直接測 compute_evidence_score、_strategy_sample_evidence_payload、evidence_modifier_for_score、apply_evidence_confidence、RR 顯示、防抖判斷。
2. formatter 層：測卡片分數行、RR 行、summary 計數行。
3. official generator 層：用 message-list / official report replay 驗證手機閱讀順序與文案。
4. runner artifact 層：跑 RUN_MODE=daily_evidence 或等價 CI command，驗證當日 confirmed row。
5. production source 層：若可 read-only，驗證 market_theme_confirmed_evidence.trade_date 當日存在；若 QA 無 production 權限，只能用 Architect 提供的 safe read-only artifact，否則 market daily freshness 結論最多
conditional pass。

## 已存在且不得回退的契約

- 使用者可見報文版本不得低於 v20.4.34。
- evidence 不足時 fail closed，不得假造 confirmed / ready。
- market/theme confirmed_trend 才能作 strong boundary evidence；supporting / single_day 不得升成 confirmed。
- hard blockers 不得被 evidence 放寬：RR、overheat、chase、LIMIT_LOCK、弱勢 / 失敗結構。
- 今日買入後若轉弱，必須同行說明跌破警戒、停損或策略失效；不得無理由從新倉觀察變賣出。
- 空區塊、0-count、無新增下單占位預設不顯示。
- 同一持倉同一份報文只能有一個主行動。
- official runner / git 產生報文才是正式結果。
- production secret / credential 不入 log。
- 非 DB schema 資料寫入走既有 repo script / approved service API，不手寫 production DML。

## 明確禁止事項

- 禁止 Architect 或 PM 直接改產品代碼；本任務必須走 Tech -> QA。
- 禁止跳過 QA 或用 Tech 自檢代替 QA。
- 禁止只驗 helper 後宣稱 Telegram 報文完成。
- 禁止用 synthetic fixture 取代 Owner 具名失敗標本；fixture 可以用，但必須有等價 official replay。
- 禁止缺 MARKET_THEME_APPROVED_PAYLOAD 時靜默 skip。
- 禁止在 log 輸出 secret / credential / approved payload 原文。
- 禁止 live Telegram delivery。
- 禁止 DB schema / RLS / grant / policy / role / index / constraint 變更。
- 禁止手寫 production DML。
- 禁止改 RR 公式。
- 禁止讓弱勢 / 失敗 / EXTREME 過熱股因 confirmed market 或 strategy evidence 被抬分。

## 阻塞條件

- Owner / Architect 無法提供或允許產生 safe read-only artifact，且 QA 需要驗 production 當日 market confirmed row。
- MARKET_THEME_APPROVED_PAYLOAD secret 未配置，且任務目標要求完成 daily_evidence production smoke；此時 automation 應 fail closed，QA 不能通過 market daily freshness。
- repo 缺可執行測試環境且無法補齊。
- 找不到既有 approved service API / script 可寫入 market/theme confirmed evidence；不得改用手寫 DML，需 blocked。
- Owner 要求 live Telegram delivery，但未給本輪單獨批准。
- 實作需要 DB schema 變更；本輪未授權，需回 Owner / Architect 確認。

## 本輪停止條件

完成條件：

- Tech 依本 TASK 完成最小範圍實作與 probes。
- CHANGELOG 說明修改檔案、契約影響、版本、直接消費者、測試命令、覆蓋層級與未測層級。
- QA 以 Owner 具名失敗標本或等價 official replay 反證，且至少補一個 Tech 未覆蓋的 consumer / 負面案例 / 手機誤讀路徑。
- 五個必要 probes 均通過：
- 不同股 strategy modifier 不同。
- 當日 confirmed_evidence 時 market 進分數。
- 弱勢 / 失敗股 modifier <=1.0。
- 至少一卡 綜合 != 技術。
- 收盤後 daily_evidence 跑出當日 confirmed row。
- 無 RR 公式、DB schema、live Telegram、secret log 回退。

不納入本輪，只記待辦：

- 全量 production evidence 歷史補洞。
- 長期資料品質 / source-of-truth governance。
- 其他股票 ranking 或策略重設。
- observation day / 持倉天數持久化。
- 非 Owner 指定的報文降噪與版面重排。
