# CURRENT_STATE.md

本文件由 Architect 維護，作為專案短上下文。新會話應先讀本文件，再依任務讀必要摘要文件或局部源碼。

## 專案狀態

- 專案：台股策略報文機器人。
- 目前穩定線：`v20.0.6 Telegram Report Clarity And Query Performance` 已完成本地合併、QA L2 conditional pass；尚未 commit / push。
- 最新流程線：`CAO Runner Process Hardening` 已完成本地修復；本輪只改 runner gate 與流程規則，不改產品代碼。
- 最新已推送 commit：`a34df7a docs: compress workflow state after v20.0.1`
- 交付形態維持不變：定時 GitHub Actions / 腳本 -> 產生 Telegram 報文 -> 發送給 Owner。
- 預設只處理 `core/watchlist.py` 的 12 檔股票。

## v20.0 已完成

- 新增 `services/strategy_evidence.py`：market bars、feature snapshots、outcome metrics、classification audit、classification report / Telegram evidence summary。
- `core/generator.py` 新增 `📊 策略證據 v20.0`。
- `scripts/dry_run_replay.py` 與 `scripts/backfill_signals.py` 接入 evidence dry-run path。
- QA L3 通過：full pytest `99 passed, 21 warnings`，synthetic replay/backfill dry-run 通過且不寫庫。

## v20.0.1 已完成

- 修正 evidence schema 未啟用時 Telegram 露出 Supabase raw error 的問題。
- schema missing 顯示：`策略證據尚未啟用：資料表未建立，主報文不受影響`。
- generic DB failure 顯示：`證據層暫時略過：資料更新失敗，主報文不受影響`。
- 樣本不足仍顯示樣本不足，不被誤判為更新失敗。
- 主報文版本升至 `v20.0.1`，策略證據區塊名稱仍為 `📊 策略證據 v20.0`。
- QA L2 通過：formatter / evidence fallback、notifier contract、策略不變性。
- 未 apply production schema、未正式寫庫、未改策略。

## v20.0.2 已完成

- 完成安全瘦身：刪除本地 generated cache / 系統產物 `.DS_Store`、`.pytest_cache/`、`.pycache/`。
- 未刪除 `.venv/`、`config.py`、`core/holdings.py`、replay/backfill、Telegram/Supabase runtime 相關文件。
- 收縮 CAO 代理規則：Owner 日常只需走 Architect；底層 agents 只能由 Architect runner 串接，不得互相 handoff / assign / send_message。
- 本輪無策略、報文、DB、Telegram、watchlist、排程行為變更。
- QA L3 通過：full pytest `101 passed, 21 warnings`；synthetic replay/backfill dry-run 通過且不寫庫。

## Workflow Rules v2 已完成

- `AGENTS.md` 新增三層硬規則：
  - 代理規則：Owner 只對 Architect；CAO agents 只由 Architect runner 串接。
  - 代碼規則：Architect 預設不改代碼；Tech write 只在隔離 worktree 產生 diff；live 副作用需單獨批准。
  - 文件規則：固定 8 份 Markdown 不刪；正式交付不接收終端流水、完整聊天或未壓縮過程。
