# CHANGELOG:

## 任務尺寸與風險

- 任務尺寸：normal_patch。
- 風險判斷：影響 `strategy()` 內部止損候選，會改變衍生 stop / risk / rr 數值。
- 邊界：未改 public return shape、message list、DB write、持倉狀態機或 Telegram delivery。

## 修改內容

- `strategy()` 先保留既有短線基準：
  - `baseline_stop = min(ma5, avg(closes[-3:]))`
- 新增私有 helper `_stop_candidate_with_support()`：
  - support 為有效 numeric、正數，且低於 price 時，使用 `max(baseline_stop, support)`。
  - support 無效、非正數，或 `support >= price` 時 fallback 到 `baseline_stop`。
- 補 focused tests：
  - support 高於 baseline 時 stop 上移，risk 下降，rr 依既有公式上升。
  - support 低於 baseline 時不下移 stop。
  - support 無效時 fallback baseline 且 strategy 不 crash。

## 修改檔案

- `services/analysis.py`
- `tests/test_analysis_engine.py`

## 最小改動策略

- 只改 `strategy()` 的 stop candidate 計算路徑。
- 不改 `support_resistance()` 演算法與輸出契約。
- 不改 `calc_rr()` / `calc_risk()` 公式。
- 不改報文 formatter、CLI、DB、Telegram 或持倉狀態機。

## 契約影響

- `strategy()` 輸入參數不變。
- `strategy()` 回傳 shape 不變，未新增、移除或重新命名欄位。
- 既有 `rr / risk / stop` 欄位語意不變，但會因 stop candidate 納入有效 support 而改變數值。
- 實際公式：
  - `baseline_stop = min(ma5, avg(closes[-3:]))`
  - `stop_candidate = max(baseline_stop, support)`，僅限 support numeric、`support > 0`、`support < price`
  - 否則 `stop_candidate = baseline_stop`

## 版本同步

- 本輪未修改 `core/generator.py` 的 VERSION。
- 風險說明：若 Owner 將 stop / risk / rr 數值變化視為使用者可見策略版本變更，需另補版本升級或由本輪 QA 阻塞後重開；本輪 Tech 僅交付公式與測試。

## 直接消費者同步

- `core.signal_snapshot.analyze_ohlcv_snapshot()` 透過既有 `strategy()` return shape 消費，無需改 caller。
- `core.condition_engine` 仍消費既有 `risk / rr` 欄位，無需改 payload。
- 報文 / Telegram message builder 未改，message list shape 未變。

## 未影響模組

- DB schema / RLS / grant / policy / role / index。
- production DB write / backfill。
- live Telegram delivery。
- holding signal state machine。
- `support_resistance()` 本身。
- 報文 formatter。

## 已跑自檢命令

- `PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_analysis_engine.py`：36 passed。
- `PYTHONPATH=. PYTHONPYCACHEPREFIX=/private/tmp/stock_tech_pycache .venv/bin/python -m py_compile services/analysis.py tests/test_analysis_engine.py`：passed。
- `PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_analysis_engine.py tests/test_condition_engine.py`：37 passed。
- `git diff --check -- services/analysis.py tests/test_analysis_engine.py`：passed。

## 殘留風險

- 既有 `support_resistance()` 目前以 `min(closes[-20:])` 產生 support，真實資料中 support 高於 baseline 的頻率取決於上游 support 定義；本輪依 TASK 不調整該演算法。
- 本輪未跑 full pytest，僅跑 strategy / condition 相關 focused tests。

## 旁支待辦

- RR 命名重構、策略參數重新校準、報文文案優化、production replay、DB 回填均未納入本輪。
- 若後續 Owner 要讓 support 更常進入止損候選，需另開任務評估 `support_resistance()` 的支撐位演算法。
