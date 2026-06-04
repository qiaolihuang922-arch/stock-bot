# DISPATCH.md

依 `AGENTS.md` 啟動順序閱讀；本文件只保留任務看板、handoff 指針與固定啟動命令。

- task_md_holds: `recently_done`
- task_md_task_id: `telegram_future_30d_watch_v20_4_45`
- task_md_note: `TASK.md / CHANGELOG.md / QA_REPORT.md 目前是最近完成任務的滾動 handoff，不代表仍在 Tech/QA。`

## Active

- none

## Queued

- none

## Recently Done

- `v20.4.45`｜`telegram_future_30d_watch_v20_4_45`｜minor/L3｜新增可選第 4 則 Telegram `【未來30日關注】`，由 `generate_report()` 預設追加在持倉 / 未持倉 / 決策簡報三則之後，不污染前三則；區塊固定為 `歷史類比`、`法說會提醒`、`全球事件`。歷史類比在資料不足時顯示 `無高相似崩盤樣本｜依據不足/相似度低`；MOPS 法說會 adapter 維持 fail-closed 並明示 source-error；全球事件預設加入 2026-06-04 起 30 日官方日程 seed/snapshot，最多顯示 5 筆，支援 `06/10-11`、`06/15-16` 等多日區間 label，前 5 筆為 ECB、CPI、BOJ、G7、Fed，06/18 BoE / 06/25 BEA 因 max 5 不顯示。focused tests v20.4.45 4 passed、future slice 3 passed、py_compile / diff check passed；QA 補 official `generate_report(dry_run=True)` 手機閱讀 probe，確認 4 則順序、前三則無污染、第 4 則無可買 / 可下單 / 崩盤預測語意，QA `通過`。未改交易策略、RR、持倉風控、DB schema/write、live Telegram；live official adapters / MOPS / historical timeline source 仍是後續任務。
- `v20.4.44`｜`telegram_card_evidence_wording_v20_4_44`｜normal_patch｜只改 Telegram 卡片顯示語意：證據鏈不再把 `決策證據：來源可追溯` 當交易依據外露，不顯示 raw `hard stop` / `持倉硬風控` / `既有買點與倉位規則通過`；未持倉非可買卡維持 `卡關主因` / `量化差距`，新增更清楚的 `解鎖` / `依據`，有可信數字時優先顯示 RR、距突破、熱度、警戒/停損距離，沒有數字才寫事件型 blocker；光寶科類 prepare 改 `買點：明日準備｜不可下單`、`卡關主因：開盤確認未完成`、`量化差距：盤後待開盤確認`、`解鎖：明日開盤後仍守突破區 / 不追價`；建準類持倉觀察不刷 generic evidence，停損/減碼持倉顯示人話風險與距警戒/停損距離；QA `通過`，core 4 passed、wide regression 14 passed、QA-only mobile replay passed、py_compile / diff check passed；未改策略 decision、RR、heat/breakout 判定、DB/write、live Telegram。
- `v20.4.43`｜`evidence_chain_decision_layers_v20_4_43`｜risk_patch｜保留 v20.4.42 卡片顯示風格，新增每檔 `decision_judgment` evidence-chain 聚合與 `決策證據：...` reason slot；`stock.*.decision_judgment` / `report_context["stock_judgments"]` 可追溯 eligibility、evidence_status、blocking/progress reasons；RR不足、過熱/EXTREME、突破失敗、source missing/error/conflict、量能、追高/漲停、持倉 hard stop 等 hard gates 會讓 judgment / summary / funnel / card 同步 fail closed，不再只做文字說明；低 RR `trend_continuation` 降 `等RR修復` 並保留 `卡關主因` / `量化差距`；focused official replay 14 passed、py_compile / diff check passed、混合 direct consumer probe passed；QA `conditional pass`，原因是正式 QA runner 遇 Codex usage limit，但本地 official message-list 反證通過；未改 RR 公式、strategy threshold、DB schema/write、live Telegram。
- `v20.4.42`｜`pm-20260604-v20.4.42-unheld-attribution-readable-gap`｜normal_patch｜未持倉非可買卡片 attribution 由單行 `到達可買差距` 改為兩行 `卡關主因` / `量化差距`：RR不足顯示 RR 現值、門檻與差值；距突破 >4% 顯示差值，<=4% 不列；過熱 / Lv.3、盤後待確認、突破失敗、資料來源缺失、策略樣本、漲跌停鎖定、弱反彈皆人話化；真正可買與 `trend_continuation` 小倉 BUY 不顯示卡關兩行；版本升 `v20.4.42`，tests current-version `v20.4.41` 殘留已清空；focused official replay 12 passed、py_compile / diff check passed、QA `通過`；未改策略、RR、can_buy/is_valid_entry、持倉、DB、live Telegram。
- `v20.4.41`｜`v20.4.41-post-market-unheld-gate-attribution-readability`｜tiny_patch｜盤後未持倉 gate attribution 可讀性修正：真正可買與 `trend_continuation` 小倉 BUY 不顯示 `到達可買差距`；未達可買卡仍顯示可信差距；`FAILED_BREAKOUT` 只顯示 `突破失敗/需重新轉強` 且不顯示假 RR 0；盤後 ordinary prepare 顯示 `盤後訊號/需開盤後重新確認` 與 `盤後待確認` 原因；`EXTREME/HOT` 冷卻前只顯示極熱 / 過熱主因；`LIMIT_LOCK/LIMIT_REBOUND/WEAK_REBOUND` 人話化；QA 曾抓到 `距突破 2%/需<=4%` 已達標仍被列為差距，已修為距離 >4 才列入 gap；focused official message-list replay 4 passed、py_compile / diff check passed、QA `通過`；未改策略、RR、can_buy/is_valid_entry、DB、live Telegram。
- `v20.4.40`｜`telegram-unheld-gate-attribution-v20.4.40`｜normal_patch｜未持倉非可買卡片新增 `到達可買差距` 單行 gate attribution，最多顯示 1-3 個可信阻擋條件，例如 RR、heat、source、突破距離、entry quality、LIMIT_LOCK；真正 `可買` 與 `trend_continuation` 小倉 BUY 不顯示差距行；修正 QA 抓到的 `LIMIT_LOCK/AVOID + heat NORMAL` 不再誤顯 `heat NORMAL/需降溫`，改以開板回測 / 追高風險解除方向呈現；focused official message-list replay 4 passed、py_compile / diff check passed、QA `通過`；未改 RR 公式、strategy decision、can_buy/is_valid_entry、DB schema/write、live Telegram。
- `v20.4.39`｜`phase_a_after_close_unheld_buy_prepare_v20_4_39`｜normal_patch｜Phase A 盤後未持倉 ordinary BUY 改為 `可準備（不可買）`：光寶科類需明日開盤後確認的候選不再在 summary / 漏斗 / 卡片顯示 `新倉建議`、`可買`、`40%倉`、`買點成立` 或 `新增有效進場`；卡片改 `🟡 明日準備｜不可買｜開盤後確認` 與 `買點：尚未成立｜盤後僅追蹤｜明日開盤後確認｜不追價`，RR / 技術 / 單檔回測仍保留；mixed 盤後 trend_continuation 小倉 BUY + ordinary prepare 不再被 prepare-only summary 覆蓋，盤中 ordinary BUY 與 trend_continuation 既有可行動路徑未回退；focused message-list tests 4 passed、py_compile / diff check passed、QA `通過`；未改 RR 公式、strategy decision、DB schema/write、live Telegram。
- `20260604_144316_6186_online_research_pair`｜research｜完成「條件性放寬」策略寬度研究：結論不是全域放寬，而是拆成 `可準備（不可買）`、`趨勢延續小倉<=15%`、一般 `可買` 三層；RR不足未解除、HOT/EXTREME、漲停/弱反彈、突破失敗、source-error 不得被 evidence 覆蓋；建議若進開發先做 Phase A `可準備` / gate attribution，不新增 BUY；詳見 `RESEARCH.md`。
- `v20.4.38`｜`fix-v20-4-37-rr-insufficient-message-readability`｜normal_patch｜修復 RR不足 / 等RR修復 報文誤讀：光寶科類卡片不再把 RR不足寫成 `證據：資料不足`，改為 `原因：RR不足，等待RR修復`；summary 回測摘要排除僅追蹤 / 等RR修復標的，不再顯示 `回測（光寶科）`，但保留建準候選回測；版本升 `v20.4.38`；official message-list replay 4 passed、py_compile / diff check passed、QA 補 formatter probe `通過`；未改 RR 公式、strategy decision、DB schema/write、live Telegram；git completion gate passed。
- `v20.4.37`｜`2026-06-04-v20.4.37-generate-mobile-consistency`｜normal_patch｜升版修復 06/04 真實 `generate()` 報文跨區塊一致性：首屏未持倉括號改吃同源 prepare bucket，`不可追高觀察 1` 不再漏於首屏；今日已買改為 `今日已買 N（已風控 M/觀察 K）`，移除不可追溯 `風控中`；未持倉回測取消跨股票聚合，改單檔 `回測（建準）` / `回測（緯創）`；actual `generate()` 已輸出 `v20.4.37` 且首屏 / 漏斗 / 索引合計一致；focused tests 4 passed、py_compile passed、QA 補 final message-list parser `通過`；未改策略 decision、RR、DB schema/write、live Telegram；未跑 production runner artifact。
- `bbee321`｜`v20_4_36_0604_report_readability_convergence`｜normal_patch｜收斂 06/04 v20.4.36 手機閱讀誤讀：正常資料行與普通 cross-day 歷史不再逐卡刷屏；未持倉原因優先級改為風控/淘汰優先於過熱，量能不足顯示 `量能不適用`；建準可買但回測偏弱時同卡補 `回測僅輔助，分批小倉、不追價`；首屏 `今日新建倉 3` 改為 `今日已買 N｜風控中 M`；official message-list replay 9 passed、py_compile / diff check passed；QA `通過`；未改 RR 公式、strategy decision、DB schema/write、live Telegram，版本維持 `v20.4.36`。
- `900d107`｜`trend_continuation_buy_path_phase2_20260603`｜major/risk_patch｜Owner 授權只在 trend_continuation 路徑放開「證據可開 BUY」邊界；新增回踩站回同源判定、positive evidence gate、`decision_type="trend_continuation"` / `trend_observation`、小倉 `<=15%`、回踩低點下方止損、5 日 edge 退出；official report 新增 `🟢 趨勢延續買入｜小倉` 與獨立 funnel，版本升 `v20.4.36`；資料依據在 trend_continuation BUY 時強制顯示同源策略樣本與候選資料 basis，避免 BUY 卡缺證據鏈；focused tests 6 passed、py_compile / diff check passed；QA `通過`；未改 RR 公式、DB schema/write、live Telegram。
- `9eea5c4`｜`trend_continuation_v20_4_36_validation_monitor_report_noise_20260603`｜mixed_patch｜補 v20.4.36 trend_continuation 觸發驗證、只讀 monitor、資料依據預設隱藏、manifest/source_status QA probe、同 setup_key 回測行去重；主 repo focused command `17 passed`，monitor 缺 source fail closed `source-error`，py_compile / diff check passed；QA_REPORT `conditional pass`，原因是 QA agent 兩次報舊測試狀態，已列 runner_gap；未改 RR 公式、DB schema/write、live Telegram，版本維持 `v20.4.36`。
- `caab930` / `83fd163`｜`research_daily_price_backfill_and_trend_sample_expansion_20260603`｜risk_patch/research｜Owner 明確要求「直接回填」後，已用 `scripts/backfill_daily_price_history.py --write --confirm-write --years 2 --skip-existing --read-after-write` 逐檔走既有 approved write path 回填 watchlist 12 檔 `daily_price`；12/12 read-after-write `ok`，合計新增 5,218 rows，日期範圍 2024-06-03..2026-06-03；重跑 `scripts/research_trend_continuation.py` 後 `total_hit_count=232`、`meets_min_sample_count=true`，5 日勝率 55.17%、5 日平均 +2.26%，`pullback_continuation_edge=positive`；本輪仍未改策略 / 報文 / DB schema / live Telegram，階段二 `trend_continuation` 買路需另開 major 任務並由 Owner 授權。
- `5045045`｜`research_daily_price_backfill_and_trend_sample_expansion_20260603`｜risk_patch/research｜新增 `scripts/backfill_daily_price_history.py` 與擴充 `scripts/research_trend_continuation.py` artifact；當時只完成 tooling / dry-run / fail-closed / tests，尚未 production write。已被上一條直接回填結果取代。
- `3f67e3e`｜`research_trend_continuation_phase1`｜research｜新增只讀研究腳本 `scripts/research_trend_continuation.py`、focused tests 與 `reports/research/trend_continuation_20260603.{txt,json}`；production DB read-only `daily_price` 實跑 `source_rows=516`，`pullback_continuation` 樣本 5、5 日勝率 20.00%、5 日平均 -3.89%，低於 min_sample 30 且不符合正 edge；extended spike 對照組 1.08/1.15/1.22 樣本 78/46/30，5 日平均 +6.23%/+7.45%/+6.17% 只作對照，不構成追高授權；結論 `insufficient-data`，不得進入階段二 trend_continuation 買入實裝；focused tests 4 passed，py_compile / diff check / mutation scan passed；QA conditional pass，因未消費 `signal_outcomes` / `daily_signal_snapshot` 作三表完整研究。
- `32098c1`｜`v20.4.35-report-semantics`｜risk_patch｜維持 `v20.4.35`：過熱 / 不可追高 evidence boost blocker 擴到 `AVOID`、`LIMIT_LOCK / LIMIT_REBOUND` 與 RR overheat blocker，光寶科類漲停鎖價不再顯示 `證據 +`，改 `過熱不適用`；低量降級文案改 `縮量觀察`，避免 `突破確認｜待確認`；非加碼持倉資料行保留 `V`，格式為 `不適用（既有持倉）｜V {vol}x`；首屏簡報改 `執行動作 N` / `今日新建倉 M` 去歧義；主 repo `tests/test_generator_report.py` 157 passed，py_compile / diff check passed；QA conditional pass，未取得正式 runner artifact。
- `58969a8`｜`report-score-evidence-display-20260603`｜risk_patch｜升版 `v20.4.35`：非加碼持倉卡片 `數據` 行整段顯示 `不適用（既有持倉）`，不再顯示 RR / 綜合 / 技術 / 證據 / V；加碼與新倉候選仍顯示分數；`final_confidence` 封頂 100；過熱 / 風控 / 資料不足三類 evidence unavailable 文案分流；盤後縮量整理降 `極強` 為 `待確認｜縮量`；低分或 rounded 無變化顯示 `微幅` 而非 `+X%`；主 repo generator + market tests 195 passed，py_compile / diff check passed；QA conditional pass，未取得正式 runner artifact。
- `5b9523f`｜`render_market_theme_evidence_freshness_20260603`｜risk_patch｜新增 Render route 前置 market/theme freshness check：每次啟動先檢最近 5 個 confirmed trading days，已完整日期跳過，未到台北 14:00 只讀不寫，缺失且過安全時間走既有 approved backfill/upsert 並 read-after-write；失敗時 blocking dispatch 且不寫 already-sent tag；confirmed evidence 完整性要求 9 個官方 TWSE 題材 key；backfill workflow/CLI 改吃 start_date/end_date + historical-range，不再 May-only；targeted tests 45 passed、py_compile / diff check passed；QA conditional pass，待 Render production log 驗證真實 5 分鐘觸發。
- `135bae7`｜`20260603_evidence_score_effective_market_freshness_v20_4_34`｜risk_patch｜維持 `v20.4.34`：per-stock strategy evidence 改用各股 `backtest_context`，sample 36/38 且參考度高可在 global sample partial 時進 ready；緯創 / 華邦等價 replay 顯示 `綜合 != 技術`、證據 +8% supporting，弱勢 / FAILED_BREAKOUT modifier <= 1.0；daily evidence cron 改台北 14:00，Phase3 runner 缺 `MARKET_THEME_APPROVED_PAYLOAD` fail closed，payload trade_date mismatch 不進 write；主 repo generator + Phase3 + workflow tests 179 passed，py_compile / diff check passed；QA conditional pass，因未讀 production DB / 未取得正式 runner artifact，不能宣稱 2026-06-03 confirmed row 已落庫。
- `b38ae26`｜`20260603_evidence_sample_gating_v20_4_34`｜risk_patch｜升版 `v20.4.34`：strategy sample count 統一讀 `row_count / sample_rows / evidence_count / sample / sample_count / classification_sample_count`，避免 classification 樣本 36/38 被讀成 0 後降為 partial；8 天 confirmed_trend market/theme 維持 decision eligible；official message-list replay 覆蓋建準等價卡片 `綜合 90｜技術 78｜證據 +15%（confirmed）`，不再 `partial/+0%` 或 `綜合=技術`；過熱卡保留等冷卻 hard block 但 evidence 不誤顯不足；主 repo evidence targeted 6 passed、generator/market/strategy suite 206 passed、py_compile / diff check passed；QA agent runner 遇 usage limit，QA_REPORT 標為 conditional pass 並記錄本地反證。
- `ea75f15`｜`20260603_same_day_risk_report_replay_regressions`｜risk_patch｜升版 `v20.4.33`：同日建倉入場即錯（-3% 且突破失敗 / 結構轉弱）覆蓋新倉觀察並顯示減碼；hard_stop 仍優先；光寶科類前態淘汰 / failed / weak 單次 BUY 防抖，卡片顯示 `不買｜前態待確認` 而非 `不買｜進場`；過熱 / 等冷卻 / 過熱觀察 RR 顯示 `-（過熱）`；簡報原因行單句化；06/03 v20.4.32 failure specimen 補 official message-list replay；QA passed；主 repo targeted suite 240 passed；py_compile / diff check passed。
- `32a7a8b`｜`process_validation_route_for_owner_report_samples`｜process｜不改產品代碼：Owner 完整報文成為 failure specimen；PM 必須定義驗收路由，Tech 必須標明 probe 覆蓋層級，QA 必須用同層 replay / artifact 反證，否則只能 conditional / blocked；agent profile contract gate、Architect scope gate、diff check passed。
- `7ccc808`｜`20260603_strategy_evidence_report_risk_patch`｜risk_patch｜升版 `v20.4.32`：strategy evidence loader 移除 version filter 並以 `.range()` 分頁取得最近 60 個 distinct trade_date；交易執行 / 新倉建議拆分，未持倉可買標示尚未買入 / 建議分批；原因 / 風險按對象拆分；partial +0% 顯示 `僅輔助參考`；同日建倉 hard_stop / 入場價 -3% / 入場 K 低點觸發當日減碼，僅破警戒維持新倉風控觀察；D1 光寶科翻轉 deferred；QA passed；主 repo targeted tests 201 passed；Git completion gate passed。
- `32fcfd8`｜`telegram_message_noise_consistency_20260603`｜normal_patch｜不升版仍維持 `v20.4.31`：首屏市場行去重並改為 compact count；有可買時顯示 `可買N/僅追蹤N/淘汰N`，無可買時維持不可推薦語氣；刪冗餘新倉/背景/持倉行；交易執行短文案；僅追蹤與 cross-day 歷史 token 降噪；淘汰/弱勢不可行動 RR 顯示 `-（不可行動）`；partial +0% 顯示 `僅輔助參考`；QA passed；主 repo `tests/test_generator_report.py` 146 passed。
- `a92a884`｜`presentation_noise_reduction_v20_4_31`｜normal_patch｜不升版仍維持 `v20.4.31`：簡報市場/結論、原因/風險合併；無有效進場時 `追蹤最強` 改為 `僅追蹤`；盤中/盤後正常來源隱藏資料依據、異常才顯示；卡片不可用歷史/回測降噪；B5 Summary / 漏斗 / card 一致；QA passed；主 repo rendered tests 8 passed。
- `0d20b35`｜`per_stock_evidence_score_funnel_p0_p3_20260602`｜risk_patch｜不升版仍維持 `v20.4.31`：strategy setup sample 成為 per-stock 分量；缺 explicit setup fail closed；弱勢 / 失敗 / EXTREME / technical=0 不吃正向 boost；旺宏 / 聯電 modifier 不同；B5 Summary / 漏斗 / card 一致；QA passed；主 repo targeted tests 4 passed。
- `c4c8b0e`｜`fix_market_theme_evidence_gate_v20_4_31`｜normal_patch｜不升版仍維持 `v20.4.31`：market/theme confirmed_trend 不再疊 15 日二次門檻；per-stock 缺 market_theme fallback report-level market evidence；英業達卡片顯示 `證據 +8%（supporting）` 而非不適用；strategy 跨版本回測 filter 回歸通過；QA passed；主 repo targeted tests 4 passed。
- `32d7422`｜`evidence-wiring-and-funnel-consistency-20260602`｜risk_patch｜不升版仍維持 `v20.4.31`：strategy evidence loader 移除 version filter，跨版本 outcomes 可進樣本；market/theme string summary path 傳入 trade_date 並消費 confirmed evidence_trend；D2/B5 `等冷卻 / 隔日確認` 漏斗與卡片 rendered message 一致；QA passed；主 repo targeted tests 4 passed。

