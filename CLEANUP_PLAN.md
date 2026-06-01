# CLEANUP_PLAN.md

保存待補流程與高信號事故摘要；不保存長篇流水，不把單次事故塞進 `AGENTS.md`。

## Governance

- `AGENTS.md` 只放跨任務原則。
- 具體事故進本文件或 `CURRENT_STATE.md`，並定期壓縮。
- 規則變更先分類：
  - `one_off`：只記摘要。
  - `repeated_pattern`：合併既有規則或任務卡契約。
  - `high_risk_invariant`：才升級到硬規則。
  - `runner_gap`：補 runner / agent prompt / worktree gate。
  - `doc_bloat`：壓縮或刪除過期流水。

## Completed

- `telegram-evidence-human-readable-v20.4.17`:
  - 問題：Owner 指出第三則 `資料依據` 又出現 `production DB`、`classification backtest`、`source-of-truth`、`available/derived/as_of` 等工程語，且沒有用人話說明證據源是否可靠、策略是否有用。
  - 結果：PM -> Tech -> QA 完成，QA `通過`；收口需 commit / push 並跑 Git completion gate。
  - 關鍵修正：第三則改為三段人話資料依據：市場 / 題材背景可靠度與不作買點；策略樣本不可用時可靠度低且不納入買賣判斷；持倉 / 價格 / 候選資料可支持風控 / 分類，缺資料標的保守處理。
  - QA 反證：完整三則 sample 注入 raw 工程語、ISO timestamp、不可用 strategy sample 後，第三則仍不含 `production`、`runtime`、`source_status`、`as_of`、`classification backtest` 等禁詞；market/theme 未升格買點，strategy sample 未進入買賣判斷。
  - 流程問題：前一輪 QA 已指出第三則 `決策簡報` 仍會從 summary 帶出 `production/runtime` 診斷，本輪補強輸出層過濾並同步舊測試契約，避免只修 `資料依據` 三行而漏掉同一則訊息的其他段落。
  - 規則治理：`repeated_pattern` + `evidence_chain` + `mobile_reading`。證據鏈要用人話回答可靠度、用途與限制；不可把表名、欄位狀態或 debug source 當作使用者可見證據。
  - 邊界：不改策略 decision、候選分類、DB schema/write、live Telegram。
- `telegram_card_source_humanize_v20_4_16`：
  - 問題：Owner 指出第一則/第二則卡片 `Source：... available/derived` 完全看不懂，且持倉卡出現新倉 RR 數字，和「持倉不看新倉RR」衝突。
  - 結果：PM -> Tech -> QA 完成，QA `通過`；收口需 commit / push 並跑 Git completion gate。
  - 關鍵修正：持倉卡資料行改為 `資料：持倉與現價已確認；風控由持倉成本/停損推算`；未持倉卡資料行改為 `資料：現價與 OHLCV 已確認；RR/分數/量能為模型推算`；缺 price/OHLCV 時 fail-closed；持倉非加碼情境顯示 `新倉 RR：持倉不適用`。
  - QA 反證：完整三則 sample 確認第一/第二則不再有 raw Source dump；缺 price 且 strategy result 為 BUY 時仍顯示 `資料：缺現價，停止新倉判斷` 與 `新倉：無有效進場`，無可買 / 推薦語氣。
  - 流程問題：Tech 最終回答的 CHANGELOG 正確，但 runner 未寫入 worktree，QA 第一次讀到舊 v20.4.15 CHANGELOG 後阻塞；Architect 手動同步 scoped diff 與 CHANGELOG 後 Re-QA 通過。
  - 規則治理：`runner_gap` + `mobile_reading` + `evidence_chain`。卡片 source 不能用工程狀態直出；交付文件必須和實際 diff 同步，否則 QA 要阻塞。
  - 邊界：不改策略 decision、RR/score/volume 公式、DB schema/write、live Telegram。
- `telegram-brief-data-evidence-v20.4.15`：
  - 問題：Owner 指出 v20.4.14 第三則雖已去重，但仍像 market/theme、strategy sample、source、漏斗/風險多片段拼接，不像一份「簡報＋資料」。
  - 結果：PM -> Tech -> QA 完成，QA `通過`；收口需 commit / push 並跑 Git completion gate。
  - 關鍵修正：第三則改為單一 `🧾 v20.4.15 簡報＋資料依據`，只有 `決策簡報` 與 `資料依據` 兩個主要入口；資料依據集中說明 market/theme production、strategy sample、持倉/候選 source-of-truth 狀態與限制。
  - 重要退回：第一版 Tech 過度壓縮第三則，刪掉既有 summary 消費者需要的今日結論、交易執行、漏斗等內容，且 source-missing early return 仍只回單訊息；QA 阻塞後已修正。
  - QA 反證：L2 scoped tests 119 passed；source-missing early return 仍回三則；第三則 `決策簡報` count = 1、`資料依據` count = 1，無 `簡短證據摘要 / 策略證據 / 來源狀態 / 漏斗證據 / 風險證據` 多入口。
  - 規則治理：`repeated_pattern` + `mobile_reading` + `evidence_chain`。收斂第三則不能刪掉直接決策摘要；資料依據必須集中，但行動結論仍要完整可讀。
  - 邊界：不改策略 decision、DB schema/write、live Telegram；不處理 reply markup、2356 ledger、全報文文案盤點。
