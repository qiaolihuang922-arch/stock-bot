# TASK: 精確修復 market/theme evidence decision gate 與 fallback

## 任務狀態

- task_id: fix_market_theme_evidence_gate_v20_4_31
- 任務類型: normal_patch
- 狀態: done
- 版本建議: 不升版，必須保持 v20.4.31
- QA 分級建議: L2
- 主 bug: market/theme evidence 在已 confirmed 的 8 天背景下仍顯示「不適用」，且 per-stock 缺 market_theme 時未 fallback report-level evidence。

## Owner 問題

目前 core/generator.py 的 _market_theme_evidence_payload 對 reliability_confirmed 使用 observed_days >= 15，與 loader 的 confirmed_trend 定義不一致。Owner 要求 evidence gate 精準修復：

- confirmed_trend 已代表 observed >= 3 且近 3 日支持，market/theme 的 confirmed_trend 應直接 decision_eligible，或改用同一個 reliability 函數。
- basis line 與 score path 的判斷來源需一致。
- market/theme 是 report-level 市場級證據；個股 per_stock_evidence 缺 market_theme 時，不應直接 unavailable，而應 fallback 到 report-level market_theme_evidence。
- services/strategy_evidence.py load_strategy_evidence_summary 必須確認已移除 .eq('version', VERSION)，讓歷史 outcomes 可按 trade_date 跨版本進入回測。
- 不 bump VERSION，保持 v20.4.31。

## 使用者可見結果

手機閱讀 Telegram / 報文卡片時，像英業達這種 8 天 confirmed market/theme 背景，不應看到「證據不適用」或等價 unavailable 文案。

示例輸出形狀：

英業達
...
市場/題材證據：+X%（supporting / confirmed）
...

不可輸出形狀：

英業達
...
市場/題材證據：不適用
...

## 非目標

- 不重設策略邏輯。
- 不修改 RR 公式。
- 不修改買賣、加減碼、停損停利 decision。
- 不修改 DB schema、RLS、grant、policy、role、index、constraint。
- 不寫 production DB，不做 backfill，不手寫 production DML。
- 不發 live Telegram。
- 不升版，不改 VERSION。
- 不做全量 evidence / report formatter 清理。

## 影響模組與直接消費者

影響模組：

- core/generator.py
- _market_theme_evidence_payload
- market/theme evidence payload 建構路徑
- per-stock market_theme fallback 路徑
- services/strategy_evidence.py
- load_strategy_evidence_summary
- 確認 strategy outcomes 查詢不再被 current VERSION filter 限制
- 相關可重跑 probe / tests
- 必須補或更新能驗證本任務三個 regression 點的 probe。

直接消費者：

- Telegram / 報文卡片中的 market/theme evidence 顯示。
- market/theme production trend consumption check。
- strategy evidence summary 回測 outcomes 消費路徑。
- QA regression probe。

## 輸出契約

### market/theme evidence payload

_market_theme_evidence_payload 對 confirmed market/theme evidence 必須符合：

- 當輸入 evidence 已是 confirmed_trend，且 loader 定義已滿足 observed >= 3 與近 3 日支持時：
- decision_eligible 必須為 true 或等價可消費狀態。
- 不得再因 observed_days < 15 變成 unavailable。
- basis line 與 score path 必須使用一致的 reliability / confirmed 判斷來源。
- 8 天 confirmed evidence 應可顯示 positive/negative score，例如 +X%，並標示 supporting/confirmed 類型，不得顯示「不適用」。

### per-stock fallback

當個股 per_stock_evidence 沒有該股 market_theme evidence 時：

- 必須 fallback 到 report-level market_theme_evidence。
- fallback 後仍應保留 market/theme 是市場級證據的語意。
- per-stock 差異只應主要來自 strategy_sample 同類 setup，而不是因缺個股 market_theme 就 unavailable。

### strategy evidence summary

load_strategy_evidence_summary 必須按 trade_date 查歷史 outcomes，且不得重新加入：

.eq("version", VERSION)

驗收需覆蓋像 v20.4.5 這類有 outcomes 的歷史版本可進入回測 summary。

### 版本契約

- 使用者可見版本、報文 header、常量 VERSION 必須保持 v20.4.31。
- 不得為本修復 bump version。

