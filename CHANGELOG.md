# CHANGELOG: multi_day_rebound_retest_v21_1_20260616

## 修改內容與檔案

- `core/generator.py`
  - 新增 `multi_day_rebound_needs_retest(data)`。
  - 使用當次 payload 的 `closes` 與 `price` 判斷最近三段是否連續抬高，且累計漲幅 >= 5%。
  - 單日強彈 `live_change >= 7%` 仍走原本急彈規則。
  - `decision=FAIL`、`FAILED_BREAKOUT`、`reject_family=突破失敗` 排除，不被多日修復覆蓋。
  - 未持倉漏斗將符合條件的多日弱反彈修復從 `淘汰` 升為 `等回測`。
- `presentation/report.py`
  - 多日修復卡片顯示 `等回測｜反彈修復待回測`。
  - 進場原因顯示 `連漲修復待回測`。
  - 可買條件維持回測確認與非追高。
- `tests/test_generator_report.py`
  - 新增旺宏多日修復標本。
  - 更新既有 summary count 與弱反彈卡片預期。

## 契約影響

- message list:
  - 符合多日修復條件的 `WEAK_REBOUND` 不再顯示淘汰。
  - 不新增可買；只改成追蹤中的 `等回測`。
- 函式回傳:
  - `unheld_funnel_state` 對多日修復弱反彈可回傳 `等回測`。
- DB:
  - 無 schema change。
  - 無 write/backfill。
- CLI/runner:
  - 無 live Telegram delivery。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `generate_report(dry_run=True)` 已驗 official message list。
- `formatTelegramMessages` / `unheld_funnel_state` tests 已驗。

## 未影響模組

- 持倉行動未改。
- 停損 / 減碼 / 停利未改。
- DB writer/backfill 未改。

## 自檢命令與結果

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short -k "weak_rebound or rebound or v21_1_multi_day"`
  - `2 passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `480 passed, 8 skipped, 108 subtests passed`
- Dry-run:
  - `generate_report(dry_run=True)`
  - 旺宏顯示 `等回測｜反彈修復待回測`
  - summary 顯示未持倉 `僅追蹤8`，不再把旺宏列為淘汰。

## 覆蓋層級

- funnel state: covered。
- formatter: covered。
- official generator: covered。
- runner production artifact: 未 live delivery；需等下次 scheduled bot artifact 觀察。

## 殘留風險

- 若 production artifact 仍顯示舊淘汰文字，優先查 runner 使用的 commit / deployment path。
