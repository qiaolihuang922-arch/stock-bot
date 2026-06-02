# TASK: per-stock evidence 決策分數與 B5 漏斗一致性收口

## 任務狀態

- task_id: per_stock_evidence_score_funnel_p0_p3_20260602
- 任務類型: risk_patch
- 狀態: done
- QA 分級建議: L3
- 版本建議: 調試期不升版，使用者可見 VERSION 必須保持 v20.4.31
- 主問題: evidence 目前仍可能被當成 report-level 或文字裝飾，Owner 要求 P0-P3 / M1-M7 一次收斂為「每檔股票自己的 strategy evidence modifier」，並修正資料依據、弱勢封頂與 B5 漏斗三方一致。

## Owner 問題

Owner 要求一直做到完成：讓 evidence 真正成為 per-stock 決策分數，而不是所有股票共用同一個 market/theme boost，或在資料不足、弱勢、失敗、過熱時仍顯示正向 +8%。

本輪需按 M1-M7 執行：

- M1: services/strategy_evidence.py load_strategy_evidence_summary 移除 current version filter，按 trade_date 近 N 日跨版本 outcomes 取樣，並依每股 setup 類別 reject_family / watch_category 計算勝率。
- M2: compute_evidence_score 拆兩層：market_theme 是市場級共享背景；strategy_sample 是 per-stock 分量，用 name 取該股 setup 類別回測勝率 / MFE-MAE；合成 evidence_score = w_m * market_score + w_s *
strategy_score(name)，不同 setup 股票的 modifier 必須不同。
- M3: _market_theme_evidence_payload 在 per-stock 缺 market_theme 時 fallback report-level market/theme，不得 unavailable。
- M4: 弱勢 / 失敗 / 過熱股不吃正向 boost：decision FAIL、structure_phase FAILED_BREAKOUT / WEAK / DISTRIBUTION、heat_state EXTREME 時 evidence_modifier <= 1.0。
- M5: reliability 與 score 同一口徑：資料依據判定資料不足 / 不足以判定時 modifier = 1.0；若正向 boost，資料依據必須顯示對應可靠度，不能同時「不足 +8%」。
- M6: final <= 0 或 technical = 0 時隱藏 / 不顯示 +8%，改顯示不適用或省略。
- M7: B5 漏斗分類器統一：卡片 tomorrow_watch_state 與 unheld_funnel_state / tracking_only_count / format_unheld_funnel split_parts 一致；漲停反彈統一「隔日確認」或「等回測」，隔日確認單獨計數不併入等冷卻；拆分之和 = 僅
追蹤總數 = 卡片實際分類。

## 使用者可見結果

手機閱讀 Telegram 報文時：

- 每檔股票的「證據」分數與 modifier 要反映該股 setup 類別的 strategy 樣本，而不是所有股票因同一 market/theme 都拿到同一個 +8%。
- 突破確認旺宏與突破失敗聯電應顯示不同 evidence score / modifier。
- 聯電突破失敗、光寶科弱勢不得再顯示正向 +8%。
- 資料依據若寫「資料不足 / 不足以判定」，同一卡片不得同時顯示正向 boost。
- final 或 technical 不可用時，不顯示 +8%，只顯示「證據：不適用」或省略該加成。
- B5 僅追蹤漏斗的 Summary / 漏斗拆分 / 卡片分類一致，不再出現總數與卡片實際分類不一致。

示例輸出形狀：

旺宏
狀態：突破確認
分數：綜合 72｜技術 68｜證據 +6%（strategy: 突破確認樣本可靠）
...

聯電
狀態：突破失敗
分數：綜合 0｜技術 0｜證據：不適用
資料依據：突破失敗，不套用正向證據加成

僅追蹤 3：
- 隔日確認 1
- 等回測 1
- 等冷卻 1

上述拆分加總必須等於卡片實際 tracking only 分類數。

## 非目標

