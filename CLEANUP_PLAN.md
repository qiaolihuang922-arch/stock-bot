# CLEANUP_PLAN.md

本文件由 Architect 維護，用來記錄清理、收斂與避免重複工作的計畫。未經 Owner 或明確任務確認，不直接執行大範圍清理。

## 目前原則

- 不主動重構核心代碼。
- 不清理未知來源的未提交變更。
- 不刪除固定 8 份 Markdown 工作流文件。
- 不刪除測試或核心文件，除非有明確任務與影響判斷。
- 清理工作必須先有摘要、範圍與驗證方式。
- Architect 不直接修功能代碼；Owner 提出新功能 / 顯示 / bug / 策略需求時，先更新 `DISPATCH.md` 分派。
- QA 不是照單驗收角色；必須主動找問題、跨區塊語意一致性、使用者誤讀風險。
- 每次 Architect 完成 commit / push 後，必須壓縮工作流 Markdown，只保留最新任務與高信號摘要。
- 規則優先級固定為：三層硬規則 > 角色分工 > 任務分級 > 啟動句。
- 若 agent 輸出污染正式文件，先清理成摘要再吸收；不讓終端流水進入固定 Markdown。
- 清理任務不能用「可能有用」作為保留理由；必須提供可核驗 evidence。沒有 evidence 的保留結論只能進 `待確認`，不能算完成。
- Owner 明確確認 production 狀態後，待確認項必須重新分類；不能用「本地不知道 production history」無限期阻塞清理。
- PM / Tech / QA 代理必須按角色卡與任務卡輸出；缺輸出契約、缺直接消費者、缺主動反證的交付一律退回。
- CAO runner 的 handoff 文件不是候選 diff；若固定 Markdown 因上下文同步出現在 worktree diff，Architect 不得整包合併。
- QA 可寫暫存只限 `.qa_tmp/`；任何 tracked diff 或 handoff hash 變動都視為 QA 越權。
- Architect 不得因產品 bug 很小就跳過 PM；小 bug 只代表 QA 分級可低，不代表可越權寫 `TASK.md` 或改代碼。
- Architect 若在對話中發現自己開始定位產品代碼、寫 `TASK.md`、寫 `CHANGELOG.md` 或寫 `QA_REPORT.md`，必須停止並回到分派流程。
- Owner 明確授權「對比後沒問題就直接 push / 自己 push / 對齊 git」時，Architect 完成 final diff review 與必要驗證後可直接 commit / push，不再二次詢問；有不明 diff、QA 未通過或測試阻塞時不得 push。
- 報文 / CLI 任務必須檢查使用者可見版本字串與程式常量 / header；狀態文件版本與實際輸出版本不一致時，不得收口。

## 最新收斂

- v20.0 Strategy Evidence Foundation 已完成並推送。
- v20.0.1 Evidence Readiness Message 已完成並推送。
- v20.0.2 Project Safety Slimming 已完成本地驗證：刪除 `.DS_Store`、`.pytest_cache/`、`.pycache/`，保留所有不確定或仍有引用的文件。
- CAO online read-only research 已完成第一階段接入，僅作 Architect 輔助研究，不自動寫真實 repo。
- CAO Tech safe read-only planning 已完成第一階段接入，僅作 Architect 技術可行性輔助，不自動寫真實 repo。
- CAO Tech write sandbox 已完成第一階段接入，只寫隔離 worktree，不直接寫主 repo。
- CAO QA code readonly 與 auto dev cycle runner 已建立，可自動串 PM -> Tech -> QA。
- CAO 入口已收縮：Owner / Architect 日常只使用 `run_architect_task.sh` 的 `research`、`plan`、`auto` 三種模式。
- 底層 agents 不得互相派工；只允許 Architect runner 控制順序。
- 已新增三層硬規則：代理規則、代碼規則、文件規則，作為後續所有任務的第一判斷層。
- 已新增代理交付證據門檻：Tech 必須對每個清理候選項列 evidence，QA 必須逐項反證。
- 已實際驗證代理門檻有效：第一輪 Tech 因無證據表被退回，第二輪補齊證據表後 QA 給 conditional pass。
- SQL 草案已由 Owner 決策刪除：線上 DB 已建立、回測已寫入 DB，本地 `docs/v*_schema.sql` 不再保留。
- Code/comment slimming 已完成：吸收 9 個 Python 檔案註解-only diff，L3 驗證通過。
- CAO runner 已修復：PM 輸出清洗、Tech worktree 每輪清理、QA 強制證據表與殘留區分。
- CAO worktree post-push 清理已補強：每次 commit / push 後由 Architect 執行 `/Users/liveroom/stock-bot-agent-context/cleanup_agent_worktrees.sh`，將 `tech_write` 對齊主 repo 當前 `HEAD`，移除 tracked / untracked / `.qa_tmp` 殘留，只保留 `.venv`。
- v20.0.4 Telegram 顯示一致性已完成：summary、未持倉分組、詳情索引與最後行動清單已補顆粒度。
- CAO auto cycle 環境缺口已修復：Tech / QA worktree 啟動前會自動確保 `.venv` 與 pytest 可用。
- v20.0.5 已修正手機 Telegram 報文閱讀問題：未持倉分組拆成冷卻 / 回測 / RR / 量能 / 淘汰，summary 改短。
- Workflow Rules v3 已完成：補 PM / Tech / QA 角色卡固定欄位、TASK / CHANGELOG / QA_REPORT 任務卡固定欄位、Architect 拒收條件，並同步 CAO stock agent profiles 與 runner prompt。
- v20.0.6 已修正 Telegram 報文清晰度與查詢效能：
  - strategy evidence summary 改 DB 端 order/limit。
  - 同一 run 共用 Supabase client。
  - 淘汰股高層降噪，明細保留追溯。
  - 修正 `明日執行清單` / `今日可執行` 時間語意衝突。
  - QA L2 conditional pass，主 repo `75 passed, 21 warnings`。
