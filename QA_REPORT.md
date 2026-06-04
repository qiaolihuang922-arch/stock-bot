# QA_REPORT:

## 測試範圍

- 任務：`future_30d_watch_live_readonly_sources_v20_4_46`，normal_patch / L2。
- 範圍：第 4 則 `【未來30日關注】` live readonly source 試行；不擴成 full pytest、production replay、backfill 或 live delivery。
- 可吸收 diff：`core/future_watch.py`、`core/generator.py`、`tests/test_generator_report.py`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md`、收口文件。
- 邊界：未做 DB read/write/backfill，未做 live Telegram。

## 風險預算與停止條件

- 風險 1：MOPS malformed / SPA / 安全頁被誤判成「無事件」或假法說會。停止條件：malformed MOPS 列出公司事件，或法說會段消失。
- 風險 2：第 4 則污染前三則或手機閱讀像交易建議。停止條件：前三則出現未來關注內容，或第 4 則出現可買、可準備、今日下單、新倉建議、停損、停利、即將崩盤、重演。
- 風險 3：新增 DB read/write 或 live Telegram path。停止條件：future-watch adapter 需要 DB client、write path、credential 或 live Telegram。

## 關聯風險掃描

- `live_mops_adapter()` 在無 rows / 欄位不可辨識時回 `source-error`，不是 available empty。
- `collect_mops_events()` 遇 adapter `source-error` 立即 fail closed。
- `format_future_watch_message()` 在 MOPS `source-error` 時輸出 `法說會提醒：source-error（MOPS），本次不列事件`。
- `generate_report()` 只把 `default_future_watch_sources(now)` 接進第 4 則 source 建立；未新增交易 decision、DB write 或 Telegram send。

## 跨區塊語意一致性

- QA probe 結果：`message_count=4`，前三則依序為持倉、未持倉、決策簡報，第 4 則為 `【未來30日關注】`。
- malformed MOPS table 沒有被列成 `2301 光寶科｜法人說明會`，而是顯示 `source-error（MOPS）`。
- 歷史類比保持 `無高相似崩盤樣本｜依據不足/相似度低｜source=TWSE`，未寫成崩盤預測。
- 全球事件只在第 4 則，不污染 summary / 漏斗 / 索引。

## 使用者誤讀風險

- 手機閱讀順序已檢查：前三則沒有未來關注段落；第 4 則只呈現關注 / 提醒 / source 狀態。
- 第 4 則未出現可買、可準備、今日下單、新倉建議、停損、停利、即將崩盤、重演。
- 殘留誤讀風險：global seed fallback 可見行仍顯示事件 source，不另外標 seed-fallback；本輪不阻塞，後續若要完全 live-only 可另開。

## 質疑與反證

- Focused tests：
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_46_live_future_watch arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_46_future or v20_4_46_live or v20_4_46_generate_report_appends_live' -q` -> 9 passed, 173 deselected。
- QA 補充 official message-list probe：
  - malformed MOPS HTML：`<table>...<td>-</td><td>2301 光寶科</td>...`
  - 結果：`qa_probe_pass message_count=4 malformed_mops=source-error first_three_clean=true no_db_client_requested=true`。
- Syntax / hygiene：
  - `py_compile core/future_watch.py core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
- DB / live Telegram 掃描：
  - `core/future_watch.py` 未見 DB write / Telegram send 入口。
  - 本輪未執行 live Telegram、未做 DB write/backfill。

## 未測項目

- 未跑 full pytest。
- 未跑 production runner artifact。
- 未做 live Telegram delivery。
- 未做 live production DB read/write smoke。
- 未驗真實 MOPS live 長期可解析；目前只驗 malformed / blocked fail closed 與 mock parsed rows。
- 未驗全球官方頁真實 HTML 改版後的全部 parser，只驗 mock live / fallback focused path。

## QA 結論

conditional pass。

產品行為對本輪核心風險通過：MOPS malformed table 會 source-error 並顯示法說會提醒段；第 4 則不污染前三則；QA probe 未觸發 DB client；未見新增 live Telegram / write path。conditional 原因是 QA runner 初次指出收口文件仍停在 v20.4.45；Architect 收口已更新 `DISPATCH.md` / `CURRENT_STATE.md` 後再進 completion gate。
