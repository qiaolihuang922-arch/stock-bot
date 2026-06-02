# TASK: evidence_score enters decision score and funnel boundary

## 任務狀態

- task_id: evidence-score-decision-funnel-phase1-2-2b
- 任務類型: major
- 狀態: done / QA passed
- 版本建議: 使用者可見報文內容變更，需升版或更新報文 header / version 常量；不得回退既有版本字串。
- QA 分級建議: L3

## Owner 問題

Owner 要把 evidence_score 正式接入決策分數、排序與漏斗邊界，但只允許它作為技術 setup 的加權證據，不允許變成獨立買進訊號、追高放寬或風控覆蓋。

本輪要完成 Phase 1 / Phase 2 / Phase 2b：

- Phase 1: 產生個股 evidence score 與 source eligibility。
- Phase 2: 以 evidence modifier 調整 final confidence，並讓排序使用 final confidence。
- Phase 2b: 僅對接近漏斗邊界且已有技術 setup 的候選，允許 evidence 做有限邊界調整並留下原因。

## 使用者可見結果

Telegram / report 手機閱讀時，每檔標的分數行需能看出：

- 綜合分數是最終排序 / 漏斗使用的分數。
- 技術分數仍可獨立閱讀。
- 證據加權只呈現為增減幅或資料不足，不包裝成買進理由。

示例輸出形狀：

2330 台積電｜可準備
綜合 82｜技術 78｜證據 +5%（confirmed）
理由：技術 setup 接近可準備門檻，產業主題 confirmed + strategy sample ready，證據僅調整邊界，不放寬RR/過熱限制。

資料不足時：

2454 聯發科｜僅追蹤
綜合 74｜技術 74｜證據：不適用（資料不足）
理由：證據不足，沿用純技術分數與原漏斗邊界。

手機閱讀路徑：

- Summary 仍只回答今天能不能買、持倉先處理什麼、未持倉哪些只是追蹤。
- 分組標題、卡片狀態、漏斗、索引與詳情必須一致。
- 無 setup 或硬風控阻擋的標的，即使 evidence confirmed，也不得在手機報文中呈現為可買。

## 非目標

- 不改 RR 公式。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不新增 production write / backfill / live delivery。
- 不送 live Telegram。
- 不做 Phase 3。
- 不重設策略核心、不重定義既有技術 setup。
- 不把 evidence 做成 standalone BUY source。
- 不放寬 chase / overheat / RR / risk controls。
- 不處理本輪以外的報文清理、全量 refactor 或資料庫治理問題。

## 影響模組與直接消費者

影響模組：

- evidence score 計算模組或新增 helper。
- load_strategy_evidence_summary 的既有讀取消費路徑。
- market theme / evidence trend 讀取與判斷路徑。
- decision confidence / candidate scoring。
- pick_best_stock。
- funnel sorting / funnel boundary 判斷。
- manifest / report 產生器。
- Telegram/report formatter 中個股分數行。

直接消費者：

- 日報 / Telegram 報文讀者。
- pick_best_stock 的呼叫方。
- funnel 分組與排序的呼叫方。
- manifest/report artifact 消費者。
- QA probes / regression tests。

## 輸出契約

### evidence score helper

新增或補齊：

compute_evidence_score(report_context, name) -> tuple[float | None, str]

契約：

- score: 0.0 <= score <= 1.0，或 None。
- status: 必須可區分至少以下狀態：
- confirmed
- supporting
- partial
- neutral
- unavailable
- 所有 source insufficient 時：score=None, status="unavailable"。
- 部分 source insufficient 時：不得 fail open；只能 neutral / partial。
- source 不足不得產生強證據分數。

### evidence sources

strategy_sample：

- 來源為 load_strategy_evidence_summary 的既有 setup winrate / MFE-MAE summary。
- sample threshold 使用既有門檻，Owner 鎖定為約 10；Tech 不得另創新門檻。
- sample >= existing threshold about 10 且資料可用才可視為 ready / decision_eligible。
- sample <10 必須是 neutral / partial，不得當 confirmed。