- CAO auto 完成條件補強：未產生合格 `TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 不得標記完成。
- 本輪只改工作流文件，未改產品代碼。

## Workflow Rules v3 已完成

- 參考公開多代理 / AGENTS.md 實務後，補強角色卡與任務卡契約。
- `AGENTS.md` 新增每個代理必備欄位：
  - mission、inputs、allowed_actions、forbidden_actions、output_schema、block_conditions、self_check、handoff_contract。
- PM `TASK.md` 必須包含 Owner 問題、使用者可見結果、非目標、影響模組、直接消費者、輸出契約、驗收條件、範例 / fixture、禁止事項、阻塞條件。
- Tech `CHANGELOG.md` 必須包含契約影響、直接消費者同步、未影響模組、自檢命令與殘留風險。
- QA `QA_REPORT.md` 必須主動補 Tech 未覆蓋的直接消費者、負面案例、使用者誤讀路徑或契約風險；不能只重跑 Tech 測試。
- Architect 拒收條件明確化：標題不符、缺直接消費者、缺契約影響、缺 QA 主動反證、報文未測手機閱讀路徑、無 evidence 結論，一律退回。
- 已同步 CAO stock agent profiles 與 runner prompt，讓自動代理啟動時也吃到同一套規則。
- 本輪只改流程文檔與代理 prompt / runner；未改產品代碼。

## CAO Runner Process Hardening 已完成

- 修復上一輪自動鏈暴露的流程缺口：
  - QA runner 不再因 read-only 無暫存目錄而跳過 formatter / evidence / notifier 測試；允許 `.qa_tmp/` 與 dummy `config.py`，仍禁止 tracked file 修改。
  - QA runner 會檢查候選 diff hash 與 handoff file hash；若 QA 改了 tracked diff 或交接文件，結果拒收。
  - Tech runner 每輪從乾淨 worktree 開始，並把 `AGENTS.md`、`DISPATCH.md`、`RESEARCH.md`、`CURRENT_STATE.md`、`CLEANUP_PLAN.md`、`TASK.md`、`QA_REPORT.md` 當 read-only handoff context，避免固定文件殘留混入候選 diff。
  - Tech / QA answer extraction 改為只吸收最後一個合法 `# CHANGELOG:` / `# QA_REPORT:`，避免終端 transcript 污染正式摘要。
  - auto cycle 只有在 QA 報告結構合格後，才把 `CHANGELOG.md` / `QA_REPORT.md` 寫回主 repo。
- `AGENTS.md` 已新增 Runner hygiene gates，明確規定 worktree 殘留隔離、QA `.qa_tmp/` 權限、hash gate、交付抽取與 performance conditional pass。
- 驗證：`bash -n` 通過 `run_tech_write.sh`、`run_qa_code.sh`、`run_auto_dev_cycle.sh`。
- Architect final review 驗證：
  - full pytest：`105 passed, 21 warnings`
  - replay synthetic dry-run validate：`VALIDATION OK`
  - backfill synthetic dry-run：`VALIDATION OK`、`DRY RUN ONLY: no database writes`
  - runner shell syntax：`bash -n` 通過
- 未執行新的 CAO auto 任務；下一次實際 auto 任務需觀察 gate 是否如預期阻止殘留與污染。

## Architect Role Self Lock 已完成

- 修復總控越權風險：Architect 不得因為 bug 小就直接定位產品代碼、寫 `TASK.md`、改產品代碼或測試。
- 新對話 / 上下文壓縮後，Architect 第一個動作必須確認自己是總控，不是 PM / Tech / QA。
- 產品 bug / 顯示 bug / feature request 的預設流程：
  - Architect 只更新 `DISPATCH.md` 分派，設 `pm_status: todo`、`tech_status: waiting_pm`、`qa_status: waiting_tech`。
  - PM 產出 `TASK.md`。
  - Tech 按 `TASK.md` 實作並產出 `CHANGELOG.md`。
  - QA 按 `TASK.md` / `CHANGELOG.md` 驗證並產出 `QA_REPORT.md`。
- Architect 只有在 Owner 明確說「你直接代 PM 寫 TASK」或「你直接實作 / 不走部門」時，才可越過對應角色。
- 若 Architect 已越權改文件，必須先恢復越權改動，再更新流程規則。

## Telegram Unheld Funnel Count Bug 已完成本地修復

- 修正短報文 `未持倉漏斗（非執行）` 數量誤讀：
  - 先顯示 `未持倉總數 N 檔`。
  - 再顯示同層母集合：可買 / 可準備 / 僅追蹤 / 淘汰。
  - 再用 `其中僅追蹤 N 檔拆分` 顯示等冷卻 / 等回測 / 等RR修復 / 等量能。
  - 另用 `非執行追蹤合計` 明確表示可準備 + 僅追蹤。
