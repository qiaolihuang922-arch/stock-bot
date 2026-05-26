# CHANGELOG:

## 修改內容

- 修復 Telegram 短報文 `未持倉漏斗（非執行）` 的數量誤讀：
  - 改為先顯示 `未持倉總數 N 檔`。
  - 第二行只列同層母集合：`可買 / 可準備 / 僅追蹤 / 淘汰`。
  - 第三行明確標示 `其中僅追蹤 N 檔拆分`，拆 `等冷卻 / 等回測 / 等RR修復 / 等量能`。
  - 第四行補 `非執行追蹤合計 N 檔（可準備 + 僅追蹤）`，避免 `可準備 > 0` 時把 `其中` 誤讀成非執行追蹤總數拆分。
- `等冷卻` 在短報文漏斗中維持獨立子分類，不再併入 `等回測`。
- 補上 `可準備 1 + 僅追蹤 3` 的 formatter 回歸測試，確認 `其中` 的母集合是 `僅追蹤 3`，不是 `非執行追蹤 4`。
- 更新既有短報文測試，覆蓋 12 檔 watchlist、5 檔持倉、7 檔未持倉案例：`未持倉總數 7`、`僅追蹤 6`、`淘汰 1`，且追蹤子分類合計為 6。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 契約影響

- Telegram summary 文字契約有變更：`未持倉漏斗（非執行）` 由單行 pipe 並列改為多行總數 / 同層母集合 / 子分類拆分 / 非執行追蹤合計格式。
- `format_unheld_funnel()` 仍回傳字串，回傳型態未改；字串內容改為多行。
- `formatTelegramMessages()` 回傳的 message list 外層結構未改；測試仍覆蓋 3 則訊息路徑。
- `等冷卻` 從漏斗子分類與未持倉排序中獨立於 `等回測` 顯示；這是使用者可見文字與卡片排序的 formatter 層變更，不改策略判斷。
- Telegram payload 外層結構、DB payload、策略 decision、watchlist、行情來源未改。

## 直接消費者同步

- `formatTelegramSummary()` 直接消費 `format_unheld_funnel()`，已同步輸出新的多行漏斗文字。
- `formatTelegramMessages()` 直接消費 summary message；已用 `tests/test_generator_report.py` 覆蓋 message list 與 summary 內容。
- `tests/test_generator_report.py` 已同步 formatter snapshot / contract，包含：
  - 12 檔 watchlist、已持倉 5 / 未持倉 7 的手機誤讀回歸案例。
  - `可準備 > 0` 時 `非執行追蹤合計` 與 `其中僅追蹤` 母集合分離案例。
- `tests/test_notifier.py` 已重跑，確認 Telegram notifier 消費 message list 的路徑不需同步代碼。

## 未影響模組

- `services/analysis.py` 策略判斷、分數、買賣規則未改。
- `core/condition_engine.py` 條件映射未改。
- `core/watchlist.py` 與 12 檔清單未改。
- `services/signal_store.py`、`services/daily_snapshot_store.py` DB 寫入未改。
- live Telegram delivery 未執行。
- live Supabase write 未執行。
- replay / backfill 流程與正式寫入未改、未執行。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; m.TOKEN="dummy-token"; m.CHAT_ID="dummy-chat"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_generator_report.py", "-q"]))'`
  - 結果：`35 passed, 21 warnings`
- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; m.TOKEN="dummy-token"; m.CHAT_ID="dummy-chat"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_generator_report.py", "tests/test_notifier.py", "-q"]))'`
  - 結果：`37 passed, 21 warnings`

## 殘留風險

- 本輪只做 Tech 最小自檢，未宣告 QA 通過。
- 未執行 full pytest、live Telegram、live Supabase write、正式 replay/backfill；依 TASK 與 Tech 邊界未執行。
- 短報文漏斗文字契約已改為多行，仍需 QA 以手機閱讀路徑驗證最終視覺可讀性。