- `telegram-evidence-entry-dedupe-v20.4.14`：
  - 問題：Owner 指出 v20.4.13 第三則同時顯示 `📊 策略證據 v20.0` 與 `簡短證據摘要`，兩個證據入口語意重複。
  - 結果：PM -> Tech -> QA 完成，QA `通過`；收口需 commit / push 並跑 Git completion gate。
  - 關鍵修正：第三則只保留 `v20.4.14 簡短證據摘要`；legacy `📊 策略證據 v20.0` 長段在 Telegram 第三則被跳過；`missing-source / insufficient-data` 保留在唯一摘要內 fail closed。
  - QA 反證：注入 legacy strategy evidence block 後，三則順序仍為持倉、未持倉、short/evidence；第三則 `簡短證據摘要` count = 1，legacy heading count = 0，且仍含 `missing-source` 與 `fail-closed`。
  - 規則治理：`repeated_pattern` + `mobile_reading` + `evidence_chain`。同一第三則不能同時用兩種 evidence entrance 說同一件事；證據狀態要集中呈現。
  - 邊界：不改策略 decision、DB schema/write、live Telegram；`formatTelegramSummary()` standalone 仍可保留原始 strategy evidence，因本輪只約束 TG 第三則。
- `tg-evidence-short-ux-v20.4.13`：
  - 問題：Owner 貼出 v20.4.12 第三則報文，指出 evidence/short 像 debug 輸出，包含 raw source/date/table/key 與互相衝突的 0-count/source 行，手機上需要自然語言整理。
  - 結果：PM -> Tech -> QA 完成，QA `通過`；收口需 commit / push 並跑 Git completion gate。
  - 關鍵修正：第三則保留決策短訊但過濾 raw/debug evidence；舊 `Evidence Compact` 改為 `v20.4.13 簡短證據摘要`，用自然語言說明持倉依據、未持倉依據、資料不足 fail-closed 與結論。
  - QA 反證：sector-only market/theme probe 確認 raw summary 原本會有 `來源：sector_index/latest_trade_date`，第三則 formatter 後禁止詞命中為空；策略樣本 unavailable 不升級為可買或推薦；message order 仍持倉、未持倉、short/evidence。
  - 規則治理：`repeated_pattern` + `evidence_chain` + `mobile_reading`。證據鏈不是把 source raw dump 給 Owner；應把 source-of-truth 翻成可讀結論，同時保留 fail-closed 邊界。
  - 流程優化：QA probe 必須覆蓋 raw evidence filter 的負面樣本，尤其是單一 source 行如 `來源：sector_index...`，不能只驗常見 `watchlist_breadth` 組合。
  - 邊界：不改策略 decision、DB schema/write、live Telegram；前兩則卡片既有 card-level Source 行非本輪目標。
- `tg-message-order-v20.4.12`：
  - 問題：Owner 貼出 v20.4.11 盤中 Telegram output，指出 TG 發送順序應為 `1.持倉 2.非持倉 3.報文短訊`，而不是 summary first。
  - 結果：PM -> Tech -> QA 完成，QA `通過`；收口需 commit / push 並跑 Git completion gate。
  - 關鍵修正：`formatTelegramMessages()` 改為 messages[0] 持倉、messages[1] 未持倉、messages[2] summary + Evidence Compact；`include_detail=True` 時 Details Backup 仍最後；版本升至 v20.4.12。
  - QA 反證：完整 fixture 同時含持倉與未持倉；確認持倉 action 只在第一則、未持倉 candidate 只在第二則、summary/evidence 在第三則；`services/notifier.py` / mock `send_many()` 確認 sender 不重排。
  - 規則治理：`repeated_pattern` + `mobile_reading`。Summary first 對一般報告可讀，但 TG 實際 delivery 要 action-first；未來任務卡必須區分「報文內容順序」與「Telegram 多訊息送出順序」。
  - 流程優化：Tech worktree stale diff 第一次產出不可吸收，已丟棄隔離 worktree 舊候選並從 current main clean baseline 重跑，避免舊 v20.4.7 diff 混入。
  - 邊界：不改策略 decision、DB schema/write、live Telegram；reply markup 仍掛最後一則 message，另列旁支。
