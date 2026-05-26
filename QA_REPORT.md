# QA_REPORT.md

本文件由 QA 維護，提交給 Architect。只記錄本輪 v19.5 QA 結果。

## 任務狀態

- 狀態：QA 驗證完成
- 對應 TASK / CHANGELOG：`TASK.md`、`CHANGELOG.md`
- 提交日期：2026-05-26
- 任務：`v19.5-report-summary-execution`
- 版本：v19.5
- QA 等級：L2

## 測試範圍

依 `DISPATCH.md` 指定 `qa_level=L2`，本輪驗證範圍為顯示不變性、formatter、summary view model、Telegram contract、策略與 snapshot 局部不變性。

覆蓋範圍：
- v19.5 summary 新區塊：`🧭 今日結論`、`✅ 明日執行清單`、`未持倉漏斗`、`📎 詳情索引`。
- 明日執行清單最多 5 項、持倉項保留目前盈虧百分比。
- STOP / REDUCE / TAKE_PROFIT / 風控持倉優先，風控超過 5 項時需顯示剩餘風控提示。
- 等待標的保留 `不買 / 不追價 / 不可買` 語意，不得被誤解為可買。
- 弱勢淘汰壓縮後仍保留名稱與主因，12 檔 watchlist 可追溯。
- `messages[-1]` 仍為總覽摘要，`include_detail=True` 完整詳情 chunk 仍在摘要之前。
- `reply_markup` 仍由 `send_many()` 綁定最後摘要段。
- strategy action / decision / is_tradeable / is_best_candidate、snapshot validator、daily snapshot store 局部不變性。

未執行 full pytest、replay/backfill dry-run、live Telegram、live Supabase write、正式 backfill。

## 執行命令

```bash
.venv/bin/python -m pytest tests/test_generator_report.py tests/test_notifier.py
```

```bash
.venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py tests/test_daily_snapshot_store.py
```

另執行 QA 補充 smoke：
- 12 檔 watchlist 可追溯、summary 長度、持倉盈虧百分比、等待語意、reply_markup 最後摘要段、`include_detail=True`、`generate()` list join fallback。
- 風控持倉超過 5 項時的 `另有 N 檔風控見詳情`。
- 無持倉 / 無新追蹤時的空狀態與淘汰追溯。

## 測試結果

### Formatter / Notifier

結果：通過。

```text
34 passed, 21 warnings in 1.56s
```

### Strategy / Snapshot 局部不變性

結果：通過。

```text
41 passed, 13 warnings in 0.43s
```

### QA 補充 Smoke

結果：通過。

```text
QA_SMOKE_OK 3 396 5 12
CONTROL_OVERFLOW_OK 5
EMPTY_TRACKING_OK 214
```

結論：
- 預設 formatter 輸出 3 段，順序為持倉詳情、未持倉詳情、總覽摘要。
- Summary 包含 v19.5 四個新增區塊，且低於 3500 字截斷風險。
- 12 檔 watchlist 均可在摘要或詳情追溯。
- 明日執行清單最多 5 項。
- 持倉執行項包含 `+/-xx.xx%` 盈虧百分比。
- 等待類未持倉項包含 `不買 / 不追價 / 不可買` 語意。
- `reply_markup` 綁定最後摘要段，前面詳情段不帶 markup。
- `include_detail=True` 時完整詳情 chunk 在前，最後仍是 v19.5 摘要。
- `generate()` list join fallback 未破壞。
- 6 檔風控持倉時只列 5 項，並顯示 `另有 1 檔風控見詳情`。
- 無持倉且無追蹤候選時，摘要顯示明確空狀態，淘汰標的仍可追溯。

## 關聯風險掃描

### 直接呼叫方

- `core/generator.generate_report()`：仍回傳 `(messages, reply_markup)`。
- `core/generator.formatTelegramMessages()`：仍回傳 list，摘要仍在 `messages[-1]`。
- `main.py`：仍以 `messages, reply_markup = generate_report()` 後呼叫 `send_many(messages, reply_markup=reply_markup)`。
- `services/notifier.send_many()`：未修改，list 訊息只把 `reply_markup` 附在最後一段；單段 string 保留原行為。
- `core/generator.generate()`：list join fallback 已用 mock 驗證未破壞。

### 下游與副作用

