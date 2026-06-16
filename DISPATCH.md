# DISPATCH.md

## Active

- task_md_holds: `afterhours_summary_trade_plan_v21_1_20260616`
- status: `implemented + QA passed + full pytest passed + pushed`
- current_version: `v21.1`
- no live Telegram delivery in this cycle.
- no DB schema/write/backfill/prune in this cycle.

## Result Summary

- Owner challenged the盤後 `決策簡報`: only `持倉風控檢查` was useful; market counts, today-buy flow and unheld funnel were noise.
- Web benchmark checked:
  - Schwab trade plan: what to trade / when to enter / sizing / risk.
  - IG checklist: market conditions, entry/exit signals, risk rules.
  - ForTraders checklist: entry rules, support/resistance, volume, stops, risk/reward.
- Implemented:
  - afterhours summary now uses decision-plan structure:
    - `結論`
    - `明日計畫`
    - `持倉風控檢查`
  - removed market count line, duplicate today-buy status line, empty `新增有效進場：無`, and no-action unheld funnel.

## Verification

- Targeted:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short -k "afterhours or brief or summary or today_buy or funnel"`
  - result: `37 passed, 169 deselected, 49 warnings, 3 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `484 passed, 8 skipped, 165 warnings, 110 subtests passed`
- Official dry-run:
  - summary:
    - `結論：新倉無有效進場；今日買入紀錄已轉風控。`
    - `明日計畫：英業達、建準減碼/停損優先；未持倉：華邦電、南亞科等冷卻；旺宏、群創等回測；聯電等型態；仁寶、技嘉、緯創等接近。`
    - `持倉風控檢查`

## Current Git State

- branch: `main`
- completion: git completion passed after push.

## Next Action

- Observe next production `run_mode=bot` artifact.
