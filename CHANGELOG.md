# CHANGELOG: v20.4.35-report-semantics

## 任務尺寸與風險

- 任務類型：risk_patch。
- 風險原因：本輪修正使用者可見 Telegram 報文中的 evidence boost 邊界、盤面文案、持倉數據行與簡報計數。
- 未碰：RR 公式、DB schema / write path、策略 decision、持倉狀態機、live Telegram。

## 修改內容

- `core/generator.py`
  - `apply_evidence_confidence()` 的 boost blocker 擴大到不可追高 / 漲停鎖價 / 漲停反彈 / 過熱 RR blocker。
  - `trade_state=AVOID`、`price_behavior=LIMIT_LOCK/LIMIT_REBOUND`、`should_show_overheat_rr_blocker(...)` 任一成立時，evidence modifier 固定為 `1.0`，不再顯示正向 boost。
- `presentation/report.py`
  - evidence unavailable 的 heat 判定同步納入 `AVOID`、`LIMIT_LOCK`、`LIMIT_REBOUND`，讓顯示文案與分數 blocker 對齊。
  - 低量收縮降級不再輸出裸 `待確認`，改用 `縮量觀察`，避免 `突破確認｜待確認` 同時出現。
  - 持倉非加碼資料行保留量比，格式為 `數據：不適用（既有持倉）｜V {vol}x`。
  - 簡報第一行改為明確區分 `執行動作 N` 與 `今日新建倉 M`，並在可辨識時標注動作類型。
- `tests/test_generator_report.py`
  - 更新既有 summary 斷言為 `執行動作` / `今日新建倉`。
  - 補不可追高 / 漲停鎖價 replay：RR 為過熱時 `evidence_modifier=1.0`，卡片顯示 `證據：過熱不適用`，且不出現 `證據 +`。
  - 補非加碼持倉保留 V、低量降級不含 `突破確認｜待確認` 的回歸斷言。

## 修改檔案

- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`

## 最小改動策略

- 只在既有 scoring / formatter / summary line 路徑補 gate 與文案對齊。
- 不改 RR 計算、不改候選池、不改 DB payload、不新增 schema。
- 以 official message-list replay 與既有 generator tests 覆蓋手機可見輸出。

## 契約影響

- 過熱 / 不可追高契約：RR 過熱、漲停鎖價、漲停反彈、不可追高狀態不得取得 evidence boost。
- 持倉非加碼資料行契約：仍豁免 RR / 綜合 / 技術 / 證據，但保留 V。
- 簡報契約：`交易執行 N` 改為 `執行動作 N`，另列 `今日新建倉 M`。
- 使用者可見版本維持 `v20.4.35`，未回退。
- Message order、DB contract、RR formula 未變。

## 直接消費者同步

- `presentation/report.py` 持倉 / 未持倉卡片與簡報 formatter 已同步。
- `core/generator.py` official message path 已同步。
- `tests/test_generator_report.py` 覆蓋 Owner 指定四個 probe。

## 未影響模組

- 未改 DB schema / RLS / grant / policy / role / index / constraint。
- 未改 production write / backfill / live Telegram。
- 未改 RR 公式、候選來源、策略 decision、持倉狀態機。
- 未改 Render freshness preflight。

## 已跑自檢命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -q`
  - Tech 結果：157 passed，241 warnings。

## 覆蓋層級

- helper / formatter：covered。
- official generator / message artifact：covered by `formatTelegramMessages` replay。
- runner artifact / production source：not covered，本輪未執行 live runner、未讀 production、未 live delivery。

## 殘留風險

- QA 取得的是 official generator message-list replay，不是 Render / GitHub runner 產出的正式 artifact。
- 若 production payload 使用不同欄位表達不可追高，仍需另補 mapping；本輪已覆蓋現有 `heat_state`、`trade_state`、`price_behavior`、RR blocker 路徑。

## 旁支待辦

- 若後續報文仍出現其它同義不可追高狀態吃 boost，另開 mapping 收斂任務。