market_theme：

- 來源為 evidence_trend。
- 狀態包含 confirmed / supporting / single_day。
- 只有 confirmed 可作強證據。
- single_day 不得獨立推升到 confirmed，不得放寬 chase。

### decision eligibility

輸出 evidence payload 必須包含：

evidence.market_theme.decision_eligible
evidence.strategy_sample.decision_eligible
evidence.*.forbidden_effects

decision_eligible：

- market_theme: 只有 confirmed 才可 true。
- strategy_sample: 只有 ready 且 sample 達既有門檻才可 true。

forbidden_effects 必須至少表達：

- no standalone BUY
- no chase relaxation
- no override risk controls

### final confidence

final_confidence = technical_confidence * evidence_modifier
evidence_modifier = clamp(1 + 0.3 * (evidence_score - 0.5), [0.85, 1.15])

Owner 鎖定參數：

- k = 0.3
- floor = 0.85
- ceiling = 1.15

當 evidence_score is None：

- evidence_modifier = 1.0
- final_confidence = technical_confidence
- 不做 funnel boundary adjustment。

### sorting / picking

- pick_best_stock 必須使用 final_confidence。
- funnel sorting 必須使用 final_confidence。
- manifest/report 需保留或揭露 technical_confidence、evidence_modifier、final_confidence，避免無法重跑驗證。

### report data line

使用者可見報文分數行拆成：

綜合 X｜技術 Y｜證據 +Z%（status）

資料不足時：

綜合 X｜技術 Y｜證據：不適用（資料不足）

### Phase 2b boundary adjustment

只允許：

- 候選已有既有 technical setup。
- 候選接近既有 funnel boundary。
- evidence 是 strong confirmed。
- 調整方向只能讓 等回測 / 等RR修復 這類 near-boundary 狀態更接近 可準備。
- manifest/report 必須標註 evidence adjustment reason。

硬限制：

- 無 technical setup 不得變 BUY。
- confirmed evidence 不得使無 setup 變可買。
- overheat / chase ban 不得放寬。
- RR / overheat hard blockers 仍然阻擋。
- risk controls 不得被 evidence 覆蓋。

## 版本契約

已存在且不得回退的契約：

- 報文 Summary 只回答決策，不得把追蹤標的寫成推薦。
- 可買、可準備、僅追蹤、淘汰 / 不可行動必須分開。
- 無可買時不得使用像推薦的文案。
- 同一持倉同一份報文只能有一個主行動。
- 空區塊、0-count、無新增下單占位預設不顯示。
- 使用者可見報文變更需核對版本字串，不得回退版本。
- production DB / Telegram live delivery 不在本輪。

若 Tech 發現既有程式沒有可定位的 version/header 常量，需在 CHANGELOG 標成 residual risk，並不得自行擴大成版本系統重構。

## 驗收條件

必須新增可重跑 probes / tests，至少覆蓋：

1. missing evidence

- compute_evidence_score 回傳 None/unavailable。
- evidence_modifier=1.0。
- final_confidence == technical_confidence。
- 無 funnel adjustment。

2. confirmed evidence + no technical setup

- 不得 BUY。
- 不得進可買。
- 不得越過 no setup hard gate。
- report/manifest 必須能看出 evidence 未覆蓋 setup。

3. confirmed evidence + existing setup near boundary

- score/ranking 使用 final_confidence。
- boundary 可被 evidence 調整。
- modifier 不得超過 1.15。
- 不得違反 RR / overheat hard blockers。
- manifest/report 有 adjustment reason。

4. report score split

- 手機報文可重現：
- 綜合 X｜技術 Y｜證據 +Z%（status）
- insufficient 時 證據：不適用（資料不足）
- 分組標題、卡片狀態、詳情理由一致。

5. market_theme alone confirmed

- 可貢獻 evidence score。
- 不得放寬 chase。
- 不得 standalone BUY。

