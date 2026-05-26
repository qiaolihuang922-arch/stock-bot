# QA_REPORT.md

本文件由 QA 維護，提交給 Architect。只記錄本輪 v20.0.1 L2 驗證結果。

## 任務狀態

- 狀態：QA 驗證完成
- 對應任務：`v20.0.1-evidence-readiness-message`
- 版本：`v20.0.1`
- QA 等級：`L2`
- 提交日期：2026-05-26
- 依據文件：`AGENTS.md`、`DISPATCH.md`、`CURRENT_STATE.md`、`TASK.md`、`CHANGELOG.md`、`RESEARCH.md`

## 測試範圍

本輪依 `qa_level=L2` 驗證 evidence readiness / friendly fallback：

- formatter / evidence fallback。
- Telegram summary-last / reply_markup-last contract。
- 策略不變性。
- 直接消費者：`generate_report()`、`formatTelegramMessages()`、`main.py -> send_many()`、`services.notifier.send_many()`。
- 負面案例：schema missing、generic DB failure、含 URL / token / Traceback 的 raw error、樣本不足。
- 跨區塊語意一致性與使用者誤讀風險。

未執行 full pytest、replay/backfill dry-run、production schema apply、live Supabase write、live Telegram delivery。

## 執行命令

```bash
.venv/bin/python -m pytest tests/test_strategy_evidence.py tests/test_generator_report.py tests/test_notifier.py
```

結果：

```text
44 passed, 21 warnings in 0.52s
```

```bash
.venv/bin/python -m pytest tests/test_analysis_engine.py tests/test_signal_validator.py
```

結果：

```text
33 passed in 0.03s
```

QA 補充 smoke：

```text
QA_L2_SMOKE_OK 3 290
```

## 測試結果

### Evidence Fallback

結果：通過。

已驗證 schema missing 類錯誤：

- raw error：`Could not find the table 'public.market_daily_bars' in the schema cache`
- Telegram 顯示：`策略證據尚未啟用：資料表未建立，主報文不受影響`
- 不顯示：
  - `Could not find the table`
  - `schema cache`
  - `public.market_daily_bars`
  - `{'message': ...}`

已驗證 generic DB failure 類錯誤：

- raw error 含 `Traceback`、URL、`apikey`、token-like 片段。
- Telegram 顯示：`證據層暫時略過：資料更新失敗，主報文不受影響`
- 不顯示 raw timeout、URL、token、Traceback 或 connection detail。

已驗證樣本不足：

- 查詢成功但樣本不足時，仍顯示 `樣本不足，不判讀`。
- 樣本不足不被顯示為 `更新失敗` 或 `暫時略過`。

### Telegram Contract

結果：通過。

- `formatTelegramMessages()` 仍回傳 messages list。
- `messages[-1]` 仍是總覽 summary。
- 主報文版本升為 `v20.0.1`。
- `📊 策略證據 v20.0` 區塊仍在最後 summary 段。
- `services.notifier.send_many()` mock 驗證 `reply_markup` 只綁最後 summary 段，前面詳情段不帶 `reply_markup`。
- schema missing readiness message 不會擠掉 `🧭 今日結論` 或 `✅ 明日執行清單`。

### 策略不變性

結果：通過。

- 策略不變性測試：`tests/test_analysis_engine.py`、`tests/test_signal_validator.py` 共 33 passed。
- `git diff` 未顯示下列檔案有本輪修改：
  - `services/analysis.py`
  - `core/signal_snapshot.py`
  - `core/signal_validator.py`
  - `services/daily_snapshot_store.py`
  - `services/signal_store.py`
  - `services/notifier.py`
  - `services/stock_api.py`
  - `scripts/dry_run_replay.py`
  - `scripts/backfill_signals.py`
  - `docs/v20_strategy_evidence_schema.sql`
- QA smoke 驗證加入 evidence readiness message 後，原始 payload 的 `decision=BUY`、`action=0.1`、`is_tradeable=True` 不變。

### 負面案例

結果：通過。

- 多張 evidence table 缺失類錯誤：歸類為 schema 未啟用，只顯示一條友善提示。
- Supabase schema cache error：歸類為 schema 未啟用，不露 raw error。
- generic timeout / network / URL 類錯誤：歸類為 DB 暫時失敗，不露 raw error。
- 樣本不足：維持樣本不足語意，不誤報 DB failure。
- 主報文仍正常保留今日結論與明日執行清單。

## 關聯風險掃描

直接呼叫方：

- `core/generator.generate_report()`：evidence record / summary load 的 exception 交由 `format_strategy_evidence_summary(error=...)` 清洗；主報文仍產生。
- `core/generator.formatTelegramMessages()`：仍接受可選 `strategy_evidence_summary`，summary-last 未回退。
- `main.py -> notifier.send_many()`：messages list + reply_markup 契約未變。
- `services.notifier.send_many()`：未修改，mock 驗證最後段帶 `reply_markup`。

下游與副作用：

- 本輪未 apply production schema。
- 本輪未正式寫 Supabase。
- 本輪未改 replay/backfill。
- 本輪未改交易策略或外部事件 ingestion。
- 若未來 Supabase table-missing error 格式大幅變化，可能落入 generic DB fallback；仍會顯示友善訊息，不會露 raw error。