- 本輪 diff 未修改 `services/analysis.py`、DB store、snapshot payload、replay/backfill scripts、watchlist、notifier。
- v19.5 summary 是新的決策入口；主要風險不是策略計算，而是資訊壓縮後的誤讀。
- `send()` 仍有 3500 字截斷邏輯；本輪 smoke 的 summary 長度為 396，局部 fixtures 安全。真實極端內容仍需保留長度 regression。

## 質疑與反證

### PM 是否漏需求

PM 已補入 QA 研究要求的硬條件：風控不可漏看、等待不可誤解、低優先級可追溯、summary/reply_markup 不回退、持倉項保留盈虧百分比。

QA 反證結果：
- 多風控持倉超過 5 項時，摘要顯示剩餘風控提示。
- 等待標的行包含 `不買 / 不追價 / 不可買`。
- 弱勢淘汰保留名稱與主因。
- 12 檔標的未因壓縮完全消失。

### Tech 是否漏同步

Tech 已在 `CHANGELOG.md` 列出直接消費者同步，且實作未改 `main.py` / `services/notifier.py`。

QA 反證結果：
- formatter-to-notifier contract smoke 通過，`reply_markup` 綁在最後摘要段。
- `generate()` list join fallback 通過。
- `include_detail=True` 仍保持完整詳情在摘要之前。

### 測試是否能證明沒有破壞直接消費者

本輪不只重跑 Tech 自檢，也補了直接契約與負面 smoke：
- 真實 formatter messages list 餵入 `send_many()`。
- 風控溢出情境。
- 無持倉 / 無追蹤候選情境。
- 12 檔追溯與 summary 長度。

結論：足以支撐 L2 範圍內通過；不等同 live Telegram 或 full regression。

## 驗收項結果

- `version_level=minor`：通過。
- `qa_level=L2` 實測：通過。
- 新增 `🧭 今日結論`：通過。
- 新增 `✅ 明日執行清單`：通過。
- 新增 `未持倉漏斗`：通過。
- 新增 `📎 詳情索引`：通過。
- 明日執行清單最多 5 項：通過。
- 風控 / 停利 / 減碼優先於未持倉追蹤：通過。
- 風控超過 5 項有剩餘提示：通過。
- 持倉項保留目前收益百分比：通過。
- 等待未持倉保留不可買 / 不追價語意：通過。
- 合格 BUY 不被等待狀態覆蓋：通過。
- `續抱` 不單獨出現在摘要，會展開為觀察語意：通過。
- 弱勢淘汰名稱與主因可追溯：通過。
- 12 檔 watchlist 可追溯：通過。
- 回測不產生 BUY、只影響同類排序：通過既有 formatter / strategy 不變性測試。
- 不改 strategy action / decision / is_tradeable / is_best_candidate：通過局部不變性測試。
- 不改 DB schema、股票池、replay/backfill：未見 diff，未執行相關流程。
- 預設 `messages[-1]` 為總覽摘要：通過。
- `reply_markup` 綁定最後摘要段：通過。
- `include_detail=True` 完整詳情 chunk 在摘要之前：通過。
- `generate_report()` 可被 `main.py -> send_many()` 消費：通過 contract smoke。
- 單段 string 行為未回退：通過 `tests/test_notifier.py`。
- Summary 長度未觸發截斷風險：本輪 smoke 通過。

## 未測項目

本輪未執行：
- full pytest。
- replay / backfill dry-run。
- live Telegram delivery。
- live Supabase write。
- formal backfill write。
- Telegram 客戶端實機渲染截圖。
- 真實生產日所有行情來源混合情境。

原因：
- `DISPATCH.md` 本輪明確指定 `qa_level=L2`。
- `TASK.md` / `CHANGELOG.md` 均限定本輪不改策略層、DB、replay/backfill、股票池、notifier。
- live Telegram / live Supabase / formal backfill 不屬於預設 L2 驗證。

## 殘留風險

- 真實 Telegram 平台仍可能有到達順序或 UI 顯示差異；本輪只用 mock 驗證 `send_many()` 參數契約。
- Summary 目前在 smoke fixture 中長度安全；若未來詳情索引、淘汰主因或持倉數增加，仍需保留 summary length regression。
- 弱勢淘汰目前以名稱與主因追溯，若 Owner 後續要求每檔完整原因仍在摘要內，需另開產品調整。
- 本輪未跑 replay/backfill；若後續 Tech 改 snapshot payload 或 replay script，需升級驗證。

## QA 結論

QA 結論：通過。

v19.5 收盤決策壓縮與執行清單升級已通過 L2 驗證。可交回 Architect 更新狀態。
