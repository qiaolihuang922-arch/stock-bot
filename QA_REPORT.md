# QA_REPORT: trend_continuation_v20_4_36_validation_monitor_report_noise_20260603

## 測試範圍

- 任務尺寸：mixed_patch；1/2 為 risk_patch，3/4/5 為 normal_patch。
- QA 分級：L3。
- 本輪驗證範圍：
  - trend_continuation 正向觸發、反例、研究 / 實盤判定 parity。
  - official generator / report 手機路徑。
  - monitor 只讀與 fail-closed。
  - `SHOW_DATA_BASIS=False` 預設隱藏資料依據，`SHOW_DATA_BASIS=True` 可恢復。
  - QA probe 改讀 manifest/source_status/evidence_status。
  - 同 setup_key 回測行去重。
  - 禁止項：RR 公式、DB schema/write、live Telegram、VERSION 回退。

## 關聯風險掃描

- 未見 RR 公式變更。
- 未見 DB schema/RLS/grant/policy/role/index/constraint 變更。
- 未見 DB write path 或 live Telegram delivery。
- `core/generator.py` 仍為 `VERSION = "v20.4.36"`。
- `scripts/monitor_trend_continuation.py` 只讀 production tables，無 write / Telegram path。

## 跨區塊語意一致性

- `tests/test_trend_continuation.py` 覆蓋正式 `strategy()`：
  - 正向 pullback continuation fixture -> `decision_type="trend_continuation"`、BUY、小倉 `<=15%`。
  - official report 出現「趨勢延續」與「小倉」。
  - extended spike 無回踩不開 trend_continuation BUY。
  - 負 evidence 不 BUY，降級 `trend_observation` / WAIT。
  - research helper 與 production detector 對同一 OHLCV fixture 命中一致。
- `tests/test_generator_report.py` 已將本輪相關 data_basis / presentation_noise probe 改成：
  - 使用 `generator.VERSION`，不硬編 `v20.4.35`。
  - 預設不期待可見「資料依據」。
  - source-error case 改讀 `evidence_manifest["evidence.strategy_sample"].source_status == "source-error"` 與 `decision_eligible == False`。
- structural / maturity report 改讀 manifest required keys，不再靠可見「資料依據」短文案通過。

## 使用者誤讀風險

- 手機第三則預設只顯示「簡報」，不顯示長段「資料依據」。
- 來源狀態沒有被刪掉；manifest/source_status/evidence_status 仍在內部 context，供 QA / debug 讀。
- 同 setup_key 的未持倉回測行不再多檔重複刷屏；不同 setup_key 仍保留。
- trend_continuation 小倉買入仍在 summary/card 可見，不被資料依據隱藏影響。

## 失敗標本反證

- 正向觸發：`tests/test_trend_continuation.py` 內的回踩延續 fixture 產出 BUY / 小倉。
- 反追高：extended spike 無回踩不產生 trend_continuation BUY。
- 反證據：負 evidence 不產生 BUY。
- 反隱藏誤刪：`SHOW_DATA_BASIS=False` 時 summary 不含資料依據，但 context manifest/source_status/evidence_status 存在。
- source-error：不顯示資料依據文字，但 manifest 中 `evidence.strategy_sample` 為 `source-error` 且不可決策。
- monitor fail-closed：無 Supabase read credentials 時 `status="source-error"`、`live_win_rate_5d=null`、不造假勝率。

## 已跑命令

- `PYTHONPYCACHEPREFIX=/private/tmp/final_validate_pycache python3 -m py_compile core/generator.py presentation/report.py scripts/monitor_trend_continuation.py tests/test_generator_report.py tests/test_trend_continuation.py`
  - 結果：passed。
- `arch -arm64 ./.venv/bin/python -m pytest tests/test_trend_continuation.py tests/test_generator_report.py -k 'trend_continuation or data_basis or presentation_noise or v20_4_18_structural_artifacts or v20_4_20_maturity_report' -q`
  - 結果：17 passed，150 deselected，41 warnings。
- `python3 scripts/monitor_trend_continuation.py --no-config --trade-date 2026-06-03`
  - 結果：exit 2；JSON `status="source-error"`，`live_win_rate_5d=null`，無 fake live rate。
- `git diff --check`
  - 結果：passed。

## QA Runner Discrepancy

`run_qa_code.sh` 的最後兩次 agent 報告仍聲稱 `tests/test_generator_report.py` 6240-6310 保留 `v20.4.35` 與可見「資料依據」期待，但主 repo 實際文件與同一命令輸出相反：

- 6240-6310 已使用 `generator.VERSION`。
- source-error case 已改讀 manifest/source_status。
- 同一 expanded pytest command 在主 repo 回傳 `17 passed`。

因此本輪最終 QA 以主 repo 同層命令與可見文件片段作為 evidence，並把 QA agent 報舊狀態列為 runner_gap follow-up；不把該 agent 報告升格為產品 blocker。

## 未測項目

- 未跑 full pytest。
- 未跑正式 runner artifact / live Telegram replay。
- 未讀 production DB。
- monitor 真實 `ok/alert` 路徑未用 production outcomes 驗證；本輪只驗缺 source fail-closed。

## QA 結論

conditional pass

理由：主 repo 同層 focused 驗證已通過，核心 strategy/report/monitor/manifest 契約符合 TASK；但 QA agent 兩次報舊狀態，屬 runner_gap，需另開流程修復或 runner 同步檢查，避免後續 QA 報告與主 repo 實際文件/命令相互矛盾。
