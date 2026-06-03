# TASK: 修正證據加權仍 partial / 綜合=技術 的源頭

## 任務狀態

- task_id: evidence-weighting-source-fix-20260603
- 任務類型: risk_patch
- 狀態: ready_for_tech
- 版本建議: 使用者可見報文若證據區或 header 版本字串有既有版本契約，需升版或同步常量；不得回退既有版本字串。
- QA 分級建議: L3

## Owner 問題

Owner 發現證據加權仍顯示 partial / +0%，導致「綜合=技術」沒有反映 market theme 與 strategy sample 的有效證據。源頭疑似：

- market_theme 已是 8 天 confirmed_trend，但仍被 15 天二次門檻壓成不 eligible。
- strategy_sample 沒接到真實有效樣本數，回測/報文顯示 36/38 類樣本，但 structured status 仍像缺樣本。
- strategy evidence 可能仍被 version filter 限制，導致跨版本歷史樣本沒有進入樣本數。

## 使用者可見結果

在手機 Telegram 報文或等價 official message-list replay 中：

- 建準或等價標的若 market confirmed + strategy sample >=10，證據行不得再顯示 partial +0%。
- 該標的綜合分數/綜合判斷必須受證據加權影響，不能仍等於純技術結果。
- 過熱股若 market confirmed 且沒有設計上的 hard block，證據加權需非 0；若被 hard block 壓制，報文/資料不得誤顯為 false partial，QA 必須明確反證原因。

手機閱讀路徑示例形狀：

建準 ...
技術: X
證據: +Y% confirmed/supporting
綜合: Z

其中 Y 必須非 0，且 Z != 技術 X。實際文案以現有報文格式為準，不在本輪重設版型。

## 非目標

- 不改 RR 公式。
- 不重設策略核心、買賣規則、停損停利、加減碼邏輯。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不改 production write path。
- 不做 live Telegram delivery。
- 不做 production backfill。
- 不手寫 production DML。
- 不把本輪擴成全量 evidence framework 重構或報文版型重設。

## 影響模組與直接消費者

影響模組：

- core/generator.py
- _market_theme_evidence_payload
- _strategy_sample_row_count
- strategy_sample_structured_status 上游填充處
- official generator / message-list 內證據加權輸出路徑
- services/strategy_evidence.py
- load_strategy_evidence_summary

直接消費者：

- Telegram / official message-list 產生器。
- 證據加權 payload 消費者。
- 使用 strategy_evidence_summary 與 structured_status.sample / row_count 判定 strategy sample readiness 的 formatter / generator。
- QA replay/probe artifact。

## 輸出契約

已存在且不得回退的契約：

- market_theme 的 confirmed_trend 代表已滿足自身趨勢確認條件；本輪不得新增更嚴格市場門檻。
- 無可買/可買/追蹤/不可行動等 Telegram 分組規則不得因本修正變更。
- 同一持倉在同一份報文仍只能有一個主行動。
- 使用者可見報文版本字串不得回退。
- load_strategy_evidence_summary 不得要求 production write 或 backfill 才能讀取既有 evidence。

本輪目標契約：

- _market_theme_evidence_payload:
- decision_eligible = confirmed and trend_status == "confirmed_trend"
- 刪除 observed_days >= 15 的二次門檻。
- 8 天 confirmed_trend 應回傳 score=1.0、status=confirmed、decision_eligible=true。
- _strategy_sample_row_count:
- 必須能從 strategy_sample_structured_status.sample 或 row_count 取得真實有效樣本數。
- 樣本數 >=10 時，_strategy_sample_evidence_payload 應回傳 status=ready、score=1.0。
- load_strategy_evidence_summary:
- 確認已移除 .eq("version", version)。
- 若 structured 樣本仍被 version 限制，改為按 trade_date 跨版本統計有效 classification 樣本數。
- official message-list / equivalent generator replay:
- market confirmed + strategy sample >=10 時，證據顯示為 confirmed/supporting 且非 0 加權。
- 綜合結果不得仍等於純技術結果，除非有明確 hard rule 阻擋，且該阻擋不可被顯示成 false partial。

## 版本契約

- 若本輪改變 Telegram 使用者可見 evidence 狀態、加權顯示或報文 header 版本相關常量，Tech 必須同步版本字串並在 CHANGELOG.md 寫明。
- 若現有版本契約位置不明，Tech 必須先定位既有 header / version 常量；找不到則標記 partial，不得自行假設無需升版。

