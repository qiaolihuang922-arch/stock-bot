# QA_REPORT:

## 測試範圍

- 任務：telegram_future_30d_watch_v20_4_45，TASK 為 minor / L3；本輪驗證聚焦官方 `generate_report` message-list、第 4 則 future watch、手機閱讀順序與 fail-closed，不擴成 full pytest / replay / backfill。
- 讀取：`TASK.md`、`CHANGELOG.md`、`git status --short`、`git diff`、`core/future_watch.py`、`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`。
- 可吸收 diff：`CHANGELOG.md`、`core/future_watch.py`、`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`，均屬本輪 future-watch / version / test 範圍。
- worktree 殘留：`git status --short` 只顯示上述 5 個 tracked path；未看到無關 tracked 殘留。

## 風險預算與停止條件

- 風險 1：第 4 則混入前三則或改變手機閱讀順序。驗證：official `generate_report(dry_run=True)` 與 focused tests 檢查 4 則順序。停止條件：前三則含 `【未來30日關注】`、全球事件、法說會提醒 即阻塞。
- 風險 2：預設全球事件 seed 顯示超量、無官方 source、日期區間錯誤，導致 06/18 或 06/25 擠入前 5 筆。驗證：focused tests + QA probe 檢查 5 lines、source、排序與 label。停止條件：超過 5 筆、缺 source、06/18/06/25 出現即阻塞。
- 風險 3：MOPS / 歷史類比資料不足時假造事件或把未來關注讀成今日可下單。驗證：fail-closed test + 手機閱讀 forbidden words probe。停止條件：出現假 MOPS、崩盤預測字眼、可買/可準備/可下單/今日下單 進入第 4 則即阻塞。

## 關聯風險掃描

- `core/generator.py` 將 `VERSION` 升為 `v20.4.45`，`generate_report()` 預設注入 `default_future_watch_sources()`；未見買賣、加減碼、停損停利或 DB write path 變更。
- `presentation/report.py` 只在既有 3 則後 append `future_watch_message`；`include_detail` 仍於其後追加 detail，未重排前三則。
- `core/future_watch.py` 預設 MOPS adapter 為 fail-closed，歷史類比預設 insufficient-data，全球事件為固定官方 seed snapshot。
- 清理 / 瘦身 / refactor 證據表要求不適用，本輪不是清理任務。

## 跨區塊語意一致性

- `TASK.md` 要求第 4 則可選追加、不污染前三則；`CHANGELOG.md` 宣告相同，diff 實作符合 append-only。
- TASK 原尺寸 minor / L3，CHANGELOG 寫本輪 Re-Tech 為 normal_patch；QA 視為修補範圍說明，不降低 QA 驗證口徑，仍按 L3 使用者可見路徑驗證。
- 第 4 則區塊順序已反證：歷史類比 -> 法說會提醒 -> 全球事件。
- 版本一致：`generator.VERSION == v20.4.45`，focused tests 覆蓋 header / evidence version 更新。

## 使用者誤讀風險

- QA 額外 probe 直接跑 official `generate_report(dry_run=True)`：回傳 4 則，前三則分別為持倉、未持倉、決策簡報，第 4 則才是 `【未來30日關注】`。
- 第 4 則未出現 可買、可準備、新倉建議、今日下單、可下單、即將崩盤、重演。
- MOPS 顯示 `法說會提醒：source-error（MOPS），本次不列事件`；歷史類比顯示 `無高相似崩盤樣本｜依據不足/相似度低`，不會被讀成今天交易指令。

## 質疑與反證

- Tech 自檢不是唯一證據：QA 另補 official consumer probe，檢查 `generate_report` 預設 message-list 的手機閱讀順序、前三則污染、future watch forbidden wording、global event 前 5 筆。
- focused tests：
  - `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_45_future' -q` -> 3 passed。
  - `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_45' -q` -> 4 passed。
  - `arch -arm64 ./.venv/bin/python -m py_compile core/future_watch.py core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
- QA probe 結果：`QA_PROBE_OK`；`message_count 4`；`future_watch_global_lines 5`；第 4 則首行 `【06/04 未來30日關注｜v20.4.45】`。
- 預設全球事件前 5 筆為 06/10-11 ECB、06/10 CPI、06/15-16 BOJ、06/15-17 G7、06/16-17 Fed；06/18 BoE 與 06/25 BEA 未因 seed 超量顯示。

## 未測項目

- 未跑 full pytest，避免把本輪驗證擴成全專案。
- 未跑 live Telegram delivery、production DB read/write、正式 runner artifact。
- 未驗 live official global adapters、live MOPS adapter、historical analogy official timeline source；本輪 diff 也明確維持 MOPS / history fail-closed。
- 未驗官方來源是否在未來改期；目前只驗 2026-06-04 起 30 日固定 seed snapshot 的輸出契約。

## QA 結論

通過