- QA 第一輪發現 `可準備 > 0` 時母集合不一致，已回派 Tech 第二輪補修。
- QA 第二輪結論：`通過`。
- 修改檔案：
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`
  - `DISPATCH.md`
- 未改策略 decision、DB payload、watchlist、live Telegram、live Supabase、replay/backfill write path。
- 驗證：`tests/test_generator_report.py tests/test_notifier.py`，`37 passed, 21 warnings`。

## v20.0.3 瘦身審計進度

- 已用 CAO agents 跑真正瘦身審計。
- PM 產出任務後曾混入 transcript，Architect 已清理 `TASK.md`。
- Tech 第一輪不合格：缺 `path / claim / evidence / risk / action` 證據表，已退回。
- Tech 第二輪在隔離 worktree 產生候選 diff 與證據表。
- QA 第二輪結論：`conditional pass`。
- 候選產品 diff 已收斂為註解-only：
  - `core/condition_engine.py`
  - `core/generator.py`
  - `core/holdings.py`
  - `core/utils.py`
  - `services/analysis.py`
  - `services/notifier.py`
  - `services/stock_api.py`
  - `scripts/dry_run_replay.py`
  - `scripts/backfill_signals.py`
- 已吸收至主 repo，尚未 commit / push。
- 已在主 repo 補跑 L3：full pytest、replay/backfill dry-run、payload path 檢查。
- SQL schema 草案已因 Owner 明確確認線上 DB 已建立且回測已寫入而刪除；不再列待確認。

## v20.0.4 已完成

- 修正 Telegram summary / 詳情 / 漏斗的跨區塊語意一致性。
- `🔥 最強` 文案分層：
  - 可買存在時：`最強可買`。
  - 無可買但有追蹤標的時：`無有效進場中相對最強：不可買／僅追蹤`。
- summary 新增持倉顆粒度：續抱、觀察、減碼或風控、停利停損。
- summary 新增未持倉顆粒度：可買、可準備、追蹤、等回測或樣本不足。
- 明日執行清單新增四層閱讀路徑：今日可執行、明日盤前準備、僅追蹤、不可行動 / 等回測。
- 未持倉詳情新增分組標題，讓 `等回測 4` 可追溯到 `【等回測 4｜不可買】`。
- 詳情索引補上 `等回測` 與 `等RR修復` 數量。
- 未改策略 decision、DB payload、watchlist、live Telegram、live Supabase、replay/backfill write path。
- 驗證：formatter / evidence / notifier 相關測試 `44 passed, 21 warnings`；full pytest `101 passed, 21 warnings`。

## v20.0.5 已完成

- 修正 v20.0.4 手機閱讀體驗問題。
- `AGENTS.md` 新增手機 Telegram 報文硬規則：手機優先、短 summary、分組語意一致、無可買不得像推薦。
- 無可買文案改為：
  - `追蹤最強：<股票>｜<狀態>｜不可買`
  - 或 `新倉：無有效進場`
- 未持倉顯示改為實際狀態分組：
  - 冷卻
  - 回測
  - RR
  - 量能
  - 淘汰
- summary、漏斗、詳情索引、未持倉明細分組已統一分類，不再出現 `等回測 4` 裡面包含 `等冷卻 3` 的問題。
- 明日行動區縮短為：今日可執行、明日盤前、僅追蹤、不可行動。
- 未改策略 decision、DB payload、watchlist、live Telegram、live Supabase、replay/backfill write path。
- 驗證：formatter / evidence / notifier 相關測試 `44 passed, 21 warnings`；full pytest `101 passed, 21 warnings`。

## v20.0.6 已完成

- 修正 Owner 指出的三個報文問題：
  - 查詢資料耗時回歸：strategy evidence summary 改為 DB 端 order/limit，並讓同一 run 的 record/load evidence 共用 Supabase client。
  - `旺宏` 淘汰重複曝光：高層 summary / 明日清單 / 索引不再反覆列淘汰股票名，只保留淘汰數量與詳情入口；明細仍可追溯。
  - 明日/今日語意混亂：非盤中 summary 改 `盤後結論`，明日清單內改 `盤後持倉檢視：N 檔`，不再出現 `今日可執行：持倉 N`。
- 補強 `best=旺宏` 且 `旺宏=淘汰` 的負面案例：高層 `🔥 最強` 顯示 `無有效進場標的`，不以推薦語氣曝光淘汰股。
- 修改檔案：
  - `core/generator.py`
  - `services/strategy_evidence.py`
  - `tests/test_generator_report.py`
  - `tests/test_strategy_evidence.py`
- 未改策略 decision、DB payload、watchlist、live Telegram、live Supabase、replay/backfill write path。
- QA L2 conditional pass：
  - 主 repo 驗證 `75 passed, 21 warnings`。
  - QA 追加手機長報文 fixture 通過。
  - 殘留風險：未量測 production 真實秒數；本輪以 query contract / client reuse 作為替代證據。

## SQL 草案清理已完成

- 已刪除本地過期 SQL schema draft：
  - `docs/v19_2_position_zero_migration.sql`
  - `docs/v19_backfill_schema.sql`
  - `docs/v19_position_execution_schema.sql`
  - `docs/v20_strategy_evidence_schema.sql`
- 刪除理由：Owner 已確認線上 DB 已建立、回測已寫入 DB，本地 SQL 草案不再作為 canonical migration / rollback 唯一來源。
- 本輪未改 runtime DB code、Telegram function、Supabase client code、backfill/replay executable code。
- full pytest 通過：`101 passed, 21 warnings`。
- 後續若需要正式 migration 管理，應另建 canonical migration 流程，不再用 `docs/v*_schema.sql` 草案堆積。

## Code / Comment Slimming 已完成

- 已吸收隔離 worktree 中經 QA conditional pass 的候選 Python diff，且在主 repo 補跑 L3 驗證通過。
- 清理內容只限註解 / banner：
  - `services/analysis.py`
  - `core/generator.py`
  - `core/condition_engine.py`
  - `services/stock_api.py`
  - `services/notifier.py`
  - `core/holdings.py`
  - `core/utils.py`
  - `scripts/dry_run_replay.py`
  - `scripts/backfill_signals.py`
- 未改策略 decision、Telegram 使用者可見文字、DB payload、watchlist、replay/backfill write protection。
- 驗證：
  - full pytest：`101 passed, 21 warnings`
  - replay dry-run validate：`VALIDATION OK`
  - backfill dry-run：`VALIDATION OK`、`DRY RUN ONLY: no database writes`

## CAO Runner Fixes 已完成

- `run_auto_dev_cycle.sh` 已補強：
  - PM 輸出會抽取乾淨 `# TASK:` 內容，不再直接吸收 transcript。
  - PM / Tech / QA 任一階段失敗會寫入 summary 的 FAILED 區塊並停止。
  - Tech 缺 `CHANGELOG.md` 時視為失敗。
