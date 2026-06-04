# RESEARCH.md

保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Latest Research｜Conditional Strategy Width｜2026-06-04

- task_id：`20260604_144316_6186_online_research_pair`
- 問題：不是全域放寬策略，而是定義「符合什麼條件」時，原本 `僅追蹤 / 等冷卻 / 等RR修復` 可以升級為 `可準備`、`趨勢延續小倉` 或一般 `可買`。
- 狀態：研究完成；本輪只讀研究，未改產品代碼、未改 DB、未發 Telegram。
- 來源輸出：`.cao_agent_context/outputs/20260604_144316_6186_online_research_pair.md`
- Architect 補充取證：讀取 `services/analysis.py`、`core/generator.py`、`RESEARCH.md`、`reports/research/trend_continuation_20260603.*`，並跑 2026-06-04 watchlist 只讀 snapshot。

## Core Conclusion

條件性放寬應拆成三層，不應把所有強勢股直接放成 `可買`：

1. `可準備`：報文 / 漏斗層升級，仍是不可買；用來標出「差一個條件」的候選，避免全部混進僅追蹤。
2. `趨勢延續小倉`：策略層小倉 BUY，僅限回踩站回同源 setup，倉位 `<=15%`，回踩低點下方停損，5 日 edge 退出。
3. 一般 `可買`：仍走既有 BUY gate，不因 evidence、題材、分數、回測摘要單獨放寬。

## Current Strategy Gates

- 一般突破買：`MIN_RR_BREAKOUT = 1.5`。
- 突破前買：`MIN_RR_PREBREAK = 1.0`。
- 強勢跟隨買：`MIN_RR_STRONG = 2.0`。
- 過熱分層：price / ma20 >= `1.08` 為 Lv1，`1.15` 為 HOT / EXTENDED，`1.22` 為 EXTREME / AVOID。
- `can_buy()` 硬擋：`LIMIT_LOCK`、`LIMIT_REBOUND`、`WEAK_REBOUND`、`EXTREME`、`AVOID`、距離觸發 > 4%、entry_quality `C/D`。
- `entry_quality_score()` 封頂：RR < 0.8 最高 49；RR < 1.2 最高 64；HOT 且 RR < 1.5 最高 64。
- 報文 `is_valid_entry()` 再擋一次：普通 BUY 必須無 blockers、entry_quality A+/A/B、非 HOT/EXTREME；trend_continuation 必須小倉 <=15%、非 HOT/EXTREME、非漲停/弱反彈。

## Conditional Matrix

| 原狀態 | 可升級到 | 必要條件 | 仍不可升級 |
|---|---|---|---|
| 僅追蹤 / 等回測 | 可準備 | 技術接近突破或回測邊界；無追高 hard blocker；RR 不低於 1；source / evidence ready；entry 或 market grade A/B；不得進交易執行 | 突破失敗、弱勢、漲停鎖價、弱反彈、source-error、RR不足 |
| 不可追高觀察 | 可準備 | 追價風險解除後，價格重新接近買點或回測不破；不得仍是 HOT/EXTREME；不得只靠題材加分 | HOT/EXTREME 當下、距離觸發 > 4%、LIMIT_LOCK / LIMIT_REBOUND |
| 等冷卻 | 可準備 | 必須先降溫：heat 從 HOT/EXTREME 回 NORMAL，trade_state 非 EXTENDED/AVOID，且回測不破或站回突破區 | 還在 HOT、EXTREME、EXTENDED、AVOID 時不可升級 |
| 等RR修復 | 可準備 | RR不足 blocker 已消失；RR 至少 >= 1；source/evidence 完整；非追高 | RR < 1 或 trade_state=LATE_ENTRY 時只能留 `等RR修復` |
| 回踩延續 setup | 趨勢延續小倉 | daily_price 同源 positive evidence；sample >=30；5D win >=55%；5D avg >0；回踩 ma5/ma10 不破；回踩日縮量；觸發日站回 ma5 且量比 >=1；非 failed/fake/extreme/limit/no-volume | 只有 extended spike、沒有回踩站回、缺 OHLCV、負 evidence、NO_VOLUME、EXTREME |
| 一般 BUY setup | 可買 | 既有 strategy decision=BUY；RR 達標；can_buy 通過；entry_quality A/B 以上；無 blockers；source eligible | evidence、題材、回測摘要不得單獨轉 BUY |

## Hard Boundaries

