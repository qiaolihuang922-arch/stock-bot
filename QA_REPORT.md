# QA_REPORT:

## 測試範圍

- 任務：`pm-20260601-afterhours-telegram-brief-dedupe`，normal_patch，QA L2。
- 驗證聚焦：盤後 Telegram message list、第三則簡報、卡片文案、策略樣本狀態、持倉 RR 顯示與可重跑 probe。
- 未擴大到 full repo pytest、production DB read/write、backfill 或 live Telegram。

## 風險預算與停止條件

1. 第三則仍複製完整 summary 或交易細節。
   - 驗證：新增 test 與 QA 手機閱讀 fixture。
   - 停止條件：第三則包含完整 `今日交易`、`持倉風控檢查` 或卡片明細。
2. 策略樣本狀態重複或衝突。
   - 驗證：卡片去重與第三則單一狀態；QA 補 source-error 負面路徑。
   - 停止條件：同一報文同時出現 missing-source / 樣本不足 / source-error 多個主狀態，或卡片逐檔重複不可用。
3. 盤後手機閱讀仍有盤中語境或持倉 RR 誤導。
   - 驗證：按 message[0] 持倉、message[1] 未持倉、message[2] 第三則掃描。
   - 停止條件：非加碼持倉顯示新倉 RR 數字，或盤後輸出含盤中觸發 / 盤中先觀察 / 即時進場等詞。

## 關聯風險掃描

- `presentation/report.py` 新增盤後摘要、策略樣本單一狀態行、盤後文案替換與卡片策略樣本去重。
- `core/generator.py` 只新增 `_strategy_sample_unavailable` deps 注入，未改策略 decision 或 DB path。
- `tests/test_generator_report.py` 新增本輪可重跑 probe。
- `core.generator.VERSION` 仍為 `v20.4.21`。
- 無 DB schema/write、live Telegram、notifier delivery consumer diff。

## 跨區塊語意一致性

- TASK 要求第三則摘要化、策略樣本狀態單一化、卡片去噪、盤後語境與非加碼持倉 RR 一致；實際 diff 覆蓋上述項目。
- CHANGELOG 已修正為「盤後 Telegram 可見文案與第三則語意變更」，不再宣稱無文案變更。
- Message order 未變：持倉卡 -> 未持倉卡 -> 簡報＋資料依據；Details Backup only when requested。

## 使用者誤讀風險

- 第三則現在以 `📌 盤後簡報` 開頭，只保留結論、策略樣本狀態、明日前確認與資料依據，不再複製完整 summary。
- 策略樣本不可用集中顯示一次，避免每檔卡片刷屏。
- 盤後卡片不再輸出被測盤中詞；非加碼持倉不顯示新倉 RR 數字，新倉候選 RR 保留。

## 質疑與反證

- Tech 自檢外，QA 補了 source-error negative fixture：第三則顯示來源讀取異常，不混入 missing-source 或樣本不足主狀態。
- QA 另補 NEW_POSITION_RISK_WATCH 盤後持倉負面路徑：`盤中先觀察` 會改為盤後語境。
- QA 按手機閱讀順序掃描三則訊息：message_count=3，第三則是 brief，卡片沒有逐檔策略樣本不可用。
- 測試結果：
  - `tests/test_generator_report.py -k 'afterhours_brief_is_concise or v20_3_3_afterhours or v20_4_18_non_add_holding'`：1 passed，91 deselected。
  - `tests/test_generator_report.py`：92 passed，181 warnings。
  - QA independent source-error fixture：all checks true。

## 已跑命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：92 passed，181 warnings。
- `git diff --check`：passed。
- `tools/cao_agent/run_qa_code.sh ...` Re-QA：通過；QA output `.cao_agent_context/outputs/20260601_174507_27838_stock_qa_code_readonly.answer.txt`。

## 未測項目

- 未跑 live Telegram delivery。
- 未做 production DB write/read smoke。
- 未跑 full repo pytest、正式 replay 或 backfill；本輪 normal_patch/L2 不要求。
- 未處理 Telegram reply markup 附著最後一則 message 的旁支風險。

## QA 結論

通過
