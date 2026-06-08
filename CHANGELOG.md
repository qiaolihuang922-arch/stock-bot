# CHANGELOG: unheld_volume_tracking_reclassification_20260608

## 修改內容與修改檔案
- `core/generator.py`
  - 版本升至 `v20.4.55`。
  - 新增未持倉結構性淘汰判斷，只有 `FAIL`、弱反彈、突破失敗、派發等結構性失敗才直接淘汰。
  - `量能不足` 優先歸到 `等量能`，不再因 market grade `D` 自動淘汰。
  - 遠離突破且量能不足時，觸發文字改成 `量能回升且重新接近買點`。
  - 淘汰主因排序保留真主因，避免 RR 噪音蓋過弱反彈/市場弱。
- `presentation/report.py`
  - unheld card 若 funnel 已是淘汰，標題主因回查 `rejected_primary_reason`。
- `tests/test_generator_report.py`
  - 新增 v20.4.55 regression：弱市、遠離突破、量能不足但非結構失敗時列 `等量能`。
  - 更新既有量能不足與弱反彈淘汰測試。
- `tests/test_market_theme_evidence.py`
  - 版本同步。

## 契約影響
- message list 順序不變。
- 未持倉漏斗語意改為：可恢復候選進 `僅追蹤`，結構壞掉才進 `淘汰`。
- 使用者可見版本為 `v20.4.55`。
- 無 DB write、無 live Telegram delivery。

## 直接消費者同步
- official `generate_report(dry_run=True)` 已重放。
- GitHub runner 仍走同一 generator / presentation 路徑；本輪未改 workflow。

## 未影響模組
- 持倉風控、停損/減碼策略未改。
- future-watch 法說會、財報、歷史類比未改本輪邏輯。
- Telegram live sender 未改且未執行。

## 自檢命令與結果
- `python -m pytest tests/test_generator_report.py::GeneratorReportTest::test_v19_4_volume_blocked_non_weak_stock_enters_wait_volume tests/test_generator_report.py::GeneratorReportTest::test_v20_4_55_volume_blocked_far_weak_market_tracks_instead_of_rejecting tests/test_generator_report.py::GeneratorReportTest::test_rejected_weak_rr_uses_true_reject_reason_not_rr -q` -> 3 passed。
- broader focused pytest with future-watch/notifier routes -> 9 passed。
- `python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py tests/test_market_theme_evidence.py` -> passed。
- `python -m pytest tests/test_market_theme_evidence.py -q` -> 38 passed, 13 subtests passed。
- `generate_report(dry_run=True)` -> 4 messages, header `v20.4.55`, no live Telegram delivery。
- official dry-run unheld summary: `未持倉 7｜僅追蹤 7（等回測1/等量能6）`。

## 覆蓋層級
- helper: `tomorrow_watch_state` / `unheld_funnel_state` / reject reason。
- formatter: unheld card title and trigger wording。
- official generator: `generate_report(dry_run=True)` replay。
- runner artifact: not live delivered; runner path uses same committed generator after push。

## 殘留風險
- 這輪只重分類「仍有恢復可能」的未持倉候選；沒有把候選升成買點。
- 外部資料只用來校準交易語意，不作為新增資料源。