## 版本契約

已存在且不得回退的契約：

- VERSION 保持 v20.4.31。
- market/theme confirmed 判斷必須與 loader confirmed_trend 定義一致。
- strategy evidence historical outcomes 查詢不得依 current VERSION 過濾。
- report-level market_theme_evidence 可作為個股卡片缺 per-stock market_theme 時的 fallback。
- Telegram / 報文不可把 confirmed 且可消費的 market/theme evidence 顯示成「不適用」。

若 Tech 發現現有 loader confirmed_trend 定義與 Owner 描述不符，必須 blocked 並交回 Architect 補證，不得自行改定義。

## 驗收條件

1. 8 天 confirmed market/theme evidence 可消費
- 使用英業達或等價 fixture：observed_days = 8、confirmed_trend = true、近 3 日支持。
- 卡片 market/theme evidence 顯示 +X%（supporting / confirmed） 或等價正向證據。
- 不得顯示「不適用」或 unavailable。
- build_market_theme_production_trend_consumption_check 結果必須包含 uses_history=True。
2. per-stock 缺 market_theme fallback
- fixture 中 per_stock_evidence 刻意不放該股 market_theme。
- report-level market_theme_evidence 有 confirmed evidence。
- 個股卡片仍能顯示 report-level market/theme evidence，不得直接 unavailable。
3. strategy 跨版本 history 未回歸
- probe 必須反證 load_strategy_evidence_summary 沒有 current VERSION filter。
- fixture / mock outcomes 包含非 v20.4.31 的歷史版本，例如 v20.4.5。
- 只要 trade_date 範圍符合，該 outcomes 應能進入 summary / 回測消費路徑。
4. VERSION 不變
- 測試或 probe 必須確認使用者可見版本與 VERSION 仍是 v20.4.31。

## 範例或 Fixture

最小 fixture 形狀：

report_level_market_theme_evidence = {
"confirmed_trend": True,
"observed_days": 8,
"recent_3d_supported": True,
"score_pct": 0.12,
"direction": "supporting",
}

per_stock_evidence = {
"英業達": {
# no market_theme key here
"strategy_sample": {
"setup": "same_theme_setup"
}
}
}

期望卡片片段：

市場/題材證據：+12%（supporting / confirmed）

strategy outcomes fixture：

outcomes = [
{
"trade_date": "2026-05-20",
"version": "v20.4.5",
"setup": "same_theme_setup",
"outcome": "win",
}
]

期望：在查詢日期範圍符合時，此筆可被 load_strategy_evidence_summary 消費，不因 version != v20.4.31 被排除。

## 明確禁止事項

- 禁止修改 RR 公式。
- 禁止修改 DB schema / write path / production DML。
- 禁止 live Telegram delivery。
- 禁止 bump VERSION。
- 禁止把本任務擴成策略核心重設。
- 禁止用 observed_days >= 15 作為 confirmed market/theme decision eligibility 的唯一門檻。
- 禁止 per-stock 缺 market_theme 時直接輸出 unavailable，而不嘗試 report-level fallback。
- 禁止重新加入 .eq("version", VERSION) 或等價 current-version-only filter。

## 阻塞條件

- 找不到 loader confirmed_trend 的既有定義，或其定義不符合 Owner 所述 observed >= 3 且近 3 日支持。
- 無法構造或重跑 market/theme evidence probe。
- 無法確認 VERSION 常量或使用者可見報文版本。
- strategy evidence 查詢路徑無法在 test/probe 中反證是否存在 version filter。
- 任何修復需要 DB schema/write/live Telegram 權限。

## 本輪停止條件

本輪完成只限於：

- _market_theme_evidence_payload confirmed gate 與 basis/score path 對齊。
- per-stock 缺 market_theme 時 fallback report-level market_theme evidence。
- load_strategy_evidence_summary 跨版本 outcomes filter regression 確認。
- VERSION 保持 v20.4.31。
- 補可重跑 probe / tests，QA 反證四個指定風險。

旁支問題只記待辦，不納入本輪：

- 其他 evidence formatter 文案優化。
- 其他股票或其他策略 setup 的命中率調整。
- 全量 market/theme evidence cleanup。
- DB 歷史資料補寫或 backfill。
- Telegram 報文整體版面重設。
