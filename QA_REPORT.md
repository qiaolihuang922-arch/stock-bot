# QA_REPORT: evidence-chain hard-gate fail-closed v20.4.43

## 測試範圍

- 驗證 Tech diff：`core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`、`CHANGELOG.md`。
- 驗證層級：official `formatTelegramMessages` message list、`build_report_context` / `stock_judgments`、summary / funnel / card 手機閱讀順序。
- 未執行 DB write、backfill、manual DML、live Telegram。

## 風險預算與停止條件

- 風險 1：`decision_judgment` 只變成可見文字，summary / funnel / card 仍把 hard-gated 標的列為可買。停止條件：低 RR `trend_continuation` 出現 `新倉建議`、綠卡或小倉買點即 blocked。
- 風險 2：source missing / source-error / conflicting evidence 被 evidence-chain 說明誤讀成可授權買入。停止條件：任一路徑顯示新倉建議或推薦語氣即 blocked。
- 風險 3：持倉 hard stop 被 evidence wording 稀釋，或 DB/live non-bypass restriction 外露成操作授權。停止條件：hard stop 卡缺風控阻塞，或可見報文出現 live Telegram 授權語氣即 blocked。

## 關聯風險掃描

- `VERSION` 升至 `v20.4.43`，測試中的可見版本同步更新。
- `stock.*.decision_judgment` 與 `report_context["stock_judgments"]` 是新增 report context / manifest 欄位；未新增 DB contract。
- `unheld_funnel_state` 新增 hard-gate fail-closed guard，低 RR / 過熱 / 量能 / failed breakout 不再保留 `可買`、`趨勢延續`、`可準備`。
- `presentation/report.py` 把 `決策證據：...` 合併到既有 reason slot，未新增大區塊，v20.4.42 `卡關主因` / `量化差距` 兩行保留。

## 跨區塊語意一致性

- Focused official replay 通過：低 RR `trend_continuation` 的 `eligibility_state` 是 `blocked`，summary 不顯示 `新倉建議 1` / `趨勢延續買入 1 檔小倉`，卡片顯示 `等RR修復`、`卡關主因`、`量化差距`、`決策證據`。
- 混合場景額外 probe 通過：一檔真正 BUY + 一檔低 RR `trend_continuation` 時，summary 只列真正 BUY；低 RR 標的只進 `等RR修復`，不污染可買計數。
- 持倉 hard stop 卡片保留停損語意，並追加 `決策證據：來源可追溯；阻塞 hard stop / 持倉風控`。

## 使用者誤讀風險

- 已降低「證據達標 = 一定可買」的誤讀：hard gate 在 judgment、summary、funnel、card 四層同步 fail closed。
- 可見報文不顯示 `live Telegram`，DB/live non-bypass restriction 只留在 manifest / context blocking reasons，不變成下單授權。
- 殘留風險：`決策證據` 的 wording / blocker 排序仍可再精修，但不阻塞本輪「證據鏈必須能推敲且不得假可買」。

## 質疑與反證

- Tech focused suite：
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_43_localqa_focused arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_43 or v20_4_42_postmarket_unheld_gate_attribution_readability_message_list_replay or confirmed_evidence_preserves_limit_lock_chase_hard_blocker or v20_4_39_post_market_mixed_trend_and_prepare_keeps_trend_actionable or v20_0_14_post_market_fixture_uses_next_day_plan_semantics or v20_4_18_structural_artifacts_cover_three_fail_closed_cases or v20_4_20_maturity_report or v20_4_25_strategy_sample_source_error_blocks_action_without_hiding_available_price or v20_4_16_unheld_card_fails_closed_when_ohlcv_missing or trend_continuation_official_report_has_separate_small_buy_bucket' -q` -> 14 passed。
- QA 補充 direct consumer probe：
  - official `formatTelegramMessages` mixed payload：`建準 BUY` + `緯創 trend_continuation rr=0.8` -> summary 只列 `建準 可買`；`緯創` 卡為 `等RR修復｜RR不足`，含 `卡關主因` / `量化差距` / `決策證據`，且不含小倉買點。
- Static checks：
  - `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/v20_4_43_localqa_pycompile arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py` -> passed。
  - `git diff --check` -> passed。
- QA runner gap：
  - `tools/cao_agent/run_qa_code.sh ...` 啟動後卡在 Codex usage limit 互動提示；直接 `codex exec --model gpt-5.4-mini` 也回報 usage limit。這是 runner / quota gap，不是產品驗證失敗。

## 未測項目

- 未跑 full pytest。
- 未跑 production runner artifact。
- 未驗 production DB source artifact。
- 未做 DB write、backfill、manual DML、live Telegram。

## QA 結論

conditional pass。可吸收 diff 範圍限於 `core/generator.py`、`presentation/report.py`、`tests/test_generator_report.py`、`TASK.md`、`CHANGELOG.md`、`QA_REPORT.md` 及收口文件；正式 QA agent 被 usage limit 阻塞，但本地 official message-list replay 與補充 direct consumer probe 已反證本輪主要手機閱讀風險。
