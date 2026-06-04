# QA_REPORT:

## 測試範圍

本輪任務 `telegram-unheld-gate-attribution-v20.4.40` 是 normal_patch / L2，QA 範圍控制在 `TASK.md` 指定的 official `formatTelegramMessages` / message-list replay 與 formatter 契約，不擴成 full pytest、production replay、DB/backfill 或 live Telegram。

已讀取並比對：

- `TASK.md`
- `CHANGELOG.md`
- `git status --short`
- `git diff --stat`
- `git diff -- CHANGELOG.md core/generator.py presentation/report.py tests/test_generator_report.py`
- 相關 formatter / generator 局部源碼

可吸收 diff：

- `CHANGELOG.md`
- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`

## 風險預算與停止條件

本輪最值得抓的風險：

1. 非可買未持倉卡片新增差距行後，被手機讀成推薦買入。
   - 驗證：沿 summary -> 未持倉列表 -> card 順序檢查 RR、HOT/source missing/LIMIT_LOCK 案例；檢查不可買卡無 `建議買入` / `可立即買`。
   - 停止條件：summary 說不可買但 card 顯示可買語氣，或不可買卡缺差距行。
2. gate attribution 錯因，尤其 `LIMIT_LOCK/AVOID + heat NORMAL` 誤顯 `heat NORMAL/需降溫`。
   - 驗證：Tech focused test + QA 補充 official replay。
   - 停止條件：`LIMIT_LOCK/AVOID+NORMAL` 顯示 `heat NORMAL` 或沒有開板回測 / 追高解除方向。
3. 版本與 handoff 文件錯輪。
   - 驗證：`CHANGELOG.md` diff 與版本掃描。
   - 停止條件：`CHANGELOG.md` 仍是 v20.4.39 Phase A，或使用者可見 header / constant 未升 v20.4.40。

## 關聯風險掃描

`TASK.md`、`CHANGELOG.md`、diff 大致一致：本輪只碰 Telegram 未持倉 card attribution、版本常量與 focused replay 測試；未看到策略 decision、RR 公式、DB schema/write、live delivery、runner/backfill 變更。

`presentation/report.py` 新增 `_unheld_buy_gap_line`，插入未持倉卡 buy_line 後。顯示條件排除 `valid_entry`、`funnel_state == "趨勢延續"`、`decision_type == "trend_continuation"`，符合真正可買與 trend continuation 小倉 BUY 不顯示差距的契約。

`core/generator.py` 只升 `VERSION` 到 `v20.4.40`。

`tests/test_generator_report.py` 新增 / 調整 focused official replay，覆蓋 RR不足、HOT、source missing、可買、trend continuation、LIMIT_LOCK/AVOID+NORMAL。

## 跨區塊語意一致性

Tech replay 通過：

- RR 案例：卡片仍是 `等RR修復｜RR不足`，顯示 `到達可買差距：RR 0.98/需>=1.5; 距突破 6%/需<=4%`。
- HOT 案例：卡片仍是 `等冷卻｜過熱觀察`，顯示 `heat HOT/需降溫`。
- source missing：卡片仍是不可行動，顯示 `missing-source/需可用`。
- 真正可買卡：不顯示 `到達可買差距`。
- `trend_continuation` 小倉 BUY：不顯示 `到達可買差距`。
- summary 保留可買 / 趨勢延續 / 僅追蹤 / 淘汰分組，不把 RR/HOT/source missing 寫成推薦。

QA 補充 replay：

- `LIMIT_LOCK + trade_state=AVOID + heat_state=NORMAL` 卡片為 `等回測｜漲停不追`，差距行為 `LIMIT_LOCK/需開板回測; RR 1.4/需>=1.5`，沒有 `heat NORMAL/需降溫`。
- Summary 首屏仍寫 `新倉：無有效進場`，手機閱讀順序未形成「summary 不可買、card 像推薦」衝突。

## 使用者誤讀風險

本輪主要手機誤讀風險已被覆蓋：不可買卡新增的是 `到達可買差距` 而不是下單建議；focused replay 明確檢查不可買卡不含 `建議買入` / `可立即買`。

殘留風險：QA 補充的相鄰案例 `trade_state=AVOID + heat_state=NORMAL + price_behavior=NORMAL` 會顯示 `等冷卻`，但差距行退成 `資料不足/需可用`，同卡下一步仍說過熱降溫且回測不破。這不是 TASK 指定五類主驗收，也不是 `LIMIT_LOCK/AVOID+NORMAL` 的開板回測路徑；後續若 Owner 要把所有 `AVOID+NORMAL` 都解釋為追高風險解除，需另開 gate attribution ranking / wording 任務。

## 質疑與反證

主動質疑 1：Tech 是否只驗 helper，而未打到使用者可見報文？

反證：新增測試與 QA 補充都走 `generator.formatTelegramMessages`，再取 summary / unheld message / card block 驗最終 Telegram message-list 文本。

主動質疑 2：`LIMIT_LOCK/AVOID+NORMAL` 是否仍被 heat gate 誤歸因？

反證：QA 補充 replay 實際卡片為 `到達可買差距：LIMIT_LOCK/需開板回測; RR 1.4/需>=1.5`，未出現 `heat NORMAL/需降溫`。

主動質疑 3：`CHANGELOG.md` 是否仍殘留 v20.4.39 Phase A？

反證：`CHANGELOG.md` 標題與內容已是 v20.4.40 gate attribution；diff 顯示 Phase A 舊內容被替換。版本掃描中 v20.4.39 僅出現在 `TASK.md` 的升版背景，不是本輪 `CHANGELOG.md` 殘留。

## 驗證命令

- `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_40_unheld_non_buy_cards_show_gate_attribution_only or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics' -q` -> 4 passed, 165 deselected。
- `PYTHONPYCACHEPREFIX=.qa_tmp/pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
- `git diff --check` -> passed。
- QA 補充 official replay：`LIMIT_LOCK + AVOID + heat NORMAL`，以及相鄰 `AVOID + heat NORMAL` 無 LIMIT 負面讀法。

## 未測項目

- 未跑 full pytest；本輪 L2 focused validation 足夠覆蓋指定 Telegram formatter/message-list 契約。
- 未跑 production runner artifact、read-only production smoke、DB read/write、backfill、live Telegram delivery。
- 未驗 gate ranking 的完整策略診斷最佳排序；TASK 明確列為旁支，不納入本輪。

## QA 結論

通過
