# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：使用者可見 Telegram 未持倉卡片 RR 文案修正。
- 邊界：不改策略 decision、RR 計算、DB、持倉狀態或 live delivery。

## 修改內容

- 新增未持倉 RR 顯示優先序：當 rr 四捨五入後為 `0.00`，且 blocker / 狀態為過熱時，`rr_display_text(..., holding=False)` 顯示 `-（過熱）`。
- 保留正數 RR 既有顯示，避免盤後候選卡片原本的 RR 2.x 被誤改成過熱 blocker。
- 新增技嘉類未持倉卡片 regression：`可準備｜過熱降溫 + rr=0 + calc_rr=0 + 過熱 blocker` 時，卡片顯示 `數據：RR -（過熱）`，不顯示 `RR 0.00（不足）`。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`

## 最小改動策略

- 只在 RR 顯示 helper 前置加入窄條件。
- 不改 `calc_rr`、`entry_blockers`、`strong_prepare_bucket`、分組排序或策略判斷。
- 測試只補 TASK 指定的未持倉卡片 regression，沿用既有非過熱 `RR 0.00（不足）` 測試防止全域誤改。

## 契約影響

- 使用者可見未持倉卡片 RR 文案變更：
  - 過熱 blocker 且 `rr=0.0` 時由 `RR 0.00（不足）` 改為 `RR -（過熱）`。
- 函式回傳結構、payload、message list 順序、報文分組、DB 寫入、CLI 輸出：未變更。
- VERSION：未變更，符合 TASK 版本建議。

## 直接消費者同步

- Telegram message list / dry-run output 透過既有 `rr_display_text` 消費修正。
- `formatTelegramUnheldCard` 無簽名變更；直接呼叫方不需改介面。
- Regression test 已覆蓋 Owner 手機閱讀卡片路徑。

## 未影響模組

- 策略 decision / `calc_rr` 公式未改。
- DB schema / write path / production data 未改。
- 持倉狀態機、買賣 / 加減碼 / 停損停利建議未改。
- live Telegram delivery 未執行。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'rr_zero_display_marks_insufficient_when_not_hidden or unheld_overheat_prepare_rr_zero_uses_overheat_blocker or v20_4_21_afterhours_mobile_readability_probe or v19_3_2_intraday_summary_classifies_0526_cases'`：4 passed，93 deselected，21 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：97 passed，201 warnings。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py tests/test_generator_report.py`：passed。
- `git diff --check`：passed。

## 殘留風險

- 本輪只處理過熱 blocker 且 `rr=0.0` 的使用者可見 RR 顯示；其他 blocker reason 的 RR 優先序未重整。
- warnings 為既有第三方 deprecation / Python 版本提示，非本輪新增失敗。

## 旁支待辦

- 其他 blocker reason 的 RR 文案優先序若還有不一致，需另開 TASK。
- 全量 RR formatter 命名或架構清理不在本輪範圍。
- production 既有報文不回補。
