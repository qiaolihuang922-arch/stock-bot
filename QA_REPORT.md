# QA_REPORT:

## 測試範圍

- 任務：`risk_patch_20260601_2301_today_buy_after_close_reading`，QA L2。
- 驗證重點：盤後手機閱讀順序、今日買入來源說明、`current_can_buy=false` 與 `executed_today=true` 不混淆、distance > 4 弱勢不可 can_buy、版本 `v20.4.22`、無 DB write / live Telegram / 持倉狀態機改動。

## 風險預算與停止條件

1. 手機第一則持倉卡仍把「今日已買」讀成「現在可買」。
   - 驗證：檢查持倉卡在盤面行後、決策行前新增說明；跑 2301 類三來源 fixture 與 QA 額外 phone-order probe。
   - 停止條件：出現 `光寶科｜可買`、`買點：可買`、`推薦買入` 或可被讀成當前 BUY 的主行動。
2. 來源不足時未 fail closed，錯把 ledger / 未知買入歸因成策略 BUY。
   - 驗證：檢查 today buy source helper 與 fallback；QA 額外 probe 用無 `buy_source`、只有 `position_events` 的今日買入。
   - 停止條件：缺明確來源時輸出策略今日已執行，或不標示來源限制。
3. 策略層仍允許 distance=5.43、弱勢/普通、遠離突破 can_buy。
   - 驗證：跑 can_buy 負面測試，確認 Tech 未只用文案掩蓋策略錯誤。
   - 停止條件：distance > 4 仍回傳 can_buy true，或 diff 修改 strategy decision 但缺 probe。

## 關聯風險掃描

- TASK / CHANGELOG / diff 一致。
- 可吸收 diff：
  - `core/generator.py`：VERSION = `v20.4.22`；新增 today buy source / current can buy / context line helper；注入 presentation deps。
  - `presentation/report.py`：盤後持倉卡在盤面行後插入說明行。
  - `tests/test_generator_report.py`：2301 類三來源 fixture、版本期望。
  - `tests/test_analysis_engine.py`：distance > 4 can_buy 負面 probe。
  - `tests/test_market_theme_evidence.py`：版本同步。
  - `CHANGELOG.md`：同步本次變更摘要。
- 未新增 schema/RLS/grant/policy/role/index/constraint；未改 production write/backfill；未改 live Telegram delivery；未改 holding_status / strategy holding state machine。

## 跨區塊語意一致性

- 版本：`core/generator.py` 已升 `v20.4.22`，CHANGELOG 與測試期望同步。
- 持倉卡：盤面顯示 `洗盤回測｜弱勢｜普通｜遠離突破（5.43%）` 後接說明，直接否定「現在可繼續買」。
- 第三則 / 簡報：fixture 顯示 `今日交易已建立新倉 1 檔；新增有效進場：無。`，與持倉卡不衝突。
- Payload / message list：payload shape 未改；message order 未改，手機順序仍是持倉、未持倉、簡報＋資料依據。

## 使用者誤讀風險

- 通過 phone-order probe：第一則先看到持倉卡，卡片同時出現今日買入、盤後弱勢遠離突破、來源限制與「不代表可繼續買」。
- QA 額外 probe：無 `buy_source`、有 `position_events.event_count=1 / bought_shares=50` 時，輸出手動/ledger 與非當前策略買點，未默認成策略 BUY。
- 殘留但不阻塞：卡片仍有否定語 `暫不加碼`；語意是禁止加碼，不是主行動。若 Owner 要完全不出現「加碼」兩字，另開文案收斂任務。

## 質疑與反證

- 質疑：Tech 測試只覆蓋 explicit `buy_source` 三值，可能漏掉真實上游只有 ledger event、沒有 source 欄位的情境。
  - 反證：QA 額外 inline probe 通過，position_events only 情境會 fail closed 為手動/ledger，且不顯示當前可買主行動。
- 質疑：formatter 文案是否掩蓋策略 can_buy 錯誤。
  - 反證：`tests/test_analysis_engine.py::AnalysisEngineTest::test_can_buy_rejects_weak_far_from_breakout` 通過，現有 can_buy() 對 distance > 4 回傳 false。
- 質疑：版本升版是否任意。
  - 反證：TASK 要求使用者可見報文變更需升版或同步更新；CHANGELOG 明確記錄升 `v20.4.22`；版本測試同步。

## 已跑命令

- `git diff --check`：passed。
- Targeted pytest：
  - `tests/test_generator_report.py::GeneratorReportTest::test_afterhours_today_buy_holding_explains_current_non_buy_by_source`
  - `tests/test_generator_report.py::GeneratorReportTest::test_afterhours_brief_counts_today_buy_holdings_as_executed_new_positions`
  - `tests/test_analysis_engine.py::AnalysisEngineTest::test_can_buy_rejects_weak_far_from_breakout`
  - `tests/test_market_theme_evidence.py::MarketThemeEvidenceTest::test_readonly_smoke_cli_outputs_auxiliary_render_artifact`
  - Result：4 passed, warnings only。
- QA inline phone-order / missing-source probe：passed。
- Re-QA output：`.cao_agent_context/outputs/20260601_213156_18119_stock_qa_code_readonly.answer.txt`，結論 `通過`。

## 未測項目

- 未跑 full pytest，符合 L2 風險預算。
- 未做 replay/backfill。
- 未做 production DB read-only smoke。
- 未發 live Telegram。
- 未全量盤點其他股票同型來源缺口。

## QA 結論

通過