- 不改 RR 公式。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不改 DB write path，不做 production write / backfill / 手寫 DML。
- 不發 live Telegram。
- 不改 approved write CLI 或 Phase 3 production 寫入流程。
- 不升版，VERSION 保持 v20.4.31。
- 不重設策略核心、不新增買賣規則、不用 evidence 單獨造 BUY。
- 不把 M1-M7 擴成全量報文重構或 evidence 資料治理工程。
- 不處理 production evidence 長期資料品質 / 樣本不足分布，除非阻塞本輪驗收。

## 影響模組與直接消費者

影響模組：

- services/strategy_evidence.py
- load_strategy_evidence_summary
- strategy outcomes 查詢與 setup 類別聚合。
- core/generator.py
- compute_evidence_score(report_context, name)
- evidence modifier / final confidence 計算路徑。
- _market_theme_evidence_payload
- B5 / unheld funnel 分類與統計路徑。
- presentation/report.py 或既有 rendered message formatter，如卡片 evidence line / 資料依據 line 由該模組輸出。
- 相關 tests / probes。

直接消費者：

- Telegram rendered message。
- 未持倉卡片 direct card consumer。
- Summary / 未持倉漏斗 / tracking_only_count。
- stock.<name>.risk.value 或等價 manifest / payload 中的 score、modifier、funnel state。
- QA rendered-message probe，不能只驗 helper return value。

## 輸出契約

### Strategy Evidence Summary

load_strategy_evidence_summary 必須：

- 不使用 current VERSION 過濾 outcomes；不得存在 .eq("version", version) 或等價 current-version-only filter。
- 以 trade_date 近 N 日跨版本歷史取 outcomes。
- 對每股 setup 類別計算樣本：
- setup key 來源優先使用 reject_family / watch_category。
- 若兩者皆缺，必須 fail closed 為 insufficient，不得亂歸類。
- 輸出至少能支援 sample_count、win_rate、mfe_mae 或等價 strategy score 所需欄位。
- 有效樣本 > 0 時 status 必須可進入 ready / available 口徑。
- 樣本不足、source-error、欄位缺失時不得產生正向 modifier。

### Evidence Score

compute_evidence_score(report_context, name) 必須分層：

- market_theme: market-level shared background，只提供共享背景分。
- strategy_sample: per-stock 分量，必須依 name 找到該股 setup 類別回測結果。
- 合成公式契約：
- evidence_score = w_m * market_score + w_s * strategy_score(name)
- 權重沿用既有 evidence weighting pattern；若現有權重不明，Tech 必須保守最小落地並在 CHANGELOG 寫清楚，不得重設策略權重。
- evidence_modifier 必須由合成後的 per-stock evidence_score 得出。
- 不同 setup 的股票在 strategy sample 不同時，evidence_score / evidence_modifier 必須可不同。

### Modifier Gate

以下任一條件成立時，正向 evidence boost 必須封頂：

- decision == FAIL
- structure_phase in {FAILED_BREAKOUT, WEAK, DISTRIBUTION}
- heat_state == EXTREME

契約：

- evidence_modifier <= 1.0
- 不顯示正向 +8% 或等價 boost 文案。
- 不得放寬 RR / overheat / chase hard blocker。

### Reliability / Score 同口徑

- 資料依據若判定 資料不足、不足以判定、insufficient、missing-source、source-error，則 modifier = 1.0。
- 若 rendered message 顯示正向 boost，資料依據必須顯示對應可靠度與來源，例如 strategy setup 樣本有效、market/theme confirmed/supporting。
- 禁止同一卡片同時出現「資料不足」與 +8%。

### final / technical 不可用顯示

- final <= 0 或 technical == 0 時，報文不得顯示 +8%。
- 可顯示：
- 證據：不適用
- 或省略 evidence boost line。
- 不得把 unavailable score 格式化成正向 modifier。

### B5 漏斗分類

以下四者必須同一分類來源或可證明等價：

