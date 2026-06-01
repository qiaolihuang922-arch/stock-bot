# QA_REPORT:

## 測試範圍

- 任務：`report_v20_4_21_holding_rr_conflict_followup`，normal_patch，QA L2。
- 驗證範圍限於 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`presentation/report.py`、`tests/test_generator_report.py`。
- 未擴大到 full repo pytest、production replay、backfill、DB write 或 live Telegram。

## 風險預算與停止條件

1. 今日買入持倉主行動已是 `新倉風控觀察`，但底層 `ADD_10 / allow_add=True` 仍讓卡片露出 `RR 2.73`。
   - 驗證：檢查 fixture、artifact、手機閱讀卡片順序與 scoped tests。
   - 停止條件：持倉卡主行動為 `新倉風控觀察` 時仍出現 `數據：RR 2.73`。
2. presentation 顯示層暗中接 DB writer、evidence writer、schema alter 或 fake production path。
   - 驗證：AST/boundary test、rg 掃描與 artifact 安全旗標。
   - 停止條件：presentation 新增 DB client / writer / schema alter 依賴，或 artifact 標示 write/live/schema。
3. TASK / CHANGELOG / diff 口徑不一致。
   - 驗證：`git diff --name-only`、`git diff --check`、文件內容與實際 diff 對照。
   - 停止條件：實際 tracked diff 超出指定檔案，或 CHANGELOG 漏列/誤列產品 diff。

## 關聯風險掃描

- `git diff --name-only` 只有 5 個 tracked 檔案：`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、`presentation/report.py`、`tests/test_generator_report.py`。
- `core/generator.py` 無 diff，VERSION 仍為 `v20.4.21`。
- `presentation/report.py` 無 import；未發現 DB writer / evidence writer / schema alter 入口。
- AST 額外掃描只命中 `lines.insert(...)` 這種 list method，不是 DB insert writer。

## 跨區塊語意一致性

- fixture 保留 `holding_decision.level=ADD_10`、`allow_add=True`、`position_events.bought_shares=50`。
- 手機持倉卡同時顯示：
  - `決策：新倉風控觀察，暫不加碼`
  - `數據：新倉 RR：不適用（既有持倉）｜S 5/5｜V 0.9x`
- 未持倉候選仍保留新倉 RR 顯示，測試確認 `數據：RR 2.4` 仍存在。
- 第三則資料依據仍和持倉卡一致。

## 使用者誤讀風險

- 已反證 Owner 指出的主誤讀路徑：同一卡片不再同時出現 `新倉風控觀察，暫不加碼` 與 `數據：RR 2.73`。
- `.qa_tmp/v20_4_21_holding_rr_dry_run_card.json` 驗證：
  - `credential_values_included=false`
  - `schema_change=false`
  - `data_write=false`
  - `live_telegram=false`
  - `card_found=true`
  - card 含 `新倉 RR：不適用（既有持倉）`
  - card 不含 `數據：RR 2.73`

## 質疑與反證

- 底層 `ADD_10 / allow_add=True` 是否會繞過修正：不會，fixture probe 通過。
- 顯示層是否引入 DB/schema/evidence writer：未發現，boundary test 通過。
- CHANGELOG 是否還宣稱上一輪大範圍修正：已收斂到持倉 RR 衝突補修，修改檔案與 diff 對齊。

## 已跑命令

- `git diff --name-only`
- `git diff --check`：passed。
- artifact JSON 安全旗標與卡片內容檢查：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py::GeneratorReportTest::test_presentation_report_module_has_no_storage_or_evidence_write_imports tests/test_generator_report.py::GeneratorReportTest::test_v20_4_21_afterhours_mobile_readability_probe`：2 passed，17 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：92 passed，181 warnings。
- Re-QA output：`.cao_agent_context/outputs/20260601_183214_25279_stock_qa_code_readonly.answer.txt`，結論 `通過`。

## 未測項目

- 未執行 live Telegram delivery。
- 未做 production DB write、backfill、DML、schema / RLS / grant / policy 實機檢查。
- 未跑 full repo pytest、歷史 replay 或 evidence 全矩陣。
- 未驗 Telegram reply markup 附著位置。

## QA 結論

通過
