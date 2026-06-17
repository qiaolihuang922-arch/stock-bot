# CHANGELOG: db_backed_price_transition_v21_1_20260617

## 修改內容與檔案

- `core/generator.py`
  - 新增 `recent_price_transition`，用 DB `daily_price` 最近收盤與當前價判斷 `UP_THEN_DOWN` / `DOWN_THEN_UP` / `CONTINUOUS_UP` / `CONTINUOUS_DOWN`。
  - `multi_day_rebound_needs_retest` 不再要求先被標成 `WEAK_REBOUND`；若 DB 日線確認連漲修復、當前價相對最新日線回落，直接進入待回測。
  - 新增 data-aware result merge，將 top-level `volume_ratio` / distance 合入局部 result，但不污染原始 payload。
  - `volume_ratio >= 1.1` 時，不再被舊 `NO_VOLUME` / `volume_state=WEAK` 硬打成 `量能不足`。
  - `volume_ratio < 1.1` 只在接近買點區時作主 blocker；遠離區仍優先走低位修復 / 等接近。
- `presentation/report.py`
  - formatter 改用 data-aware result，避免核心判斷與卡片數據行衝突。
  - 盤面文字會根據 DB-backed recent transition 移除不合理的 `趨勢延續` / `極強`。
  - evidence unavailable 的量能判斷同步尊重 data volume ratio。
- `tests/test_generator_report.py`
  - 新增旺宏昨日漲今日跌後應等回測 regression。
  - 新增群創 V 1.18x 不得顯示量能不足 regression。
  - 新增聯電連續轉弱不得顯示極強 / 不可追高 regression。
  - 修正舊 low-volume fixture，明確使用 `volume_ratio=0.7`。

## 契約影響

- 報文版本仍為 `v21.1`。
- Telegram message list shape 不變。
- DB:
  - no schema change。
  - no write/backfill/prune。
  - 只讀既有 `daily_price` cross-day context。
- Telegram:
  - no live delivery。

## 直接消費者同步

- official generator dry-run 已覆蓋。
- formatter、funnel state、summary bucket 使用同一個 data-aware 判斷，降低卡片與 summary 不一致。

## 未影響模組

- 不改 Supabase schema / RLS / grant / policy。
- 不改 Render/GitHub dispatch。
- 不改 live Telegram sender。
- 不改持倉 hard-stop / 減碼規則。

## 自檢命令與結果

- Generator report tests:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_generator_report.py -q --tb=short`
  - result: `211 passed, 163 warnings, 46 subtests passed`
- Full:
  - `.\.venv\Scripts\python.exe -m pytest -q --tb=short`
  - result: `494 passed, 8 skipped, 175 warnings, 110 subtests passed`
- Official generator dry-run:
  - `generate_report(dry_run=True)` returned `4` messages, no live Telegram。
  - visible checks:
    - 聯電: `等量能｜等量` with V around `0.46x`。
    - 旺宏: `等回測｜反彈修復待回測`。
    - 群創: `等冷卻｜漲停反彈待確認`，not `等量能｜量能不足`。
    - 緯創 / 技嘉 / 仁寶 remain `等低位修復` with support / 5-day MA / volume gap。

## 覆蓋層級

- helper: covered by direct tests for transition / blockers。
- formatter: covered by `formatTelegramUnheldCard` direct tests。
- official generator message list: covered by dry-run。
- production DB write: not run by design。
- live Telegram: not run by design。

## 殘留風險

- `volume_ratio >= 1.1` is now the effective volume recovery threshold for display / blocker release; future calibration may tune it, but must remain DB/report data backed.
- `等回測` still is not a buy signal. It only says the next useful observation is a pullback / retest that holds.
