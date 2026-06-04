# QA_REPORT:

## 測試範圍

本輪任務 `phase_a_after_close_unheld_buy_prepare_v20_4_39` 為 normal_patch / QA L2。驗收聚焦 official `formatTelegramMessages` message-list、summary、未持倉漏斗、未持倉卡片，不擴大到 full pytest、production runner artifact、backfill 或 live Telegram。

已檢查：

- `TASK.md` / `CHANGELOG.md` / `git diff` 一致。
- 可吸收 diff：`CHANGELOG.md`、`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`。
- worktree 殘留：同上 4 個 modified tracked files；未發現其他 tracked 殘留。QA 未修改 tracked file。

## 風險預算與停止條件

本輪最值得抓的風險：

1. 盤後 ordinary BUY 只改卡片、summary / 漏斗仍像可買。
   - 驗證：focused official replay 與 QA 自補 explicit `report_phase='盤後'` probe。
   - 停止條件：summary 出現光寶科可買、新倉建議指向 ordinary prepare、卡片出現 `40%倉` / `買點成立`。
2. mixed 盤後同時有 trend 小倉 BUY + ordinary prepare 時，summary 誤寫 `新倉：無有效進場` 或 `新增有效進場：無`。
   - 驗證：Tech mixed test + QA 自補 direct consumer probe。
   - 停止條件：trend card 可行動但 summary 第一屏說無有效進場。
3. ordinary prepare 保留回測行、但盤中 ordinary BUY 與 `trend_continuation` 不被全域降級。
   - 驗證：盤中 BUY 保護 test、trend official bucket test、QA probe 檢查 ordinary prepare card 含回測行。
   - 停止條件：盤中 BUY 或 trend BUY 被降為不可買，或 ordinary prepare 卡片缺回測行。

## 關聯風險掃描

diff 顯示 `core/generator.py` 新增 `post_market_unheld_buy_requires_open_confirmation()`，條件為非盤中 report phase、valid entry、且非 `trend_continuation`；符合「ordinary post-market prepare 降級，不全域降級 BUY」邊界。

`presentation/report.py` 同步 summary / afterhours brief / card title / buy line / backtest line。`tests/test_generator_report.py` 補 official final message-list replay，覆蓋單一 ordinary prepare、mixed trend + prepare、盤中 BUY 保護與版本 `v20.4.39`。

未發現 DB schema/write、RR 公式、策略核心 decision、live delivery 相關 diff。

## 跨區塊語意一致性

通過。驗證結果支持：

- ordinary post-market prepare：summary 有 `新倉：無有效進場`、`可準備：1 檔需明日開盤後確認，未確認前不可下單`；漏斗為可準備；卡片為 `🟡 明日準備｜不可買｜開盤後確認`。
- 卡片買點行改為 `買點：尚未成立｜盤後僅追蹤｜明日開盤後確認｜不追價`，未見 `40%倉` / `買點成立`。
- mixed trend + ordinary prepare：summary 保留 trend 小倉可行動，未同時出現 `新倉：無有效進場` / `新增有效進場：無`。
- 使用者可見版本為 `v20.4.39`。

## 使用者誤讀風險

按手機閱讀順序檢查：

- summary 第一屏不會把 ordinary prepare 讀成今日可買或明日必買。
- mixed case summary 第一屏仍可讀到 trend 小倉 BUY 是可行動，不被 ordinary prepare-only 文案覆蓋。
- 未持倉卡片標題與買點行不再給 ordinary prepare `40%倉`、`買點成立` 或可立即下單語氣。
- 殘留風險：mixed case 仍使用 `新增有效進場：1 檔需明日開盤前確認` 描述 `trend_continuation`；`CHANGELOG.md` 已標旁支，非本輪 blocker。

## 質疑與反證

執行命令：

- `pytest tests/test_generator_report.py -k 'test_v20_0_14_message_list_uses_single_report_phase_when_phase_drifts or test_v20_0_14_post_market_fixture_uses_next_day_plan_semantics or test_v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable' -q`：3 passed。
- `pytest tests/test_generator_report.py -k 'test_trend_continuation_official_report_has_separate_small_buy_bucket' -q`：1 passed。
- `PYTHONPYCACHEPREFIX=.qa_tmp/pycache python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `git diff --check`：passed。
- QA 自補 probe：explicit `report_phase='盤後'` 的 mixed official message-list，確認 trend actionable、ordinary prepare 不可買、ordinary prepare card 保留回測行：passed。

第一次 py_compile 未設 `PYTHONPYCACHEPREFIX` 時因 sandbox 無法寫入使用者 cache 失敗；改用 `.qa_tmp/pycache` 後通過，非程式語法錯誤。

## 未測項目

- 未跑 full pytest，符合 normal_patch / L2 風險預算。
- 未取 production runner artifact。
- 未做 production DB read/write、backfill 或 live Telegram。
- 未重新命名 `trend_continuation` 的 `新增有效進場` summary 詞彙，列為旁支風險。

## QA 結論

通過
