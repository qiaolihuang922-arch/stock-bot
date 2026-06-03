# QA_REPORT: report-score-evidence-display-20260603

## 測試範圍

- 任務：`report-score-evidence-display-20260603`
- QA 分級：L3。
- 使用者可見面：
  - Telegram 卡片 `數據` 行。
  - 證據不可用原因文案。
  - 強度標籤與低量一致性。
  - 報文版本字串。
- 未擴大到 production DB、live Telegram、full runner artifact。

## 關聯風險掃描

- DB schema / write path：未改。
- RR 公式：未改。
- Strategy decision / holding state machine：未改。
- Render freshness preflight：未改。
- Telegram visible report：已改，版本升 `v20.4.35`。

## 跨區塊語意一致性

- TASK 要求非加碼持倉不顯示新倉品質分；message-list replay 確認非加碼持倉卡片只有 `數據：不適用（既有持倉）`，不含 `綜合 / 技術 / 證據 / RR`。
- TASK 要求持倉加碼仍可顯示分數；QA 自補探針確認 `ADD_10` 持倉仍含 `數據：RR / 綜合 / 技術`。
- TASK 要求 `綜合 <= 100`；message-list replay 斷言不出現 `綜合 10[1-9]`，且高分候選顯示 `綜合 100｜技術 96`。
- TASK 要求過熱文案不再是資料不足；message-list replay 顯示 `證據：過熱不適用`。
- TASK 要求風控 / 缺資料分流；message-list replay 顯示 `證據：風控不適用` 與 `證據：資料不足`。
- TASK 要求低量不顯示 `極強`；message-list replay 顯示 `待確認` 與 `縮量`。

## 使用者誤讀風險

- 非加碼持倉不再同時顯示 `RR 不適用` 和 `綜合/技術`，避免把既有持倉誤讀成新倉品質評分。
- 加碼持倉仍保留分數，避免把可加碼情境誤讀成不可評估。
- 過熱 / 風控 / 資料不足三類文案分開，避免全部顯示成 `資料不足`。
- 低量盤後整理不再呈現 `極強｜V<0.8` 的直覺衝突。

## 失敗標本反證

- Owner 標本：建準暫不加碼持倉曾顯示 `綜合106`。
- 等價 replay：
  - 非加碼持倉：`數據：不適用（既有持倉）`，且不含 `綜合 / 技術 / 證據 / RR 2.7`。
  - 高分新倉候選：顯示 `綜合 100｜技術 96`，無 `綜合 >100`。
  - 過熱：`證據：過熱不適用`。
  - 風控：`證據：風控不適用`。
  - 缺資料：`證據：資料不足`。
  - 低量：無 `極強`，有 `待確認` 與 `縮量`。
  - 低分：無 `證據 +`，顯示 `證據：微幅（confirmed）`。

## 質疑與反證

- 質疑：修非加碼持倉會不會誤傷加碼？
  - 反證：QA 自補 `ADD_10` 持倉探針確認加碼卡仍顯示 `RR / 綜合 / 技術`。
- 質疑：版本只改常量但沒進 message header？
  - 反證：official message-list replay 顯示 `【06/03 盤後｜v20.4.35】`。
- 質疑：Tech handoff 曾錯輪？
  - 反證：第一次 QA blocked 抓到 CHANGELOG 錯輪；Architect 已重寫本輪 CHANGELOG / QA_REPORT，並在主 repo 重跑測試。

## 已跑命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py`
  - 結果：157 passed，241 warnings。
- `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py`
  - 結果：38 passed，13 warnings。
- `PYTHONPYCACHEPREFIX=/private/tmp/report_score_display_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`
  - 結果：passed。
- `git diff --check`
  - 結果：passed。

## 未測項目

- 未跑 full pytest。
- 未執行 live Telegram。
- 未讀寫 production DB。
- 未取得 Render / GitHub runner artifact；本輪驗 official generator message-list replay。

## QA 結論

conditional pass

理由：使用者可見 message-list replay 與相關 regression tests 已覆蓋本輪核心錯誤，且錯輪 CHANGELOG 已修正；但尚未取得正式 runner artifact，因此不寫成完全 `通過`。
