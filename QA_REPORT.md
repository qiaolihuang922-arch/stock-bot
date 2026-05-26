# QA_REPORT: Telegram Report Clarity And Query Performance

## 測試範圍

- 任務：`telegram-report-clarity-performance`
- 驗證範圍：Telegram formatter、strategy evidence 查詢、notifier message list contract、策略不變性。
- 可吸收候選 diff：
  - `core/generator.py`
  - `services/strategy_evidence.py`
  - `tests/test_generator_report.py`
  - `tests/test_strategy_evidence.py`
  - `CHANGELOG.md`

## 實測命令

- `arch -arm64 .venv/bin/python -c '... pytest.main(["tests/test_generator_report.py", "tests/test_strategy_evidence.py", "tests/test_analysis_engine.py", "tests/test_notifier.py", "-q"])'`
  - 結果：`75 passed, 21 warnings`
- QA 追加手機長報文 fixture：
  - 5 檔持倉。
  - `旺宏` 為淘汰。
  - `best=旺宏`。
  - 盤後語境。

## 關聯風險掃描

- `formatTelegramMessages()` 仍回傳 message list；`services/notifier.py` contract 測試通過。
- `record_strategy_evidence(..., client=None)` 新增 optional client，既有不傳參呼叫方行為不變。
- `generate_report()` 已共用同一 Supabase client 給 record/load evidence，降低同 run 重複 client 建立。
- `load_strategy_evidence_summary()` 已測 `order("trade_date", desc=True)`、`limit()`、order -> limit -> execute 順序與最新 audit row 顯示。
- `services/analysis.py` 未改，`tests/test_analysis_engine.py` 通過，策略 decision 主體未被修改。
- QA 未修改 tracked files；`run_qa_code.sh` 已用 diff hash 檢查。

## 跨區塊語意一致性

- Summary 顯示 `v20.0.6` 與 `盤後結論`。
- `明日執行清單` 內不再出現 `今日可執行`。
- 持倉行改為 `盤後持倉檢視：5 檔`。
- 冷卻 / 回測 / RR / 淘汰 數量能對上漏斗、索引與明細。
- `旺宏` 只在未持倉淘汰明細保留追溯；summary 不再重複曝光股票名。

## 使用者誤讀風險

- 已反證：`best=旺宏` 且 `旺宏=淘汰` 時，高層不會顯示 `🔥 最強：旺宏` 或任何推薦語氣。
- 已反證：`旺宏` 不會進入可買、準備、僅追蹤或明日行動候選。
- 已反證：盤後報文不再混用 `明日執行清單` 與 `今日可執行`。
- 殘留風險：尚未量測 production 真實秒數；本輪以 query order/limit、client reuse 與測試 contract 作為替代證據。

## 質疑與反證

- PM 是否漏需求：未漏，已列手機閱讀路徑、淘汰降噪、明日/盤後語境、query performance、notifier consumer。
- Tech 是否漏同步：未漏，formatter、strategy evidence、notifier contract、strategy decision 測試均覆蓋。
- 測試是否能證明直接消費者未破壞：可接受，formatter/evidence/analysis/notifier 測試通過，QA 另補手機長報文負面 fixture。
- QA 主動找到的風險：worktree 有非候選固定文件殘留，不可整包合併；Architect 已按候選文件挑選吸收。

## 未測項目

- 未跑 full pytest；本輪 QA 分級為 L2。
- 未執行 live Telegram delivery。
- 未執行 live Supabase write。
- 未執行正式 replay / backfill。
- 未做 production 秒數 benchmark。

## QA 結論

conditional pass。

候選產品 diff 可吸收；不可整包合併隔離 worktree。