- `intraday_20260601_report_sequence_execution_memory_noise_v20_4_11`：
  - 問題：Owner 貼出 2026-06-01 盤中完整報文，指出主體/詳情順序不符合手機閱讀、英業達 2356 第二段停利仍像沿用上週操作、報文 source/backtest/detail 噪音過多。
  - 結果：PM -> Tech -> QA 完成，QA `通過`；主 repo 工作樹已吸收 scoped diff，未 commit / 未 push。
  - 關鍵修正：`formatTelegramMessages()` 固定 Summary -> action body -> Evidence Compact -> optional Details Backup；2356 second-stage execution memory 未確認時 fail closed；verbose source/backtest/detail 移到 compact evidence / details backup；`evidence_manifest` 補 execution_memory。
  - Production 反證：`.qa_tmp/production_readonly_2356_positions_events.json` 顯示 2356 production `positions` 為 `shares=0 / CLOSED`，`position_events` 有 sell summary 但無 second-stage-like labels。報文不得把一般賣出事件講成「已確認第二段停利」；若 Owner 認定未賣，需另查 ledger source truth。
  - 規則治理：`repeated_pattern` + `evidence_chain` + `mobile_reading` + `runner_gap`。完整報文問題不得切片驗收；QA artifact 必須在 QA worktree 可見，否則會造成假 conditional。
  - 流程優化：Architect 生成 safe read-only artifact 後，需同步到 QA 實際 worktree 或改 runner 標準 artifact path，避免「主 repo 有、QA 看不到」的缺檔反覆。
  - 邊界：不改 DB schema/write/live delivery；不校正 production ledger；旁支 dirty files 不得用本輪結論整包吸收。
- `unified_report_db_source_manifest_v20_4_10`：
  - 問題：Owner 指出完整 Telegram 報文被切成片段理解，且使用者可見資料沒有明確連回 DB / source-of-truth；缺 source 的 BUY-like 候選仍可能在 Summary 看起來像推薦。
  - 結果：PM -> Tech -> QA 反覆到 QA `通過`；主 repo 工作樹已吸收 scoped diff，未 commit / 未 push。
  - 關鍵修正：Summary first；新增共用 `report_context / evidence_manifest`；price/OHLCV/RR source 不足時 Summary、漏斗、交易執行 / 明日計畫、未持倉卡一致 fail closed；`🔥 最強` 不再顯示 source-ineligible candidate 的排序 / 評級；混合 source-valid / source-ineligible 候選不互相污染。
  - QA 反證：盤中與盤後完整報文 probe passed；source-ineligible BUY-like candidate 不出現可買、交易執行、明日計畫、最強候選、排序分或評級分；runtime/local 缺源卡片不顯示精確 RR / S / V / 價格。
  - 規則治理：`repeated_pattern` + `evidence_chain`。不可只做 manifest 或卡片 source line；必須驗完整手機閱讀順序與所有直接消費者。
  - 流程優化：完整報文任務的 QA 應固定補一個 Tech 未覆蓋的首屏 Summary 反證，且至少包含「有效來源候選 + 缺源高分候選」混合情境，防止 source gate 停在局部 formatter。
  - 邊界：不改 DB schema/write/live delivery；旁支 dirty files 不得用本輪結論整包吸收。
- `fix_strategy_sample_evidence_consumption_v20_4_8`：
  - 問題：報文 `策略證據 v20.0` 仍顯示 `樣本 0 / 樣本不足`，手機閱讀上像 strategy evidence 有被使用但沒有提供有效結論。
  - 結果：已由 PM -> Tech -> QA 完成並吸收到工作樹；QA `通過`，未 commit / 未 push。
  - 邊界：未做 live Telegram / DB write / schema；production read-only dry-run 已驗證 v20.4.9 會 fail closed。
  - Production 現況：缺 `classification backtest source-of-truth`，所以正確結論是 strategy sample 層不可用，不是可買 / 不可買決策依據。
  - 抽象教訓：證據鏈不能只「有區塊」；每一層要有狀態、source、不可用原因與對 stock decision 的作用邊界。
- `runner_gap: qa_handoff_sync`：
  - 問題：QA runner 使用可重用 tech worktree，但啟動前未同步主 repo handoff files，導致主 repo 已更正 `CHANGELOG.md` 後，QA 仍讀到 worktree stale 內容並反覆 conditional。
  - 結果：`tools/cao_agent/run_qa_code.sh` 已在 QA 啟動前同步固定 handoff Markdown。
  - 分類：`runner_gap`。
  - 抽象教訓：重跑流程前先消除 runner 的 stale-input 來源；不能靠下一輪 agent 記住上輪錯誤。