- card tomorrow_watch_state
- unheld_funnel_state
- tracking_only_count
- format_unheld_funnel split_parts

契約：

- 隔日確認 單獨計數，不併入 等冷卻。
- 漲停反彈只能落在一致的「隔日確認」或「等回測」分類，不得同一股票在卡片與漏斗分裂。
- sum(split_parts) == 僅追蹤總數 == 卡片實際 tracking-only 分類數。

## 版本契約

已存在且不得回退的契約：

- 使用者可見版本保持 v20.4.31。
- market_theme 是市場級 evidence；per-stock 缺 market_theme 時可 fallback report-level。
- strategy_sample 必須是 per-stock evidence，不得退回所有股票共用單一 strategy modifier。
- 缺資料 / source-error / insufficient 必須 fail closed。
- evidence 不得單獨造 BUY，不得放寬 RR、過熱、追高 hard blockers。
- supporting / partial 不得冒充 confirmed 強證據。
- B5 漏斗手機閱讀路徑需 summary / funnel / card 三方一致。
- live Telegram delivery 需要 Owner 單獨批准，本輪禁止。

若 Tech 發現既有程式沒有可識別的 reject_family / watch_category 或 direct card consumer，必須 blocked 並交回 Architect 補資料，不得自行改 schema 或臆造資料。

## 驗收條件

1. M1 strategy 跨版本有效樣本

- 先補 probe。
- fixture outcomes 包含非 v20.4.31 的歷史版本。
- 查詢以 trade_date 近 N 日取樣，非 current version filter。
- setup 類別由 reject_family / watch_category 聚合。
- 驗收：有效樣本 > 0，status ready / available。

2. M2 兩檔不同 setup modifier 不同

- 先補 probe。
- fixture 至少包含：
- 旺宏：突破確認 setup，strategy 樣本偏正。
- 聯電：突破失敗 setup，strategy 樣本偏弱或失敗。
- 驗收：兩者 evidence_score 與 evidence_modifier 不同。
- rendered message / direct card consumer 可看出兩者證據口徑不同。

3. M3 market_theme fallback

- per-stock evidence 缺 market_theme。
- report-level market/theme 有 available / confirmed payload。
- 驗收：個股不顯示 unavailable；market/theme 背景可被 score path 消費。
- 不得把 market/theme fallback 當成 per-stock strategy sample。

4. M4 弱勢 / 失敗 / 過熱 modifier 封頂

- 先補 probe。
- 聯電突破失敗、光寶科弱勢或等價 fixture。
- 驗收：evidence_modifier <= 1.0，報文不顯示 +8%。
- heat_state EXTREME 也需覆蓋。

5. M5 reliability 與 score 一致

- 先補 probe。
- fixture 中資料依據為 insufficient / 不足以判定。
- 驗收：modifier = 1.0。
- 若任一卡片顯示正向 boost，資料依據必須顯示對應可靠度；不得「不足 +8%」。

6. M6 final / technical 不可用

- final <= 0 或 technical == 0。
- 驗收：不顯示 +8%，顯示 證據：不適用 或省略。
- rendered message 必須納入驗收。

7. M7 B5 漏斗一致

- 先補 probe。
- 覆蓋漲停反彈、隔日確認、等回測、等冷卻至少一組。
- 驗收：
- card tomorrow_watch_state 與 unheld_funnel_state 一致。
- tracking_only_count 與 format_unheld_funnel split_parts 一致。
- sum(split_parts) == 僅追蹤總數 == 卡片實際分類數。
- 隔日確認不併入等冷卻。

8. VERSION 不變

- 驗收：core/generator.py 或實際版本來源仍為 v20.4.31。
- rendered header 不得升版。

9. QA L3 必查

- QA 必須檢查 rendered message / direct card consumer。
- QA 不能只重跑 Tech helper tests。
- QA 至少補一個 Tech 未覆蓋的使用者誤讀或契約風險 probe。

## 範例或 Fixture

Strategy outcomes fixture 形狀：