- `hard_stop`、持倉停損、同日入場即錯風控不可放寬。
- `FAILED_BREAKOUT`、fake breakout、market_grade D、trend DOWN / market WEAK 不升級。
- `RR不足` 未解除時，不得用 evidence 覆蓋；只能等 RR 修復。
- HOT/EXTREME / AVOID 當下不升可買；等冷卻只在降溫後重新評估。
- `LIMIT_LOCK`、`LIMIT_REBOUND`、`WEAK_REBOUND` 不因強勢或題材轉買。
- source missing / source-error / unresolved-conflict 必須 fail closed。
- `market/theme evidence` 不能單獨把不可買改成 BUY，不能放寬追高。
- `extended_spike` 對照組只能留在研究，不得成為追高授權。

## Current 2026-06-04 Snapshot

只讀 snapshot 顯示當下 12 檔主要卡點：

- 可買：建準、光寶科，皆為普通 BUY 且無 blockers；即時價會波動，不等同正式交易指令。
- 等冷卻 / 禁止追高：緯創、南亞科、華邦電、英業達、仁寶，主因 HOT/EXTREME/EXTENDED/AVOID。
- 弱勢淘汰 / 失敗：智原、聯電、群創、技嘉、旺宏，主因 market_grade D、突破失敗、量能不足或距離觸發太遠。

策略含義：可條件性放寬的主要對象不是失敗股，而是「強勢但被冷卻 / RR / 回測條件卡住」的修復候選。

## Phased Plan

Phase A：只新增 / 收斂 `可準備` 規則，不新增 BUY。

- 目標：把強勢但差一條件的標的從普通僅追蹤裡分出來。
- 行為：Summary / 漏斗 / 卡片明確寫 `可準備（不可買）`。
- 禁止：不得進 `今日盤中交易執行`，不得顯示像推薦。

Phase B：只保留 / 強化 `趨勢延續小倉`。

- 目標：把已有正 edge 的 pullback continuation 作為唯一條件性小倉 BUY 例外。
- 行為：`decision_type="trend_continuation"`、position `<=0.15`、回踩低點下方停損、5 日未續漲退出。
- 禁止：不得把 extended spike、過熱、漲停鎖價納入。

Phase C：做 portfolio cap 與 forward monitor。

- 指標：同日 trend_continuation 總曝險、5 日勝率、5 日平均報酬、MAE、停損觸發率、5 日未續漲退出率。
- 反證：不能只看總平均；需檢查 per-symbol edge 是否集中在少數高 beta 股票。

## Validation Requirements

- official generator / message-list replay 必須覆蓋：可準備但不可買、等冷卻不可升格、等RR修復不可升格、trend_continuation 小倉 BUY。
- 負面案例必測：LIMIT_LOCK、LIMIT_REBOUND、WEAK_REBOUND、HOT/EXTREME、FAILED_BREAKOUT、market_grade D、NO_VOLUME、RR不足、source-error。
- 手機閱讀必測：Summary / funnel / index / card 同源一致；`可準備` 不能像 `可買`；`趨勢延續` 不能像滿倉買入。
- 若進入實作，屬 risk_patch；QA 至少 L2，改正式買入路徑則 L3。

## Trend Continuation Evidence State

- artifact：`reports/research/trend_continuation_20260603.txt`、`reports/research/trend_continuation_20260603.json`。
- universe：watchlist 12 檔。
- total_hit_count：232，meets_min_sample_count=true。
- pullback continuation：1 日勝率 46.98%、平均 +0.45%；3 日勝率 55.17%、平均 +1.74%；5 日勝率 55.17%、平均 +2.26%；10 日勝率 54.74%、平均 +2.77%；MFE +9.85%、MAE -4.89%。
- extended spike 對照：雖有正平均，但只作對照；不授權追高。
- 限制：主要使用 `daily_price`，未完整整合 `daily_signal_snapshot / signal_outcomes`；artifact date_range 欄位仍需補強。

## Data Roles

- `positions`：持倉 source-of-truth。
- `position_events`：已買 / 已賣 / 已停利 / 已減碼 execution ledger；跨日防重必須用它。
- `daily_signal_snapshot`：每日當時版本留存，用於追溯，不要求舊月份回填 current version。
- `daily_price`：trend continuation 研究主要 OHLCV 來源。
- `market_theme_confirmed_evidence`：production market/theme evidence，用於背景與輔助，不直接轉 BUY。
- `market_theme_index_daily_bars`：market/theme index source table，供 evidence / audit 使用。
- `sector_theme_members`：mapping，不是 daily history。

## Next Product Question

下一步若 Owner 要進開發，建議先做 Phase A：新增 / 收斂 `可準備（不可買）` 條件與報文分組，並產生 gate attribution，讓每檔清楚顯示「只差哪一條」。Phase B 的 `趨勢延續小倉` 已有實作基礎，但需要 portfolio cap 與 forward monitor 補強。
