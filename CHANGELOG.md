# CHANGELOG: v20.4.37 generate() 報文手機閱讀一致性修復

## 任務尺寸與風險

- 任務尺寸：normal_patch
- 風險：使用者可見 Telegram message-list / summary formatter 變更。
- 版本：升小版本到 `v20.4.37`，同步 `core/generator.py` 的 `VERSION`。
- 邊界：不改策略 decision、RR 公式、DB schema/write、production backfill 或 live Telegram。

## 修改內容

- 首屏未持倉括號改讀同一份 prepare 分桶結果，`不可追高觀察 1` 不再只出現在漏斗而漏於首屏。
- 今日已買摘要由 `今日已買 N｜風控中 M` 改為 `今日已買 N（已風控 M/觀察 K）`，讓今日買入與風控數可追溯。
- 未持倉回測摘要取消跨股票 body 聚合，改為單檔行；不再輸出 `回測（建準、緯創）`。
- 補 v20.4.37 official `formatTelegramMessages` replay，覆蓋首屏 / 漏斗 / 詳情索引 / 卡片分類一致、普通 observe 歷史噪音、單檔回測契約。
- 同步測試中的可見版本字串為 `v20.4.37`。

## 修改檔案

- `core/generator.py`
- `presentation/report.py`
- `tests/test_generator_report.py`
- `CHANGELOG.md`

## 最小改動策略

- 僅改報文 formatter、版本常量與 message-list replay 測試。
- 不改持倉主行動判斷、不改未持倉策略分類、不改 RR / evidence 計算。
- 不新增資料來源、不讀寫 production DB、不觸發 Telegram delivery。

## 契約影響

- 使用者可見 header / 簡報版本變為 `v20.4.37`。
- 首屏未持倉總數與括號分類需等於漏斗 / 詳情索引同源結果。
- 今日已買摘要現在明示今日買入中已風控與仍觀察的拆分。
- 回測摘要多檔時使用：
  - `回測摘要`
  - `回測（建準）：...`
  - `回測（緯創）：...`
- 函式回傳結構、DB payload、strategy decision payload 未變更。

## 直接消費者同步

- `presentation/report.py` 的首屏 compact market line 消費 `core/generator.py` 提供的 prepare bucket helper。
- `tests/test_generator_report.py` 使用 official `formatTelegramMessages` final message-list replay，不是 helper-only。
- 實際 `core.generator.generate()` 已在主 repo 跑過，產出 `v20.4.37` 報文。

## 未影響模組

- 未改 `services/analysis.py`。
- 未改 `core/condition_engine.py`。
- 未改 RR 公式。
- 未改 DB schema / RLS / grant / policy / role / index / constraint。
- 未改 DB write path。
- 未執行 production backfill、production write 或 live Telegram。

## 已跑自檢命令

- `arch -arm64 ./.venv/bin/python -m pytest tests/test_generator_report.py -k 'v20_4_37 or 0604_v20_4_36_mobile_readability or single_backtest or unheld_funnel_hides_zero_count_buckets or evidence_sample_count' -q`：4 passed。
- `PYTHONPYCACHEPREFIX=/private/tmp/v20_4_37_pycache arch -arm64 ./.venv/bin/python -m py_compile core/generator.py presentation/report.py tests/test_generator_report.py`：passed。
- `arch -arm64 ./.venv/bin/python - <<'PY' ... generate() ... PY`：passed；實際輸出 header 為 `v20.4.37`，首屏 / 漏斗 / 索引同源一致，普通 history 噪音未出現。

## 覆蓋層級

- official `formatTelegramMessages` final message-list replay。
- actual `core.generator.generate()` final report output。
- 未覆蓋 production runner artifact / live Telegram。

## 殘留風險

- `generate()` 使用即時價，Owner 貼出的 1/5/2 specimen 在本次實跑中會隨價格更新變成 1/6/1、2/5/1 等形狀；本輪驗證的是分類合計同源一致，不宣稱價格分類不會變。
- 未跑 full pytest；上一輪已知 full `tests/test_generator_report.py` 有 legacy contract failures，本輪只跑 focused contract。
- 光寶科 `RR不足` 顯示 `證據：資料不足` 仍是旁支文案風險；本輪未擴大處理 RR/evidence reason 分流。

## 旁支待辦

- 若 Owner 要把所有 `RR不足` 的 evidence reason 也改為非資料不足，另開報文原因分流任務。
- 若要正式上線驗證，需取得 production runner artifact；本輪未 live delivery。
