# CHANGELOG:

## 任務尺寸與風險

- 任務類型：normal_patch。
- 風險判斷：使用者可見 Telegram 持倉報文 formatter 與 `position_events` 消費 guard 變更；不改 strategy decision、DB schema/write、live Telegram、持倉狀態機。

## 修改內容

- 新增 `position_events_dict(data)`，讓完整 formatter 遇到 list-shaped `position_events` 時一律 fail-closed 為 `{}`。
- 收斂 `today_event_weight()`、`event_summary_text()`、`holding_status()` 前後相關 `position_events` consumer：只在 dict 時讀 `.get()`，否則視為無可信事件。
- 保留 `positive_observation_days_from_holding()` 不信任 `position_events` list 的契約。
- 補完整手機閱讀 regression：`position_events=[{"observation_days": 7}]` 時 `formatTelegramMessages()` 不 crash，不輸出 `弱勢觀察第 7 天`，輸出 `觀察天數未確認`，主決策仍是 `續抱觀察`。

## 修改檔案

- `core/generator.py`
- `tests/test_generator_report.py`
- `tests/test_market_theme_evidence.py`

## 最小改動策略

- 只加 dict guard helper，套到同檔內直接消費 `position_events.get()` 或傳入持倉狀態計算的必要路徑。
- 不改 observation source 信任範圍：list 不作為可信觀察天數來源。
- 不重構 formatter、不改報文分組、不改持倉策略 decision。

## 契約影響

- Public/helper contract：`position_events` 非 dict 時，formatter 視為無可信事件，不 crash。
- Message list：弱勢遠離且「續抱觀察」持倉在 list-shaped `position_events` 下顯示 `觀察天數未確認`。
- Payload shape、報文順序、分組、DB 寫入、CLI 輸出：未改。
- 版本契約：維持本任務版本同步 `v20.4.24`，未回退。

## 直接消費者同步

- Telegram 持倉卡 formatter：list-shaped `position_events` fail-closed。
- QA 手機閱讀 probe：新增完整 `formatTelegramMessages()` regression 覆蓋 list-shaped `position_events`。
- 既有 holding / dict-shaped `position_events` 正例與 top-level / result / invalid fail-closed 測試保留。

## 未影響模組

- 未修改買入 / 賣出 / 加碼 / 減碼 / 停損 / 停利 decision。
- 未修改 strategy decision、持倉狀態機、風控閾值、分數、漏斗、排序或分組。
- 未修改 DB schema、RLS、grant、policy、role、index、constraint。
- 未執行 live Telegram、live Supabase write、正式 backfill。

## 已跑自檢命令

- `/usr/bin/arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py -k 'v20_4_24_weak_far_holding or observation_days_only_trusts_persistent_sources'`：5 passed，98 deselected。
- `PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache /usr/bin/arch -arm64 .venv/bin/python -m py_compile core/generator.py tests/test_generator_report.py`：passed。
- `/usr/bin/arch -arm64 .venv/bin/python -m pytest -q tests/test_generator_report.py tests/test_market_theme_evidence.py`：139 passed。
- `git diff --check`：passed。

## 殘留風險

- 若 production 沒有可信 dict 形狀 observation source，報文會按契約 fail-closed 顯示 `觀察天數未確認`。

## 旁支待辦

- production source 長期補齊 observation start / observation days 的資料治理不在本輪。
- 全部持倉卡文案統一、其他降級規則重設、DB schema/backfill 設計、live Telegram 驗證不在本輪。
