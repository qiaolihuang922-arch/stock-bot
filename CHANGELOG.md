# CHANGELOG: afterhours_summary_trade_plan_v21_1_20260616

## 修改內容與檔案

- `presentation/report.py`
  - `_afterhours_brief_lines` 改為交易計畫摘要。
  - 移除盤後 summary 的市場統計流水與今日買入重複行。
  - 新增 `明日計畫` 聚合：
    - 今日買入風控優先。
    - 今日買入觀察守警戒。
    - 有新倉候選 / 可準備時列明開盤確認。
    - 無新倉候選時用未持倉策略分組作明日追蹤。
  - `未持倉狀態` 僅在 actionable / prepare 存在時顯示。
- `tests/test_generator_report.py`
  - 更新盤後 summary regression，防止市場統計流水、空新倉占位、無操作漏斗回退。

## 契約影響

- 盤後 summary message list 變短：
  - 保留結論 / 明日計畫 / 持倉風控檢查。
  - 不再輸出空的新倉占位與純統計漏斗。
- 策略判斷不變：
  - 不新增可買。
  - 不改持倉減碼 / 停損 / 續抱。
  - 不改未持倉卡片判斷。

## 版本同步

- Runtime 報文版本維持 `v21.1`。

## 直接消費者同步

- `generate_report(dry_run=True)` official summary covered。
- `formatTelegramMessages` targeted summary tests covered。
- live Telegram 未執行。

## 未影響模組

- `core/generator.py` 策略核心未改。
- DB schema / write / backfill / prune 未改。
- future watch、財報、歷史類比未改。

## 自檢命令與結果

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short -k "afterhours or brief or summary or today_buy or funnel"`
  - `37 passed, 169 deselected, 49 warnings, 3 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - `484 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Official dry-run:
  - `generate_report(dry_run=True)`
  - Summary now:
    - `結論：新倉無有效進場；今日買入紀錄已轉風控。`
    - `明日計畫：英業達、建準減碼/停損優先；未持倉：華邦電、南亞科等冷卻；旺宏、群創等回測；聯電等型態；仁寶、技嘉、緯創等接近。`
    - `持倉風控檢查`

## 覆蓋層級

- formatter: covered。
- official generator message list: covered。
- dry-run artifact: covered。
- production runner / live Telegram: not run by design。

## 殘留風險

- `.pytest_cache` 仍有 WinError 5 warning，不影響測試結果。