## Blocked / Deferred

- future-watch live adapters：v20.4.45 第 4 則已可顯示固定官方全球事件 seed/snapshot；若要長期自動更新，需另開任務補 live official global event adapters、MOPS official 法說會 adapter、historical analogy timeline source 與 production-safe read-only artifact。未實作前不得假造法說會或崩盤類比。
- `strategy-support-stop-candidate-20260601`：blocked，未吸收產品 diff。原因：support stop candidate 會改變使用者可見 `stop / risk / rr`，但 VERSION / Owner 放行契約未完成。主 repo 未吸收 `services/analysis.py` / `tests/test_analysis_engine.py` candidate diff。
- production source follow-up：若 Owner 要長期顯示持倉觀察第 N 天，需另開 observation start / observation days 持久來源治理；本輪只保證有可信來源時顯示、缺來源時不假造。

## Next Action

- v20.4.45 未來 30 日關注第 4 則已 QA 通過；若 Owner 要 live 更新法說會 / 全球事件 / 歷史類比，再另開 source adapter 任務。
- v20.4.44 卡片證據語意已 QA 通過；若 Owner 要更細的全市場 wording 矩陣或排序，另開顯示文案任務，不在本輪改策略。
- 前一輪 Render freshness 仍需部署後看 Render 5 分鐘觸發 log，確認 freshness preflight 真實 runtime output。
- 開新任務前先看 `task_md_holds`，不要用 `TASK.md` 內部舊狀態反推當前看板。
- 報文 / 策略 / 產品修復仍走 PM -> Tech -> QA；流程治理文件可由 Architect 直接改。

## Fixed Commands

Owner 對 Architect：

```text
你是 Architect / 總控，不是 PM、Tech、QA。依 AGENTS.md 啟動順序讀文件；產品/策略/報文 feature 先分派 PM，不直接寫產品代碼。
```

Architect 入口：

```text
tools/cao_agent/run_architect_task.sh research "<研究問題>"
tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"
```

CAO 服務：

```text
tools/cao_agent/ensure_cao_services.sh
CAO API: http://127.0.0.1:9889/
CAO UI:  http://127.0.0.1:5173/
```