6. strategy_sample below threshold

- sample < existing threshold about 10 時為 neutral / partial。
- 不得 decision_eligible true。
- 不得產生 strong confirmed boundary adjustment。

7. pick_best_stock

- 排名與 winner 使用 final_confidence。
- 測試需能區分 technical score 與 final score，避免仍用 technical score 的假通過。

QA L3 必須補 Tech 未覆蓋的負面 probe 或手機誤讀路徑，且不能只重跑 Tech 命令。

## 範例或 Fixture

最小 fixtures：

A_missing_evidence:
technical_confidence=80
strategy_sample=missing
market_theme=missing
expected_modifier=1.0
expected_final=80
expected_funnel_adjustment=false
expected_report="證據：不適用（資料不足）"

B_confirmed_no_setup:
technical_confidence=70
technical_setup=false
market_theme=confirmed
strategy_sample=ready/sample>=10
expected_no_buy=true
expected_no_prepare_if_existing_rules_block=true
expected_forbidden_effects=["no standalone BUY", "no chase relaxation", "no override risk controls"]

C_confirmed_near_boundary:
technical_confidence=78
technical_setup=true
near_boundary=true
market_theme=confirmed
strategy_sample=ready/sample>=10
expected_modifier<=1.15
expected_sort_by=final_confidence
expected_boundary_adjustment_reason_present=true
expected_rr_overheat_hard_blockers_preserved=true

D_strategy_sample_low:
strategy_sample=9
market_theme=missing_or_supporting
expected_status="partial_or_neutral"
expected_strategy_sample_decision_eligible=false
expected_no_strong_boundary_adjustment=true

E_chase_ban:
technical_setup=true
market_theme=confirmed
strategy_sample=ready/sample>=10
chase_or_overheat_blocker=true
expected_no_chase_relaxation=true
expected_no_buy=true
expected_report_reason_mentions_hard_blocker=true

## 明確禁止事項

- 禁止改 RR 公式。
- 禁止 DB schema/write/backfill/live delivery。
- 禁止 live Telegram。
- 禁止 evidence 產生 standalone BUY。
- 禁止 evidence 放寬追高、過熱、RR 或 risk controls。
- 禁止無 technical setup 因 evidence 變成 BUY / 可買。
- 禁止把 sample <10 的 strategy evidence 當 ready。
- 禁止只改報文字串、不讓 pick_best_stock 與 funnel sorting 使用 final_confidence。
- 禁止把 Phase 3 或全策略重構納入本輪。
- 禁止用 local cache / runtime dict / agent 記憶當跨日 source-of-truth。

## 阻塞條件

若以下任一條成立，Tech 必須 blocked，不得自行假設：

- 找不到 load_strategy_evidence_summary 或無法確認既有 sample threshold。
- 找不到 market theme / evidence_trend 可用來源。
- 既有 candidate payload 無法同時保留 technical_confidence 與 final_confidence，且需要改 public contract 但 TASK 未覆蓋。
- 需要 DB schema/write 才能完成。
- 需要 live Telegram 驗證才可判斷完成。
- 既有 RR / overheat / chase hard blocker 定義不可定位，導致無法驗證 forbidden effects。
- 測試環境不可用且無法補齊。

## 本輪停止條件

完成條件：

- Phase 1 evidence score 與 source eligibility 可重跑。
- Phase 2 final confidence、modifier、report split、sorting、pick_best_stock 全部接入。
- Phase 2b 僅 near-boundary + existing setup + strong confirmed evidence 可調整，且 hard blockers 不被放寬。
- Tech 提供 CHANGELOG 與自檢命令。
- QA L3 通過，包含手機閱讀與負面 probes。

本輪不處理：

- Phase 3。
- RR 公式合理性。
- strategy evidence 歷史資料品質重建。
- DB schema / production write。
- Telegram live delivery。
- 其他報文清理與版面重構。
- 新發現但不阻塞本輪驗收的策略邊界問題；只記入後續待辦。