outcomes = [
{
"trade_date": "2026-05-20",
"version": "v20.4.5",
"name": "旺宏",
"watch_category": "突破確認",
"reject_family": None,
"result": "win",
"mfe": 0.08,
"mae": -0.02,
},
{
"trade_date": "2026-05-21",
"version": "v20.4.8",
"name": "聯電",
"watch_category": None,
"reject_family": "突破失敗",
"result": "loss",
"mfe": 0.01,
"mae": -0.06,
},
]

Score fixture 形狀：

report_context = {
"market_theme_evidence": {
"status": "available",
"score": 0.62,
"reliability": "supporting",
},
"per_stock_evidence": {
"旺宏": {
"strategy_sample": {
"setup_key": "突破確認",
"sample_count": 12,
"win_rate": 0.67,
"mfe_mae_score": 0.70,
"status": "ready",
}
},
"聯電": {
"strategy_sample": {
"setup_key": "突破失敗",
"sample_count": 10,
"win_rate": 0.30,
"mfe_mae_score": 0.35,
"status": "ready",
}
},
},
}

Rendered message 期望形狀：

旺宏｜突破確認
分數：綜合 ...｜技術 ...｜證據 +6%（strategy: 突破確認樣本 reliable）

聯電｜突破失敗
分數：綜合 ...｜技術 ...｜證據：不適用
資料依據：突破失敗，不套用正向證據加成

B5 fixture 期望形狀：

僅追蹤 3
- 隔日確認 1
- 等回測 1
- 等冷卻 1

## 明確禁止事項

- 禁止修改 RR 公式。
- 禁止修改 DB schema / RLS / grant / policy / role / index / constraint。
- 禁止 production write / backfill / 手寫 DML。
- 禁止 live Telegram delivery。
- 禁止 bump VERSION。
- 禁止把 current version filter 加回 strategy outcomes 查詢。
- 禁止用 report-level strategy evidence 取代 per-stock strategy sample。
- 禁止資料不足時輸出正向 boost。
- 禁止弱勢 / 失敗 / 過熱股顯示正向 evidence modifier。
- 禁止 evidence 單獨造 BUY 或放寬 hard blockers。
- 禁止只改文案不補 probe。
- 禁止只驗 helper，不驗 rendered message / direct card consumer。
- 禁止把 B5 漏斗統一擴成整份 Telegram 版面重構。

## 阻塞條件

- 無法從既有 payload 取得每股 reject_family / watch_category 或等價 setup 類別。
- strategy outcomes 沒有可測的 trade_date / version / outcome 欄位，且無既有 interface 可補。
- 需要 DB schema 或 write path 變更才能完成。
- 需要 production live data 或 live Telegram 才能驗收。
- direct card consumer / rendered message path 無法定位。
- 權重契約在既有程式中不可判斷，且會影響策略決策口徑；此時 Tech 必須 blocked，交回 Architect / Owner 補確認。

## 本輪停止條件

本輪完成只限於 M1-M7：

- strategy evidence 可跨版本按 trade_date 取樣，且有效樣本 > 0 時 status ready。
- evidence score 拆成 market-level background 與 per-stock strategy sample，兩檔不同 setup 股票 modifier 可不同。
- per-stock 缺 market_theme 時 fallback report-level market/theme。
- 弱勢 / 失敗 / 過熱 / final<=0 / technical=0 不顯示正向 boost。
- reliability 與 score 不再出現「資料不足 +8%」衝突。
- B5 卡片 / 漏斗 / count / split_parts 三方一致。
- QA L3 驗 rendered message / direct card consumer 後通過。
- VERSION 仍為 v20.4.31。

旁支問題只記待辦，不納入本輪：

- production evidence 樣本量長期不足。
- setup taxonomy 重新設計。
- DB source-of-truth / backfill / write automation。
- Telegram 整體排版重構。
- RR、買賣決策、停損停利、持倉狀態機調整。
- live delivery 或正式上線推送。
