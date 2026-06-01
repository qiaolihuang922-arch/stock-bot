# QA_REPORT:

## 測試範圍

- 任務尺寸 / QA：normal_patch / L2。
- 驗證範圍：Telegram 持倉 formatter、`position_events` guard、版本字串與相關 regression。
- 已讀：`TASK.md`、`CHANGELOG.md`、`core/generator.py`、`tests/test_generator_report.py`、`tests/test_market_theme_evidence.py`。
- 未做 production read-only smoke、replay、backfill、live Telegram；本輪為 formatter patch。

## 關聯風險掃描

- `TASK.md` / `CHANGELOG.md` / diff 一致：`position_events_dict`、list fail-closed、完整 formatter regression、`v20.4.24`、不改 DB/live/strategy，均可在 diff 中對應。
- `core/generator.py` 版本由 `v20.4.23` 升為 `v20.4.24`；測試中的 header / evidence version 同步。
- `rg` 掃描未見未 guard 的 `position_events.get` 直接崩潰路徑；剩餘 `data.get("position_events")` 位於 helper 入口、manifest source 值與 loader 組 payload，不是本輪 `.get()` crash 消費點。
- 未發現 DB schema、RLS、grant、policy、role、index、constraint、live Telegram 或 production write diff。

## 跨區塊語意一致性

- 持倉卡手機閱讀順序驗證：message 0 為持倉、message 1 為未持倉、message 2 為簡報＋資料依據。
- dict-shaped `position_events` / holding source 可顯示 `弱勢觀察第 N 天`，且同份報文只出現一次。
- list-shaped `position_events` 在完整 formatter 中不 crash、不顯示 `弱勢觀察第 7 天`，顯示 `觀察天數未確認`。
- top-level / result / invalid observation values fail-closed，不輸出推測天數。
- 主決策維持 `續抱觀察 / 決策：續抱觀察，暫不加碼`；未出現 `建議賣出`、`已降級`。

## 使用者誤讀風險

- 觀察狀態位於持倉卡條件行，可直接回答「第幾天或未確認」。
- fail-closed 文案仍是條件式：`若無法重新接近買點 / 突破區，降低優先級`，未把降級寫成已發生事實。
- 殘留風險：若 production 長期沒有可信 dict / holding observation source，使用者會看到 `觀察天數未確認`；這符合本輪契約，資料治理需後續處理。

## 質疑與反證

- Tech regression：`pytest -q tests/test_generator_report.py -k 'v20_4_24_weak_far_holding or observation_days_only_trusts_persistent_sources'`：5 passed，98 deselected。
- 關聯測試：`pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：139 passed。
- QA 自補反證：完整 formatter probe 驗證 dict `watch_days` 顯示 N、list fail-closed、top-level/result fail-closed、invalid fail-closed、手機順序、decision unchanged、`v20.4.24`，全部 PASS。
- `git diff --check`：passed。

## 未測項目

- 未做 production read-only smoke、replay、backfill、live Telegram。
- 未驗證 production 是否已有可信 observation source；TASK 已允許缺 source 時 fail-closed。
- 未做全 repo pytest；本輪風險集中在 generator formatter 與相關 evidence/version tests。

## QA 結論

通過
