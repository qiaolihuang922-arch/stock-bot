# CHANGELOG: v20.4.39 Phase A 盤後未持倉普通 BUY 可準備不可買

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：使用者可見 Telegram 盤後 summary、未持倉漏斗、未持倉卡片語意調整；不改策略 decision、RR 公式、DB schema/write、production backfill 或 live Telegram。
- 版本：使用者可見報文版本同步為 `v20.4.39`。

## 修改內容

- 盤後未持倉 ordinary `BUY` 且仍需明日開盤後確認時，未持倉 funnel 改歸 `可準備`，卡片顯示 `🟡 明日準備｜不可買｜開盤後確認`。
- ordinary 盤後準備卡片買點行改為 `買點：尚未成立｜盤後僅追蹤｜明日開盤後確認｜不追價`，避免顯示 `40%倉`、`買點成立` 或立即可買語氣。
- ordinary 盤後準備卡片保留單檔回測輔助行，避免從卡片層遺失原報文中的回測資訊。
- 盤後 summary 在 prepare-only case 顯示 `新倉：無有效進場` 與 `可準備：...未確認前不可下單`；在 mixed trend_continuation + ordinary prepare case，actionable 計數納入 `趨勢延續`，不再用 `新倉：無有效進場` / `新增有效進場：無` 覆蓋 trend 小倉 BUY。
- 新增 official `formatTelegramMessages` mixed replay：一檔 `trend_continuation` 小倉 BUY + 一檔盤後 ordinary prepare，驗證 summary、漏斗、卡片一致。

## 修改檔案

- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 最小改動策略

- 只調整 official generator / presentation formatter 中未持倉盤後分類與 summary 分支。
- 測試只補 official `formatTelegramMessages` replay 與版本期待值，不新增 helper-only 假契約。
- 不改 RR 計算、策略核心買賣判斷、持倉風控、DB schema/write、runner 或 live delivery。

## 契約影響

- 使用者可見 header / 簡報版本為 `v20.4.39`。
- 盤後未持倉 ordinary `BUY` 在明日開盤後確認前，summary / 漏斗 / 卡片一致呈現為可準備不可買。
- `trend_continuation` 小倉 BUY 仍保留可行動路徑；mixed case 的 actionable count 包含 `趨勢延續`。
- 盤中有效 ordinary `BUY` 仍保留既有可買路徑。
- 函式回傳結構、DB payload、strategy decision payload 未變更。

## 直接消費者同步

- `presentation/report.py` 的盤後 summary brief 同步 `趨勢延續` actionable 計數與 ordinary prepare 提醒。
- `presentation/report.py` 的未持倉卡片同步 ordinary post-market prepare 文案與回測輔助行。
- `core/generator.py` 將 post-market ordinary BUY 判斷 helper 傳入 presentation deps，並同步未持倉 funnel / prepare count。
- `tests/test_generator_report.py` 覆蓋 official final message-list：盤中 BUY 保護、單一盤後 ordinary prepare、mixed trend + ordinary prepare。

## 未影響模組

- 未改 `services/analysis.py`。
- 未改 `core/condition_engine.py`。
- 未改 RR 公式與策略分數。
- 未改持倉狀態機。
- 未改 DB schema / RLS / grant / policy / role / index / constraint。
- 未改 DB write path。
- 未執行 production backfill、production write 或 live Telegram。

## 已跑自檢命令

- `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'test_v20_0_14_message_list_uses_single_report_phase_when_phase_drifts or test_v20_0_14_post_market_fixture_uses_next_day_plan_semantics or test_v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable' -q`：3 passed。
- `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'test_trend_continuation_official_report_has_separate_small_buy_bucket' -q`：1 passed。
- `PYTHONPYCACHEPREFIX=/private/tmp/v20_4_39_pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `git diff --check`：passed。

## 覆蓋層級

- official `formatTelegramMessages` final message-list replay。
- 覆蓋 summary / 未持倉漏斗 / 未持倉卡片三層。
- 未覆蓋 production runner artifact / live Telegram。

## 殘留風險

- 未跑 full pytest；本輪按 normal_patch 只跑 focused formatter / message-list contract。
- 未取 production runner artifact；驗證使用等價 official formatter replay。
- 既有報文中 `新增有效進場` 對 trend_continuation 仍沿用原 summary 詞彙；本輪只修正不要被 prepare-only 文案覆蓋，不重設整體命名。

## 旁支待辦

- 若 Owner 要把 trend_continuation 的盤後 summary 詞彙從 `新增有效進場` 細分成專用名稱，需另開報文命名任務。
