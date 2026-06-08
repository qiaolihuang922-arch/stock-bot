# TASK: unheld_volume_tracking_reclassification_20260608

## 任務狀態
- task_id: `unheld_volume_tracking_reclassification_20260608`
- 任務類型: `normal_patch`
- 狀態: `qa_passed`
- 版本建議: `v20.4.55`
- QA 分級: `L2`

## Owner 問題
Owner 指出 v20.4.54 未持倉標的大量顯示 `⛔ 淘汰｜量能不足`，但這類狀態其實可能在量能回升、重新接近買點後變成可買候選，不應直接被判成死淘汰。Owner 要求上網查後修改。

外部核對口徑：突破/接近突破需要量能確認；低量能代表確認不足、假突破風險較高，合理處理是等待量能或回測確認，而不是永久淘汰。

## 使用者可見結果
- 未持倉若主因是 `量能不足`，即使市場 grade 偏弱，只要不是結構性失敗，改列 `👀 等量能｜量能不足`。
- 若同時遠離突破，明日觸發改成 `量能回升且重新接近買點`，避免讓使用者誤會只要放量就能追。
- `弱反彈待確認`、`突破失敗`、`DISTRIBUTION`、明確 `FAIL` 仍可列淘汰。
- 總結漏斗不再顯示奇怪的 `未持倉 7｜淘汰 7`，改以 `僅追蹤` 分組呈現。

## 非目標
- 不把任何未持倉標的改成現在可買。
- 不改持倉停損/減碼建議。
- 不改 DB schema、DB write、runner secrets 或 live Telegram delivery。
- 不新增外部行情資料源。

## 影響模組與直接消費者
- `core/generator.py`: 未持倉 funnel/state/trigger/reject reason。
- `presentation/report.py`: unheld card title reason fallback。
- `tests/test_generator_report.py`: owner failure specimen regression。
- `tests/test_market_theme_evidence.py`: 版本同步。
- 直接消費者：official `generate_report(dry_run=True)` message list、GitHub runner generated TG report。

## 輸出契約
- 未持倉卡片狀態分組仍是可買/準備/僅追蹤/淘汰。
- `量能不足` 類候選輸出為 `等量能`，不是 `淘汰`。
- 遠離突破且量能不足時，觸發文字必須同時要求量能與重新接近買點。
- 淘汰主因不得被 RR 或資料噪音覆蓋，必須顯示真主因。
- 使用者可見版本升到 `v20.4.55`。

## 驗收條件
- focused pytest 通過，覆蓋量能不足在弱市仍列追蹤。
- official `generate_report(dry_run=True)` replay 中，Owner 貼出的 7 檔未持倉不再全數淘汰。
- summary 漏斗顯示 `未持倉 7｜僅追蹤 7（等回測1/等量能6）`，不得殘留 `淘汰 7`。
- 不執行 live Telegram delivery。

## 失敗標本與驗收路由
- 失敗標本：Owner 貼出的 v20.4.54 未持倉報文，7 檔全列 `⛔ 淘汰`，多數主因為 `量能不足`。
- 驗收路由：official generator `generate_report(dry_run=True)` 最終 message list。

## 禁止事項與阻塞條件
- 禁止 live Telegram delivery。
- 禁止 production DB write / schema change。
- 若 official dry-run 無法產生 message list，結論只能 blocked。
