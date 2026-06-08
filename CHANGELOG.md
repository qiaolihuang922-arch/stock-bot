# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險：Summary 語意錯誤會讓 Owner 把已轉風控的今日買入誤讀成可接受的新倉成立。

## 修改內容

- `presentation/report.py`
  - 新增 `_today_buy_risk_names()`，集中判斷今日買入中已轉停損 / 減碼 / 硬風控的名稱。
  - 盤後簡報結論依今日買入狀態分三種：
    - 全部已風控：`今日已買 N 檔，已全部轉入風控/停損減碼`。
    - 部分風控：`今日已買 N 檔（已風控 M/觀察 K）`。
    - 全部仍觀察：保留 `今日交易已建立新倉 N 檔`。
  - 今日買入明細同樣分流為 `今日買入後風控` / `今日買入狀態` / `今日交易已建立新倉`。
- `tests/test_generator_report.py`
  - 新增「今日買入全部轉風控」盤後 Summary regression。
  - 既有今日買入純觀察、來源說明、明日計畫測試維持通過。

## 修改檔案

- `presentation/report.py`
- `tests/test_generator_report.py`
- `TASK.md`
- `CHANGELOG.md`
- `QA_REPORT.md`
- `DISPATCH.md`
- `CURRENT_STATE.md`

## 契約影響

- Telegram 報文版本維持 `v20.4.47`。
- 只改盤後 Summary 文案分流，不改 message list 數量、卡片排序、DB payload、策略 decision、RR、notifier 或 workflow。

## 直接消費者同步

- `generate_report(dry_run=True)` 的 Summary 已反映同日買入後全部風控的狀態。
- Owner 手機閱讀時，`今日已買 5（已風控 5）` 不再被下一行「已建立新倉」抵消。

## 未影響模組

- 未改 `core/generator.py` 版本與策略。
- 未改 DB read/write/backfill。
- 未改 Telegram live delivery / notifier。
- 未改 GitHub Actions。

## 自檢命令與結果

- `.venv/Scripts/python.exe -m pytest tests/test_generator_report.py -k "afterhours_brief_counts_today_buy_holdings_as_executed_new_positions or afterhours_brief_does_not_call_all_risk_today_buys_established_new_positions or afterhours_today_buy_holding_explains_current_non_buy_by_source or post_market_holding_risk_precedes_tomorrow_plan_without_duplicate_downgrade" -q` -> 4 passed, 3 subtests passed。
- `.venv/Scripts/python.exe -m py_compile presentation/report.py tests/test_generator_report.py` -> passed。
- `.venv/Scripts/python.exe -c "from core.generator import generate_report; messages, _ = generate_report(dry_run=True); ..."` -> Summary 顯示 `今日已買 5 檔，已全部轉入風控/停損減碼` 與 `今日買入後風控：5 檔（英業達、智原、建準、聯電、旺宏）`。

## 覆蓋層級

- formatter：盤後 Summary helper 分流已測。
- official generator：`formatTelegramMessages` regression 已測。
- runner artifact / production source：`generate_report(dry_run=True)` 已用本機 Supabase read-only config 產出 official Summary artifact。
- 未測 live Telegram delivery，且本輪禁止 live delivery。

## 殘留風險

- 未對外發送 TG，只驗證本地 official dry-run output。
- `.pytest_cache` 仍有 Windows 權限 warning，不影響測試結果。