- QA runner 已修正：`stock_qa_code_readonly` 不改 tracked files，但允許 `.qa_tmp/` 測試暫存，並用 diff hash 防止 QA 修改候選 diff。
- CAO runner process hardening 已完成：
  - Tech runner 將固定 handoff Markdown 隔離為 read-only context，避免 worktree 殘留被誤當候選 diff。
  - QA runner 加上 handoff hash gate，避免 QA 偷改交接文件。
  - Tech / QA 交付抽取只吸收最後合法標題後內容，降低 transcript 污染。
  - auto cycle 延後寫回 `CHANGELOG.md` / `QA_REPORT.md`，避免 QA 失敗時主 repo 留下假完成交付。
- Architect role self-lock 已完成：
  - 新對話先確認總控身份。
  - 產品 bug 先分派 PM，不直接寫 `TASK.md`。
  - 未經 Owner 明確授權，不代 Tech / QA 實作或驗收。
  - 越權改動需先恢復，再更新流程規則。
- Telegram unheld funnel count bug 已完成本地修復：
  - PM / Tech / QA 已按流程接力。
  - QA 第一輪 conditional pass 發現 `可準備 > 0` 邊界，已回派 Tech 補修。
  - QA 第二輪通過，主 repo 局部驗證 `37 passed, 21 warnings`。
- Auto push after final review 已寫入流程：Owner 授權後，Architect 對比確認無問題即可直接推送。
- Version contract gate 已寫入流程：PM 定義版本契約、Tech 同步 `VERSION` / header / 測試、QA 以實際輸出核對版本。
- v20.0.13 Market Theme Evidence Guard 已形成限定可吸收候選：
  - 不建表、不新增 evidence provider，只防止舊 `market_summary` 自我證明 AI / 電子供應鏈 confirmed bullish。
  - QA 結論為 `conditional pass`；指定 formatter / notifier 驗證通過。
  - broader formatter smoke 仍有 3 個 phase-sensitive failures，需另開任務處理，不得宣告整體 formatter suite 全綠。
- v20.0.14 Post-market Phase Message Consistency 已形成限定可吸收候選：
  - 修復盤後 summary / index / reason / unheld card 的 phase 語意一致性。
  - `formatTelegramMessages()` 同輪固定一次 `report_phase`，避免卡片盤中、summary 盤後。
  - QA 結論為 `通過`；`tests/test_generator_report.py tests/test_notifier.py` 為 `52 passed, 21 warnings`。
- push 後仍需壓縮：
  - `DISPATCH.md`
  - `TASK.md`
  - `CHANGELOG.md`
  - `QA_REPORT.md`
  - `RESEARCH.md`
  - `CURRENT_STATE.md`
  - `CLEANUP_PLAN.md`
- 本輪不清理核心代碼。
- 本輪確認「瘦身」不等於大量刪檔；不確定項只記錄，不刪。
- CAO 測試日誌每次 runner 結束會清空；研究輸出保留於 `/Users/liveroom/stock-bot-agent-context/outputs`。
- `run_project_research.sh` 會更新 `RESEARCH.md`，但不 commit / push；仍需 Architect review。

## 待處理項目