- `run_tech_write.sh` 已補強：
  - 每輪預設清理隔離 worktree，避免上一輪 diff 殘留污染下一輪。
  - 清理 / 瘦身 / refactor 任務強制要求 `path / claim / evidence / risk / action` 證據表。
- `run_qa_code.sh` 已補強：
  - TASK / CHANGELOG / diff 不一致時不得通過。
  - 缺證據表時必須 blocked。
  - 必須區分可吸收 diff 與 worktree 殘留，不得建議整包合併。
- `stock_pm_online_readonly` profile 已補強：TASK 輸出必須從 `# TASK:` 開始，不得混入 transcript。
- 目前隔離 worktree 已清乾淨。

## CAO Worktree Test Environment 已完成

- 已修復 Tech / QA 隔離 worktree 缺 `.venv` 導致代理卡住或跳過測試的流程問題。
- `run_tech_write.sh` 與 `run_qa_code.sh` 啟動前會自動確保 worktree 有可用 `.venv/bin/python` 與 pytest。
- 補環境策略：
  - 優先連到主 repo 既有 `.venv`。
  - 主 repo `.venv` 不可用時，建立 worktree `.venv` 並安裝 `requirements.txt` 與 pytest。
- Tech / QA prompt 已明確禁止因環境缺失繞過測試；若 runner 補環境後仍不能測，必須 blocked。
- 已在 `/Users/liveroom/stock-bot-agent-worktrees/tech_write/.venv` 建立可用環境連結，確認 `pytest 8.4.2`。
- 已補 `.venv` 忽略規則，tech worktree status clean，避免 QA 誤判環境 symlink 是殘留 diff。
- 本輪只改 runner 腳本與流程規則，未改產品代碼。

