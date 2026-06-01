# QA_REPORT:

## 測試範圍

- 任務：`tiny_patch_cleanup_unused_variables_analysis_py_20260601`，QA L1。
- 讀取 `TASK.md`、`CHANGELOG.md`、`git diff -- services/analysis.py` 與三個相關函式片段。
- 本輪只驗證 `services/analysis.py` 三處指定 dead / redundant code 刪除。
- 未擴大到 full pytest、replay、backfill、production DB 或 Telegram live delivery。

## 風險預算與停止條件

1. 誤刪造成策略或函式輸出改變。
   - 驗證：對 `detect_entry_stage()` / `holding_signal()` 做 AST static equivalence，刪除指定 unused assignment 後其餘 AST 等價。
   - 停止條件：若出現其他條件、return、payload key 或呼叫參數變更，blocked。
2. `pick_best_stock()` 因刪除 C/D filter 放行非 A+/A。
   - 驗證：AST 確認 A+/A allowlist 仍存在；補直接消費者 probe，B/C/D/None/空字串不會被選中，A/A+ 仍可被選中。
   - 停止條件：若 C/D 或其他非 A+/A 可被選中，blocked。
3. 文件、任務與實際 diff 不一致。
   - 驗證：比對 TASK 三處指定刪除、CHANGELOG 清理證據表、實際 scoped diff。
   - 停止條件：若缺 path / claim / evidence / risk / action 表，或 diff 超出 `services/analysis.py` 三處刪除，blocked。

## 關聯風險掃描

- TASK / CHANGELOG / diff 一致：三處刪除分別是 `breakout_lv`、`profile`、`entry_quality in ["C", "D"]` redundant filter。
- CHANGELOG 已包含 cleanup evidence table，欄位具備 path / claim / evidence / risk / action。
- `git diff --check -- services/analysis.py`：passed。
- `py_compile services/analysis.py`：passed。
- AST targeted check：passed，三處指定 dead / redundant code 不再存在，A+/A allowlist 保留。
- static equivalence check：passed，`detect_entry_stage()` 與 `holding_signal()` 在移除指定 unused locals 後 AST 等價。
- `pick_best_stock()` consumer probe：passed，tuple return contract preserved；B/C/D/None/空值排除，A/A+ 接受。
- diff grep 未發現 VERSION、Telegram、summary、payload、DB、header、return 或 message 相關改動；只有指定刪除。

## 跨區塊語意一致性

- TASK 要求不改策略、輸出、DB、Telegram、版本；CHANGELOG 宣告相同；實際 code diff 未碰這些面向。
- `pick_best_stock()` 仍以 `entry_quality not in ["A+", "A"]` 作為 allowlist，符合 C、D 以及其他非 A+/A 值仍排除的契約。
- Tech 自檢聲稱環境缺 pyflakes / ruff / flake8，改用 AST targeted static check；以 tiny_patch L1 來看可接受，因本輪驗收不是全檔 lint cleanup。

## 使用者誤讀風險

- 本輪沒有 Telegram / summary / dashboard 報文改動；手機閱讀順序無新增或刪除區塊可查。
- scoped diff 確認沒有報文 header、版本字串、message list、summary 文案或 DB / Telegram delivery 變更。
- 使用者可見結果應保持不變；本輪不能宣稱策略改善，只能宣稱清理指定 dead / redundant code。

## 質疑與反證

- 質疑：刪除 `pick_best_stock()` 的 C/D filter 是否會讓 B 或未知品質混入？
  - 反證：直接 consumer probe 顯示 B/C/D/None/空字串均不會勝出；只有 A/A+ 可被選中。
- 質疑：`breakout_lv` 或 `profile` 是否可能有副作用？
  - 反證：刪除的是 local assignment；AST static equivalence 顯示移除指定 assignment 後函式其餘結構不變。TASK 已明確定義該計算 unused，後續 stage 判斷仍使用原本的 `breakout_hold_days()` / `is_fresh_breakout()` 等路徑。

## 已跑命令

- `git diff --check -- services/analysis.py`：passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile services/analysis.py`：passed。
- Re-QA output：`.cao_agent_context/outputs/20260601_194500_12054_stock_qa_code_readonly.answer.txt`，結論 `通過`。

## 未測項目

- 未跑 full pytest，符合 TASK 的 tiny_patch / L1 停止條件。
- 未跑 production DB read、backfill、replay 或 Telegram live delivery，因本輪沒有 DB / Telegram / runner 改動。
- 未驗全 repo lint warning；其他 unused / redundant code 不納入本輪。

## QA 結論

通過
