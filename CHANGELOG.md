# CHANGELOG: report_actionability_consistency_v21_1_20260624

## 修改內容與修改檔案

- `core/generator.py`
  - 新增 `LOW_REPAIR_VOLUME_NOT_LOST_THRESHOLD = 0.8`。
  - 低位修復狀態新增 `support_broken`。
  - 低位修復量能門檻從硬性 `1.0x` 改為 `0.8x` 未失控門檻。
- `presentation/report.py`
  - 量能文字改為 `不足 / 偏低未失控 / 剛好 / 有效 / 攻擊量`。
  - 支撐跌破時顯示 `已跌破`，觸發改為 `重新站回支撐`。
  - 低位修復支撐跌破時標題改為 `等重新築底｜低位修復失效`。
  - 已突破但 RR 不足時改成 `已突破但追價風險過高`，等待回測後修復。
  - `等站回` 在絕對價差大於 10 時顯示 `站回距離偏大`。
  - 低位修復可買卡改為 `可買：小倉試單｜不追價`，並列失效線。
- `tests/test_generator_report.py`
  - 更新低位修復、RR 追價、突破站回距離與可買卡測試。
  - 新增支撐跌破與 0.9x 量能反證。

## 契約影響

- 低位修復的量能判斷不再要求必須大於 1.0x；`0.8x~1.0x` 為偏低但未失控。
- `support_broken` 成為 presentation 可用狀態欄位。
- 使用者可見 RR 極低情境改為語意說明，不再主顯示 raw RR gap。
- 報文排序與分組沒有新增 bucket。
- DB 寫入契約無變更。

## 版本同步

- 使用者可見版本仍為 `v21.1`。

## 直接消費者同步

- Telegram 未持倉卡片。
- Telegram 簡報摘要。
- dry-run report。

## 未影響模組

- DB schema / RLS / grant / policy。
- live Telegram delivery。
- position ledger / trade write path。
- market theme evidence backfill。

## 自檢命令與結果

- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "low_repair or failed_breakout or rr_blocker or actionability or reclaim or chase_risk or breakout_with_low_rr" -q`
  - Result: `12 passed, 219 deselected`
- `.\.venv\Scripts\python.exe -m pytest tests/test_generator_report.py -k "telegram_messages_use_summary_cards_and_detail or unheld_cards_follow_summary_group_order" -q`
  - Result: `2 passed, 229 deselected`
- `generate_report(dry_run=True)` smoke:
  - `HAS_NEAR_BUY=False`
  - `HAS_RAW_ELIMINATED=False`
  - `HAS_OLD_LOW_BUY=False`
  - `HAS_SUPPORT_WAIT_WHEN_BROKEN_SAMPLE=False`
  - `MESSAGE_COUNT=4`

## 覆蓋層級

- helper: `_low_repair_compact_lines`, `_breakout_distance_line`, `_entry_check_lines`。
- formatter: `formatTelegramUnheldCard`。
- official generator path: `formatTelegramMessages` related tests and `generate_report(dry_run=True)` smoke。
- production source: read-only dry-run only; no DB writes.

## 殘留風險

- Full `tests/test_generator_report.py` still contains older summary expectation failures unrelated to this patch.
- `.pytest_cache` permission warning persists on Windows and is non-blocking.
