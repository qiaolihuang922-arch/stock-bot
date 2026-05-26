# DISPATCH.md

本文件由 Architect 維護，用來讓獨立對話窗按共享文件接力。各部門不需要收到即時通知，只要讀本文件判斷自己是否該工作。

## Current Task

- task_id: `v20.0-strategy-evidence-foundation`
- task_name: `v20.0 Strategy Evidence Foundation`
- task_type: `development`
- version_level: `major`
- qa_level: `L3`
- owner_status: `requested`
- architect_status: `qa_accepted`
- pm_status: `task_ready`
- tech_status: `changelog_ready`
- qa_status: `qa_passed`

## Next Action

- Architect: 已吸收 QA `QA_REPORT.md`；本輪 v20.0 major 開發已通過 L3，下一步做提交前 diff 檢查與必要驗證後提交推送。
- PM: 已完成 v20.0 `Strategy Evidence Foundation` 正式 `TASK.md`，範圍限定策略證據資料層、分類績效報告與 Telegram 策略證據摘要。
- Tech: 已交付 `CHANGELOG.md`，實作 v20.0 策略證據資料層、分類績效報告、Telegram 策略證據摘要與 replay/backfill dry-run 路徑。
- QA: 已完成 L3 驗證並提交 `QA_REPORT.md`；full pytest、replay/backfill dry-run、DB payload/schema、Telegram contract、策略不變性、未來資料洩漏與證據層降級均通過。
- Owner: 等待 Architect 收口提交；production schema apply、live Supabase write、live Telegram delivery 需另開明確批准流程。

## Task Brief

Owner 反馈：

- Owner 質疑策略本身可能有問題，不是顯示問題，也不是只針對旺宏單股：
  - 旺宏 2337 昨日約 140，今日約 160。
  - 昨日策略輸出淘汰，今日仍輸出淘汰。
  - 若外部行情、新聞、評論都顯示旺宏強勢，策略連續淘汰可能代表策略條件、資料映射或分類語意有缺陷。
- Owner 進一步指出：整個策略層不能只用簡單單日邏輯判斷複雜股市；資料不夠可以抓，需要多日資料可以做資料庫處理。
- Owner 要求建立能檢驗策略是否真的有效的流程，不接受只用內部策略測試說「沒問題」。
- Owner 明確定調：後續開發主線必須升級策略層，而不是一直修改顯示層。顯示層升級不能替代策略過時問題。
- Owner 補充硬邊界：所有 v20 設計最終仍必須服務現有「定時執行 GitHub Actions / 腳本 -> 產生報文 -> 發送到 Owner Telegram」流程，不做脫離 TG 報文的獨立平台或重型儀表板。
- Architect 初步外部搜尋發現公開資料確有旺宏近期強勢與題材線索，例如 StockGo 顯示 2337 旺宏收盤 160.00，MoneyDJ 新聞提到 4 月營收年增 153.71%；CMoney 有旺宏上漲逾 9% 至 157.5 的即時新聞；富聯網/時報資料提到旺宏曾因短期漲幅過大列注意股。
- PM 研究已確認：旺宏不一定應直接買，但 `淘汰｜弱反彈待確認` 可能錯誤表達「強題材 + 高波動 + 注意股」。
- 本輪已進入 v20.0 major 開發：第一版只建立策略證據資料層、分類績效報告與 Telegram 策略證據摘要，不直接改策略門檻。

不可變更：

- 本輪 Architect 只分派與收口，不直接實作。
- Tech 可依 `TASK.md` 修改資料層、證據報告、Telegram 摘要、replay/backfill dry-run 與必要 DB payload / schema 文件。
- 不改 BUY / SELL 判斷，不改 `decision=BUY` 產生條件，不改 `is_tradeable=True` 條件，不改 `action_pct`。
- v20 設計不得超出現有交付形態：最終輸出仍是 Telegram 報文；資料層與驗證層只能支撐報文策略品質，不應變成需要 Owner 改工作流的新產品。
- 不用內部測試通過來替代外部事實比對。
- Tech 不做全 repo 分析；QA L3 可依任務執行 full pytest、replay/backfill dry-run、DB payload 路徑與 Telegram contract 驗證。

## Status Values

- `todo`: 等待該角色處理。
- `waiting_pm`: Tech 或 QA 等待 PM 交付。
- `waiting_tech`: QA 等待 Tech 交付。
- `task_ready`: PM 已交付 `TASK.md`。
- `changelog_ready`: Tech 已交付 `CHANGELOG.md`。
- `qa_passed`: QA 驗證通過。
- `qa_failed`: QA 驗證失敗。
- `blocked`: 該角色遇到阻塞，需 Architect 或 Owner 判斷。
- `completed`: 非開發類任務已由負責角色完成。
- `not_required`: 本輪不需要該角色處理。
- `qa_accepted`: Architect 已吸收 QA 結論並更新狀態。
- `research_dispatched`: Architect 已建立研究任務。
- `research_ready`: 該角色已提交研究摘要。
- `research_accepted`: Architect 已吸收研究摘要並整理結論。

## Version / QA Levels

- version_level `patch`：bug / 文案 / 顯示一致性，不改策略意圖。
- version_level `minor`：新增使用者可見能力或報文結構。
- version_level `major`：改策略核心、DB schema、交易狀態機、正式寫庫或跨日持久化。
- version_level `none`：純流程 / 文件規則補強，不對應產品版本。
- qa_level `L1`：局部 formatter / snapshot / 指定回歸。
- qa_level `L2`：策略不變性 + formatter + snapshot + 相關模組測試。
- qa_level `L3`：full pytest + replay/backfill dry-run + 入庫 payload 路徑 + 額外風險掃描。
- qa_level `process`：純流程文件補強，不要求測試部門驗證。
- qa_level `research`：研究任務，不執行測試；QA 後續只做研究反證與風險質疑。
- minor 預設 L3；major 必須 L3 且需 Owner 明確批准。

## Fixed Startup Commands

Owner 對 Architect：

```text
按 AGENTS.md 和 DISPATCH.md 處理這個需求，分派並更新狀態文件。
```

Owner 對 PM：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、RESEARCH.md，按 PM 職責處理；v20 研究已 conditional approval，請撰寫 v20.0 Strategy Evidence Foundation 的正式 TASK.md。第一版只做策略證據資料層與分類績效報告，不直接改 BUY / SELL、不把外部新聞直接接入買點，且所有產物必須回到定時任務產生 Telegram 報文。
```

Owner 對 Tech：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、RESEARCH.md，按 Tech 職責處理；如果 tech_status 是 todo 且 TASK.md 已 ready，就實作 v20.0 Strategy Evidence Foundation。第一版只做策略證據資料層、分類績效報告與 Telegram 策略證據摘要；不得直接改 BUY / SELL、不得放寬 RR / 過熱 / 停損 / 停利 / 加碼門檻、不得把外部新聞直接接入買點。完成後改寫 CHANGELOG.md。
```

Owner 對 QA：

```text
讀取 AGENTS.md、DISPATCH.md、CURRENT_STATE.md、TASK.md、CHANGELOG.md、RESEARCH.md，按 QA 職責處理；若 qa_status 是 todo 且 Tech 已交付 CHANGELOG.md，請執行本輪 qa_level 指定驗證，補直接消費者、跨區塊語意一致性、使用者誤讀風險、負面案例與關聯風險掃描，完成後改寫 QA_REPORT.md。
```

Owner 回到 Architect：

```text
讀取 DISPATCH.md、RESEARCH.md，整理 Architect Conclusion，更新 CURRENT_STATE.md 和 CLEANUP_PLAN.md。
```
