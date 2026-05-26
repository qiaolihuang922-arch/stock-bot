# CHANGELOG:

## 修改內容

- 主報文版本升至 `v20.0.6`。
- 修正 Telegram summary / 明日執行清單的時間語意：
  - 盤後 / 收盤 / 非盤中報文使用 `盤後結論`；盤中報文保留 `今日結論`。
  - 持倉改用 `盤後持倉檢視：N 檔`、`持倉 N 檔先檢視`。
  - 不再產生 `今日可執行：持倉 N` 類文案。
- 未持倉高層分類改為分開顯示：
  - `可買`
  - `準備`
  - `僅追蹤`
  - `冷卻`
  - `回測`
  - `RR`
  - `量能`
  - `淘汰`
- 淘汰標的降噪：
  - Summary / 明日執行清單 / 詳情索引只保留淘汰數量、主因與見詳情入口。
  - 淘汰明細卡保留完整股票與原因，`旺宏` 作為淘汰標的仍可追溯。
  - 淘汰標的不列入可買、準備、僅追蹤或明日行動項。
  - 補強 `best=旺宏` 但 `旺宏=淘汰` 的 formatter 防護；若上游誤傳非有效買點為 `best`，高層 `🔥 最強` 顯示 `無有效進場標的`，不重新曝光為推薦語氣。
- 策略證據查詢效能收斂：
  - `load_strategy_evidence_summary()` 對三張 evidence table 加上 `order("trade_date", desc=True)` 與 `limit()`，避免每次拉全表後本地 slicing。
  - `record_strategy_evidence()` 支援注入既有 Supabase client。
  - `generate_report()` 同一 run 內 record evidence 與 load summary 共用同一 Supabase client，避免重複建立 client。
  - 補強 `load_strategy_evidence_summary()` order -> limit -> execute 後，下游 summary 使用最新 audit row 的契約測試，避免反向排序誤導分類警示。

## 修改檔案

- `core/generator.py`
- `services/strategy_evidence.py`
- `tests/test_generator_report.py`
- `tests/test_strategy_evidence.py`
- `CHANGELOG.md`

## 契約影響

- Telegram message list 數量與 `formatTelegramMessages()` 回傳型態未改。
- Telegram summary 文字契約有變更：
  - 版本：`v20.0.6`。
  - 非盤中 summary 結論標籤由 `今日結論` 改為 `盤後結論`；盤中仍是 `今日結論`。
  - `明日執行清單` 內改用盤後 / 明日語境。
  - 未持倉漏斗與詳情索引新增冷卻 / 回測分離欄位。
  - 淘汰高層行改為 `淘汰 N｜主因：...｜詳情見淘汰分組`，不再列淘汰股票名。
  - `🔥 最強` 僅顯示 `is_valid_entry()` 通過的有效買點；淘汰 / 等待 / 追蹤標的即使被傳入 `best` 也不顯示股票名。
- `services.strategy_evidence.record_strategy_evidence()` public helper 新增 optional `client=None` 參數；既有呼叫方不傳參時行為不變。
- DB schema、DB payload、Supabase upsert rows、策略 decision、watchlist、Telegram payload 發送入口未改。

## 直接消費者同步

- `core/generator.generate_report()` 已同步使用 `record_strategy_evidence(..., client=evidence_client)`，並把同一 client 傳給 `load_strategy_evidence_summary()`。
- `core/generator.formatTelegramSummary()` 直接消費 `best_stock_text()`；已同步防護淘汰 / 非有效買點的 `best` 不會進入 `🔥 最強` 股票名。
- `tests/test_generator_report.py` 已同步 formatter snapshot / contract，覆蓋手機長報文、淘汰降噪、冷卻 / 回測分離、明日清單語境、`best=旺宏且旺宏=淘汰` 負面案例與 `v20.0.6`。
- `tests/test_strategy_evidence.py` 已新增查詢 `order/limit`、order -> limit -> execute 順序、下游 summary 最新 audit row 顯示與 injected client reuse 測試。
- `services/notifier.py` message list 消費契約未變；已用 notifier 測試確認不需同步代碼。

## 未影響模組

- `services/analysis.py` 策略 decision、分數、買賣判斷未改。
- `services/signal_store.py`、`services/daily_snapshot_store.py` DB payload 未改。
- `core/watchlist.py` 未改。
- live Telegram delivery 未執行、未修改。
- live Supabase write 未執行；測試只用命令列注入 dummy `config` module。
- replay / backfill write path 未改，未執行正式 replay / backfill。

## 已跑自檢命令

- `.venv/bin/python -m pytest tests/test_generator_report.py tests/test_strategy_evidence.py -q`
  - 結果：blocked by environment，x86_64 Python 載入 arm64 `pydantic_core` 失敗。
- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_strategy_evidence.py -q`
  - 結果：blocked by environment，缺少 `config` module。
- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_generator_report.py", "tests/test_strategy_evidence.py", "-q"]))'`
  - 結果：`46 passed, 21 warnings`
- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; m.TOKEN="dummy-token"; m.CHAT_ID="dummy-chat"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_analysis_engine.py", "tests/test_notifier.py", "-q"]))'`
  - 結果：`29 passed`
- `arch -arm64 .venv/bin/python -c 'import sys, types, pytest; m=types.ModuleType("config"); m.SUPABASE_URL="https://example.supabase.co"; m.SUPABASE_KEY="dummy-key"; m.SUPABASE_SERVICE_ROLE_KEY="dummy-key"; m.TOKEN="dummy-token"; m.CHAT_ID="dummy-chat"; sys.modules["config"]=m; raise SystemExit(pytest.main(["tests/test_generator_report.py", "tests/test_strategy_evidence.py", "tests/test_analysis_engine.py", "tests/test_notifier.py", "-q"]))'`
  - 結果：`75 passed, 21 warnings`

## 殘留風險

- 本地未量測真實 production 秒數；本輪以 fake client 測試證明 evidence summary 查詢改為 DB 端 order / limit，並消除同 run 重複建立 Supabase client。
- `.venv` 預設執行會因架構不一致失敗；自檢需用 `arch -arm64` 才能載入目前環境的 compiled dependency。
- 未執行 full pytest、live Telegram、live Supabase write、正式 replay/backfill；依本輪 Tech 邊界保留給 QA / Architect 決定。
