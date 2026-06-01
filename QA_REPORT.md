# QA_REPORT:

## 測試範圍

- 任務尺寸：`normal_patch`
- QA level：`L2`
- 核對：`TASK.md`、`CHANGELOG.md`、git diff、`core/generator.py`、相關測試 diff。
- 可吸收 diff：`CHANGELOG.md`、`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`、`TASK.md`、`QA_REPORT.md`。
- 清理 / 瘦身 / refactor 證據表要求：本輪非清理任務，不適用。

## 風險預算與停止條件

1. 第三則仍分裂成多個 evidence/status 入口。
   - 驗證：檢查第三則 standalone heading count、禁止詞、手機閱讀順序。
   - 停止條件：出現 `簡短證據摘要`、獨立 `策略證據`、`來源狀態`、`漏斗證據`、`風險證據` 即 blocked。
2. source-missing / position_warning early return 仍只回單訊息或觸發 StopIteration。
   - 驗證：直接 patch `generate_report()` 的 source-missing 路徑，檢查回傳 3 則、第三則可被找到。
   - 停止條件：非 3 則、第三則缺 `簡報＋資料依據`、或 helper 找不到第三則即 blocked。
3. market/theme 與 strategy missing-source 被誤讀成可買依據。
   - 驗證：檢查第三則資料依據與決策簡報文案，確認 market/theme 只作背景，strategy sample missing/insufficient 仍 fail-closed。
   - 停止條件：第三則把 confirmed 寫成買點、推薦、可準備或進場理由即 blocked。

## 關聯風險掃描

- `TASK.md` / `CHANGELOG.md` / diff 一致：版本升至 `v20.4.15`，範圍限第三則 Telegram message、source-missing early return 與測試。
- 未看到 DB schema、write path、backfill、live Telegram 相關 diff。
- `git diff --check`：passed。
- L2 scoped tests：`arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：119 passed，169 warnings。

## 跨區塊語意一致性

- `formatTelegramMessages()` 維持 messages[0] 持倉、messages[1] 未持倉/候選、messages[2] 第三則；`include_detail=True` 時 Details Backup 仍追加最後。
- 第三則標題為 `🧾 v20.4.15 簡報＋資料依據`。
- QA 補充 probe 驗證第三則只有：
  - `決策簡報` count = 1
  - `資料依據` count = 1
  - 無 `簡短證據摘要`、`策略證據`、`來源狀態`、`漏斗證據`、`風險證據`
- source-missing early return 直接驗證：3 則訊息、第三則含 `今日結論`、`交易執行`、`持倉風控檢查`、`未持倉漏斗`，且含 `strategy sample：missing-source / fail-closed / 不產生進場理由`。

## 使用者誤讀風險

- 手機閱讀順序符合 TASK：先持倉卡、再未持倉卡、最後第三則簡報＋資料依據。
- 第三則先給持倉/新倉/背景短句，再放集中資料依據；未再拆出多個 evidence/status 入口。
- market/theme confirmed 文案限制為用途限市場/題材背景、不構成買點；QA 未發現第三則因此升格成可買、推薦或進場理由。

## 質疑與反證

- 反證 1：不只重跑 Tech tests，額外直接 patch `generate_report()` 的 `position_warning` 路徑，確認不再單訊息 early return，也沒有第三則定位失敗。
- 反證 2：額外用 `formatTelegramMessages(... include_detail=True)` 產生完整訊息，確認前兩則仍分離持倉/未持倉，第三則無 raw source noise，Details Backup 在最後。
- 反證 3：掃 diff 關鍵詞，未見 schema/write/live delivery 擴權痕跡。

## 未測項目

- 未跑 full pytest，符合 `normal_patch / L2` 範圍。
- 未做 production DB read/write、replay/backfill、live Telegram。
- 未稽核 2356 ledger/source-of-truth，TASK 明列非目標。
- 未處理 reply markup 附著最後一則 message 旁支風險，TASK 明列非目標。

## QA 結論

通過
