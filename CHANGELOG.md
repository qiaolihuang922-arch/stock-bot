# CHANGELOG:

## 任務尺寸與風險

- 任務類型：tiny_patch。
- 風險判斷：只刪除 `services/analysis.py` 三處已指定 dead / redundant code。
- 邊界：不改策略條件、輸出契約、DB、Telegram 或版本。

## 修改內容

- 刪除 `detect_entry_stage()` 內未使用的 `breakout_lv` 計算。
- 刪除 `holding_signal()` 內未使用的 `profile = result.get("entry_profile", "NONE")`。
- 刪除 `pick_best_stock()` 內被下一行 `entry_quality not in ["A+", "A"]` 覆蓋的冗餘 C/D 過濾。

## 修改檔案

- `services/analysis.py`

## 清理證據表

| path | claim | evidence | risk | action |
| --- | --- | --- | --- | --- |
| `services/analysis.py::detect_entry_stage()` | `breakout_lv` 賦值後未在該函式使用 | AST targeted check 確認函式內不再有 `breakout_lv` assignment；`py_compile` passed | 誤刪可能影響 stage 判斷 | 僅刪 unused assignment，保留 `breakout_hold_days()` 與後續判斷 |
| `services/analysis.py::holding_signal()` | `profile` 賦值後未在該函式使用 | AST targeted check 確認函式內不再有 `profile` assignment；`py_compile` passed | 誤刪可能影響持倉訊號輸出 | 僅刪 unused local，未改 signal / action / reason 邏輯 |
| `services/analysis.py::pick_best_stock()` | C/D 過濾被下一行 A+/A allowlist 覆蓋 | AST targeted check 確認 C/D-specific redundant filter removed；行為 probe 確認 B/C/D 不會被選中，A 仍可被選中 | 誤刪可能放行非 A+/A | 保留 `entry_quality not in ["A+", "A"]` allowlist |

## 契約影響

- 函式回傳契約：不變。
- payload / dict key：不變。
- message list / Telegram 報文排序：不變。
- CLI 輸出：不變。
- DB 讀寫契約：不變。
- 版本契約：不升 VERSION，未改報文 header 或版本字串。
- Public helper / 呼叫方：未改 public helper contract，無需同步呼叫參數或回傳解析。

## 直接消費者同步

- `detect_entry_stage()` 消費者：輸入與回傳不變。
- `holding_signal()` 消費者：signal / action / reason / entry profile 相關輸出不變。
- `pick_best_stock()` 消費者：仍只接受 `entry_quality` 為 A+ 或 A 的候選；C、D、B 與其他非 A+/A 仍排除。
- 驗收消費者：因 `.venv` 無 pyflakes / ruff / flake8，改用 AST targeted static check 覆蓋本任務三處指定 dead code。

## 未影響模組

- 未改 `presentation/`、`core/`、DB schema/write path、Telegram delivery、runner、測試 fixture。
- 未改 RR、entry quality scoring、買賣 / 加減碼、停損停利、持倉狀態機或報文內容。

## 已跑自檢命令

- `git diff --check -- services/analysis.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache .venv/bin/python -m py_compile services/analysis.py`：passed。
- `.venv/bin/python -m pyflakes services/analysis.py`：failed，實際錯誤 `No module named pyflakes`。
- `.venv/bin/python -m ruff check services/analysis.py --select F841,F601,F821`：failed，實際錯誤 `No module named ruff`。
- `.venv/bin/python -m flake8 services/analysis.py --select=F841,F821,F601`：failed，實際錯誤 `No module named flake8`。
- AST targeted static check for the three TASK-specified dead/redundant code sites：passed。
- `pick_best_stock_non_A_quality_excluded` inline behavior probe：passed。
- `git diff --stat`：`services/analysis.py | 8 --------`。

## 殘留風險

- 未跑 full pytest，符合本輪 tiny scoped cleanup。
- 環境缺 pyflakes / ruff / flake8，因此沒有一般 linter 的全檔 unused report；已用 AST targeted check 覆蓋 TASK 指定三處，不擴大到全 repo lint cleanup。

## 旁支待辦

- 若團隊需要固定 pyflakes 證據，後續可由 runner / 環境任務補齊 lint dependency 或標準 lint command。
- 其他 lint warning 或 dead code cleanup 不納入本輪。
