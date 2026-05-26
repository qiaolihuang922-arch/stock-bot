# CHANGELOG

## 2026-05-26 - v19.3.3 formatter 一致性修正

### 修改內容
- 依 `TASK.md` 實作 v19.3.3 formatter 顯示層一致性修正。
- 版本顯示由 `v19.3.2` 更新為 `v19.3.3`。
- 未持倉合格 `BUY`：
  - 摘要新增 / 支援 `【可買 N】...` 分組。
  - 合格買點不再被歸入 `可觀察但不可買`。
  - 詳情仍顯示 `🟢 可買｜買點成立` 與建議倉位。
- 持倉 `ADD_10 / ADD_20 / ADD_30`：
  - 摘要 / 詳情標題明確顯示 `加碼10 / 加碼20 / 加碼30`。
  - 詳情決策行直接顯示策略 action，例如 `決策：加碼 20%，趨勢延續`。
  - 詳情條件行顯示 RR / 品質 / 信心條件。
- 持倉停利 / 減碼 / 停損：
  - `TAKE_PROFIT_*` 顯示 `停利`，詳情顯示鎖定部分獲利。
  - `REDUCE_*` 顯示 `減碼`，詳情顯示降低風險。
  - `STOP_100` 顯示 `停損`，不再被壓成 `減碼`。
  - 詳情決策行優先使用策略 action / level，不再只依 blocker 拆句。
- 持倉摘要排序調整為需處理優先：
  - 停損 / 清倉
  - 減碼 / 停利
  - 加碼
  - 核心續抱
  - 洗盤警戒 / 洗盤續抱 / 續抱觀察
  - 普通續抱
- 保留 v19.3.2 大版型：
  - 市場摘要
  - 持倉摘要
  - 未持倉分組
  - 持倉標的
  - 未持倉標的

### 修改檔案
- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

### 未影響模組
- `services/analysis.py` 策略門檻
- RR 門檻
- 過熱規則
- 加碼 / 減碼 / 停利 / 停損策略判斷條件
- DB schema
- position DB 結構
- replay / backfill
- daily snapshot 寫入邏輯
- 股票池
- Telegram 大版型
- v19.4 策略方向
- Supabase Edge Function
- TWSE/Yahoo provider 底層請求邏輯

### 風險點
- 本次只修 formatter 映射，不代表策略會更頻繁產生 BUY / ADD / STOP 訊號。
- 若策略長期不輸出 `ADD_* / STOP_100 / TAKE_PROFIT_* / REDUCE_*`，報文仍不會憑空顯示交易動作。
- `可買` 分組依賴既有 `is_valid_entry()` 判斷；若 blocker 規則改變，QA 需同步驗證摘要與詳情一致性。
- 本次未跑 full regression、live Telegram、DB、replay/backfill。

### 建議 QA 驗證範圍
- 合格未持倉 `BUY`：
  - 摘要顯示 `【可買 N】...`
  - 不進入 `可觀察但不可買`
  - 詳情顯示 `🟢 可買｜買點成立`
  - 買點行顯示建議倉位與 `現在可分批`
- 持倉加碼：
  - `ADD_10 / ADD_20 / ADD_30` 顯示加碼語意。
  - 詳情標題與決策行不可顯示普通 `續抱`。
- 停利 / 減碼 / 停損：
  - `TAKE_PROFIT_*` 顯示停利。
  - `REDUCE_*` 顯示減碼。
  - `STOP_100` 顯示停損，不可只顯示減碼。
  - 詳情決策行直接呈現策略 action。
- 阻擋原因一致性：
  - `RR不足`
  - `過熱觀察`
  - `市場弱`
  - `量能不足`
  - `遠離觸發`
- 已執行最低必要驗證：
  - `.venv/bin/python -m pytest tests/test_generator_report.py`
  - 結果：`27 passed`
