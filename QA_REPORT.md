# QA_REPORT:

## 測試範圍

- 依據：`TASK.md`、`CHANGELOG.md`、git diff、`core/generator.py` 局部 diff、`tests/test_generator_report.py`、`tests/test_notifier.py`。
- 本輪不是清理 / 瘦身 / refactor 任務，path / claim / evidence / risk / action 證據表不適用。
- 可吸收 diff 僅限本輪任務相關：
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `tests/test_notifier.py`
  - `CHANGELOG.md`
- worktree 殘留：git status 只顯示上述 4 個 modified tracked files，未見其他 unrelated tracked diff；Architect 仍只吸收上述任務 diff。
- 已跑測試：
  - `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py`
  - 結果：`52 passed, 21 warnings`
- QA 額外 smoke：
  - 補反向 phase drift：第一次 `get_market_phase()` 回傳 `盤後`，後續若被錯誤重讀會變 `盤中`。
  - 結果：`phase_mock.call_count == 1`，summary / 未持倉卡均維持盤後語意，未出現盤中交易執行或可買卡。

## 關聯風險掃描

- `formatTelegramMessages()`：未傳入 `report_phase` 時只讀一次 `get_market_phase()`，並傳入未持倉卡與 summary；符合 TASK。
- `formatTelegramSummary()`：由 message list 路徑傳入 `report_phase` 時不重讀 phase；直接呼叫未傳入時仍自行讀一次，屬 optional contract，與 `CHANGELOG.md` 一致。
- phase-sensitive helpers：`today_conclusion_text()`、`today_reason_text()`、`format_execution_checklist()`、`detail_index_text()` 已接收 `report_phase`。
- notifier 直接消費者：`tests/test_notifier.py` 驗證最後一則 summary header 仍保留 `v20.0.14`，`send_many()` 介面未改。
- `generate_report()`：同輪固定一次 `report_phase` 並傳入 DB/evidence 記錄參數與 `formatTelegramMessages()`；未發現 live write、新 schema 或策略 decision diff。
- `price_label_for_source()` 仍即時讀 phase；`CHANGELOG.md` 已列為殘留風險。本輪 TASK 目標是 Telegram message list phase drift，不把行情標籤層擴大為阻塞。

## 跨區塊語意一致性

- Owner 手機閱讀順序檢查：
  - 最後一則 summary header 顯示單一 phase 與 `v20.0.14`。
  - 盤中 fixture：summary 出現 `今日盤中交易執行`，未持倉卡出現 `可買｜10%倉` 與 `盤中觸發`，未混入 `明日計畫`。
  - 盤後 fixture：summary 出現 `今日交易紀錄 / 無新增` 與 `明日計畫 1`，未持倉卡出現 `明日追蹤` 與 `明日觸發`，未混入 `今日盤中交易執行`、`交易執行 1`、`分批執行`。
- message list 順序仍是持倉、未持倉、summary；未超出本輪結構契約。

## 使用者誤讀風險

- 盤後路徑已避免把未持倉有效買點寫成今日可買或分批執行，降低 Owner 誤判「今天要買」的風險。
- Summary 的「今日結論」標籤下仍會包含「明日計畫 N」，但同段下方有 `今日交易紀錄 / 無新增` 與 `明日計畫` 區塊，未達阻塞。
- 未發現同一批 Telegram messages 中 summary 是盤後、卡片是盤中，或反向混用的可見輸出問題。

## 質疑與反證

- PM 是否漏需求：TASK 有列直接消費者、輸出契約、手機閱讀路徑與驗收案例，未缺阻塞欄位。
- Tech 是否漏同步：diff 顯示 summary、未持倉卡、execution/checklist/index/reason helper 與 `generate_report()` 都同步 `report_phase`；未見只修測試。
- 測試是否能證明沒有破壞直接消費者：除 Tech 指定測試外，QA 補了反向 drift smoke，覆蓋「第一次盤後、後續盤中」的負面路徑。
- TASK / CHANGELOG / diff 是否一致：一致。版本契約為沿用 `v20.0.14`，未升到新版本。
- 主動風險：`price_label_for_source()` 仍可在完整詳情或行情標籤層即時讀 phase；本輪 scope 沒有要求重構行情來源，且 `generate_report()` 的主 Telegram header / message list 已固定，不列阻塞。

## 未測項目

- 未跑 full pytest、replay/backfill dry-run、DB payload 實寫；本輪 TASK 禁止 live write / 正式 backfill。
- 未測 live Telegram delivery；符合禁止事項。
- 未全面檢查行情來源與 `price_label_for_source()` 的 phase label drift；`CHANGELOG.md` 已列殘留風險，非本輪直接 message list contract。

## QA 結論

通過
