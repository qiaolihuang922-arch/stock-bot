# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `r3-hot-evidence-prepare-layer-v20.2.4`
- task_name: `R3 Hot Market Evidence Wording And Prepare Layer`
- task_type: `normal_patch`
- version_level: `patch`
- qa_level: `L2`
- owner_status: `requested`
- architect_status: `qa_passed_absorbed_pending_push`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`
- commit: `pending`

## Current Result

- Owner 指出 `v20.2.3` 在外部盤面明顯強勢、R3 進攻偏熱、漲停 / 過熱股很多時，`市場 / 題材證據 absent` 與 `無有效進場` 容易被誤讀成系統否定市場強勢，並要求確認「沒有證據時策略是否正確」。
- 本輪只修 Telegram 手機報文語意與強勢準備層：不放寬 BUY / 可買門檻，不改 RR / 過熱 / 漲停不追 / 回測 / 量能 threshold，不改 DB schema，不 live、不 backfill。
- CAO 服務已確認：
  - API: `http://127.0.0.1:9889/`
  - UI: `http://127.0.0.1:5173/`
- PM 已交付 `TASK.md`，定義：
  - `evidence absent` 只能表示內部結構化市場 / 題材資料未啟用或不足，不得寫成外部市場沒有證據。
  - R3 進攻偏熱且未持倉有漲停鎖價、過熱強勢、接近 / 已突破但不可追標的時，summary 新增 `強勢準備` 層。
  - 準備層必須標示不可追高、不可買或待觸發；不可混成可買。
  - 漏斗維持 `可買 / 可準備 / 僅追蹤 / 淘汰`，summary、漏斗、詳情數量與分類一致。
- Tech 已交付候選 diff：
  - `core/generator.py` VERSION 升為 `v20.2.4`。
  - `core/market_theme_evidence.py` 把 absent 文案改成 `內部結構化證據未啟用`，限制句改為仍依量價 / 風控判斷，不代表外部市場不強。
  - `core/generator.py` 新增 R3 `強勢準備` 顯示層與 `可準備` funnel：漲停鎖價、過熱降溫、突破回測都保持不可買 / 不追高 / 待觸發。
  - summary overflow 修正：隱藏項同狀態才可寫 `同狀態`；跨狀態改成 `另 N 檔：過熱降溫 1、突破回測 2，見詳情`。
- QA 最終驗證通過：
  - 第一次 QA 有效阻塞：強勢準備超過 3 檔且 hidden items 跨狀態時，原 summary 會誤寫 `另 3 檔同狀態見詳情`。
  - Tech 修正後，QA direct fixture 確認跨狀態 overflow 會按分類數量輸出，不再混桶。
  - `evidence absent` 文案不再否定外部市場強勢。
  - 可買仍為 0，準備層不進交易執行清單，卡片明確顯示不可追高 / 不可買 / 待觸發。
  - 無策略門檻、DB schema、watchlist、live Telegram、Supabase write、replay/backfill、持倉停利 dedupe diff。
  - 主 repo 驗證：`19 passed, 13 warnings`；策略 smoke `39 passed`；`git diff --check` 通過。
- Post-cycle review：
  - 根因分類：`repeated_pattern` / 手機 summary 壓縮與跨狀態分組漏測；既有手機閱讀、分類一致性與 QA 主動反證規則已覆蓋。
  - 本輪不新增 `AGENTS.md` 硬規則，避免把已覆蓋的執行漏測硬塞成文件膨脹；改沉澱到 `TASK.md` fixture、`QA_REPORT.md` 反證與 `CLEANUP_PLAN.md` 待觀察。

## Next Action

- commit / push 後清理 tech worktree。
- 後續若要讓 market/theme evidence 真的引用外部市場 / 產業資料，需要另開 provider / DB / cache 任務並先通知 Owner。

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

Architect 可用 CAO：

```text
研究：tools/cao_agent/run_architect_task.sh research "<研究問題>"
規劃：tools/cao_agent/run_architect_task.sh plan "<技術規劃問題>"
自動開發：tools/cao_agent/run_architect_task.sh auto "<Owner 任務>"

CAO 服務確認：tools/cao_agent/ensure_cao_services.sh
分配或啟動 CAO agents 後，Architect 必須先確認服務已啟動，再回覆 Owner 前端地址：http://127.0.0.1:5173/
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
