# CHANGELOG: v20.4.17 第三則資料依據人話化

## 任務尺寸與風險

- 任務尺寸：`normal_patch`
- 風險判斷：只改 Telegram 第三則「簡報＋資料依據」formatter 與版本字串，不改策略 decision、候選分類、DB schema/write path、live delivery。

## 修改內容

- 將使用者可見版本由 `v20.4.16` 升為 `v20.4.17`。
- 第三則「資料依據」改為三段人話：
  - 市場 / 題材背景：說明近幾個交易證據日是否支持背景、可靠度與「不等於買點」。
  - 策略樣本：不可用時顯示本輪缺少可驗證樣本、可靠度低、未納入買賣判斷。
  - 持倉 / 價格 / 候選資料：說明可支持風控/分類；缺資料標的保守處理，不給有效進場。
- 第三則過濾 raw 狀態字與工程語，避免 `production DB`、`classification backtest`、`source-of-truth`、`available`、`derived`、`as_of`、ISO timestamp 等出現在第三則。
- 相關測試改為驗完整三則 Telegram sample、版本、第三則 forbidden-term scan 與 ISO timestamp scan。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## 最小改動策略

- 僅修改第三則 brief/evidence formatter helper 與 `VERSION`。
- 沒有改 `formatTelegramMessages` 的三則訊息順序。
- 沒有改第一則/第二則卡片 formatter 的策略語意。
- 沒有改策略計算、持倉狀態機、DB 讀寫或 live Telegram delivery。

## 契約影響

- 使用者可見版本：`v20.4.17`。
- Telegram message list：維持三則主體順序：
  - messages[0] 持倉標的
  - messages[1] 未持倉標的
  - messages[2] 簡報＋資料依據
- 第三則文字契約改為人話可靠度與用途說明；不再輸出 raw table/source/status/timestamp 類工程語。
- 回傳結構、payload shape、DB contract、策略 decision 未變。

## 直接消費者同步

- `tests/test_generator_report.py` 同步完整三則 sample、版本字串、第三則 forbidden-term scan。
- `tests/test_market_theme_evidence.py` 同步 market/theme 背景只作環境、不構成買點的人話預期。
- Telegram renderer 直接消費者仍使用既有 `formatTelegramMessages` message list，不需改呼叫介面。

## 未影響模組

- 不改買入、賣出、加碼、減碼、停損、停利、觀察判斷。
- 不改候選分類邏輯。
- 不改 DB schema、RLS、grant、policy、role、index、constraint。
- 不改 DB write path。
- 不改 live Telegram delivery。
- 不改 replay/backfill。

## 已跑自檢命令

- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m py_compile core/generator.py services/notifier.py`：passed
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py tests/test_notifier.py`：120 passed，169 warnings
- `git diff --check`：passed

## 殘留風險

- 第三則已覆蓋本輪 forbidden raw 語彙與 ISO timestamp scan；其他報文區塊仍可能保留既有 production/runtime 診斷文字，本輪非目標。
- 測試警告為既有第三方 deprecation，未在本輪處理。

## 旁支待辦

- 其他報文區塊文案優化另開任務。
- 候選分類策略調整、歷史資料補齊、DB source-of-truth 設計、Telegram delivery runner 改造，本輪不處理。
