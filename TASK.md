# TASK: v20.0 Strategy Evidence Foundation

## 時間性

- 任務日期：2026-05-26
- 來源任務：`RESEARCH.md` Architect Conclusion / `DISPATCH.md` Current Task
- 目標版本：`v20.0`
- 任務性質：策略證據資料層、分類績效報告、Telegram 策略證據摘要
- version_level：`major`
- qa_level：`L3`
- 狀態：PM 正式需求，等待 Architect 交 Tech
- 邊界：第一版只建立策略證據資料層與分類績效報告；不直接改 BUY / SELL，不放寬 RR / 過熱 / 停損 / 停利 / 加碼門檻，不把外部新聞直接接入買點。

## 需求目標

v20.0 的目標不是立刻讓策略變聰明，而是先讓策略「可被證據驗證」。

目前旺宏 2337 案例暴露的問題是：策略可以因風控理由不買，但分類語意可能把「強題材高波動、不宜追價」壓成 `弱勢淘汰`。這代表系統缺少能事後回答以下問題的資料層：

- `淘汰` 後 1 / 3 / 5 / 10 日是否經常大漲。
- `等回測` 是否真的等到更好的風報。
- `RR不足` 是否真的比追價安全。
- `弱勢淘汰` 是否混入高波動強題材標的。
- `可買` 是否真的比不可買追蹤組有更好的 MFE / MAE / 相對報酬。

v20.0 第一版要建立「策略證據基礎設施」，讓之後調整 taxonomy 或策略門檻時有數據依據，而不是用單一錯過案例調參。

所有產物必須回到現有工作流：

```text
定時 GitHub Actions / 腳本 -> 策略產出 -> 證據資料更新 -> 產生 Telegram 報文 -> 發送給 Owner
```

不得做成需要 Owner 改用新平台、長時間手動操作儀表板、或脫離 Telegram 報文的重型系統。

## 使用者可見變化

### 1. Telegram 增加策略證據摘要

每日定時任務產生的 Telegram 報文需新增簡短證據摘要。此摘要用來告訴 Owner：目前策略分類在歷史樣本中的事後表現如何。

建議位置：

- 放在總覽摘要中，不要取代既有持倉 / 執行清單。
- 如摘要過長，可放在總覽下方的 `📊 策略證據` 區塊。

範例：

```text
📊 策略證據 v20.0
淘汰：近 N 筆｜3日勝率 38%｜大漲漏失 2 筆
等回測：近 N 筆｜5日給更佳買點 46%｜追價回撤偏高
RR不足：近 N 筆｜3日相對 -0.8%｜等待有效
分類警示：旺宏類 1 筆｜強題材高波動被歸淘汰
```

若資料不足：

```text
📊 策略證據 v20.0
樣本不足：需累積 N 筆後啟用分類績效判讀
```

### 2. 不改買賣結論，只新增證據與警示

v20.0 報文可以新增：

- 分類績效摘要。
- 分類失真疑慮。
- 高波動 / 注意股 / 強題材的 audit note。
- 樣本不足提示。

v20.0 報文不得新增：

- 因新聞或題材直接產生的 `BUY`。
- 因分類績效初步結果直接產生的 `SELL`。
- 未經回測證明的加碼 / 減碼建議。
- 讓 Owner 誤以為外部新聞已接入買點的文案。

### 3. 分類績效報告需可被 Telegram 消費

分類績效報告不能只存在 DB 或開發者 console。定時任務需能產出一段可讀摘要，至少包含：

- 分類名稱。
- 樣本數。
- 1 / 3 / 5 / 10 日其中至少 3 日與 5 日結果。
- 勝率或中位數報酬。
- MFE / MAE 或大漲漏失 / 回撤風險。
- 是否資料不足。

第一版可以只顯示 Top 3 重要分類：

```text
淘汰
等回測
RR不足
```

旺宏類 audit 必須能在報文中被點名或統計：

