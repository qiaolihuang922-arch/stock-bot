# CHANGELOG:

## 任務尺寸與風險

- 任務類型：risk_patch。
- 任務階段：trend_continuation phase2，屬使用者可見策略 / 報文契約變更，風險接近 major；本輪仍限定單一路徑，不擴成全策略重構。
- 風險原因：正式 BUY 決策、condition gate、strategy payload、official generator、手機報文 funnel / card 狀態同步新增 trend_continuation 路徑。
- 明確未碰：DB schema / write、RR 公式、live Telegram、其他 setup 的 evidence-to-BUY 政策。

## 修改內容

- 接入 trend_continuation 回踩站回買入路徑：
  - 正式策略可在「趨勢成立 + 回踩 ma5/ma10 + 放量站回 + 同源研究證據達標」時輸出 `decision_type="trend_continuation"` 與 `decision="BUY"`。
  - 證據缺失、不足或為負時降級為 `decision_type="trend_observation"` / `WAIT`。
  - extended spike / 無回踩 / 純創新高追價不開 BUY。
- 研究與正式策略共用 `scripts/research_trend_continuation.py` 的形態判定函數，避免同一 setup 在研究與 production 漂移。
- 新增小倉、止損、退出 payload：
  - 倉位 `<=15%`，標示小倉。
  - 止損為回踩低點下方。
  - 退出 / 持有對齊 5 日 edge。
- official generator 與 presentation report 新增「趨勢延續」單獨 funnel / 手機報文狀態。
- trend_continuation BUY 會強制顯示資料依據，即使資料源正常也保留同源策略樣本與候選資料說明，避免小倉買入缺證據鏈。
- 報文版本同步升至 `v20.4.36`。
- 補 focused tests 覆蓋正向 BUY、負證據 WAIT、spike 無回踩、同源判定、official report 手機閱讀、空 watch_items official generator、負面 evidence official report。

## 修改檔案

- `services/analysis.py`
- `scripts/research_trend_continuation.py`
- `core/condition_engine.py`
- `core/generator.py`
- `core/signal_snapshot.py`
- `presentation/report.py`
- `tests/test_analysis_engine.py`
- `tests/test_generator_report.py`

## 最小改動策略

- 只開放 trend_continuation 單一路徑，不放寬其他 setup。
- 不改 RR 計算公式。
- 不改 DB schema / RLS / grant / policy / role / index / constraint。
- 不做 DB write、正式 backfill 或 live Telegram。
- 不重構整體 strategy tree / condition engine，只同步必要直接呼叫方與報文消費者。
- 未以寫死 fixture 壓過真實邊界；負證據與缺資料路徑維持 fail closed。

## 契約影響

- strategy decision payload 新增 / 傳遞：
  - `decision_type="trend_continuation"`
  - `decision_type="trend_observation"`
  - `trend_continuation_evidence`
  - `trend_continuation_setup`
  - `position_label`
  - `stop_label`
  - `exit_rule`
  - `exit_horizon_days`
- `strategy()` 入口新增 optional 參數：
  - `ohlcv_bars`
  - `trend_continuation_evidence`
  - `stock_id`
- `core.signal_snapshot.analyze_ohlcv_snapshot()` 同步新增 optional 參數並傳入 `strategy()`。
- message list / 報文分組新增「趨勢延續」分類與卡片狀態：
  - `🟢 趨勢延續買入｜小倉`
  - 顯示 `回測 55% 勝 / +2.26%`
  - 顯示倉位、止損、5 日持有 / 退出規則。
- 版本契約：`core/generator.py` 版本字串同步為 `v20.4.36`。
- DB contract：無 schema / payload / write path 變更。
- RR contract：公式未變。

## 直接消費者同步

- `core/generator.py`
  - load stock signal 時傳入 OHLCV bars 與 trend_continuation evidence。
  - unheld funnel、execution item、summary、new entry suggestions、pending trade items 同步識別「趨勢延續」。
- `presentation/report.py`
  - 未持倉卡片、摘要、資料依據、手機閱讀路徑同步新增 trend_continuation 小倉買入文案。
- `core/condition_engine.py`
  - BUY condition gate 同步 trend_continuation，WAIT observation 同步 event 判定。
- `core/signal_snapshot.py`
  - snapshot 分析呼叫方可傳入同源 OHLCV / evidence。
- tests 同步 official generator / report 層級，避免只驗 helper。

## 未影響模組

- 未改 DB schema、RLS、grant、policy、role、index、constraint。
- 未新增 DB write path。
- 未改 RR 計算公式。
- 未做 live Telegram delivery。
- 未改首次突破倉位邏輯。
- 未把其他 setup 改成 evidence 達標即可 BUY。
- 未改 production persistence / 跨日 source-of-truth。
- 未做 full strategy refactor。

## 已跑自檢命令

- focused phase2 tests
  - 結果：6 passed，17 warnings（主工作區 final focused subset）；先前 Tech/QA phase2 擴充 subset 為 13 passed，17 warnings。
- empty watch_items official generator probe
  - 結果：passed。
- negative evidence official report probe
  - 結果：passed。
- py_compile
  - 結果：passed。
- `git diff --check`
  - 結果：passed。

## 覆蓋層級

- helper：研究形態判定與正式策略共用函式。
- strategy：正向 trend_continuation BUY、缺 / 負 evidence WAIT、spike 無回踩不買。
- condition engine：trend_continuation BUY / trend_observation WAIT 條件摘要。
- official generator：趨勢延續小倉 bucket、load stock signal 傳入 OHLCV / evidence、缺 source fail closed。
- report formatter：手機可讀卡片、摘要、資料依據、空 watch_items fail-safe。
- 未測：full pytest、正式 runner artifact、live Telegram、production DB。

## 殘留風險

- 未跑 full pytest；本輪自檢只代表 focused phase2 與指定 official generator probes。
- Tech 自檢不代表 QA 通過。
- trend_continuation evidence 目前只允許同源 positive sample 開 BUY；後續若要接 production 長期監控或動態 artifact，需要另開任務。
- legacy `strong_follow` 等既有 BUY 路徑不在本輪改造範圍。

## 旁支待辦

- 後續另開任務處理長期實盤 vs 回測勝率監控 artifact / dashboard。
- 其他 setup 的 evidence gate 政策不納入本輪。
