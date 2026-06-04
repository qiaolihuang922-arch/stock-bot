# CHANGELOG: v20.4.38 RR不足 / 等RR修復 報文可讀性修復

## 任務尺寸與風險

- 任務尺寸：normal_patch
- 風險：使用者可見 Telegram 卡片數據行與 summary 回測摘要變更。
- 版本：升小版本到 `v20.4.38`，同步 `core/generator.py` 的 `VERSION`。
- 邊界：不改策略 decision、RR 公式、DB schema/write、production backfill 或 live Telegram。

## 修改內容

- `RR不足 / 等RR修復` 卡片的 hidden score 文案改為 `原因：RR不足，等待RR修復`，不再顯示會被誤讀為資料源缺失的 `證據：資料不足`。
- summary 回測摘要只納入可買 / 趨勢延續 / 可準備候選語境；`等RR修復 / 僅追蹤` 標的不再出現在 summary 回測摘要。
- 新增 official `formatTelegramMessages` replay，覆蓋建準 + 光寶科 failure specimen：建準回測保留，光寶科卡片仍為 `等RR修復｜RR不足`，但 summary 不列 `回測（光寶科）`。
- 同步測試中的可見版本字串為 `v20.4.38`。

## 修改檔案

- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 最小改動策略

- 僅改 formatter / summary helper / message-list replay 測試。
- 不改 RR 計算、進出場門檻、未持倉 decision 或持倉主行動。
- 不處理交易執行排序，因不阻塞本輪 RR不足 / 回測摘要可讀性驗收。

## 契約影響

- 使用者可見 header / 簡報版本變為 `v20.4.38`。
- `等RR修復｜RR不足` 卡片數據行可以顯示 RR 數值與 V，但不可把 RR 不足寫成 `證據：資料不足`。
- summary 回測摘要不再列入僅追蹤 / 等RR修復標的；這類標的仍透過未持倉漏斗與卡片呈現。
- 函式回傳結構、DB payload、strategy decision payload 未變更。

## 直接消費者同步

- `presentation/report.py` 卡片數據行同步 RR不足 reason 文案。
- `core/generator.py` 的 `format_backtest_groups()` 使用 final formatter 的未持倉狀態判斷排除僅追蹤標的。
- `tests/test_generator_report.py` 使用 official `formatTelegramMessages` final message-list replay，不是 helper-only。
- 實際 `core.generator.generate()` 已在主 repo 跑過，產出 `v20.4.38` 報文：光寶科卡片原因正確，summary 只保留建準回測。

## 未影響模組

- 未改 `services/analysis.py`。
- 未改 `core/condition_engine.py`。
- 未改 RR 公式。
- 未改 DB schema / RLS / grant / policy / role / index / constraint。
- 未改 DB write path。
- 未執行 production backfill、production write 或 live Telegram。

## 已跑自檢命令

- `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_38_rr_wait_card_reason_and_backtest_summary_readability or 0604_v20_4_37_generate_mobile_consistency_message_list_replay or v20_4_37_single_backtest_lines_are_not_aggregated or v20_4_36_non_actionable_unheld_hides_score_numbers' -q`：4 passed。
- `PYTHONPYCACHEPREFIX=/private/tmp/v20_4_38_pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `git diff --check`：passed。
- `arch -arm64 ./.venv/bin/python - <<'PY' ... generate() ... PY`：passed；實際輸出 header 為 `v20.4.38`，summary 不含 `回測（光寶科）`，光寶科卡片顯示 `原因：RR不足，等待RR修復`。

## 覆蓋層級

- official `formatTelegramMessages` final message-list replay。
- actual `core.generator.generate()` final report output。
- 未覆蓋 production runner artifact / live Telegram。

## 殘留風險

- `generate()` 使用即時價，RR 數值會隨行情變動；本輪驗證文案語意與 summary 納入規則，不宣稱固定 RR 值。
- 未跑 full pytest；本輪只跑 focused contract。
- 未改交易執行排序；若 Owner 要 card / execution / checklist 同序，需另開排序任務。

## 旁支待辦

- 如需正式 runner 取證，另取 production runner artifact；本輪未 live delivery。