```text
分類警示：強題材高波動被歸淘汰 1 筆（旺宏）
```

## 報文 / 流程設計

### 定時任務流程

v20.0 後，定時任務概念流程應是：

```text
1. 取得 watchlist 12 檔行情
2. 產生既有策略結果
3. 寫入 / 更新策略特徵快照
4. 補算可得的 outcome path metrics
5. 產生分類績效報告
6. 產生既有 Telegram 報文
7. 將策略證據摘要併入 Telegram 總覽
8. 發送 Telegram
```

關鍵要求：

- 如果證據資料更新失敗，不能阻斷既有 Telegram 報文。
- 若分類績效資料不足，顯示資料不足，不可硬解讀。
- 研究表查詢不得明顯拖慢正式報文。
- 所有新資料寫入需可重跑且不重複。

### 策略證據摘要格式

建議格式：

```text
📊 策略證據 v20.0
淘汰｜樣本 42｜3日勝率 31%｜5日MFE中位 +1.2%｜漏失 3
等回測｜樣本 28｜5日給更佳買點 46%｜MAE中位 -2.1%
RR不足｜樣本 33｜3日相對 -0.8%｜等待偏有效
⚠ 分類警示：強題材高波動被歸淘汰 1 筆
```

如果樣本不足：

```text
📊 策略證據 v20.0
淘汰｜樣本 5｜樣本不足，不判讀
等回測｜樣本 3｜樣本不足，不判讀
RR不足｜樣本 4｜樣本不足，不判讀
```

### 分類績效報告範圍

第一版至少需要支援以下分類或 blocker family：

- `淘汰`
- `弱勢淘汰`
- `等回測`
- `等RR修復`
- `RR不足`
- `追價風險 / 過熱`
- `高波動觀察` 若目前尚未正式 taxonomy，可先作 audit label。

報告需支援：

- 按分類聚合。
- 按股票聚合。
- 按日期區間聚合。
- 按 horizon：1 / 3 / 5 / 10 日。

## 策略證據資料層需求

### 1. 多日 OHLCV 研究資料

需建立或強化多日行情資料層，支援 outcome path 計算。

最小欄位：

- `stock_id`
- `trade_date`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `turnover` 若來源可得
- `source`
- `created_at / updated_at`

要求：

- 使用 `stock_id + trade_date + source` 或等效 unique key。
- 重跑不得重複寫入。
- 缺資料時不得污染正式 daily snapshot。
- 正式報文仍以既有資料流程為主；研究行情層不得阻塞報文。

### 2. Strategy Feature Snapshots

每天每檔需保存策略當下可見的特徵快照，避免日後只能看最終文字。

最小欄位：

- `stock_id`
- `trade_date`
- `strategy_version`
- `price`
- `change_pct`
- `chg_1d / chg_3d / chg_5d / chg_10d`
- `vol_ratio_5 / vol_ratio_10`
- `breakout_distance`
- `rr`
- `score / confidence`
- `market_state`
- `trend`
- `structure_state / structure_phase`
- `volume_state`
- `heat_state`
- `trade_state`
- `decision / action`
- `is_tradeable / is_best_candidate`
- `watch_category`
- `reject_family`
- `blockers`
- `raw_reason_summary`

要求：

- `watch_category` 與 `reject_family` 必須是穩定 taxonomy，不應只存 Telegram 文案。
- 若 taxonomy 尚未完整重構，先保存現有分類並允許 `audit_category` 補充。
- 此快照只能保存當時可見資料，不得混入未來 outcome。

### 3. Outcome Path Metrics

需能補算策略分類後 1 / 3 / 5 / 10 日結果。

每個 snapshot / horizon 至少保存：

- `horizon_days`
- `close_return_pct`
- `relative_return_pct`
- `max_favorable_excursion_pct`，MFE
- `max_adverse_excursion_pct`，MAE
- `hit_breakout_after_signal`
- `hit_stop_like_drawdown`
- `best_entry_gap_pct`
- `outcome_label`

