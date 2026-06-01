# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：調整盤後 Telegram 使用者可見報文與測試 probe；不改 strategy decision、RR 計算、holding_status、DB write path、schema、VERSION 或 live delivery。

## 修改內容

- `presentation/report.py`：盤後第三則改為高密度「盤後簡報」，不再把第一則 summary 的交易段落、持倉風控清單、漏斗與索引整段搬進第三則。
- `presentation/report.py`：策略樣本不可用狀態改為盤後第三則集中顯示一次，原因單一化為來源缺失 / 樣本不足 / 來源讀取異常之一。
- `presentation/report.py`：盤後持倉 / 未持倉卡片不再逐檔重複 `策略樣本：不可用，本次不納入判斷`。
- `presentation/report.py`：盤後卡片輸出時把盤中語境詞替換為盤後 / 下一交易日語境。
- `core/generator.py`：在 presentation deps 中注入 `_strategy_sample_unavailable`，供卡片決定是否省略逐檔策略樣本不可用行。
- `tests/test_generator_report.py`：新增可重跑 probe，覆蓋本輪 Owner 指出的主要誤讀風險。

## 修改檔案

產品 / 測試 diff：

- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`

Architect handoff / 復盤：

- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`
- `CLEANUP_PLAN.md`

## 契約影響

- Message list 順序不變：持倉卡、未持倉卡、第三則簡報＋資料依據，Details Backup 仍只在 `include_detail=True` 時追加。
- 盤後第三則可見文案有變更：從近似完整 summary 改為短摘要，集中回答新倉、持倉、策略樣本資料狀態與明日前確認事項。
- 盤後卡片可見文案有變更：不再逐檔重複策略樣本不可用；盤後不再顯示盤中語境詞。
- 非加碼持倉仍顯示 `新倉 RR：不適用（既有持倉）`，不顯示新倉 RR 數字；新倉候選 RR 保留。
- DB 寫入、payload shape、策略 decision、持倉狀態機、VERSION、live Telegram delivery 無變更。

## 可重跑檢查 / QA Probe

- 新增測試：`test_v20_4_21_afterhours_brief_is_concise_and_cards_do_not_repeat_strategy_sample`。
- 覆蓋錯誤：
  - 第三則複製完整 summary / 交易細節。
  - 策略樣本不可用在整份盤後報文重複出現。
  - 單檔卡片重複策略樣本不可用。
  - 盤後報文出現盤中語境。
  - 非加碼持倉顯示新倉 RR 數字。
  - 新倉候選 RR 被誤刪。
- QA 另補 source-error 負面路徑，確認同一份報文不混用 missing-source / 樣本不足 / source-error 主狀態。

## 直接消費者同步

- `formatTelegramMessages()` 直接消費者會看到盤後第三則摘要化，但 message order 不變。
- GitHub runner / dry-run 仍消費同一 list of messages。
- Telegram live delivery 未執行。

## 未影響模組

- DB schema / RLS / grant / policy / role / index / constraint。
- production DB write、backfill、live Telegram。
- 策略選股、買賣、加碼、減碼、停損、停利決策。
- `core/generator.VERSION`，仍為 `v20.4.21`。
- notifier / Telegram delivery consumer。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：92 passed，181 warnings。
- `git diff --check`：passed。

## 殘留風險

- 盤後第三則摘要化會改變依賴第三則完整細節的舊閱讀習慣；本輪按 Owner 要求把細節留在前兩則卡片，第三則只留決策摘要與資料狀態。
- 盤後語境替換目前是 formatter 層字串替換；未來若新增新的盤中詞，需同步擴充 probe。
- 未驗 live Telegram reply markup 附著位置；這是既有旁支風險。

## 今日錯誤復盤與流程補強

- 根因：今天多次把「輸出看起來有證據」誤當成「手機閱讀上有用」，導致第三則重複 summary、卡片逐檔重複狀態、策略樣本狀態互相打架。
- QA 是否攔住：本輪 QA 攔住了 CHANGELOG 仍寫成舊 refactor 口徑的錯誤，避免把可見文案變更講成無變更。
- 流程補強：不新增死規則，改用 `tests/test_generator_report.py` 的盤後手機閱讀 probe 固化檢查；以後同類錯誤會在測試中直接 fail。
- Runner gap：Tech worktree 殘留上一輪 diff 阻塞新任務；本輪已用 discard 清掉隔離 worktree 舊候選，後續應把 worktree hygiene 自動化列為 runner follow-up。
