# CLEANUP_PLAN.md

本文件由 Architect 維護，用來記錄清理、收斂與避免重複工作的計畫。未經 Owner 或明確任務確認，不直接執行大範圍產品清理。

## Cleanup Principles

- 固定 8 份 Markdown 不刪除，只改寫內容。
- 不主動重構核心代碼，不清理未知來源未提交變更。
- 流程文件可以由 Architect 直接壓縮；產品代碼、測試、runtime 文件清理需 PM / Tech / QA 接力。
- 清理不能用「可能有用」作保留理由；保留、刪除、待確認都要有 evidence。
- 不確定項只記入待確認，不直接刪。
- commit / push 後必須壓縮工作流 Markdown，避免它們變成聊天流水。

## Rule Hygiene

- 不把每次事故直接塞進 `AGENTS.md`。
- Post-cycle review 先分類：
  - `one_off`：單次任務上下文問題，只寫入 `CURRENT_STATE.md` 或本文件短摘要。
  - `repeated_pattern`：同類問題重複發生，合併到既有規則。
  - `high_risk_invariant`：會造成越權、錯單、live 副作用、版本回退、手機誤讀，可升為硬規則。
  - `runner_gap`：交由 runner / agent prompt 補丁，不用文案規則硬撐。
  - `doc_bloat`：壓縮或刪除過期流水。
- 新規則必須優先改寫 / 合併既有段落；只有沒有現成位置時才新增小節。
- 若新增規則讓文件更長，必須同時刪除或壓縮已被取代的舊描述。

## Completed Compression

- `CURRENT_STATE.md` 已由版本流水改為：
  - 專案快照。
  - 當前流程狀態。
  - CAO 可用性。
  - 最近高信號里程碑。
  - 穩定產品契約。
  - 模組圖、邊界、待辦。
- `CLEANUP_PLAN.md` 已由長流水改為：
  - 清理原則。
  - 規則治理。
  - 已完成壓縮。
  - 待確認項。
- `RESEARCH.md` 保留市場 / 題材證據鏈研究結論，刪除終端過程與長表格流水。
- `DISPATCH.md` 切換為本輪流程審計與壓縮任務，不再保存上一輪產品任務完整過程。
- CAO runner prompt 已補任務尺寸 / 最小改動 / 風險預算 / 停止條件，避免 PM、Tech、QA 把小任務擴成大任務。
- CAO 本機部署資產已收斂到 repo：
  - runner 腳本、profile 模板、profile 安裝、bootstrap、部署說明都在 `tools/cao_agent/`。
  - 可下載依賴只記錄來源與安裝指令，不把外部 runtime 塞進 repo。

## Pending / Watchlist

- Tech runner gap 已補：`run_tech_write.sh` 改為讓 Tech 在 final answer 輸出 `# CHANGELOG:`，由 runner 寫入 worktree `CHANGELOG.md`，避免 agent 卡在直接編輯交付文件。
- 本輪 `v20.2.1` tiny patch 中，QA 曾攔下 `CHANGELOG.md` / tracked diff / VERSION 不一致：
  - 根因分類：`runner_gap` / handoff drift，不是產品規則缺失。
  - 已用 QA 重跑與主 repo 驗證收口。
  - 已補 runner guard：`run_tech_write.sh` 遇到 dirty tech worktree 時預設拒絕 reset，避免修交付摘要時丟掉候選產品 diff；若要修 handoff 文件，需用 `CLEAN_TECH_WORKTREE=0`，若要刻意丟棄需顯式 `ALLOW_DISCARD_TECH_WORKTREE=1`。
- 本輪 `v20.2.2` 首次 auto 被 runner guard 誤攔：
  - 根因分類：`runner_gap`，guard 把正常 `TASK.md` handoff 當成 candidate diff。
  - 已補腳本：dirty worktree guard 只攔手稿 / 產品 / 測試候選 diff，不攔固定 handoff files。
  - QA 另攔下第二段停利文案不明與 CHANGELOG 不一致，已修正並通過。
- 本輪 `v20.2.3` 第二段停利去重：
  - 根因分類：`repeated_pattern` / 手機跨區塊一致性不足，不是單純文案 bug。
  - QA 三次攔截有效：未執行第二段被過度去重、持倉卡 `今日 無` 與 execution 文案同卡矛盾、`CHANGELOG.md` 自述與 diff 不一致。
  - 已用任務卡與測試沉澱：completed / partial / unexecuted 三段 fixture，以及持倉卡 / summary / 風控檢查同源驗證。
  - 暫不新增 `AGENTS.md` 硬規則，因既有手機閱讀、持倉一致性、QA 主動反證規則已覆蓋；本輪屬於執行不到位，後續用 QA fixture / runner review 追蹤。
  - 待補流程：若類似問題再發生，將「execution state 必須單一來源供應卡片 / summary / checklist」升級為高風險 invariant。
- 下一次產品任務完成後，確認 Post-cycle Review Gate 是否有做到：
  - 根因分類。
  - QA 攔截是否沉澱成 guard。
  - 是否避免把 one-off 事故塞進 `AGENTS.md`。
  - 是否壓縮 `DISPATCH.md` / `CURRENT_STATE.md` / `CLEANUP_PLAN.md`。
- 下一次 CAO auto 任務後，確認：
  - PM 是否真的先判斷任務尺寸，且 tiny patch 沒膨脹。
  - Tech 是否真的維持最小 diff，且未過擬合測試或回退既有契約。
  - QA 是否真的使用風險預算與停止條件，且未無理由擴大驗證。
  - Tech worktree 是否乾淨起跑。
  - QA `.qa_tmp/` 是否足夠且未改 tracked files。
  - handoff hash gate 是否有效。
  - `CHANGELOG.md` / `QA_REPORT.md` 是否無 transcript 污染。
- 證據鏈 production 化若需要 DB table / cache / external provider，先通知 Owner，再進 PM 任務，不在本文件直接決策。
- 若要做真正 code cleanup，需另開清理任務並要求 Tech 提供 `path / claim / evidence / risk / action` 表，QA 逐項反證。
- 中文 CAO UI 是大型外部 checkout；若 Owner 要求重部署時完全保留中文化，需要另開任務抽最小中文 patch 或建立獨立 fork，不直接整包塞進主 repo。

## Fixed Keep List

- `AGENTS.md`
- `DISPATCH.md`
- `RESEARCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`

## Cleanup Levels

- `L0`：文件壓縮，只更新總控摘要文件，不碰產品代碼。
- `L1`：局部文案 / 測試說明 / 命名收斂。
- `L2`：formatter、策略、資料來源或 DB 邊界相關清理，需 PM 任務與 QA 驗證。
- `L3`：跨模組、replay/backfill/DB 相關清理，需 Owner 明確批准。

## Next Action

- 本輪完成後 commit / push，並執行 CAO worktree cleanup。
- 後續等待 Owner 下一個需求；若是產品 / 顯示 / 策略 bug，先分派 PM。
