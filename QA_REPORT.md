# QA_REPORT: trade_state_machine_v21_20260608

## 測試範圍
- 狀態機 helper。
- 持倉 exit state mapping。
- 未持倉 wait state mapping。
- read-only artifact contract。
- official TG card replay。
- dry-run official generator。

## 關聯風險掃描
- `等量能` 在 source missing 時仍保持等待，不被打成不可行動。
- `停損` 持倉輸出單一 `STOP_LOSS` state。
- 狀態機 artifact 明確 `db_write=False` / `schema_change=False`。
- 報文新增狀態線不改 live delivery。

## 跨區塊語意一致性
- 持倉卡片主行動與交易狀態一致：例如 `停損` -> `交易狀態：停損`。
- 未持倉卡片主行動與交易狀態一致：例如 `等量能` -> `交易狀態：等量能`。
- Summary 仍保留原漏斗與持倉風控；v21 狀態機先作每檔唯一狀態層。

## 使用者誤讀風險
- `等量能` 顯示動作為 `等待`，不是買入。
- `今日進場` 顯示動作為 `續抱`，避免盤後誤讀成可繼續買。
- `不可行動` 僅作 blocking state，不代表所有等待候選永久淘汰。

## 失敗標本反證
- Owner 指出系統沒有交易狀態機。
- v21.0 official dry-run first holding card:
  - `交易狀態：停損｜動作：停損｜觸發：清出後等重新買點`。
- v21.0 official dry-run first unheld card:
  - `交易狀態：等量能｜動作：等待｜觸發：量能回升且重新接近買點`。
- v21.0 summary header 正確。

## 質疑與反證
- 質疑：是否需要擴 DB 欄位？
- 反證：v1 狀態機完全 read-only，由現有 payload / holding / events / source status 派生，artifact 明確 no schema change。
- 質疑：是否會把等待類候選變成可買？
- 反證：測試覆蓋 source missing + 等量能，輸出仍是 `WAIT_VOLUME` / action `WAIT`。

## 未測項目
- live Telegram delivery 未測且禁止。
- DB state snapshot write-back 未做。
- Full `tests/test_generator_report.py` 未全綠：目前 160 passed / 39 failed，需下一輪整理舊精準字串 regression 與 v21 visible-state contract。

## QA 結論
conditional pass
