# RESEARCH.md

保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Current Research Context

- 主題：DB / evidence chain 如何影響策略報文。
- 結論：DB 不是直接替代即時策略引擎；它優先承擔「記憶、證據、排序提示、去重、追溯」。
- 邊界：market/theme evidence confirmed 不能單獨把不可買改成可買，不能放寬追高限制。

## Trend Continuation Phase 1｜2026-06-03

- task_id：`research_trend_continuation_phase1`
- 研究問題：驗證「上升趨勢中，縮量回踩 ma5 / ma10 不破後放量站回」是否有足夠正 edge，作為日後 `trend_continuation` 買入路徑的前置證據。
- 可重跑腳本：`arch -arm64 .venv/bin/python scripts/research_trend_continuation.py`
- artifact：
  - `reports/research/trend_continuation_20260603.txt`
  - `reports/research/trend_continuation_20260603.json`
- 資料來源：production DB read-only `daily_price`，本輪讀取 `source_rows=516`；OHLCV、ma5 / ma10 / ma20、volume ratio 與 1/3/5/10 日 forward outcome 由腳本本地計算。
- 只讀邊界：腳本只使用 `select / order / range / execute`；沒有 DB write、schema mutation、Telegram send。
- 結果：
  - `pullback_continuation`：樣本 5，1 日勝率 40.00%、平均 -1.74%；3 日勝率 0.00%、平均 -7.65%；5 日勝率 20.00%、平均 -3.89%；10 日勝率 80.00%、平均 +9.82%；MFE +16.53%、MAE -9.89%。
  - `extended_spike >=1.08`：樣本 78，5 日勝率 65.38%、平均 +6.23%。
  - `extended_spike >=1.15`：樣本 46，5 日勝率 65.22%、平均 +7.45%。
  - `extended_spike >=1.22`：樣本 30，5 日勝率 63.33%、平均 +6.17%。
- 結論：`pullback_continuation_edge=insufficient-data`。目前定義下樣本數低於 `min_sample=30`，且 5 日勝率 20.00%、平均收益 -3.89%，不符合「勝率顯著 >50% 且平均收益為正」。
- 策略含義：階段二 `trend_continuation` 買入路徑不得實裝；更不能放開 RESEARCH.md 既有「證據不得單獨變 BUY / 不得放寬追高」邊界。若要重開，需先擴大樣本來源或重新定義 pullback setup，再跑同層研究。
- 限制：Owner 任務提到 `daily_signal_snapshot / daily_price / signal_outcomes`；本輪腳本實際以 `daily_price` 直接計算 outcomes，未消費 `signal_outcomes`。因此本結論只覆蓋 `daily_price` 可觀測 OHLCV 路徑。

## Trend Continuation Sample Expansion｜2026-06-03

- task_id：`research_daily_price_backfill_and_trend_sample_expansion_20260603`
- 目的：先補 watchlist 12 檔多年 `daily_price`，再用同一研究腳本確認回踩延續樣本是否達到 30+。
- 新增 backfill CLI：`scripts/backfill_daily_price_history.py`
  - dry-run：`arch -arm64 .venv/bin/python scripts/backfill_daily_price_history.py --dry-run --years 1`
  - 指定檔案：`--symbols 3231,2421`
  - 寫入需明確加 `--write --confirm-write`，並可搭配 `--read-after-write`。
  - approved write path：`scripts.backfill_signals.upsert_rows(price_rows, signal_rows=[], client=...)`。
  - watchlist source-of-truth：`core.watchlist.WATCHLIST_CODES`，目前 12 檔：3231、2421、3035、2303、3481、2344、2376、2408、2356、2324、2301、2337。
- 研究 artifact 已更新：
  - `reports/research/trend_continuation_20260603.txt`
  - `reports/research/trend_continuation_20260603.json`
- 實際回填：Owner 已授權後，12 檔逐檔用 approved write path 回填並 read-after-write 通過；總計新增 `daily_price` 5,218 rows。
- read-after-write row count：
  - 3231 485、2421 485、3035 485、2303 485、3481 478、2344 485、2376 485、2408 470、2356 485、2324 485、2301 464、2337 442。
  - 日期範圍皆為 2024-06-03 至 2026-06-03。
- 回填後 `daily_price` 研究結果：
  - universe_count：12。
  - total_hit_count：232，threshold：30，meets_min_sample_count：true。
  - per-symbol hit count：2301=16、2303=22、2324=31、2337=23、2344=20、2356=19、2376=16、2408=8、2421=15、3035=16、3231=31、3481=15。
  - pullback continuation：1 日勝率 46.98%、平均 +0.45%；3 日勝率 55.17%、平均 +1.74%；5 日勝率 55.17%、平均 +2.26%；10 日勝率 54.74%、平均 +2.77%；MFE +9.85%、MAE -4.89%。
  - extended spike 對照：1.08 / 1.15 / 1.22 的 5 日勝率 55.12% / 59.34% / 56.52%，5 日平均 +3.21% / +4.40% / +3.30%，仍只作對照，不等於追高授權。
- 結論：階段一研究門檻已達成，`pullback_continuation_edge=positive`。這代表可以另開階段二 major 策略設計任務；但尚未授權正式實裝，也尚未放開 `RESEARCH.md` 既有硬邊界。階段二需明確定義「只買回踩站回，不買 spike」、小倉位、回踩低點止損、同日入場即錯風控與 evidence gate。

## Data Roles

- `positions`：持倉 source-of-truth。
- `position_events`：已買 / 已賣 / 已停利 / 已減碼的 execution ledger；跨日防重必須用它。
- `daily_signal_snapshot`：每日當時版本留存，用於追溯，不要求舊月份回填 current version。
- `market_theme_confirmed_evidence`：production market/theme evidence，已用于報文中的市場/題材背景。
- `market_theme_index_daily_bars`：market/theme index source table，供 evidence / audit 使用。
- `sector_theme_members`：mapping，不是 daily history。

## Latest Evidence Chain State

- 2026-05 market/theme history 已入庫並通過 audit。
- generator 已消費 production `market_theme_confirmed_evidence`，不是 runtime/local 假資料。
- 05/31 假日报文已修：execution memory 與 evidence display 分層。

## Next Research / Product Question

下一步不是再證明資料表存在，而是定義 evidence 如何「有用但不誤導」：

- 怎樣把 market/theme trend 轉成 Summary / 強勢準備 / 風險提示？
- 怎樣讓使用者看到題材偏多，但仍知道不可追高？
- 怎樣區分 market/theme evidence、strategy sample evidence、個股買點？
- 需要哪些 QA 反證來避免 production confirmed 被讀成 BUY？
