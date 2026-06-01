# QA_REPORT:

## 測試範圍

- 任務：`risk_patch-afterhours-brief-today-buy-holdings-20260601`。
- QA 風險等級：L2，聚焦盤後第三則 Telegram 使用者可見摘要與 message list 順序。
- 可吸收 diff：`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`、`CHANGELOG.md`。
- 未擴大到 full replay / backfill / production write。

## 風險預算與停止條件

1. 手機閱讀順序衝突：第一則持倉卡有「今日 買 N股」，第三則仍寫「今日無有效新倉」。
   - 驗證：檢查 `formatTelegramMessages()` 三則 message 順序，確認 messages[0] 持倉卡與 messages[2] 盤後簡報語意一致。
   - 停止條件：第三則不含 `今日無有效新倉`，且明確出現今日交易已建立新倉。
2. 無額外可買標的被誤讀成還能追買或完全無交易。
   - 驗證：today buy holding + watch empty 時，第三則同時保留 `新增有效進場：無`。
   - 停止條件：今日買入與新增有效進場分開呈現。
3. 負面案例誤報：沒有 today buy、watch empty 時，被錯誤寫成今日已有新倉。
   - 驗證：既有持倉非 today buy 場景，第三則可寫無新增有效進場，但不得出現 `今日交易：已建立新倉`。
   - 停止條件：負面案例不誤報今日新倉。

## 關聯風險掃描

- TASK / CHANGELOG 一致：任務尺寸為 risk_patch、版本不升、範圍限盤後第三則簡報與直接測試。
- `presentation/report.py` 新增 `_today_buy_holding_names()`，`_afterhours_brief_lines()` 納入 `holding_items` today buy 判斷。
- `core/generator.py` 只在 `_telegram_presentation_deps()` 注入既有 `is_today_buy_holding`。
- `tests/test_generator_report.py` 補 today-buy holding 手機閱讀 probe，並更新既有盤後 today buy 預期。
- 未見策略 decision、DB write、live Telegram、VERSION diff。

## 跨區塊語意一致性

- 今日買入正例 inline probe：
  - 第一則 messages[0] 含 `【持倉標的】` 與 `今日 買 1000股`。
  - 第三則 messages[2] 含 `📌 盤後簡報`。
  - 第三則輸出 `結論：今日交易已建立新倉 3 檔；新增有效進場：無。`
  - 第三則輸出 `今日交易：已建立新倉 3 檔（...）` 與 `新增有效進場：無`。
  - 第三則不含 `今日無有效新倉`。
- 名稱順序為既有持倉排序結果；TASK 不要求固定 fixture 順序，不阻塞本輪。

## 使用者誤讀風險

- 已按 Owner 手機閱讀順序檢查三則 Telegram message：
  - 第一則先看到今日買入。
  - 第三則不再否定今日新倉。
  - 第三則仍清楚表示沒有額外新增有效進場，避免被解讀成還有追買推薦。
- 負面案例：
  - 無 today buy、無 watch 可買時，第三則仍可含 `結論：今日無有效新倉；既有持倉以收盤後風控觀察為主。`
  - 同時含 `新增有效進場：無`。
  - 不含 `今日交易：已建立新倉`。

## 質疑與反證

- QA 不只重跑 Tech 自檢；額外補了 inline mobile-order probe，直接驗證 `formatTelegramMessages()` 的第一則 / 第三則跨區塊語意。
- 聚焦測試：
  - `arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'afterhours_brief or post_market_holding_risk_precedes_tomorrow_plan_without_duplicate_downgrade'`：3 passed, 92 deselected。
- 編譯檢查：
  - `arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `git diff --check -- core/generator.py presentation/report.py tests/test_generator_report.py`：passed。

## 未測項目

- 未跑 full pytest，符合 L2 聚焦風險預算；Tech 已宣稱全 `tests/test_generator_report.py` 通過，本輪 QA 重跑相關盤後路徑。
- 未做 production DB read-only smoke，因本輪不涉及 DB read/write contract。
- 未做 live Telegram delivery，且 TASK 明確禁止。
- 光寶科買入解釋、技嘉 RR 0.00、縮量漲停風險、智原 observation_days 為 TASK 旁支，不納入本輪阻塞。

## QA 結論

通過