- `next_evidence_chain_development_market_theme_auxiliary_layer`：
  - 問題：production market/theme evidence 已 confirmed，但報文缺少手機可讀的策略輔助層，容易讓 Owner 無法分辨背景支持、strategy sample、個股買點/風控。
  - 結果：已由 PM -> Tech -> QA 完成並吸收到工作樹；QA `通過`，未 commit / 未 push。
  - 邊界：未做 live Telegram / DB write / schema；production positive rendering 由 safe read-only artifact 反證。
  - 抽象教訓：confirmed evidence 必須在報文中降格為背景輔助，不得升格成 BUY 或追高提示。
- `runner_gap: qa_conclusion_parser`：
  - 問題：auto wrapper 用 `\b` 解析中文 `QA 結論` 標題，導致有效 `conditional pass` 被判 failed。
  - 結果：工作樹已修 parser regex，改抓 `QA 結論` 行尾或冒號。
  - 分類：`runner_gap`。
- 05/31 holiday execution memory bug：
  - 問題：market/theme evidence 已 confirmed，但英業達 2356 因假日只讀當天 events，仍重複建議第二段停利。
  - 結果：已修，QA 通過，推送到 `main`。
  - 抽象教訓：evidence chain 不等於 execution memory；報文決策必須同時消費 production evidence 與 production execution ledger。
- market/theme 2026-05 data backfill：
  - `market_theme_confirmed_evidence` / `market_theme_index_daily_bars` 已有五月歷史並通過 audit。
  - `sector_theme_members` 是 mapping，不當 daily history。
- Markdown 已壓縮為新對話接力版。

## Active Follow-ups

- `runner_gap: git_completion_gate`
  - 問題：QA 通過後若只寫「可 commit / push」，重開對話會依文件誤判為仍未推送或忘記 push；完成定義沒有硬性 git gate。
  - 已做：新增 `tools/cao_agent/check_git_completion_gate.sh`，檢查 worktree clean、branch upstream、local HEAD 等於 upstream HEAD；`AGENTS.md` 新增 Git Completion Gate 規則。
  - 修法方向：未來若改 `run_auto_dev_cycle.sh`，可在 auto wrapper 結尾輸出 gate 狀態，但 commit/push 仍由 Architect 控制。
- `runner_gap: tech_worktree_hygiene`
  - 問題：Tech worktree stale diff 會阻塞新任務。
  - 修法方向：新任務前自動檢查、歸檔或要求 Architect 明確處理。
- `runner_gap: production_read_qa_config`
  - 問題：QA dummy Supabase config 會誤判 production read-only audit；即使允許 repo config，QA sandbox 仍可能因 DNS/network 回 source-error。
  - 已做：`run_qa_code.sh` 新增 `CAO_QA_USE_REPO_CONFIG=1`，並在 read-only QA 模式臨時覆蓋 ignored worktree `config.py`，跑完恢復。
  - 已做：`scripts/smoke_market_theme_evidence_readonly.py --auxiliary-render-artifact-json` 產生標準 safe read-only artifact，避免 Architect 手動片段。
  - 已驗：safe read-only artifact 可讓 QA 驗證 production positive rendering 並給 `通過`。
- `runner_gap: strategy_evidence_readonly_artifact`
  - 問題：本輪 strategy evidence production read-only 只能用 inline smoke；QA sandbox DNS 失敗時只能核對 Architect sanitized evidence。
  - 修法方向：補 `scripts/smoke_strategy_evidence_readonly.py` 或擴充現有 smoke CLI，輸出無 credential、無 write/live 的標準 artifact，欄位至少含 version、production_readonly、source_status、has_old_sample0_style、summary_preview。
- `runner_gap: qa_artifact_sync`
  - 問題：Architect 在主 repo 生成 `.qa_tmp/production_readonly_2356_positions_events.json`，但 QA runner 在 tech worktree 執行，第一次 Re-QA 因 artifact 不存在而 conditional。
  - 已做：本輪手動同步 artifact 到 `/Users/liveroom/stock-bot-agent-worktrees/tech_write/.qa_tmp/` 後 artifact-only Re-QA 通過。
  - 修法方向：runner 接受 artifact path 時自動同步到 agent worktree，或統一將 safe read-only artifacts 寫入 shared `.cao_agent_context/artifacts/` 並由 QA 固定讀取。

## Boundaries

- 不刪固定 8 份 Markdown。
- 不清理 production DB rows，除非另有 read-only audit、dry-run、rollback 或 Owner-approved SQL。
- 不把 blocked / conditional candidate diff 當已完成成果吸收。
