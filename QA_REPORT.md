# QA_REPORT:

## 測試範圍

- 任務：`evidence-chain-structural-coverage-100`
- 任務尺寸 / QA：`risk_patch / L3`
- 驗證範圍：structural evidence coverage、verifier、三則 Telegram artifact、fail-closed 文案、read-only artifact CLI。
- 未擴成 production replay、backfill、production read-only audit、全 repo pytest 或 live Telegram。

## 關聯風險掃描

- `TASK.md / CHANGELOG.md / diff` 一致：版本升 `v20.4.18`，三則 message order 保持，第三則補 source/status/use/limit/conflict，manifest 補 required keys。
- 可吸收 diff：`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`CHANGELOG.md`、`scripts/generate_structural_evidence_artifact.py`。
- Artifact safety flags 均為 `schema_change=false`、`data_write=false`、`live_telegram=false`、`credential_values_included=false`。
- `git diff --check`：passed。
- Targeted tests：`tests/test_generator_report.py tests/test_market_theme_evidence.py`：119 passed，169 warnings。

## 跨區塊語意一致性

- 三則手機閱讀順序已驗：messages[0] 持倉、messages[1] 未持倉、messages[2] 簡報＋資料依據。
- 三個 CLI artifact case 重跑結果：
  - `all_sources_available`：coverage 100%，pass=true，missing_slots=[]，fail_closed_violations=[]，conflict_slots=[]。
  - `missing_strategy_sample_source`：coverage 100%，pass=true，missing_slots=[]，fail_closed_violations=[]，顯示 missing-source 與「新倉：無有效進場」。
  - `ledger_position_conflict`：coverage 100%，pass=true，missing_slots=[]，fail_closed_violations=[]，conflict_slots 顯示 `position-vs-event` 與 `unresolved-conflict`。
- 必要 structural layers 已驗，三個 artifact 均無 missing required layer，manifest slots 無 required key 空值。

## 使用者誤讀風險

- missing-source case 不會被 `通過 / 有效進場 / 可買` 誤導。
- ledger conflict case 會顯示 `unresolved-conflict` 與 `position-vs-event`，未顯示已確認停利或有效執行結論。
- v20.4.17 人話資料依據未回退成 raw dump；第三則仍可讀，但保留本任務要求的標準 status token。

## 質疑與反證

- QA 補充反證：對 missing-source artifact 注入 `建準｜通過｜來源不足仍升格`，verifier 回傳 `pass=false` 且 `fail_closed_violations` 非空。
- QA 補充反證：對 missing-source artifact 注入 `建準｜有效進場｜來源不足仍升格`，verifier 回傳 `pass=false` 且 `fail_closed_violations` 非空。
- QA 確認 `coverage_pct` 與 `coverage_percent` 均為 100.0，避免 artifact 消費者欄位名不一致。
- diff 掃描未見 DB schema / migration / production write / live Telegram send path 變更。

## 未測項目

- 未驗 production 真實資料合理度、ledger 衝突修復、策略門檻正確性、production read-only audit。
- 未跑 full repo pytest、未做 live Telegram、未做 DB write/backfill/schema 操作。
- 未驗 runner 實際發報，只驗 read-only artifact 與 generator/verifier 行為。

## QA 結論

通過
