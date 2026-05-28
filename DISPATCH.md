# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `market-context-execution-bridge`
- task_name: `Market Context and Execution Bridge`
- task_type: `telegram_strategy_report_review`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pushed`

## Current Result

- Owner 問「有沒有要優化的，有的話安排下」。
- Architect 依剛才市場 / 網路方向比對，判斷可做一個產品語意優化，不改策略核心：
  - 目前報文能說清楚 `交易執行：無新增下單`，但缺少橋接語義：市場大方向 / AI 主線仍偏多，和系統當前不追高 / 等回測並不衝突。
  - PM 需定義 summary 增加一行短句或調整原因句，例如 `主線仍偏多，但買點未成立，先等回測`；重點是把「方向」與「下單」分開。
  - 對未持倉淘汰或等回測標的，若產業方向仍屬主流但技術條件失效，文案應表達為 `題材未壞，技術觸發未成立 / 已失效`，避免 Owner 誤讀為看空產業。
  - 對持倉 AI / 電子供應鏈標的，summary 可保留持倉風控，但不要產生加碼暗示；語意應是 `主線持倉保留，新增倉位等觸發`。
  - 不改買賣決策、不改策略門檻、不新增外部即時新聞依賴、不做 live Telegram / Supabase / backfill。
  - 若修改使用者可見 Telegram 報文，版本需升為 `v20.0.12`。
- CAO 前端：`http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，版本契約升為 `v20.0.12`。
- Tech 已完成候選 diff：
  - `core/generator.py`
  - `tests/test_generator_report.py`
  - `CHANGELOG.md`
- QA 首輪阻塞：`進攻偏熱` 被硬寫成 `AI / 電子供應鏈仍偏多`，在非 AI 場景會誤導。
- Tech retry 已修正：只有 `market_summary` 明確含 AI / 人工智慧 / 電子供應鏈證據時才寫 AI 主線；否則用中性 `市場偏多但買點未成立`。
- QA 最終結論：`通過`。
- QA 驗證：`tests/test_generator_report.py tests/test_notifier.py -q`，`48 passed, 21 warnings`；補手機正反例渲染，確認 AI 有證據時可寫 AI 主線但仍顯示不追高 / 無有效進場，非 AI 場景不硬套 AI，等回測 / 淘汰不被誤讀成可買或產業轉空。

## Next Action

- 本輪已通過主 repo 驗證，完成 commit / push；等待 Owner 下一個任務。

## Status Values

- `todo`: 等待該角色處理。
- `waiting_pm`: Tech 或 QA 等待 PM 交付。
- `waiting_tech`: QA 等待 Tech 交付。
- `task_ready`: PM 已交付 `TASK.md`。
- `changelog_ready`: Tech 已交付 `CHANGELOG.md`。
- `qa_passed`: QA 驗證通過。
- `qa_failed`: QA 驗證失敗。
- `conditional_pass`: QA 有條件通過，仍有合併前必要驗證或 Owner 決策。
- `conditional_acceptance`: Architect 有條件吸收結果，不代表可 commit / push。
- `blocked`: 該角色遇到阻塞，需 Architect 或 Owner 判斷。
- `completed`: 非開發類任務已由負責角色完成。
- `not_required`: 本輪不需要該角色處理。
- `qa_accepted`: Architect 已吸收 QA 結論並更新狀態。
- `pushed`: Architect 已提交並推送。
- `research_dispatched`: Architect 已建立研究任務。
- `research_ready`: 該角色已提交研究摘要。
- `research_accepted`: Architect 已吸收研究摘要並整理結論。

## Version / QA Levels

- version_level `patch`：bug / 文案 / 顯示一致性，不改策略意圖。
- version_level `minor`：新增使用者可見能力或報文結構。
- version_level `major`：改策略核心、DB schema、交易狀態機、正式寫庫或跨日持久化。
- version_level `none`：純流程 / 文件規則補強。
- qa_level `L1`：局部 formatter / snapshot / 指定回歸。
- qa_level `L2`：策略不變性 + formatter + snapshot + 相關模組測試。
- qa_level `L3`：full pytest + replay/backfill dry-run + 入庫 payload 路徑 + 額外風險掃描。
- qa_level `process`：純流程文件補強。
- qa_level `research`：研究任務，不執行測試。

## Fixed Startup Commands

Owner 對 Architect：

```text
你是 Architect / 總控，不是 PM、Tech、QA。先讀 AGENTS.md 和 DISPATCH.md；若是產品 bug / 顯示 bug / feature request，只能先更新 DISPATCH.md 分派 PM，不得直接寫 TASK.md、不得搜尋或修改產品代碼，除非 Owner 明確說你直接代該角色。
```

Architect 可用 CAO online research：

```text
研究：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh research "<研究問題>"
規劃：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh plan "<技術規劃問題>"
自動開發：/Users/liveroom/stock-bot-agent-context/run_architect_task.sh auto "<Owner 任務>"

CAO API：/Users/liveroom/.local/bin/cao-server --host 127.0.0.1 --port 9889
CAO 中文前端：cd /Users/liveroom/.local/share/cao-web-zh/web && npm run dev -- --host 127.0.0.1 --port 5173
分配或啟動 CAO agents 後，Architect 必須回覆 Owner 前端地址：http://127.0.0.1:5173/

底層 run_project_research.sh / run_tech_plan.sh / run_auto_dev_cycle.sh / run_tech_write.sh / run_qa_code.sh 只作為內部工具，不作為 Owner 日常入口。
```

Owner 對 PM：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 PM 職責處理；若 pm_status 是 todo 或 Architect 指定 PM，請撰寫 TASK.md，不修改代碼。TASK.md 必須從 # TASK: 開始，並符合 AGENTS.md 的 PM 任務卡固定欄位；若需求不足，請輸出 blocked TASK.md。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；若 tech_status 是 todo 且 TASK.md 已 ready，就依 TASK.md 實作並改寫 CHANGELOG.md，不修改產品方向。CHANGELOG.md 必須從 # CHANGELOG: 開始，並符合 AGENTS.md 的 Tech 實作卡固定欄位；若 TASK.md 缺直接消費者、驗收條件或輸出契約，請 blocked。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；若 qa_status 是 todo 且 Tech 已交付 CHANGELOG.md，請執行本輪 qa_level 指定驗證，補直接消費者、跨區塊語意一致性、使用者誤讀風險、負面案例與關聯風險掃描，完成後改寫 QA_REPORT.md。QA_REPORT.md 必須從 # QA_REPORT: 開始；若只重跑 Tech 測試或沒有主動質疑，不能判定通過。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、TASK.md、CHANGELOG.md、QA_REPORT.md，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