## 明確未完成

- production schema apply。
- live Supabase write。
- live Telegram delivery。
- TWSE live replay / live backfill。
- 正式 backfill write。
- 真實外部新聞 / 題材 ingestion。
- Supabase RLS / 權限 / index / rollback 驗證。

以上都需 Owner 另開明確批准流程。

## 目前進行中

- CAO online read-only research 已接入為 Architect 輔助工具。
- 最新 online research 結論：v20.x 可進入 PM 需求草案，研究「External Event Evidence Pilot」，外部新聞 / 事件資料只作 evidence / risk / context，不產生 BUY。
- CAO Tech safe read-only planning 已接入，可產出技術 feasibility / patch plan，但不自動寫碼。
- CAO Tech write sandbox 已接入：可在 `/Users/liveroom/stock-bot-agent-worktrees/tech_write` 隔離 worktree 實作，不直接寫主 repo。
- CAO QA code readonly 已接入：可讀隔離 worktree 的 `TASK.md`、`CHANGELOG.md`、diff 與相關代碼，輸出 QA 報告；不改 tracked files，只允許 `.qa_tmp/` 作測試暫存。
- 自動 PM -> Tech -> QA runner 已建立；日常統一入口已收縮為：`/Users/liveroom/stock-bot-agent-context/run_architect_task.sh <research|plan|auto> "<任務>"`。
- v20.0.6 已完成本地驗證；等待 Owner 是否要求 commit / push。
- CAO auto cycle 測試環境缺口已修復；下一輪需觀察 Tech / QA 是否能正常完成測試與交付。

## 現有模組

- `main.py`：主要執行入口。
- `app.py`：Render 入口，觸發 GitHub Actions workflow。
- `core/watchlist.py`：12 檔股票唯一配置來源。
- `services/analysis.py`：策略決策來源。
- `core/generator.py`：報文產生、排序、Telegram 輸出。
- `core/condition_engine.py`：條件映射層。
- `services/stock_api.py`：行情與歷史資料來源。
- `services/signal_store.py`：`signal_runs / signal_items / signal_outcomes` 寫入。
- `services/daily_snapshot_store.py`：`daily_price / daily_signal_snapshot` 寫入。
- `core/signal_snapshot.py`：snapshot 組裝。
- `core/signal_validator.py`：snapshot 邏輯驗證。
- `services/position_store.py`：Supabase `positions` 持倉讀取。
- `services/strategy_evidence.py`：v20.0 策略證據資料層與 v20.0.1 error fallback。
- `scripts/dry_run_replay.py`：dry-run replay。
- `scripts/backfill_signals.py`：受保護 backfill，預設不寫庫。
- `supabase/functions/telegram-execution/index.ts`：Telegram 持倉文字命令處理。
- `tests/`：策略、formatter、snapshot、backfill/replay、行情來源與 evidence 測試。

## 已知風險

