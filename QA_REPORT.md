# QA_REPORT: v20.4.35-report-semantics

## 測試範圍

- 任務：`v20.4.35-report-semantics`
- QA 分級：L3。
- 已驗使用者可見面：
  - Telegram 未持倉卡片的過熱 / 不可追高 evidence blocker。
  - 持倉非加碼卡片的數據行。
  - 盤面低量降級文案。
  - 簡報第一行計數標籤。
- 未擴大到 production DB、live Telegram、full runner artifact。

## 關聯風險掃描

- DB schema / write path：未改。
- RR 公式：未改。
- Strategy decision / holding state machine：未改。
- Telegram visible report：已改，版本維持 `v20.4.35`。
- Handoff 風險：runner 第一次 QA 發現 `CHANGELOG.md` 錯輪；已在主 repo 重寫本輪 `CHANGELOG.md` / `QA_REPORT.md` 後重跑測試。

## 跨區塊語意一致性

- 過熱 / 不可追高：generator 分數 gate 與 formatter 文案同時納入 `HOT/EXTREME`、`AVOID`、`LIMIT_LOCK/LIMIT_REBOUND` 與 RR overheat blocker。
- 持倉非加碼：卡片不再顯示 RR / 綜合 / 技術 / 證據，但同一行保留 `V {vol}x`。
- 盤面強度：低量收縮降級使用 `縮量觀察`，避免 `突破確認｜待確認` 同時出現。
- 簡報計數：第一行改為 `執行動作 N` 與 `今日新建倉 M` 分開，避免不同口徑裸數字並列。

## 使用者誤讀風險

- 光寶科這類漲停鎖價 / 不可追高標的不再因 market evidence 顯示 `證據 +8%`，避免「最熱反而加分」。
- 持倉非加碼仍保留 V，避免風控閱讀少掉量能資訊。
- `縮量觀察` 比裸 `待確認` 更能說明降級原因，不與 `突破確認` 直接衝突。
- `執行動作` / `今日新建倉` 分開後，手機首屏不再把減碼動作數誤讀成新建倉數。

## 失敗標本反證

- Owner 樣本等價路徑：不可追高 / 漲停鎖價標的原本 RR 為過熱卻顯示 evidence boost。
- 等價 replay 結果：
  - `evidence_modifier == 1.0`
  - 卡片含 `RR -（過熱）｜綜合 78｜技術 78｜證據：過熱不適用`
  - 卡片不含 `證據 +`
- 持倉非加碼 replay：
  - 卡片含 `數據：不適用（既有持倉）｜V 1.4x`
  - 卡片不含 `綜合`、`技術`、`證據`
- 低量 replay：
  - 卡片含 `縮量觀察`
  - 卡片不含 `突破確認｜待確認`
- 簡報 replay：
  - 第一行含 `執行動作 ...｜今日新建倉 ...`
  - 回歸測試不再期待舊 `交易執行 N` 裸標籤。

## 質疑與反證

- 質疑：不可追高 blocker 會不會誤傷近門檻可準備候選？
  - 反證：Tech 中途測試失敗後已把新斷言移回漲停 / 不可追高 replay，近門檻可準備測試恢復既有行為。
- 質疑：持倉非加碼保留 V 是否會讓新倉分數回來？
  - 反證：回歸斷言確認同一卡片不含 `綜合`、`技術`、`證據`。
- 質疑：簡報新標籤是否只改單一路徑？
  - 反證：`tests/test_generator_report.py` 多個盤中 / 盤後 summary 斷言已同步為 `執行動作` / `今日新建倉`。

## 已跑命令

- `arch -arm64 .venv/bin/python -m pytest tests/test_generator_report.py -q`
  - Tech 結果：157 passed，241 warnings。
- QA 自補 direct consumer replay：
  - 結果：passed；非加碼持倉保留 V，summary 不再出現舊 `交易執行 0`。

## 未測項目

- 未跑 full pytest。
- 未執行 live Telegram。
- 未讀寫 production DB。
- 未取得 Render / GitHub runner artifact；本輪驗 official generator message-list replay 與 QA 臨時探針。

## QA 結論

conditional pass

理由：使用者可見 message-list replay 與相關 regression tests 已覆蓋本輪四項核心錯誤；但尚未取得正式 runner artifact，因此不寫成完全 `通過`。