- 目前本地累積的 v20.0.2-v20.0.6、瘦身、SQL 草案清理與 runner 規則文件已完成本地驗證；本輪由 Architect 做 final diff review 後 commit。
- CAO Tech write 現階段只能在 `/Users/liveroom/stock-bot-agent-worktrees/tech_write` 產生 diff；不得自動合併主 repo、commit 或 push。
- 每次 auto dev cycle 後，Architect 必須檢查隔離 worktree 的 `git status`、`git diff --stat`、必要 diff，再決定是否合併。
- 下一次實際 auto 任務後，需檢查三層硬規則是否足夠阻止：越權改碼、輸出污染、文件錯寫、未驗收標記完成。
- 下一次 auto 開發需觀察 Tech / QA 是否使用 worktree `.venv` 正常跑必要測試；不得再因缺環境跳過驗證。
- 後續所有報文任務需按 `AGENTS.md` 的手機 Telegram 報文硬規則驗收，不得只證明數字可追溯。
- 若 Owner 仍覺得查詢慢，下一步應開 performance measurement 任務，量測 production 實際秒數，不再只看 query contract。
- 若後續 Owner 發現完整詳情或行情標籤也有 phase drift，再另開 `price-label-phase-consistency` 任務；本輪只收斂 Telegram message list contract。
- 需要重跑一次真正的清理審計：
  - `core/holdings.py`
  - `docs/v19_*`：已刪除本地 SQL 草案。
  - `docs/v20_*`：已刪除本地 SQL 草案。
  - 舊版本命名測試
  - 冗長註解
  - 腳本內重複邏輯
  - 未被 runtime / tests / cron / Telegram / Supabase 消費的文件
- v20.0.3 worktree 候選尚未合併：
  - 已吸收：註解-only 瘦身 diff。
  - 不可直接吸收：測試改名、replay/backfill 重構。
  - 已在主 repo 補跑 full pytest、replay/backfill dry-run。
  - SQL schema 文件已由 Owner 確認可刪；後續如需 migration 管理，另建 canonical migration，不恢復草案文件。
- 下次 auto 任務需觀察：
  - PM 是否仍混入 transcript。
  - PM 是否列出直接消費者與輸出契約。
  - Tech 是否真的從乾淨 worktree 開始。
  - Tech handoff Markdown 是否不再污染候選 diff。
  - Tech 是否列出契約影響與直接消費者同步。
  - QA 是否能直接阻止缺證據表交付。
  - QA `.qa_tmp/` 是否足夠跑測試且不產生 tracked diff。
  - QA handoff / diff hash gate 是否能阻止越權修改。
  - QA 是否主動提出 Tech 未覆蓋的反證，而不是只重跑測試。
  - auto cycle 是否能完整跑完 PM -> Tech -> QA。
- 不再新增新 agent；若要新增，需 Owner 明確批准並先寫入本文件。
- 現階段 `run_tech_plan.sh` 只允許產出規劃，不得視為 Tech 已完成實作或 `CHANGELOG.md`；`run_tech_write.sh` 才代表隔離實作。
- 若 Owner 要正式啟用 v20 evidence DB：
  - 另開 production schema apply 任務。
  - 檢查 Supabase RLS / 權限 / index / rollback。
  - 決定 retention / archive 策略。
- 若 Owner 要 live evidence write：
  - 先做 staging 或 dry-run 對照。
  - 再批准 live Supabase write。
- 若 Owner 要 live Telegram delivery 驗證：
  - 另開明確任務，不混入一般 QA。
- 後續可改善：
  - `load_strategy_evidence_summary()` 增加顯式排序。
  - `漏失` 文案改為更低誤讀版本。
  - 擴充真實外部事件 ingestion，但不得直接接 BUY。
  - 如要進一步瘦身，先針對單一候選文件建立引用證據與回滾方案，不做批量刪除。

## 固定保留清單

- `AGENTS.md`
- `DISPATCH.md`
- `RESEARCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`

## 清理分級

- L0 文件整理：只更新摘要文件，不碰核心代碼。
- L1 局部收斂：只調整單一已確認模組的文件、測試說明或小範圍命名。
- L2 行為相關清理：涉及 formatter、策略、資料來源或 DB 寫入邊界，需 PM 任務與 QA 驗證。
- L3 大範圍清理：跨多模組或影響 replay/backfill/DB，需 Owner 明確批准。

## 下一步

- 等待 Owner 下一個需求。
- 若下一步是 v20 production 啟用，不得直接寫庫；必須先分派 PM 定義 rollout / rollback / 驗收條件。
