# QA_REPORT: trend_continuation_buy_path_phase2_20260603

## 測試範圍

本輪按 final one-line data-basis trigger 修正後的 trend_continuation phase2 驗收，不把 scope 擴成 full pytest / replay / backfill。驗證範圍收斂在：

- `TASK.md` / `CHANGELOG.md` / current diff 是否同輪一致。
- trend_continuation BUY 的手機報文是否同時顯示策略樣本 basis 與候選資料 basis。
- 缺 OHLCV / source 時不得形成 `decision_type=trend_continuation` 的 BUY。
- diff 未碰 DB schema/write、RR 公式、live Telegram。

可吸收 diff：`core/condition_engine.py`、`core/generator.py`、`core/signal_snapshot.py`、`presentation/report.py`、`scripts/research_trend_continuation.py`、`services/analysis.py`、`tests/test_analysis_engine.py`、`tests/test_generator_report.py`、`CHANGELOG.md`，均與本輪 trend_continuation phase2 / data-basis 修正相關。

## 風險預算與停止條件

1. 手機報文誤讀：trend_continuation BUY 出現，但資料依據仍寫「策略樣本只作輔助、不新增買點」或「未持倉資料不支持進場」。
   - 驗證：official generator focused test 檢查 summary / unheld card / evidence message。
   - 停止條件：BUY 卡片存在但 evidence message 未出現 trend_continuation 例外支持。
2. 缺 OHLCV/source 被誤開成 trend_continuation BUY。
   - 驗證：load_stock_signal 缺 OHLCV rows 測試與 QA 額外 inline probe。
   - 停止條件：`decision_type=trend_continuation` 且 BUY，或報文出現 trend_continuation 支持小倉進場語氣。
3. 非目標被誤碰：DB schema/write、RR 公式、live Telegram。
   - 驗證：diff 與關鍵字掃描。
   - 停止條件：新增 schema/write/live delivery，或直接改 RR 計算公式。

## 關聯風險掃描

- `TASK.md` 是 risk_patch / L3，`CHANGELOG.md` 描述的檔案、版本 `v20.4.36`、official generator/report 同步與 diff 一致；未發現 TASK / CHANGELOG / diff 矛盾。
- focused tests：6 passed，17 warnings。
- 先前用一般 `.venv/bin/python` 會因主 repo native wheel 架構不符報 pydantic_core arm64/x86_64 mismatch；改用 `arch -arm64` 後通過，這是測試環境入口問題，不是產品測試失敗。
- 額外 QA 反證：`load_stock_signal` 回傳 daily kline 缺第 7 個 `ohlcv_bars` 時，實際 decision 可由既有 `strong_follow` 路徑為 BUY，但 `decision_type != trend_continuation`、`ohlcv_bars is None`，報文不含「趨勢延續買入」與「trend_continuation 同源證據達標者支持小倉進場」。
- 非目標掃描：未見 DB schema/RLS/grant/policy/index/constraint 變更；未見新增 DB write path 或 live Telegram delivery；`calc_rr` 公式未改。

## 跨區塊語意一致性

positive BUY 路徑一致：

- strategy payload：`decision_type="trend_continuation"` / `decision="BUY"` / `position_label="小倉"` / position <= 0.15 / `stop_label="回踩低點下方"` / `exit_horizon_days=5`。
- funnel：新增「趨勢延續」bucket，不混入一般「可買」或不可追高。
- 手機報文：summary 顯示「趨勢延續買入 1 檔小倉」，未持倉卡片顯示「🟢 趨勢延續買入｜小倉」與「回測 55% 勝 / +2.26%」。
- 資料依據：有 trend_continuation BUY 時，策略樣本 basis 改為「僅此例外支持回踩站回小倉買入」，候選資料 basis 改為「trend_continuation 同源證據達標者支持小倉進場，其餘未持倉資料只支持分類觀察」。

negative / missing 路徑一致：

- missing / negative evidence 降為 `trend_observation` / WAIT。
- spike 無回踩不變成 trend_continuation。
- missing OHLCV rows 不形成 `decision_type=trend_continuation` BUY，也不顯示 trend_continuation 小倉支持語氣。

## 使用者誤讀風險

手機閱讀順序已覆蓋 summary -> unheld card -> evidence message：

- summary 有「趨勢延續買入 1 檔小倉」與「新倉建議 1」。
- unheld card 明確寫小倉、回測依據、倉位、止損、5 日持有/退出。
- evidence message 不再用「策略樣本只作輔助參考，不新增買點」否定同一張 BUY 卡片。
- 缺 OHLCV 的額外 probe 沒有出現「趨勢延續買入」或 trend_continuation 小倉支持語氣。

殘留誤讀風險：缺 OHLCV 時仍可能由既有 `strong_follow` 給 BUY；這不是本輪 trend_continuation 目標，若 Owner 要求「缺 OHLCV/source 所有 BUY 都 fail closed」，需另開任務。

## 質疑與反證

- 質疑：data-basis trigger 是否只看 source status，導致 trend_continuation BUY 時仍顯示「不新增買點」？
  - 反證：`presentation/report.py` 的 `_strategy_sample_data_basis_line()` 會掃 `report_context.results_map`，只要存在 `decision_type=trend_continuation` 且 `decision=BUY`，就輸出 trend_continuation 例外支持文案；focused official report test 已驗到該文案。
- 質疑：candidate basis 是否仍把未持倉資料寫成不支持直接進場？
  - 反證：`_position_candidate_data_basis_line()` 在 `trend_count` 存在時輸出 trend_continuation 支持小倉，其餘才是分類觀察；focused official report test 已驗到。
- 質疑：缺 OHLCV rows 是否會誤標 trend_continuation BUY？
  - 反證：Tech test + QA inline official report probe 均確認缺 OHLCV rows 不會產生 `decision_type=trend_continuation`，也不會顯示 trend_continuation 支持小倉文案。

## 已跑命令

- `arch -arm64 .venv/bin/python -m pytest ...focused 6 tests...`
  - 結果：6 passed，17 warnings。
- QA inline official report probe
  - 結果：缺 OHLCV rows 不會產生 `decision_type=trend_continuation` BUY，也不顯示 trend_continuation 支持小倉文案。
- diff / 非目標掃描
  - 結果：未發現 DB schema/write、RR 公式或 live Telegram 變更。

## 未測項目

- 未跑 full pytest。
- 未跑正式 runner artifact。
- 未做 live Telegram。
- 未做 production DB read/write/backfill。
- 未驗完整全市場 replay / evidence 全矩陣。
- 未驗既有 `strong_follow` BUY 在缺 OHLCV 時的全域 source policy，因這超出本輪 one-line data-basis trigger fix。

## QA 結論

通過

本輪 focused QA 覆蓋 data-basis trigger 修正、缺 OHLCV/source fail-closed 對 trend_continuation 的要求、官方報文手機閱讀路徑，以及非目標掃描。未發現 TASK / CHANGELOG / diff 矛盾；未發現 DB schema/write、RR 公式或 live Telegram 變更。
