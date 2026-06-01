# CHANGELOG:

## 任務尺寸與風險

- 任務類型：`tiny_patch`
- 風險判斷：只改第三則 Telegram 證據入口去重、版本字串與最小測試；不碰策略 decision、DB schema/write path、live Telegram。

## 修改內容

- 將使用者可見報文版本從 `v20.4.13` 升為 `v20.4.14`。
- 第三則 Telegram short/evidence message 會過濾獨立長段 `📊 策略證據 v20.0`，避免與 `v20.4.14 簡短證據摘要` 同時出現。
- 簡短證據摘要的 fail-closed 行補上狀態碼，例如 `策略樣本（missing-source）`、`策略樣本（insufficient-data）`，讓 missing-source 保留在唯一證據入口內。
- 更新相關測試，覆蓋第三則不再雙入口、missing-source/insufficient-data 仍 fail-closed、版本同步。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## 契約影響

- 使用者可見版本：`v20.4.14`。
- 第三則 Telegram 證據入口契約改為單一入口：保留 `v20.4.14 簡短證據摘要`，不再同時顯示 `📊 策略證據 v20.0`。
- Message list 順序不變：持倉、未持倉、short/evidence；`include_detail=True` 時 Details Backup 仍追加最後。
- Payload shape / DB write / CLI 輸出 / strategy decision 無變更。

## 直接消費者同步

- Owner 手機 Telegram 第三則：只看到一個簡短證據入口。
- Telegram dry-run / runner 產生的 messages：版本與第三則 formatter 已同步。
- 既有 snapshot/fixture 類測試：已同步 `v20.4.14` 與第三則去重斷言。
- `services/notifier.py` delivery consumer 未改，補跑既有測試確認 message list delivery 行為未受影響。

## 未影響模組

- DB schema、RLS、grant、policy、role、index、constraint。
- DB write path、backfill、live Telegram delivery。
- 持倉 / 未持倉策略 decision、買賣、加減碼、停損停利。
- strategy evidence 讀取與格式化 service 本體。
- 前兩則持倉卡與未持倉卡主結構、排序與策略語意。

## 自檢命令與結果

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/notifier.py`：passed
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_main_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：119 passed，169 warnings（第三方 deprecation 類）
- `git diff --check`：passed

## 殘留風險

- 未做 live Telegram delivery，符合本輪禁止事項。
- `formatTelegramSummary()` standalone 仍可保留 strategy evidence 長段；本輪只約束 Telegram 第三則 message 的單一證據入口。
- 非 production 標準格式的 bare `missing-source` 字串若未帶 `狀態碼` 或標準原因，可能只被去除而不保留原字樣；production 標準格式已保留 `missing-source` 並 fail closed。

## 旁支待辦

- 若 Owner 後續要求全報文 evidence formatter 收斂，需另開任務。
- Telegram reply markup 附著最後一則 message 的 consumer 風險仍屬既有旁支，本輪未處理。
