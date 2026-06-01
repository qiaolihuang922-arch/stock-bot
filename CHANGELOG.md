# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：只改 Telegram 報文顯示文案與可重跑 probe；不改 strategy decision、RR 計算、持倉狀態機、DB schema/write、VERSION 或 live delivery。

## 修改內容

- `presentation/report.py`
  - 將市場 / 題材資料依據中的「交易證據日」改為「交易日短期背景」或「短期背景資料」。
  - 盤後卡片下一步改為明日語境：`盤中先觀察` -> `明日觀察是否守住警戒`，`盤中觀察修復狀況` -> `明日確認是否修復`。
  - 盤後未持倉卡片不再逐張輸出長資料來源句。
  - 第三則資料依據改為白話邊界：持倉與價格支持風控；未持倉資料只支持分類觀察，不支持直接進場。
- `tests/test_generator_report.py`
  - 更新既有文案預期。
  - 將本輪手機閱讀 probe 更新為 `test_v20_4_21_afterhours_mobile_readability_probe`，覆蓋建準非加碼 RR、盤後下一步、資料降噪、第三則資料邊界和禁止詞。
- `tests/test_market_theme_evidence.py`
  - 同步市場 / 題材背景命名預期，避免三日資料被誤稱為交易證據日。

## 修改檔案

產品 / 測試 diff：

- `presentation/report.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

Architect handoff：

- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`

## 契約影響

- 使用者可見報文文案有變更：
  - 三日市場資料改稱短期背景 / 市場溫度。
  - 盤後下一步改為明日語境。
  - 盤後未持倉卡片移除逐檔長資料來源句。
  - 第三則資料依據明確說明未持倉不支持直接進場。
- Message list 結構、payload shape、DB contract、版本常量均未變更。
- 報文版本維持 `v20.4.21`，未回退。

## 直接消費者同步

- Telegram message renderer：同步盤後卡片文案與第三則資料依據。
- Owner 手機閱讀路徑：新增/更新 probe 檢查持倉卡、未持倉卡、第三則資料依據。
- v20.4.x report tests 與 market/theme tests 已同步。

## 未影響模組

- 策略核心與買賣決策。
- RR 計算公式與加碼 RR 顯示契約。
- 持倉狀態機。
- DB schema / RLS / grant / policy / role / index / constraint。
- DB write、backfill、live Telegram delivery。
- Telegram reply markup / delivery consumer。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：128 passed，181 warnings。
- `git diff --check`：passed。
- `rg -n "交易證據日|策略勝率|勝率證據" presentation/report.py -S`：no matches。

## QA 反證

- QA 補 source-error 盤後 fixture，確認第三則顯示來源讀取異常，不混用 missing-source / 樣本不足主狀態。
- QA 按手機閱讀順序掃描，確認建準在持倉卡、新倉候選在未持倉卡、第三則在卡片後。
- QA 確認 generated output 不含本輪禁止詞，且建準非加碼持倉不顯示 RR 2.73。

## 殘留風險

- 本輪未處理 Telegram reply markup 附著最後一則 message 的旁支風險。
- 本輪未做 production replay / backfill / live delivery。
- 其他非本輪指定文案美化、排序、策略分數與資料完整性問題未處理。
