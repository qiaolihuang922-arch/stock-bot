# QA_REPORT:

## 測試範圍

- 任務尺寸 / QA：major / L3；範圍鎖定 evidence_score Phase 1/2/2b 的直接消費者，不擴成 full repo、replay、backfill 或 production matrix。
- 已讀：TASK.md、CHANGELOG.md、git diff、core/generator.py、presentation/report.py、services/analysis.py、tests/test_generator_report.py。
- 可吸收 diff：CHANGELOG.md、core/generator.py、presentation/report.py、services/analysis.py、tests/test_generator_report.py。
- worktree 殘留：git status --short 只顯示上述 tracked 修改；QA 另在 .qa_tmp/evidence_phase_l3_probe.py 放暫存 probe，未修改 tracked file。

## 風險預算與停止條件

1. evidence 被誤用成獨立 BUY / 可準備來源。
   - 驗證：confirmed no setup、supporting_trend、single_day、sample<10、missing evidence。
   - 停止條件：任一非 strong confirmed + technical setup near-boundary 進入可買 / adjusted 可準備。
2. chase / LIMIT_LOCK / RR / overheat hard blocker 被 evidence 放寬。
   - 驗證：Tech 回歸 + QA probe 的 LIMIT_LOCK confirmed evidence 手機卡片與 manifest。
   - 停止條件：出現 adjustment reason、可準備主狀態或買點文案像推薦。
3. mixed adjusted + ordinary prepare 手機閱讀與 manifest 分裂。
   - 驗證：Summary -> 漏斗 -> card -> detail index -> manifest 順序檢查。
   - 停止條件：ordinary prepare 顯示成可準備、manifest reason 非 None，或 summary/card/detail 計數不一致。

## 關聯風險掃描

- TASK / CHANGELOG / diff 一致：CHANGELOG 宣稱的 helper、modifier、final_confidence、sorting、score line、boundary adjustment、hard blocker、mixed split 都有對應 diff 與測試。
- 未見 DB schema、RLS、grant、policy、role、index、constraint、production write、backfill、live Telegram 檔案改動。
- 版本字串由 v20.4.29 升為 v20.4.30，未回退。

## 跨區塊語意一致性

- market_theme.supporting_trend：不是 confirmed，不 decision eligible，不產生 boundary reason，不調成 adjusted 可準備。
- single_day：不 decision eligible，不成 confirmed。
- missing evidence：evidence_modifier=1.0，final_confidence == technical_confidence。
- mixed adjusted + ordinary prepare：Summary、未持倉漏斗、card、detail index、manifest 拆分一致；ordinary card / manifest 主顯示態為 不可追高觀察，strategy_funnel_state=可準備，evidence_adjustment_reason=None。
- pick/sort：pick_best_stock、watchlist sort 使用 final_confidence。

## 使用者誤讀風險

- 手機閱讀順序已檢查：Summary 先拆 可準備 與 不可追高觀察，未持倉卡片再逐檔呈現；ordinary prepare 不會在卡片標題或漏斗被誤讀成 evidence-adjusted prepare。
- chase/LIMIT_LOCK 卡片仍保留不可追高語意，雖顯示 confirmed evidence 的 score line，但沒有 boundary adjustment reason 或可準備主狀態。

## 質疑與反證

- Tech 聚焦回歸：24 passed, 105 deselected。
- QA 自補 probe：.qa_tmp/evidence_phase_l3_probe.py 通過，覆蓋 supporting_trend、LIMIT_LOCK chase、mixed 手機路徑 + manifest、missing evidence modifier。
- 完整直接消費者單檔：tests/test_generator_report.py 通過，129 passed, 225 warnings。
- git diff --check 通過。

## 未測項目

- 未跑 full repo pytest、production replay、backfill、live Telegram、production write。
- 未驗 production evidence 資料品質矩陣；本輪只驗 repo 內契約、formatter、manifest 與 regression probes。
- warnings 為既有 dependency deprecation 類，未見本輪阻塞錯誤。

## QA 結論

通過