公式需 deterministic：

- `close_return_pct`：snapshot close 到 horizon close 的報酬。
- `MFE`：snapshot 後到 horizon 期間最高價相對 snapshot close 的最大有利幅度。
- `MAE`：snapshot 後到 horizon 期間最低價相對 snapshot close 的最大不利幅度。
- `relative_return_pct`：優先相對同日 12 檔 watchlist 平均報酬；若未來有族群 benchmark 再擴充。
- `best_entry_gap_pct`：snapshot 後期間最低價相對 snapshot close 的折價，或依 Tech 定義為更佳風報點，但必須寫入公式。
- `outcome_label`：由固定規則產生，例如 win / loss / flat / late_win / whipsaw，不可人工主觀標記。

要求：

- outcome 不得被 feature snapshot 查詢混入策略當日判斷。
- outcome 可延後補算；資料不足時標記 pending。
- 重跑需冪等。

### 4. Classification Audit

需建立分類失真標記能力，第一版至少支援旺宏類問題。

Audit label 範例：

```text
高波動強勢，非弱勢淘汰
不追價合理，但淘汰語意過度負面
等回測疑似錯過強趨勢
RR不足疑似誤殺強趨勢
```

最小欄位：

- `stock_id`
- `trade_date`
- `strategy_version`
- `original_category`
- `suggested_audit_category`
- `distortion_type`
- `evidence_summary`
- `severity`
- `review_status`

要求：

- Audit 不得自動改 BUY / SELL。
- Audit 可進 Telegram 證據摘要。
- Audit 可作為後續 taxonomy 重構依據。

## 外部資料邊界

v20.0 第一版可以預留外部事件資料結構，但不得把外部新聞直接接入買點。

允許：

- 保存注意股 / 處置 / 新聞 / 營收 / 法說 / 法人籌碼的研究事件。
- 在 audit 或報文備註顯示外部事件。
- 用外部事件輔助判斷「分類語意是否失真」。

禁止：

- 外部新聞直接產生 `decision=BUY`。
- 外部題材直接讓 `is_tradeable=True`。
- 外部 sentiment 直接改 `action_pct`。
- 無時間戳 / 無來源 URL 的事件進入績效計算。

Point-in-time 契約：

每筆外部事件若入庫，至少需包含：

- `source_name`
- `source_url`
- `event_type`
- `title / summary`
- `published_at`
- `market_effective_at`
- `ingested_at`
- `dedupe_key`
- `confidence / reliability` 若有

規則：

- 回測只能使用 signal time 當下已發布且可取得的事件。
- 注意股若盤後公告，只能用於收盤後隔日計畫或事後 audit，不得回填當日盤中判斷。
- 無 `published_at / ingested_at / source_url` 的資料只能當人工備註，不得進策略特徵。

## Edge Cases

- Outcome 尚未到期：顯示 pending，不可納入績效統計。
- 樣本數不足：顯示樣本不足，不可判定分類好壞。
- OHLCV 缺漏：跳過該 horizon，標示資料不足。
- 重跑 backfill：不得重複寫入 snapshot / outcome / audit。
- 策略版本變更：績效報告需按 `strategy_version` 區分。
- 報文過長：策略證據摘要最多顯示 Top 3 分類 + Top 1 audit，完整報告留在資料層。
- DB 寫入失敗：既有 Telegram 報文仍應發送，並顯示證據層更新失敗或略過。
- 外部事件來源重複：需用 `dedupe_key` 去重，不得多來源重複加分。
- 12 檔 watchlist 樣本過小：可顯示樣本不足，不得過度解讀。
- 正式報文不應依賴大型外部新聞表即時查詢。

## 影響模組初判

預期可能影響：

- `services/daily_snapshot_store.py`
  - 多日 OHLCV / 研究資料寫入或讀取
- `services/signal_store.py`
  - strategy feature snapshot / outcome / audit 相關寫入
