# QA_REPORT:

## 測試範圍

- 任務：`report_v20_4_21_mobile_readability_remaining_fixes`，normal_patch，QA L2。
- 驗證聚焦 Telegram 報文 formatter、手機閱讀 message list、三日短期背景命名、非加碼持倉 RR、盤後下一步、卡片資料來源降噪與第三則資料依據。
- 未擴大到 full replay、backfill、production DB write 或 live Telegram。

## 風險預算與停止條件

1. 手機閱讀仍把三日背景或 strategy sample 誤讀成策略證據 / 勝率。
   - 驗證：全文掃描與 rendered message list 檢查 `交易證據日` / `策略勝率` / `勝率證據` 不出現在盤後輸出。
   - 停止條件：盤後可見報文仍出現禁止詞，或三日資料與買點 / 勝率綁定。
2. 非加碼持倉仍露出新倉 RR 數字。
   - 驗證：建準非加碼 fixture 保留 payload rr=2.73，但持倉卡只顯示新倉 RR 不適用。
   - 停止條件：持倉卡、索引、詳情或下一步出現新倉 RR 數字。
3. 文件與 diff 對齊。
   - 驗證：比對 CHANGELOG 修改檔案 / 測試名稱 / 實際 diff。
   - 停止條件：交付摘要宣稱不存在的 diff，或漏列實際 diff。

## 關聯風險掃描

- `presentation/report.py` 只改顯示文案與盤後輸出，未改策略 decision、RR 計算或 DB path。
- `tests/test_generator_report.py` 更新手機閱讀 probe。
- `tests/test_market_theme_evidence.py` 同步短期背景命名預期。
- `core/generator.py` 無本輪 diff；VERSION 仍為 `v20.4.21`。

## 跨區塊語意一致性

- 手機順序：持倉卡、未持倉卡、第三則資料依據。
- 持倉卡：建準非加碼顯示新倉 RR 不適用，且下一步為明日語境。
- 未持倉卡：新倉候選 RR 保留，未逐檔重複長資料來源句。
- 第三則：集中表達持倉與價格支持風控、未持倉只支持分類觀察、不支持直接進場。

## 使用者誤讀風險

- 已降低三日資料被誤讀成策略證據 / 勝率的風險。
- 已降低非加碼持倉被誤讀成新倉 RR 可進場的風險。
- 已降低未持倉卡片資料來源重複造成的手機噪音。

## 質疑與反證

- QA 補 source-error 盤後 fixture：第三則顯示來源讀取異常，不混用 missing-source / 樣本不足主狀態。
- QA generated output 掃描未命中本輪禁止詞。
- QA scoped tests：
  - `arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：128 passed，181 warnings。
- `git diff --check`：passed。

## 已跑命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：128 passed，181 warnings。
- `git diff --check`：passed。
- `rg -n "交易證據日|策略勝率|勝率證據" presentation/report.py -S`：no matches。
- Re-QA output：`.cao_agent_context/outputs/20260601_181248_1516_stock_qa_code_readonly.answer.txt`，結論 `通過`；補驗 source-error、confirmed trend 不升格買點、手機順序與第三則資料邊界。

## 未測項目

- 未執行 live Telegram delivery。
- 未做 production DB write、backfill、DML、schema / RLS / grant / policy 檢查。
- 未做 full repo pytest、歷史 replay 或 evidence 全矩陣。
- 未驗 Telegram reply markup 附著位置。

## QA 結論

通過
