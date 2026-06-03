# CHANGELOG: report-score-evidence-display-20260603

## 任務尺寸與風險

- 任務類型：risk_patch。
- 風險原因：本輪改使用者可見 Telegram 報文數據行、證據文案、強度標籤與版本字串。
- 未碰：DB schema/write path、RR 公式、策略 decision、live Telegram。

## 修改內容

- `core/generator.py`
  - 報文版本由 `v20.4.34` 升為 `v20.4.35`。
  - `apply_evidence_confidence()` 的 `final_confidence` 封頂為 `min(100.0, technical * modifier)`。
  - 過熱 / 延伸、FAIL / 弱結構、technical<=0 的 blocked 情境一律將 evidence 標成 unavailable，不再保留百分比或 partial。
- `presentation/report.py`
  - 持倉且非加碼時，卡片數據行改為 `數據：不適用（既有持倉）`，不顯示 RR / 綜合 / 技術 / 證據 / V。
  - 持倉加碼與未持倉新倉候選仍顯示 `RR / 綜合 / 技術 / 證據 / V`。
  - 證據不可用文案分流：
    - 過熱 / 延伸：`證據：過熱不適用`
    - FAIL / 減碼 / 結構弱：`證據：風控不適用`
    - 真缺資料：`證據：資料不足`
  - 盤後收縮整理且量比 `<0.8` 時，`極強` 降為 `待確認` 並加 `縮量`。
  - `technical < 10` 或 rounded final 等於 rounded technical 時，不顯示 `+X%`，改顯示 `證據：微幅（status）`。
- Tests：
  - 新增 official `formatTelegramMessages` message-list replay，覆蓋非加碼持倉、加碼、新倉封頂、過熱、風控、資料不足、低量、低分。
  - 同步既有版本與數據行預期。

## 修改檔案

- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## 最小改動策略

- 只改 TASK 指定的分數套用與顯示 formatter。
- 不改報文分組、排序、RR 計算、候選池或策略模型。
- 以 official message-list replay 驗手機可見結果，避免只驗 helper。

## 契約影響

- 使用者可見報文版本：`v20.4.35`。
- `result["final_confidence"]` 新契約：最大值 `100.0`。
- 持倉非加碼數據行新契約：整段 `不適用（既有持倉）`。
- 證據 unavailable 文案新增原因分流：過熱 / 風控 / 資料不足。
- Message order、payload shape、DB contract、RR formula 未變。

## 直接消費者同步

- `presentation/report.py` 的持倉 / 未持倉卡片 formatter 已同步。
- `core/generator.py` official message path 已同步。
- `tests/test_generator_report.py` 增加 Owner specimen 等價 message-list replay。
- `tests/test_market_theme_evidence.py` 同步版本字串。

## 未影響模組

- 未改 DB schema / RLS / grant / policy / role / index / constraint。
- 未改 production write / backfill / live Telegram。
- 未改 RR 公式、候選來源、策略 decision、持倉狀態機。
- 未改 Render freshness preflight。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py`
  - 結果：157 passed，241 warnings。
- `arch -arm64 .venv/bin/python -m pytest tests/test_market_theme_evidence.py`
  - 結果：38 passed，13 warnings。
- `PYTHONPYCACHEPREFIX=/private/tmp/report_score_display_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py`
  - 結果：passed。
- `git diff --check`
  - 結果：passed。

## 覆蓋層級

- helper / formatter：covered。
- official generator / message artifact：covered by `formatTelegramMessages` replay。
- runner artifact / production source：not covered，本輪未執行 runner、未讀 production、未 live delivery。

## 殘留風險

- 低量收縮降級依現有 `volume_price_state=COILING`、`structure_phase=BASE`、`lifecycle=BASE` 欄位判斷；若 production payload 使用其他同義欄位，需另補 mapping。
- 未取得正式 runner artifact；本輪以 official message-list replay 反證。

## 旁支待辦

- 若後續發現其他「縮量但極強」來源欄位，另開欄位 mapping 任務。
- 若 Owner 要把證據不可用原因寫入 structured artifact 欄位，而不只顯示文案，另開 payload contract 任務。
