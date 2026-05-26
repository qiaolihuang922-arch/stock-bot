# CHANGELOG

## 2026-05-26 - v19.4 交易閉環升級

### 修改內容
- 依 `TASK.md` 實作 v19.4 交易閉環升級，版本顯示更新為 `v19.4`。
- 摘要區新增 `📌 持倉處理優先級`：
  - 依停損 / 減碼 / 停利 / 新倉風控 / 核心風控 / 減碼後觀察 / 洗盤 / 核心續抱 / 普通續抱排序。
  - 每檔持倉顯示明日處理重點，例如守警戒價、未修復降級、修復才恢復優先級。
- 摘要區新增 `🕒 隔日追蹤`：
  - 從未持倉標的推導 `等冷卻 / 等回測 / 等RR修復 / 等量能 / 隔日確認`。
  - 每個追蹤標的都有 `明日觸發`。
  - `可買` 不被追蹤層覆蓋；弱勢淘汰不進隔日追蹤優先清單。
- 摘要區新增 `待確認候選` 分組：
  - 支援 `可買 / 等冷卻 / 等回測 / 等RR修復 / 等量能 / 隔日確認 / 弱勢淘汰`。
- 未持倉詳情卡同步顯示 v19.4 追蹤狀態與 `明日觸發`。
- 持倉 lifecycle 顯示升級：
  - 今日減碼事件顯示 `減碼後觀察`。
  - 高浮盈且過熱 / 延伸的核心倉顯示 `核心風控觀察`。
  - 已停利核心倉可顯示 `停利後核心倉`。
  - 既有停損 / 停利 / 減碼 / 加碼 action 優先保留，不被 lifecycle 覆蓋。
- 回測資訊只影響隔日追蹤排序：
  - `參考度低` 不加權。
  - `參考度中 / 高` 可依相對表現調整追蹤順序。
  - 不改 `decision`、不產生 BUY、不改 strongest candidate。
- 保留 v19.3.x 主體結構：
  - 摘要區
  - 持倉標的詳情
  - 未持倉標的詳情

### 修改檔案
- `core/generator.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

### 未影響模組
- `services/analysis.py`
- RR 硬門檻
- 過熱 / 漲停不追規則
- 加碼 / 減碼 / 停利 / 停損策略門檻
- scoring
- strongest candidate 硬規則
- snapshot 組裝與驗證
- DB schema
- DB 寫入邏輯
- replay / backfill
- 股票池
- Supabase Edge Function
- TWSE/Yahoo provider 底層請求邏輯

### 風險點
- 本次新增的是 derived state / formatter 交易流程層，不會改變策略層實際買賣 decision。
- `減碼後觀察` 依賴 `position_events.sold_shares`；如果事件缺失，會安全回退為一般持倉顯示。
- `核心風控觀察` 是顯示層 lifecycle 升級，策略 action 仍以 `holding_decision.level` 為準。
- 隔日追蹤目前是當日報文內的明日檢查清單，尚未新增跨日 tracking table。
- 回測排序只使用既有 `backtest_context`，未改回測資料寫入，也未正式 backfill。
- 本次未跑 full regression、live Telegram、DB、replay/backfill。

### 建議 QA 驗證範圍
- 報文版本顯示 `v19.4`。
- 摘要區包含：
  - `📌 持倉處理優先級`
  - `🕒 隔日追蹤`
  - `待確認候選`
- 隔日追蹤：
  - 每檔都有 `明日觸發`。
  - R3 強勢但過熱不進 `可買`，進 `等冷卻 / 等回測`。
  - RR 不足但結構強進 `等RR修復`。
  - 量能不足但非弱勢進 `等量能`。
  - 弱勢 / 遠離觸發不進隔日追蹤優先清單。
- 合格 `BUY`：
  - 仍顯示 `可買`。
  - 不被待確認或隔日追蹤狀態覆蓋。
- 持倉 lifecycle：
  - 新倉浮虧仍顯示 `新倉風控觀察` 或 `洗盤警戒`。
  - 今日減碼後顯示 `減碼後觀察`。
  - 高浮盈過熱 / 延伸核心倉顯示 `核心風控觀察` 或等效語意。
  - STOP / TAKE_PROFIT / REDUCE action 不被 lifecycle 顯示覆蓋。
- 回測排序：
  - 只影響隔日追蹤順序。
  - 不產生 BUY。
  - 不改 strongest candidate。
- 價格行右括號仍完整。
- 已執行最低必要驗證：
  - `.venv/bin/python -m pytest tests/test_generator_report.py`
  - 結果：`32 passed`
