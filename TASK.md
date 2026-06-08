# TASK: today_buy_all_risk_summary_wording_20260608

## 任務狀態

- task_id：`today_buy_all_risk_summary_wording_20260608`
- 任務類型：normal_patch
- 狀態：done
- 版本建議：不升 Telegram 報文版本，維持 `v20.4.47`
- QA 分級：L2

## Owner 問題

Owner 貼出 2026-06-08 dry-run 報文，Summary 已顯示 `今日已買 5（已風控 5）`，但下一行仍寫 `今日交易已建立新倉 5 檔`，手機閱讀會誤讀成今日有成功新進場。

## 使用者可見結果

- 若今日買入檔全部已停損 / 減碼 / 硬風控，盤後簡報不得再稱為「已建立新倉」。
- Summary 改寫為「今日已買 N 檔，已全部轉入風控/停損減碼」。
- 明細改寫為「今日買入後風控：N 檔（...）」。
- 純新倉風控觀察、未轉停損減碼的既有語意保留。

## 非目標

- 不發 live Telegram。
- 不改 DB schema / RLS / grant / policy / role。
- 不改 production DB 寫入、backfill、策略 decision、RR 或買賣判斷。
- 不改 GitHub Actions schedule / notifier。

## 影響模組與直接消費者

- `presentation/report.py`
- `tests/test_generator_report.py`
- 直接消費者：`core.generator.generate_report(dry_run=True)` 產出的 Telegram Summary / 盤後簡報。

## 輸出契約

- `今日已買 N（已風控 N）` 時：
  - 結論使用 `今日已買 N 檔，已全部轉入風控/停損減碼`。
  - 交易明細使用 `今日買入後風控：N 檔（名稱列表）`。
  - 不得出現 `今日交易已建立新倉 N 檔`。
- 今日買入若部分風控、部分觀察：
  - 結論使用 `今日已買 N 檔（已風控 M/觀察 K）`。
  - 交易明細使用 `今日買入狀態：已風控 M/觀察 K（名稱列表）`。
- 今日買入若全部仍只是新倉風控觀察：
  - 保留既有 `今日交易已建立新倉` 語意。

## 版本契約

- 報文 header / `core.generator.VERSION` 維持 `v20.4.47`。

## 驗收條件

- Owner 標本等價 dry-run Summary 不再出現 `今日交易已建立新倉 5 檔`。
- 新增 regression test 覆蓋「今日買入全部轉風控」路徑。
- 既有今日買入純觀察路徑不回退。
- py_compile 通過。

## 失敗標本與驗收路由

- 失敗標本：`已粘贴的文本.txt` 內 2026-06-08 盤後 Summary：
  - `今日已買 5（已風控 5）`
  - `結論：今日交易已建立新倉 5 檔；新增有效進場：無。`
  - `今日交易：已建立新倉 5 檔（英業達、智原、建準、聯電、旺宏）`
- 驗收路由：formatter helper -> official `formatTelegramMessages` regression -> official `generate_report(dry_run=True)` artifact。

## 禁止事項與阻塞條件

- 不得 live Telegram delivery。
- 不得用 synthetic helper 結論取代 official Summary artifact。
- 若 Supabase read source-error，需標示 blocked，不得宣告 production dry-run 通過。