- `core/signal_snapshot.py`
  - snapshot 組裝與欄位擴充
- `core/signal_validator.py`
  - 新資料完整性驗證
- `scripts/dry_run_replay.py`
  - outcome path dry-run / 回放驗證
- `scripts/backfill_signals.py`
  - 冪等 backfill / outcome 補算
- `core/generator.py`
  - Telegram 策略證據摘要
- `tests/`
  - DB payload、formatter、backfill/replay、策略不變性、Telegram contract 測試

可能新增：

- strategy evidence / classification report helper
- outcome metrics calculator
- audit report helper
- migration / schema 文件

直接消費者需檢查：

- 定時任務入口
- `generate_report()`
- `formatTelegramMessages()`
- `main.py -> send_many()`
- `services/notifier.send_many()`
- replay / backfill scripts

## 不可變更範圍

v20.0 第一版不可變更：

- 不改 BUY / SELL 判斷。
- 不改 `decision=BUY` 產生條件。
- 不改 `is_tradeable=True` 條件。
- 不改 `action_pct`。
- 不放寬 RR / 過熱 / 漲停不追 / 停損 / 停利 / 加碼硬門檻。
- 不把外部新聞、題材、法人、注意股直接接入買點。
- 不用旺宏單一案例調整全局策略。
- 不做獨立平台或重型 dashboard。
- 不要求 Owner 改工作流。
- 不讓證據資料層阻塞既有 Telegram 報文。
- 不保存外部新聞全文作為第一版必要資料。
- 不用未來 outcome 回填 strategy feature。

## 驗收標準

v20.0 需滿足：

1. `version_level` 為 `major`。
2. `qa_level` 為 `L3`。
3. 建立策略證據資料層，能保存每日每檔 strategy feature snapshot。
4. Feature snapshot 不得包含未來 outcome。
5. 建立或強化多日 OHLCV 研究資料，支援 1 / 3 / 5 / 10 日 outcome。
6. 新資料寫入具備 unique key，重跑不得重複寫入。
7. 能補算 `close_return_pct`、MFE、MAE、relative return、best entry gap、outcome label。
8. 上述 outcome 指標公式需 deterministic 並可被測試。
9. 能按分類輸出 1 / 3 / 5 / 10 日分類績效報告。
10. 分類績效報告至少支援 `淘汰`、`等回測`、`RR不足`。
11. 能標示樣本不足，不得硬解讀低樣本。
12. 能產生 classification audit，至少覆蓋旺宏類 `不追價合理但弱勢淘汰語意失真`。
13. Audit 不得自動改 BUY / SELL。
14. Telegram 報文需新增 `📊 策略證據 v20.0` 或等效摘要。
15. Telegram 策略證據摘要需由定時任務產生，不得只存在手動腳本。
16. 證據摘要需包含分類樣本數與至少一個 outcome 指標。
17. 若資料不足，Telegram 需顯示資料不足或 pending。
18. 證據資料更新失敗時，既有 Telegram 報文仍需可發送。
19. `messages[-1]` summary-last contract 不得回退。
20. `reply_markup` last summary contract 不得回退。
21. 外部事件若入庫，需包含 source、URL、published / effective / ingested time。
22. 無 point-in-time 欄位的外部資料不得進績效計算。
23. 外部新聞 / 題材 / 法人 / 注意股不得直接產生 `BUY`、`is_tradeable=True` 或 `action_pct`。
24. 研究資料層不得明顯拖慢正式 Telegram path；若資料層失敗需 degrade gracefully。
25. Backfill / replay 需 dry-run 驗證新資料路徑與冪等性。
26. QA 需做 full pytest、replay/backfill dry-run、DB payload 路徑、Telegram contract、策略不變性與未來資料洩漏檢查。
27. Tech 需在 `CHANGELOG.md` 明確列出資料表 / 欄位 / 指標公式 / 不改策略門檻的證據。