- 本地 SQL schema draft 已刪；production DB 狀態以線上 Supabase 為準。
- Evidence summary 依賴 DB 查詢；本地已驗證失敗降級，但 production latency 未測。
- `load_strategy_evidence_summary()` 查詢未顯式排序，後續可加 `.order("trade_date")`。
- backfill 正式寫庫會增加資料量，需 retention / archive 策略。
- 12 檔 watchlist 樣本偏小，策略證據第一版應維持 `樣本不足，不判讀`，避免過度解讀。
- `漏失` 一詞可能造成誤讀，後續可改成 `大漲漏失統計` 或補 `僅供檢討`。

## 流程狀態

- 固定 8 份 Markdown 工作流文件不得刪除，只允許更新內容。
- Architect 收到新功能 / 顯示 / bug / 策略需求時，預設只分派，不直接改代碼。
- Tech 自檢不等於 QA；QA 必須補直接消費者、跨區塊語意、使用者誤讀、負面案例與反證。
- PM / Tech / QA 交付必須符合角色卡與任務卡；不合格由 Architect 退回，不吸收為完成。
- QA 若只重複 Tech 測試、沒有主動質疑或反證，不能直接通過。
- production schema apply、live Supabase write、live Telegram delivery、正式 backfill write 都不是預設 QA L3，必須 Owner 明確批准。
- CAO online research runner 可由 Architect 調用：
  - `/Users/liveroom/stock-bot-agent-context/run_online_agent.sh stock_pm_online_readonly "<prompt>"`
  - `/Users/liveroom/stock-bot-agent-context/run_online_agent.sh stock_qa_online_readonly "<prompt>"`
  - `/Users/liveroom/stock-bot-agent-context/run_research_pair.sh "<研究問題>"`
  - `/Users/liveroom/stock-bot-agent-context/run_project_research.sh "<研究問題>"`
  - `/Users/liveroom/stock-bot-agent-context/run_tech_plan.sh "<技術規劃問題>"`
- CAO online context 只含摘要 Markdown，位於 `/Users/liveroom/stock-bot-agent-context/online_research`。
- CAO online agent 可 web search，但 read-only，不直接改真實 repo，不直接寫固定 8 份 Markdown。
- `run_project_research.sh` 會在 CAO 結束後由 Architect-controlled runner 更新 `RESEARCH.md`。
- CAO Tech safe context 只含摘要 Markdown，位於 `/Users/liveroom/stock-bot-agent-context/tech_plan`；只做規劃，不讀真實 repo、不改碼。
- CAO Tech write 使用隔離 worktree，主 repo 寫入 probe 已驗證為 blocked；代碼 diff 需 Architect review 後才合併。
- CAO 自動代理使用自定義 `stock_*` profiles，不使用 CAO 內建 `code_supervisor/developer/reviewer` 規則作為正式工作流。
- CAO agents 不得互相派工；只能由 Architect-controlled runner 串接。Owner 日常只對 Architect 說需求，不直接操作底層 agents。
- CAO online 實戰接入已驗證：公開資料研究 -> PM/QA online findings -> `RESEARCH.md` 高信號摘要。
- 規則優先級：三層硬規則 > 角色分工 > 任務分級 > 啟動句。

## 影響模組判斷規則

- 報文分類、顯示文字、Telegram 卡片：`core/generator.py` 與 formatter tests。
- 持倉策略、買賣/續抱/停利/風控邏輯：`services/analysis.py` 與策略 tests。
- 行情來源、TWSE/Yahoo fallback、source 標示：`services/stock_api.py`、`core/generator.py` 與行情 tests。
- snapshot / DB 寫入保護：`services/daily_snapshot_store.py`、`services/signal_store.py`、`core/signal_validator.py`。
- replay/backfill：`scripts/dry_run_replay.py`、`scripts/backfill_signals.py` 與相關 tests。
- 策略證據資料層：`services/strategy_evidence.py`、replay/backfill tests。
- Telegram 持倉命令：`supabase/functions/telegram-execution/index.ts`。