## 跨區塊語意一致性

已檢查 Telegram summary 內部語意：

- `📊 策略證據 v20.0` 是 readiness / evidence 狀態，不覆蓋 `🧭 今日結論`。
- `策略證據尚未啟用：資料表未建立，主報文不受影響` 明確說明主策略照常執行。
- DB failure 文案使用 `暫時略過`，不暗示買賣判斷失效。
- 樣本不足仍是績效判讀不足，不是系統錯誤。
- `v20.0.1` 主報文版本與 `策略證據 v20.0` evidence foundation 名稱並存，語意可接受：前者是 patch 版本，後者是 evidence foundation 區塊名稱。

結論：未發現 evidence readiness 文案與今日結論、明日執行清單、交易動作之間互相矛盾。

## 使用者誤讀風險

已降低：

- 不再把 Supabase raw dict / schema cache / table name dump 到 Telegram。
- 使用者能看懂是「策略證據尚未啟用」，不是主策略壞掉。
- 文案明確包含 `主報文不受影響`，降低誤以為今日策略不可用的風險。
- generic DB failure 不暴露 URL / token / internal connection detail。

殘留風險：

- `📊 策略證據 v20.0` 標題仍是 v20.0，而報文版本是 v20.0.1；Tech 已在 `CHANGELOG.md` 標為風險點。QA 判斷不阻塞，因它代表 evidence foundation 區塊，不是主報文版本。
- 若 Owner 期待立即啟用 evidence DB，friendly message 只能說明狀態，不能替代 production schema apply 任務。

## 質疑與反證

### PM 是否漏需求

未見關鍵漏需求。`TASK.md` 已明確定義 schema missing、generic DB failure、insufficient sample 三種狀態，以及 raw error 不得顯示的禁止項。

### Tech 是否漏同步

未見阻塞級漏同步。`CHANGELOG.md` 宣稱只改 `core/generator.py`、`services/strategy_evidence.py` 與 tests；實際 diff 符合。未影響模組中的 strategy、notifier、schema、replay/backfill 未見 diff。

### 測試是否能證明沒有破壞直接消費者

可以覆蓋本輪主要直接消費者：

- formatter / evidence fallback tests 通過。
- notifier contract tests 通過。
- QA smoke 直接將 messages list 餵給 `send_many()` mock，確認 `reply_markup` 仍綁最後 summary 段。
- 策略不變性 tests 通過。

未覆蓋 live Telegram delivery，但本輪 L2 不要求 live delivery，且 `AGENTS.md` 明確 live delivery 需另行批准。

### QA 是否主動找到指定清單之外的風險

有。除指定清單外，QA 額外檢查：

- raw error 含 URL、`apikey`、token-like 片段與 Traceback 時不會洩漏。
- 樣本不足不會誤報成 `更新失敗`。
- evidence readiness message 不會擠掉今日結論與明日執行清單。
- 主版本 `v20.0.1` 與 evidence 區塊 `v20.0` 的語意是否可能混淆。

## 驗收項結果

- `version_level=patch`：通過。
- `qa_level=L2`：通過。
- Schema 未啟用顯示 friendly readiness message：通過。
- Schema 未啟用不顯示 `Could not find the table`：通過。
- Schema 未啟用不顯示 `schema cache`：通過。
- Schema 未啟用不顯示 raw dict：通過。
- Generic DB failure 顯示友善降級訊息：通過。
- DB failure 主報文仍正常產生：通過。
- 樣本不足顯示 `樣本不足` / `樣本不足，不判讀`：通過。
- 樣本不足不顯示為 `更新失敗`：通過。
- 正常 evidence summary 格式未回退：通過既有測試。
- `messages[-1]` summary-last：通過。
- `reply_markup` last summary：通過。
- 不改 BUY / SELL / `is_tradeable` / `action`：通過。
- 不 apply production schema、不正式寫庫：通過。
- 覆蓋 schema missing、generic DB failure、insufficient sample 三種情境：通過。

## 未測項目

本輪未測：

- full pytest。
- replay / backfill dry-run。
- production schema apply。
- live Supabase write。
- live Telegram delivery。
- TWSE live replay / live backfill。

原因：

- `DISPATCH.md` 指定 `qa_level=L2`。
- `TASK.md` 明確本輪只改 readiness / friendly fallback，不改 replay/backfill、schema、live write。
- production schema apply、live Supabase write、live Telegram delivery 需 Owner 另開明確批准流程。

## 殘留風險

- Production evidence schema 尚未 apply，Telegram 仍會顯示「策略證據尚未啟用」，這是本輪預期狀態。
- Supabase 未來若改變 table-missing 錯誤文字，可能降級成 generic DB failure；仍不會露 raw error。
- 真實 Telegram 客戶端未測，但 formatter + notifier contract 已覆蓋本輪主要契約。

## QA 結論

QA 結論：通過。

v20.0.1 Evidence Readiness Message 已通過 L2 驗證。Telegram 不再暴露 Supabase raw dict / schema cache / table missing 細節；schema 未啟用、generic DB failure、樣本不足三種狀態均有可讀文案；主報文、summary-last、reply_markup-last 與策略不變性未回退。

可交回 Architect 更新狀態。production schema apply、live Supabase write、live Telegram delivery 仍需另開明確批准流程。
