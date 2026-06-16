# TASK: strategy_rule_outcome_audit_v21_1_20260616

## 任務狀態

- task_id: `strategy_rule_outcome_audit_v21_1_20260616`
- 任務類型: `risk_patch`
- 狀態: `implemented + targeted replay passed`
- 版本建議: 報文 header 維持 `v21.1`
- QA 分級: L2

## Owner 問題

Owner 要在 DB replay 做完後，繼續驗證每一條策略 gate 是否合理，而不是只證明系統存在可買路徑。

核心問題：

- 每個 `funnel_state` 後續 1/3/5/10 日表現如何。
- 每個 `primary_blocker` 是否真的有阻擋依據。
- `買點品質 / 量能 / 熱度 / 風險報酬 / 等回測 / 等接近` 是否可能太死。
- 驗證必須讀 production DB 日線，不得用對話記憶、runtime dict 或假資料。

## 使用者可見結果

- 新增 read-only outcome audit artifact：
  - `reports/audit/strategy_rule_outcomes_v21_1_20260616.json`
- artifact 會列出：
  - 依 `funnel_state` 分組的 forward outcome。
  - 依 `primary_blocker` 分組的 forward outcome。
  - 依 `decision_type / entry_quality / volume_state / heat_state` 分組的 forward outcome。
  - 每組 1/3/5/10 日平均報酬、勝率、平均 MFE、平均 MAE。
  - `flags`：後續明顯偏強但仍被阻擋的 gate。

## 非目標

- 不直接修改正式策略門檻。
- 不修改 Telegram 報文。
- 不寫 DB / 不回寫 / 不去重。
- 不做 live Telegram delivery。
- 不新增 DB schema。

## 影響模組與直接消費者

- `scripts/audit_strategy_rule_outcomes.py`
  - read-only DB outcome audit 工具。
- `tests/test_strategy_rule_outcomes.py`
  - 驗證 forward outcome 來自 DB 日線序列。
- 直接消費者:
  - Architect / Owner 讀 artifact 判斷哪些策略 gate 需要下一輪調整。

## 輸出契約

Artifact 必須包含：

- `read_only: true`
- `db_write: false`
- `schema_change: false`
- `live_telegram: false`
- `totals`
- `by_funnel_state`
- `by_primary_blocker`
- `by_decision_type`
- `by_entry_quality`
- `by_volume_state`
- `by_heat_state`
- `flags`

## 驗收條件

- Replay 從 Supabase `daily_price` read-only 讀取，不寫 DB。
- 用前一輪 replay event 重新對齊後續 DB 日線 close。
- Targeted tests 通過。
- DB artifact 產出且可說明每個 gate 的後續表現。
- Full pytest 通過後才能 commit/push。

## 失敗標本與驗收路由

- 失敗標本:
  - Owner 質疑「策略永遠等、永遠擋，漲幾天也不買」。
- 驗收路由:
  - DB read-only replay artifact。
  - `tests/test_strategy_rule_outcomes.py`。

## 禁止事項與阻塞條件

- 禁止用 synthetic fixture 代替 production DB replay 結論。
- 禁止把 audit flag 解讀成已完成策略修復。
- 禁止 DB write / schema change / live Telegram。
