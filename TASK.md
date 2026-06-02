# TASK: 修復 default bot workflow 被 May backfill range guard 阻塞

## 任務狀態

- task_id: fix-bot-workflow-may-backfill-guard-20260602
- 任務類型: normal_patch
- 狀態: ready_for_tech
- 版本建議: 不要求使用者可見 Telegram / UI 版本升版；若 workflow log 或 CLI help 文字有可見契約變更，需在 CHANGELOG 說明。
- QA 分級建議: L2

## Owner 問題

GitHub Actions Stock Bot Pro / run-bot 在 workflow_dispatch 預設 run_mode=bot 時，仍執行 Backfill official market/theme evidence (retry 3 times)，並因目前日期為 2026-06-02，觸發 May range guard：

ValueError: market_theme_confirmed_evidence blocked: source date outside requested May range

結果是正常 bot 主流程被 May 回填步驟阻塞。截圖中的 Node.js 20 deprecation 是 warning，不是本輪失敗主因。

## 使用者可見結果

- Owner 使用 GitHub Actions 手動觸發預設 run_mode=bot 時，run-bot job 不再因 May backfill range guard 失敗而中斷。
- run_mode=backfill_may 與 run_mode=backfill_and_bot 的 May 回填語意仍清楚：只能寫入符合 May range guard 的資料，不得假寫越界資料。
- workflow log 能看出 bot 模式與 May backfill 模式的行為分界。

## 非目標

- 不處理 Node.js 20 deprecation warning。
- 不改 Telegram 報文內容、不做 live Telegram delivery。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不重設市場 / 題材策略邏輯。
- 不新增 production DML 繞過既有 script / service API。
- 不做全量 workflow 清理或 GitHub Actions 大改版。

## 影響模組與直接消費者

影響模組：

- .github/workflows/stock-bot.yml
- 如有必要，限縮調整 scripts/backfill_market_theme_sources.py 的 CLI 參數、預設日期或 exit/fail 行為。
- 如有必要，補充 workflow / script 對應測試或可重跑驗證腳本。

直接消費者：

- GitHub Actions Stock Bot Pro / run-bot job。
- 手動 workflow_dispatch 使用者，特別是預設 run_mode=bot。
- May evidence backfill 操作者，透過 run_mode=backfill_may 或 run_mode=backfill_and_bot。
- production safety guard：market_theme_confirmed_evidence May range 防線。

## 輸出契約

- run_mode=bot:
- 不應執行 May-only backfill write，或即使檢查 backfill 狀態也不得因 May range guard 阻塞 bot 主流程。
- 不得使用 --write --confirm-write 嘗試寫入 May range 外資料。
- bot 主流程仍應正常進入既有後續步驟。
- run_mode=backfill_may:
- May backfill 仍需執行。
- May range guard 必須保留。
- source date 不在 May requested range 時必須 fail closed，不可假成功、不可寫入越界資料。
- run_mode=backfill_and_bot:
- May backfill 語意必須明確：先跑符合 May guard 的回填，再進 bot。
- 若 May backfill 因越界資料 fail closed，整體可失敗，不得吞掉 production safety guard。
- 不得為了讓 bot 繼續而把越界 May backfill 標成成功。
- Workflow log:
- 需能區分 bot mode skipped May backfill、backfill mode executed May backfill、或 fail-closed blocked 的原因。
- 不要求處理 Node.js warning。

## 版本契約

- 既有 workflow_dispatch 預設 run_mode=bot 不得回退。
- 既有 run_mode=backfill_may 與 run_mode=backfill_and_bot 名稱不得回退或移除，除非 Architect 另行確認。
- 既有 production safety guard 不得降級。
- 不要求 Telegram / UI 版本升版。
- 若 script CLI 參數新增或預設日期變更，需維持既有參數可用，並在 CHANGELOG 寫出相容性。

## 驗收條件

1. 模擬 run_mode=bot
- 可重跑驗證顯示 May backfill write step 不會執行，或不會因 source date outside requested May range 阻塞。
- 驗證需覆蓋 workflow 條件或等價 script invocation，不只口頭檢查 YAML。
2. 模擬 run_mode=backfill_may
- May backfill 仍會執行。
- 使用 May range 外 source date 時仍觸發 fail-closed guard。
- 不得出現越界資料被寫入或被標成成功的行為。
3. 模擬 run_mode=backfill_and_bot
- May backfill 語意清楚。
- 若 backfill 資料越界，guard 仍能阻止該模式，不可因 bot 後續流程而吞錯。
4. 回歸檢查
- Node.js 20 deprecation warning 不列為本輪修復目標。
- 不改 DB schema。
- 不觸發 live Telegram delivery。
- Tech 需提供可重跑命令與結果；QA 需補至少一個 Tech 未覆蓋的 workflow 條件或負面案例反證。

## 範例或 Fixture

建議 fixture / 模擬情境：

- run_mode=bot
- input: workflow_dispatch.run_mode=bot
- expected: May backfill write step skipped，或 log 顯示 bot mode does not run May backfill；job 不因 May range guard 失敗。
- run_mode=backfill_may
- input: May requested range，但 source date 為 2026-06-02
- expected: ValueError: ... source date outside requested May range 或等價 fail-closed error。
- run_mode=backfill_and_bot
- input: May requested range，source date 越界
- expected: fail closed before bot 或清楚標記 backfill blocked；不得假成功進入寫入完成狀態。

## 明確禁止事項

- 禁止繞過、移除或放寬 production safety guard。
- 禁止把 May range 外資料寫入 market_theme_confirmed_evidence。
- 禁止手寫 production DML。
- 禁止改 DB schema / RLS / grant / policy / role。
- 禁止 live Telegram delivery。
- 禁止把 Node.js warning 當成本輪主 bug 修。
- 禁止把本輪擴大成 workflow 全量重構或策略資料重建。

## 阻塞條件

- 若無法在目前 repo 中確認 run_mode 既有契約、workflow 名稱或 backfill script CLI contract，Tech 必須 blocked 並要求 Architect 補充。
- 若需要新增 DB schema 或改 production policy 才能修，必須 blocked。
- 若驗證需要 production secret 或 live write 才能完成，必須改用 dry-run / mock / local fixture；無法替代時 blocked。
- 若現有 backfill script 沒有可測方式區分 date range，Tech 需先補最小可測接口；若會擴成大改，blocked 交回 Architect。

## 本輪停止條件

完成到以下範圍即停止：

- run_mode=bot 不再被 May backfill range guard 阻塞。
- backfill_may / backfill_and_bot 仍保留 May guard 與 fail-closed 語意。
- 提供可重跑驗證與 QA L2 反證。

以下旁支只記待辦，不納入本輪：

- Node.js 20 warning 升級。
- GitHub Actions 全面整理。
- Telegram 報文格式調整。
- DB schema / policy 改造。
- 市場 / 題材策略重新設計。