## 驗收條件

1. market theme probe:
- fixture: observed_days=8、trend_status="confirmed_trend"、confirmed=true
- expected: _market_theme_evidence_payload 回傳 score=1.0、status=confirmed、decision_eligible=true
2. strategy sample probe:
- fixture: structured strategy sample count >=10
- expected: _strategy_sample_evidence_payload 回傳 status=ready、score=1.0
- _strategy_sample_row_count 必須讀到真實有效樣本數，而不是 0 / None / partial fallback。
3. version filter probe:
- load_strategy_evidence_summary 不得因 .eq("version", version) 排除跨版本有效 classification 樣本。
- 若 production source 無法在 sandbox 直接讀，Tech 需產生 read-only artifact/fixture 驗 code path，artifact 標明 source、無 credential、無 write、無 live delivery。
4. official message-list / generator replay:
- 建準或等價標的：market confirmed + strategy sample >=10
- expected: 數據/證據行不再是 partial +0%；顯示 confirmed/supporting 非 0 加權；綜合與技術不同。
5. overheat path:
- 過熱股在 market confirmed 時應顯示非 0 evidence 加權。
- 若 hard-blocked by design，QA 必須指出是哪個既有 hard rule 抑制顯示，並驗證不是 false partial 或樣本讀取失敗。

## 範例或 Fixture

market fixture:

{
"confirmed": true,
"trend_status": "confirmed_trend",
"observed_days": 8,
"recent_support_days": 3
}

strategy fixture:

{
"strategy_evidence_summary": {
"classification_sample_count": 36
},
"strategy_sample_structured_status": {
"sample": 36,
"row_count": 36
}
}

official replay fixture shape:

{
"symbol": "建準",
"market_theme": {
"confirmed": true,
"trend_status": "confirmed_trend",
"observed_days": 8
},
"strategy_sample": {
"classification_sample_count": 36
},
"technical_score": 10,
"expected": {
"evidence_status": "confirmed_or_supporting",
"evidence_weight_delta": "non_zero",
"composite_not_equal_technical": true
}
}

失敗標本與驗收路由：

- 失敗標本: 建準或等價標的在 market 8天 confirmed_trend + strategy樣本>=10 時仍顯示 partial +0% 且 綜合=技術。
- 驗收路由:
- helper: _market_theme_evidence_payload
- helper: _strategy_sample_row_count / _strategy_sample_evidence_payload
- data loader: load_strategy_evidence_summary
- official generator: message-list 或 equivalent generator replay
- user-visible: Telegram 手機閱讀形狀中的證據加權與綜合分數

## 明確禁止事項

- 禁止 Architect 或 PM 直接改產品碼。
- 禁止跳過 Tech / QA。
- 禁止改 RR 公式。
- 禁止 DB schema/write path/live Telegram/production backfill。
- 禁止手寫 production DML 補資料。
- 禁止只用 synthetic helper fixture 宣告使用者可見問題完成。
- 禁止把 production source 缺資料時的結果宣告為通過；只能標 missing-source / source-error / insufficient-data 或用 read-only artifact 驗 code path。
- 禁止把 hard-blocked 過熱股誤顯成 partial 樣本不足。

## 阻塞條件

- 找不到現有 official generator / message-list replay 路徑，且無法產生等價 replay artifact。
- strategy_evidence_summary 真實樣本數來源不明，無法可靠映射到 sample / row_count。
- production source 無法讀、artifact 無法產生，且任務仍要求 production evidence。
- 現有版本字串/契約位置不明且使用者可見輸出已改變。
- 修正需要 DB schema/write path/backfill 才能成立。

## 本輪停止條件

完成條件：

- 三個底層 probe 通過：market theme、strategy sample、version filter。
- official message-list 或 equivalent generator replay 通過：建準或等價標的不再 partial +0%，且 綜合 != 技術。
- overheat path 已反證：非 0 evidence 或明確 hard-block reason，且無 false partial。
- Tech 在 CHANGELOG.md 寫明覆蓋層級，QA 以 L3 補至少一個 Tech 未覆蓋的直接消費者/負面案例/誤讀路徑反證。

不納入本輪、只記待辦：

- 其他標的 evidence 權重校準。
- RR 公式或策略核心調整。
- 報文版型重設。
- production backfill 或歷史資料修補。
- 全量 evidence framework 清理。
