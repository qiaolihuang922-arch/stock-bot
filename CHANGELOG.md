# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：tiny_patch。
- 風險判斷：顯示層 / generator bridge 小範圍契約修正。
- 邊界：不碰策略 decision、RR、DB write、live Telegram、VERSION。

## 修改內容

- 移除 `presentation/report.py` 中 `_decision_brief_lines()` 對 `summary_message` 的 `noisy_contains` 硬編碼文字詞表過濾，避免合法 production summary 行被誤刪。
- 改由 generator / caller 傳入 `summary_excluded_lines`、`summary_excluded_sections` 結構化排除集合。
- 移除 `_afterhours_brief_lines()` 透過 rendered summary 文案比對 `每日快照未寫入` 的判斷。
- 改由 `daily_write_warning` 結構化參數控制盤後 brief 是否顯示資料寫入警告。
- 補兩個最小 probe：
  - 合法 summary 行含 `production` 時仍保留。
  - 盤後 brief 由 `daily_write_warning` 顯示每日快照警告。

## 修改檔案

- `presentation/report.py`
- `core/generator.py`
- `tests/test_generator_report.py`

## 最小改動策略

- 只擴充既有 presentation formatter 與 generator bridge 的 optional kwargs。
- 不新增大型 fixture、不重構 presentation 分層、不改報文 message list 順序。
- 保留既有 same-day 已執行人話明細；只用結構化狀態排除 cross-day technical memory / source missing / runtime-cache 類短 brief 噪音。

## 契約影響

- `format_brief_data_evidence_message()` 新增 optional 參數：
  - `summary_excluded_lines`
  - `summary_excluded_sections`
  - `daily_write_warning`
- 既有呼叫可不傳，向後相容。
- message list 順序不變。
- 盤後分組不變。
- VERSION 不變，仍為 `v20.4.21`。
- DB write path、schema、RLS、grant、policy、index / constraint 不變。
- live Telegram delivery 不變。

## 直接消費者同步

- `presentation.render_telegram_messages()` 已同步建立並傳入 brief 排除集合與 `daily_write_warning`。
- `core.generator.format_brief_data_evidence_message()` bridge 已同步 optional kwargs。
- `_source_missing_report_messages()` 已同步使用結構化排除集合，避免 source missing 技術行回到短 brief。

## 未影響模組

- strategy decision / 持倉建議 / 買賣加減碼 / 停損停利邏輯：未改。
- RR 計算：未改。
- holding_status / position ledger：未改。
- Supabase write / daily snapshot write / strategy evidence write：未改。
- Telegram live delivery / reply markup：未改。
- VERSION：未升版。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m py_compile presentation/report.py core/generator.py tests/test_generator_report.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'daily_write_warning or legal_production or structured_daily_write_warning'`：3 passed, 91 deselected。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_write_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py`：94 passed, 185 warnings。
- `git diff --check`：passed。
- `rg -n "noisy_contains|latest_trade_date|source_of_truth|db_table|production|runtime" presentation/report.py`：只剩 `runtime-cache` 結構化 source field 判斷，沒有 brittle summary keyword 詞表。

## 殘留風險

- 本輪只收斂 TASK 指定兩處 brittle rendered-string 判斷；全報文其他字串匹配未盤點。
- 新增 optional kwargs 屬 public helper 擴充，但既有呼叫路徑保持相容。

## 旁支待辦

- Telegram reply markup 附著最後一則 message 的落點風險仍需另開 delivery consumer 任務評估。
- 全報文其他字串匹配盤點、presentation 分層重構、production ledger/source-of-truth 稽核均未納入本輪。
