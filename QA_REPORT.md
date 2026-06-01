# QA_REPORT:

## 測試範圍

- 任務：`presentation_report_structured_noise_flags_tiny_patch_20260601`，QA L1。
- 驗證範圍限於 `presentation/report.py` 顯示層、`core/generator.py` 結構化參數 bridge、`tests/test_generator_report.py` 最小 probe。
- 未擴大到 full pytest、production replay、backfill 或 live Telegram。

## 風險預算與停止條件

1. 合法 summary 文字含 production / runtime 被舊詞表誤刪。
   - 驗證：`_decision_brief_lines()` 移除 `noisy_contains`；測試與 QA inline probe 確認合法 production summary 保留。
   - 停止條件：若仍有 presentation brief 對 summary 使用 production / runtime / source keyword 詞表過濾，阻塞。
2. `daily_write_warning` 仍由 rendered string 偵測。
   - 驗證：`_afterhours_brief_lines()` 改收 `daily_write_warning`；QA inline negative probe 確認 summary 文字單獨存在不會觸發 brief；custom warning 文案可觸發。
   - 停止條件：若仍靠 `每日快照未寫入` 字串決定 brief 顯示，阻塞。
3. tiny patch 意外改 message order / VERSION / strategy / DB / live Telegram。
   - 驗證：message list 順序未變；VERSION 仍 v20.4.21；未見 DB write / live Telegram path diff。
   - 停止條件：若 message list 順序、VERSION、strategy decision 或 DB/live path 有非任務 diff，阻塞或 conditional pass。

## 關聯風險掃描

- TASK / CHANGELOG / diff 一致：修改檔案為 `presentation/report.py`、`core/generator.py`、`tests/test_generator_report.py`。
- 可吸收 diff：
  - `presentation/report.py`：`_decision_brief_lines()` 改由 `summary_excluded_lines / summary_excluded_sections` 排除；`_afterhours_brief_lines()` 改由 `daily_write_warning` 控制資料寫入提示；message order 保持。
  - `core/generator.py`：`format_brief_data_evidence_message()` bridge 新增 optional kwargs，向後相容；`_source_missing_report_messages()` 改傳結構化排除集合。
  - `tests/test_generator_report.py`：新增合法 production summary 保留與 structured daily warning probe。
- 未看到不相關 tracked diff。
- 本任務不是清理 / 瘦身 / refactor 任務，因此不要求 path / claim / evidence / risk / action 證據表。

## 跨區塊語意一致性

- 手機閱讀順序仍為：
  - 第一則：持倉訊息。
  - 第二則：未持倉訊息。
  - 第三則：簡報＋資料依據；盤後 brief 中可顯示資料寫入警告。
- `core/generator.py` 仍為 `VERSION = "v20.4.21"`。
- 指定 diff 未改 strategy decision、RR、holding status、daily snapshot write、Supabase write 或 live Telegram delivery。
- `daily_write_warning_text()` 原本產生文案的路徑保留；本輪只改 brief 是否顯示的判斷來源。

## 使用者誤讀風險

- 合法 summary 行包含 `production` 不再被短 brief 誤刪，避免使用者只看到警告、看不到資料來源正常 / 無有效進場類決策摘要。
- 盤後資料寫入警告改由結構化 `daily_write_warning` 觸發，避免 warning 文案調整後 brief 消失，也避免單純 rendered summary 文字被反向偵測成狀態。
- 全報文其他字串匹配與 Telegram reply markup 仍是旁支，不納入本輪。

## 質疑與反證

- 質疑：`_afterhours_brief_lines()` 是否只是換位置，仍可能讀 summary_message 內的 `每日快照未寫入`？
  - 反證：函式簽名已不收 `summary_message`，只收 `daily_write_warning`；QA inline negative probe 把 `⚠ 每日快照未寫入：請檢查寫入來源` 放進 `summary_message` 但不傳 `daily_write_warning`，brief 不含資料寫入警告；custom warning 文案可正確顯示。
- 質疑：合法 production runtime summary 是否仍會因排除集合或 header 過濾消失？
  - 反證：QA inline probe 只排除 header/source line，合法 `🧭 今日結論：production runtime source 正常...` 保留在 brief；Tech 測試也覆蓋合法 production summary line。

## 已跑命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'daily_write_warning or legal_production or telegram_messages_use_summary_cards_and_detail or source_missing'`：6 passed, 88 deselected。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py core/generator.py tests/test_generator_report.py`：passed。
- `git diff --check -- core/generator.py presentation/report.py tests/test_generator_report.py CHANGELOG.md`：passed。
- Re-QA output：`.cao_agent_context/outputs/20260601_195959_7787_stock_qa_code_readonly.answer.txt`，結論 `通過`。

## 未測項目

- 未跑 full pytest，符合 tiny_patch / L1 風險預算。
- 未做 production read-only smoke、replay、backfill 或 live Telegram delivery。
- 未盤點全 repo 其他字串匹配。
- 未驗證 Telegram reply markup 落點。

## QA 結論

通過
