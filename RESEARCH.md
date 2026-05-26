# RESEARCH.md

本文件由 Architect 維護，用來承接研究型任務。PM、Tech、QA 可在各自區塊填寫摘要；Architect 最後只吸收結論，不接收完整聊天紀錄。

## Question

- task_id: `v20-strategy-intelligence-architecture`
- 任務類型：v20 策略智能層升級架構研究
- 任務日期：2026-05-26
- 研究對象：v20 策略智能層，目標是從單日簡單規則升級為多日資料、外部事件、產業題材、回測驗證與未來路徑判斷。
- 背景：Owner 指出旺宏昨日約 140、今日約 160，但策略昨日與今日都輸出淘汰。PM 外部資料研究顯示旺宏不是弱勢股，而是強題材、高波動、注意股。Owner 進一步指出這不是只針對旺宏，而是整個策略層過度依賴簡單規則，缺少多日資料、外部事件、產業題材與策略有效性驗證。Owner 已明確定調：後續主線必須升級策略層，不應繼續把重心放在顯示層 patch。
- 硬邊界：所有 v20 設計最終仍必須服務目前的運行方式：定時執行 GitHub Actions / 腳本，產生策略報文，發送到 Owner Telegram。不得設計成需要 Owner 改用新平台、長時間手動操作儀表板或脫離 Telegram 報文的系統。
- 核心問題：
  - 現有策略需要哪些多日資料才能判斷趨勢、主升、高波動、回測、降溫、假突破。
  - 目前 daily snapshot / replay / backfill 是否足以驗證策略有效性；不足之處要補哪些 DB 表或資料欄位。
  - 外部新聞、題材、注意股、法人籌碼、族群輪動資料應如何進入研究或策略輔助層。
  - 策略輸出 `淘汰 / 等回測 / 等RR修復 / 高波動觀察 / 可買` 應如何用事後績效驗證，而不是只靠規則直覺。
  - 如何避免把「不追價」錯誤顯示為「弱勢淘汰」。
  - 如何建立未來 1/3/5/10 日路徑判斷：最佳路徑、正常路徑、失敗路徑、關鍵觸發價、最大回撤與錯過風險。
  - 後續是否需要 v20 major 開發任務建立策略驗證資料層、外部資料抓取、分類重構、回測報告或策略儀表板。

## Evidence

- Owner 提供最新報文中，旺宏 2337 顯示：
  - 分類：`淘汰｜弱反彈待確認`
  - 價格：160.5（+5.25%）
  - 盤面：弱勢反彈｜中性｜普通｜遠離突破（7.7%）
  - 買點：不買｜弱反彈待確認｜等隔日確認
  - 回測：樣本13｜參考度中｜3日勝率38%｜相對+0.5%｜無明顯優勢
- Architect 初步外部搜尋線索：
  - Yahoo 股市新聞頁提供旺宏 2337 相關新聞入口。
  - StockGo 搜尋結果顯示 2337 旺宏收盤價 160.00，並引用 MoneyDJ 新聞稱旺宏 4 月營收 59.13 億元、月增 33.71%、年增 153.71%。
  - CMoney 搜尋結果顯示旺宏曾有股價上漲逾 9% 至 157.5 的即時新聞，題材包含記憶體多頭、eMMC 缺口、技術面多頭排列、主力與外資買盤延續。
  - 富聯網 / 時報搜尋結果顯示旺宏曾因近日漲跌幅過大列為注意股。
- 以上外部線索只代表需要研究，不代表策略必然錯誤；PM 必須整理來源、日期、價格、題材與策略輸出矛盾點。
- PM 已完成旺宏外部資料研究，結論是旺宏不應直接升為買進，但現有 `淘汰｜弱反彈待確認` 語意不合理，較合理的是 `強題材高波動｜注意股｜不追價｜等回測 / 隔日確認`。
- Owner 補充：這不是只看旺宏，而是要求整個策略層建立能提高勝率的資料與驗證框架；資料不夠可以抓，多日資料需要 DB 就應研究 DB 處理。
- Owner 最新定調：策略太過時，顯示層一直升級沒有意義；後續開發走向必須由 Architect 抓住，主線轉為策略智能層升級。
- Owner 補充：v20 不能超出目前最終交付形態；證據層、資料層、驗證層都必須回到 TG 報文品質與定時執行流程。

## PM Findings

### PM 結論

外部資料不支持把旺宏 2337 簡化為 `弱勢淘汰`。截至 2026-05-26 研究時點，旺宏同時具備三個狀態：

1. 價格與題材明顯強勢：近期從 4 月低檔快速拉升，5 月仍有 160 元附近成交與單日 +5% 以上反彈。
2. 基本面 / 題材偏多：4 月營收創高、NAND / eMMC / NOR 供需缺口與漲價題材明確。
3. 風險也很高：注意股、近 90 日漲幅過大、5 日曾下跌、法人短線大幅賣超，且記憶體族群曾因三星罷工轉單預期落空而急殺。

因此，產品判斷不是「旺宏應直接變可買」，而是現有 `淘汰｜弱反彈待確認` 語意過弱，容易讓使用者以為外部完全不強。更合理的策略輸出應該區分：

```text
強題材高波動｜注意股｜不追價｜等回測 / 等隔日確認
```

如果策略堅持不買，顯示語意也不應歸為「弱勢淘汰」，而應歸為「高波動觀察 / 追價風險 / 注意股觀察」。

### 外部價格比對

- PChome 即時個股頁顯示旺宏 2337 報價 `160.50`、上漲 `+8.00 / +5.25%`，開盤 154.50、最高 162.50、最低 151.00、昨收 152.50，成交約 161,304 張。這和 Owner 認知「約 140 到約 160」方向一致，顯示短線反彈不是內部資料孤例。來源：[PChome 旺宏價量走勢圖](https://pchome.megatime.com.tw/stock/sid2337.html)
- TWSE 個股 PDF 顯示 2026-04-20 收盤 120.5，2026-04-29 收盤 167.0，2026-05-06 收盤 172.0，2026-05-07 收盤 164.5，代表 4 月下旬到 5 月初已有一段強烈主升 / 高波動走勢。來源：[TWSE 個股資訊 PDF](https://www.twse.com.tw/pdf/ch/2337_ch.pdf)
- 富聯網注意股新聞顯示 2026-05-25 最新收盤價 149.50，列注意股原因為最近 90 個營業日起迄兩個營業日收盤價漲幅達 244.86%。來源：[富聯網 2026-05-25 注意股](https://ww2.money-link.com.tw/RealtimeNews/NewsContent.aspx?pu=News_0046&sn=222172030)

產品解讀：

- 價格不是弱勢橫盤，而是「高波動強彈後震盪」。
- 若策略因距離買點、RR 不足、注意股或過熱而不買，合理。
- 但若只輸出 `弱勢淘汰`，語意和外部價格行為不匹配。

### 新聞與題材比對

- TechNews 報導旺宏 2026 年 4 月合併營收 59.13 億元，月增 33.7%、年增 153.7%，前 4 月累計營收 163.81 億元、年增 93.5%。來源：[TechNews 旺宏4月營收](https://finance.technews.tw/2026/05/07/macronix-2337-202604-financial-report/)
- 經濟日報 2026-04-27 法說會報導提到，旺宏董事長吳敏求表示 NAND、eMMC NAND 供需缺口仍然非常大，NOR Flash 與 SLC NAND 下半年仍將持續調漲價格，eMMC 已採月報價；首季 NAND 銷售季增 90%、年增 382%，NOR 季增 31%、年增 47%。來源：[經濟日報旺宏法說會](https://money.udn.com/money/amp/story/5612/9467441)
- CMoney 2026-05-06 即時新聞稱旺宏盤中漲幅約 6.85%、報 171.5，題材包含記憶體族群資金迴流、均線多頭、外資與主力加碼。來源：[CMoney 2026-05-06 旺宏即時新聞](https://cmnews.com.tw/article/cmoneyairesearcher-c8069f68-48ff-11f1-a759-2a26c2e7eede)
- CMoney 2026-05-11 籌碼新聞稱外資買超旺宏 11,463 張、投信買超 5,276 張，三大法人合計買超 16,828 張，收盤 159.50，但同篇也顯示主力近 5 日 / 20 日買賣超為負，籌碼並非單向穩定。來源：[CMoney 2026-05-11 法人籌碼](https://www.cmoney.tw/notes/note-detail.aspx?nid=1188248)

產品解讀：

- 外部題材偏多，且是產業供需與公司營收共同支撐，不是純技術反彈。
- 但籌碼與價格波動劇烈，適合標示為「題材強但追價風險高」，不適合直接升為買進。

### 風險與注意股比對

- 富聯網 / 時報資料顯示旺宏 2026-05-22 被證交所列注意股，原因同為最近 90 個營業日起迄兩個營業日收盤價漲幅達 244.86%；文中並列出近 5 日跌 8.00%、近 5 日三大法人賣超 72,106 張，其中外資賣超 56,026 張、投信賣超 13,328 張。來源：[富聯網 2026-05-25 注意股與法人賣超](https://ww2.money-link.com.tw/RealtimeNews/NewsContent.aspx?pu=News_0046&sn=6183525001)
- FTNN 2026-05-19 報導記憶體族群因三星罷工轉單預期落空與產能議題出現急殺，旺宏與南亞科、華邦電、群聯同列下殺跌停，旺宏該日收 144 元。來源：[FTNN 記憶體族群急殺](https://www.ftnn.com.tw/news/546881)

產品解讀：

- 策略把旺宏列為「不買」有足夠風控理由：注意股、近 90 日大漲、短線急殺、法人賣超、族群高波動。
- 問題不是 `不買`，而是 `弱勢淘汰` 這個分類沒有反映「強題材 + 高波動 + 注意股」。

### 與策略輸出的矛盾點

Owner 報文內部策略顯示：

```text
旺宏 2337｜淘汰｜弱反彈待確認
價格：160.5（+5.25%）
盤面：弱勢反彈｜中性｜普通｜遠離突破（7.7%）
買點：不買｜弱反彈待確認｜等隔日確認
```

外部資料顯示：

- 價格層：近期不是弱勢，而是大漲後高波動。
- 題材層：營收、NAND / eMMC / NOR 漲價、記憶體族群資金均支持偏多題材。
- 風控層：注意股與法人賣超支持不追價。

PM 判斷：

- `不買` 合理。
- `等隔日確認` 合理。
- `淘汰` 不合理，因為淘汰通常代表弱勢、遠離觸發或不值得明日追蹤。
- `弱反彈待確認` 部分合理，但語氣太弱，沒有表達它是題材強彈後的高風險標的。

### 產品建議

#### 優先建議：改分類語意，不先改買入門檻

先不要直接把旺宏改成 BUY，也不要放寬 RR / 過熱 / 注意股門檻。更合理的第一步是新增或調整未持倉分類：

```text
高波動觀察｜注意股｜不追價
強題材回測｜等降溫
題材強彈｜等隔日確認
```

旺宏這類標的應從 `弱勢淘汰` 移出，進入：

```text
未持倉追蹤（不可買）
```

而不是：

```text
弱勢淘汰
```

#### 需要 Tech 後續檢查的方向

PM 建議 Tech 後續檢查以下問題，不在本輪改代碼：

1. `弱勢反彈` 是否只看價格與突破距離，導致忽略近期漲幅、題材與量價強度。
2. `遠離突破（7.7%）` 的正負語意是否符合實際價格位置；若價格大漲後被判遠離突破，可能需要確認突破基準與方向。
3. `淘汰` 是否被太早套用在「不可買但值得追蹤」標的上。
4. 注意股 / 過熱 / RR 不足是否應輸出為「風控觀察」而非「弱勢淘汰」。
5. 未持倉漏斗是否需要新增 `高波動追蹤` 類別，避免所有不買都落入淘汰。

### PM 最終判斷

旺宏 2337 外部資料顯示：

- 不是弱勢股。
- 是強題材、強波動、注意股。
- 不追價合理。
- 連續輸出 `淘汰｜弱反彈待確認` 會誤導使用者低估該股的市場強度。

建議下一步交 Tech / QA 研究策略分類與資料映射，不直接改買入門檻。若要改產品輸出，優先修正為：

```text
旺宏｜高波動觀察｜注意股，不追價｜等回測 / 隔日確認
```

而非：

```text
旺宏｜淘汰｜弱反彈待確認
```

## Tech Findings

### Tech 結論

目前策略已經不是純單日判斷：`services/analysis.py` 有 1 / 3 / 5 / 10 日漲跌、5 / 10 日量比、`multi_day_bias`、`momentum_signal`、`structure_phase`、`heat_state`、`trade_state`、RR、breakout distance 等欄位。但它仍主要依賴「價格 / 量能 / 均線 / 突破距離」這一組內部技術資料，缺少三類關鍵上下文：

1. 事件上下文：題材、營收、法說、產業供需、注意股、處置、新聞強度。
2. 市場相對上下文：同族群強弱、同日股票池排名、主題輪動、類股是否同步發動。
3. 事後驗證上下文：分類後 1 / 3 / 5 / 10 日的最大浮盈、最大回撤、是否曾出現更好買點、是否被錯誤淘汰。

因此旺宏案例不應直接用單股調參解決。技術上應建立「策略輸出可被外部事實與多日結果反證」的資料層，先驗證分類是否失真，再決定要改策略、改分類、或只改顯示語意。

### 現有策略依賴資料與缺口

已使用資料：

- 日線 close / volume，最少 20 筆。
- MA5 / MA20。
- 1 / 3 / 5 / 10 日價格變化。
- 5 / 10 日量比。
- 突破距離與 20 日壓力區。
- 單日漲跌幅、漲停 / 反彈 / 弱反彈 / 縮量回測 / 放量突破等價格行為。
- RR、risk、entry quality、confidence score、market grade、trend、structure、volume state。
- 持倉與未持倉分流：持倉股不應污染新進場 `is_tradeable / is_best_candidate`。

主要缺口：

- 缺少 20 / 60 / 90 日報酬、距高點 / 距低點、波動率、ATR、連續上漲 / 下跌天數、回撤深度。
- 缺少高低點路徑資料用於判斷「分類後是否先大漲再回落」或「是否先回測再突破」。
- 缺少族群 / 產業 benchmark，無法判斷個股是弱勢反彈，還是整個族群主升中的高波動回檔。
- 缺少注意股 / 處置 / 漲跌幅異常資料，導致 `不追價`、`高波動觀察`、`弱勢淘汰` 容易混在一起。
- 缺少外部事件與題材標籤，無法把「強題材但高風險」和「沒有題材的弱反彈」分開。
- 缺少法人 / 主力籌碼欄位，無法判斷漲跌是籌碼延續、短線出貨、或事件驅動。

### 現有 DB 是否足夠

目前五張核心回測 / snapshot 表可支撐第一版策略驗證，但不足以支撐全策略層外部驗證。

#### `daily_price`

能力：

- 保存 daily OHLCV。
- 可計算日後 1 / 3 / 5 / 10 日 close return。
- 可補算 MA、量比、回撤與突破距離。

不足：

- 目前正式寫入依賴每日報文成功取得完整 OHLCV，歷史深度不足時只能覆蓋報文日，不是完整研究型 K 線倉庫。
- 沒有調整後價格、交易值、漲跌停資訊、是否注意 / 處置。
- 若只存 12 檔 watchlist，無法計算類股 / 市場相對強弱。

#### `daily_signal_snapshot`

能力：

- 保存策略分類：pattern、market_state、structure_state、position_state、RR、score、heat_level、action、reasons、tradeable、best candidate。
- 有 12 檔完整覆蓋 guard，適合作為報文當日策略快照。

不足：

- 不保存完整策略 raw_result，只保存摘要欄位；對後續研究「為什麼判弱反彈」不夠。
- 缺少分類層次：`不買原因`、`風控原因`、`強度標籤`、`外部題材標籤` 混在 reasons 中，難以分辨「弱勢淘汰」和「強勢但不追」。
- 沒有保存外部來源與資料可信度。

#### `signal_runs / signal_items`

能力：

- 保存每日報文 run、每檔 signal item、持倉狀態、價格、change、decision、holding_action、RR、structure / volume / heat / trade state、breakout_distance。
- `raw_result` 有保存部分策略補充欄位，例如 `entry_stage`、`entry_profile`、`market_regime`、`multi_day_bias`、`extended_level`、`rank_score`、`price_source`。

不足：

- `raw_result` 刻意不保存完整 K 線，避免 DB 膨脹；這對正式報文合理，但對策略研究不足。
- 沒有 snapshot 當下的完整多日特徵，例如 20 / 60 / 90 日報酬、ATR、距高低點、族群 rank、題材分數、注意股狀態。
- 沒有保存 formatter 最終分類，如 `高波動觀察 / 等RR修復 / 淘汰` 的穩定 taxonomy；目前這類常在 formatter helper 中組合，研究時不易追溯。

#### `signal_outcomes`

能力：

- 設計上已有 1 / 3 / 5 / 10 日 outcome。
- 目前可保存 future_price、future_change_pct、outcome。

不足：

- `max_high_pct`、`max_drawdown_pct` 目前為 `None`，無法回答「淘汰後是否曾大漲」或「等回測是否先等到更低風險價格」。
- outcome 只用當日 results_map 現價更新，若未來日缺該股票價格，結果會漏。
- outcome 只按 close-to-close，缺少路徑與相對股票池 / 族群表現。
- 沒有分類混淆矩陣，無法直接比較 `淘汰 / 等回測 / 等RR修復 / 可買` 的事後分布。

### 建議新增或強化的資料表

本輪不改 DB，但後續若要開發，建議分成「研究資料層」與「策略正式輸出層」，避免外部資料尚未穩定時污染每日正式報文。

#### 1. `market_daily_bars`

用途：完整 OHLCV 研究倉庫。

建議欄位：

- `stock_id`
- `trade_date`
- `open / high / low / close / volume / turnover`
- `source`
- `is_adjusted`
- `limit_up / limit_down`
- `attention_flag / disposition_flag`
- `created_at`

目的：

- 不只服務每日報文，也服務多日研究。
- 讓 outcome 可以計算最大浮盈、最大回撤、隔日是否回測、是否突破前高。

#### 2. `strategy_feature_snapshots`

用途：保存策略當日完整特徵，不只保存輸出結果。

建議欄位：

- `stock_id / trade_date / version`
- `chg_1d / chg_3d / chg_5d / chg_10d / chg_20d / chg_60d / chg_90d`
- `vol_ratio_5 / vol_ratio_10 / vol_ratio_20`
- `atr_14 / volatility_20`
- `drawdown_from_20d_high / distance_from_20d_low`
- `breakout_distance`
- `market_grade / trend / structure_state / structure_phase / price_behavior / heat_state / trade_state`
- `entry_profile / entry_quality / confidence_score / rr`
- `watch_category`：例如可買、等回測、等RR修復、高波動觀察、弱勢淘汰。
- `reject_family`：追價風險、RR不足、弱勢、量能不足、注意股、資料不足。

目的：

- 把策略分類變成可回測的穩定 taxonomy。
- 避免只靠 raw message 文字解析。

#### 3. `strategy_outcome_metrics`

用途：取代或強化 `signal_outcomes`。

建議欄位：

- `snapshot_id`
- `horizon_days`
- `close_return_pct`
- `relative_return_pct`：相對同日股票池或族群。
- `max_favorable_excursion_pct`
- `max_adverse_excursion_pct`
- `hit_stop_like_drawdown`
- `hit_breakout_after_signal`
- `best_entry_gap_pct`：訊號後是否曾給更低風險買點。
- `outcome_label`：win / loss / flat / late_win / whipsaw。

目的：

- 回答「不買是否錯過」、「等回測是否有用」、「RR不足是否真的應等待」。

#### 4. `sector_theme_daily`

用途：族群 / 題材強度。

建議欄位：

- `trade_date`
- `theme_code / theme_name`：例如 memory、semiconductor、AI server。
- `constituents`
- `theme_return_1d / 3d / 5d / 20d`
- `theme_volume_ratio`
- `leader_stock_ids`
- `breadth`：族群內上漲比例。
- `source`

目的：

- 判斷個股強勢是孤立反彈還是族群輪動。
- 旺宏類案例可避免被單股技術狀態誤判為弱勢。

#### 5. `stock_theme_map`

用途：股票與題材 / 產業映射。

建議欄位：

- `stock_id`
- `theme_code`
- `weight`
- `valid_from / valid_to`
- `source`

目的：

- 讓 strategy feature 可以拉入「所屬題材強度」。

#### 6. `market_events`

用途：新聞、營收、法說、注意股、處置、異常波動等事件。

建議欄位：

- `event_date`
- `stock_id`
- `event_type`：news、revenue、attention、disposition、legal_person_flow、earnings、industry_supply。
- `title`
- `summary`
- `source_url`
- `source_name`
- `sentiment`：positive / negative / mixed / neutral。
- `impact_score`
- `tags`：NAND、eMMC、漲價、注意股、外資賣超等。
- `dedupe_key`

目的：

- 外部事件只先做研究 / 輔助分類，不直接產生 BUY。
- 支撐「強題材高波動」而不是硬塞進弱勢 / 可買。

#### 7. `legal_person_flows`

用途：法人籌碼。

建議欄位：

- `stock_id / trade_date`
- `foreign_net_buy`
- `investment_trust_net_buy`
- `dealer_net_buy`
- `total_net_buy`
- `source`

目的：

- 分辨主升延續、法人撤退、籌碼分歧。

#### 8. `strategy_classification_audit`

用途：專門記錄分類是否疑似失真。

建議欄位：

- `stock_id / trade_date / version`
- `original_category`
- `suggested_audit_category`
- `distortion_type`
- `evidence`
- `severity`
- `review_status`

目的：

- 不自動改策略，只標記需要人工或後續模型研究的失真案例。

### 回測指標設計

策略不能只看勝率。建議每個分類都產生以下報告：

#### 基礎結果

- n 樣本數。
- 1 / 3 / 5 / 10 日平均報酬。
- median 報酬。
- 勝率。
- 相對同日股票池報酬。
- 相對所屬族群報酬。

#### 路徑風險

- 最大浮盈 MFE。
- 最大回撤 MAE。
- MFE / MAE 比。
- 先跌後漲比例。
- 先漲後跌比例。
- 是否觸及策略停損 / 警戒區。

#### 分類有效性

- `淘汰` 後 1 / 3 / 5 日大漲比例。
- `等回測` 後是否真的給更低風險進場點。
- `等RR修復` 後 RR 是否改善，以及改善前追價績效是否較差。
- `高波動不追` 後是否更常出現大回撤。
- `可買` 後是否比 `可觀察但不可買` 有更高 MFE / 更低 MAE。
- `弱勢淘汰` 與 `高波動觀察` 的 outcome 是否顯著不同。

#### 持倉策略效果

- `續抱 / 核心續抱 / 洗盤續抱 / 洗盤警戒 / 減碼 / 停利` 後的 1 / 3 / 5 / 10 日表現。
- 停利後是否常錯過後續大漲。
- 續抱後是否常回吐。
- 小虧洗盤警戒後是否真的修復。

### 外部資料如何進入策略

短期不建議讓新聞 / 題材直接改 BUY。建議分三層：

1. 研究層：入庫、標籤化、和策略分類做事後比對。
2. 顯示 / 輔助分類層：把 `弱勢淘汰` 修正成 `高波動觀察 / 注意股 / 強題材不追` 這類更準確語意。
3. 策略層：等外部資料經過回測證明有效後，才作為權重或 guard。

外部資料可先影響：

- watch category。
- warning / risk note。
- tomorrow trigger。
- audit flag。

不應先直接影響：

- `decision=BUY`
- `action_pct`
- `is_tradeable`
- `is_best_candidate`

### 如何判斷策略分類是否失真

建議建立「分類失真」判定，不等於策略錯，也不等於必買。

#### 失真類型 A：弱勢分類與多日強勢衝突

條件例：

- 分類為 `弱勢淘汰 / WEAK_REBOUND / 市場弱`。
- 但 5 / 10 / 20 日報酬顯著高於股票池與族群。
- 且外部題材 / 注意股 / 成交量異常存在。

建議 audit label：

```text
高波動強勢，非弱勢淘汰
```

#### 失真類型 B：不追價合理，但分類過度負面

條件例：

- RR不足、過熱、注意股、遠離觸發。
- 但 trend / theme / sector 強。
- outcome 常有高 MFE，同時也有高 MAE。

建議分類：

```text
高波動觀察 / 強題材不追 / 等降溫
```

#### 失真類型 C：等回測無效

條件例：

- `等回測` 後 3 / 5 日很少出現更佳 RR 或回測點。
- 或經常直接續漲，導致機會成本高。

可能策略問題：

- 回測條件太嚴。
- 突破延續情境缺少小倉追蹤。

#### 失真類型 D：RR不足誤殺強趨勢

條件例：

- `等RR修復` 樣本在高族群強度、強題材時，後續相對報酬顯著為正。
- 但在無題材或弱族群時無效。

可能策略調整：

- RR 不應單獨放寬；應和族群強度 / 題材 / 波動風險共同判斷。

#### 失真類型 E：可買分類品質不足

條件例：

- `可買` 後 MFE 不高、MAE 高、相對報酬低於觀察組。

可能策略問題：

- entry_quality 權重錯。
- 量能 / 市場 / 位置評分過度樂觀。

### 建議後續開發順序

#### Phase 1：不改策略，補研究資料

- 強化 daily OHLCV 歷史入庫。
- 補 outcome 的 MFE / MAE。
- 保存完整 strategy feature snapshot。
- 建立 classification report：每個分類的 1 / 3 / 5 / 10 日結果。

#### Phase 2：外部事件研究入庫

- 注意股 / 處置資料。
- 法人買賣超。
- 題材 / 新聞標籤。
- 族群強度。

#### Phase 3：分類 taxonomy 重構

- 把 `淘汰` 拆成：
  - 弱勢淘汰。
  - 高波動不追。
  - 強題材等降溫。
  - RR不足等修復。
  - 量能不足等確認。
- 報文顯示先使用新 taxonomy，策略 BUY 門檻暫不動。

#### Phase 4：策略門檻回測後再調整

- 只對回測有顯著差異的分類調整門檻。
- 不用單一旺宏案例改整體策略。
- 每次調整必須輸出前後對照：信號數、勝率、MFE、MAE、相對報酬、錯失強勢股比例。

### 技術風險

- 外部新聞與題材資料噪音高，不能未經驗證直接進 BUY。
- 注意股 / 處置資料來源需要穩定且可追溯，否則會造成報文與事實不一致。
- 只看 12 檔股票池會讓族群相對強度失真；若要做族群強度，需要擴大研究資料池，但正式報文仍可維持 12 檔。
- DB 膨脹風險：完整 K 線與新聞資料應分表存，不應塞進 `signal_items.raw_result`。
- 回測不可使用未來資料：外部事件必須保存 `published_at / effective_date / ingested_at`，回測只能使用當時已知資料。
- replay/backfill 需要明確區分「策略當日可見資料」與「事後驗證資料」。

### Tech 最終建議

下一步不應直接修改 `services/analysis.py`。建議先開發「策略驗證資料層」：

1. 補完整多日 OHLCV 與 outcome path metrics。
2. 保存穩定的 strategy feature snapshots。
3. 建立分類績效報告。
4. 新增外部事件 / 題材 / 注意股研究表。
5. 用 audit report 找出 `弱勢淘汰`、`等回測`、`等RR修復` 等分類是否真的失真。

旺宏這類案例在技術上應先被標記為：

```text
不追價合理，但弱勢淘汰語意疑似失真；需要高波動 / 題材 / 注意股分類。
```

而不是直接改成 BUY 或用單股結果調整所有門檻。

## QA Findings

### QA 結論

QA 對 PM / Tech / Architect Findings 給出 conditional approval：方向正確，但目前架構只能降低旺宏類錯殺風險，還不能保證避免。最大優點是沒有直接用旺宏單一案例放寬 BUY / RR / 過熱門檻，而是先建立策略證據層、outcome path metrics、外部事件研究層與分類 taxonomy。這可以避免「看到一檔錯過就全局調參」。

但 v20 若要進入開發，必須補上明確 QA guardrail，否則會從「單日規則錯殺」變成另一種風險：用事後資料、噪音新聞、不可驗證指標或膨脹資料表製造看似智能、實際不可回測的策略層。

### 是否足以避免旺宏類錯殺

目前設計足以發現旺宏類錯殺，但不足以自動避免。理由：

- `strategy_feature_snapshots` + `strategy_outcome_metrics` 能在事後回答「弱勢淘汰後是否大漲」、「等回測是否錯過」、「RR不足是否誤殺強趨勢」。
- `market_events`、`sector_theme_daily`、`legal_person_flows` 能把旺宏這類「題材強、波動高、注意股、不適合追價」從純弱勢中分離。
- `strategy_classification_audit` 能標記 `不追價合理，但弱勢淘汰語意失真`，這正好覆蓋旺宏案例。

反證風險：

- 若 Phase 1 只做 outcome 報告，尚未改 taxonomy，使用者仍可能看到 `淘汰｜弱反彈待確認`。
- 若 Phase 2 外部事件未穩定入庫，旺宏類案例仍可能被技術面單獨壓成弱勢。
- 若 Phase 3 taxonomy 只改顯示文字，沒有保存穩定 `watch_category / reject_family / audit_label`，後續仍無法驗證分類是否真的改善。

QA 要求：v20.0 第一版不能宣稱「避免錯殺」，只能宣稱「建立可識別錯殺與分類失真的證據層」。真正避免錯殺至少要到 taxonomy 重構後，再用前後對照報告證明。

### 過度擬合風險

PM / Tech 已避免直接把旺宏改成 BUY，這是正確防線。但仍有過度擬合風險：

- 若 `高波動強題材` 的條件是用旺宏特徵倒推，例如 90 日漲幅、營收年增、注意股、記憶體題材同時成立，可能只對旺宏有效。
- 若分類報告只看 12 檔 watchlist，樣本量太小，`淘汰後大漲比例`、`等回測有效率` 容易被單一股票或單一產業週期主導。
- 若外部新聞權重靠人工主觀分數，容易把近期熱門題材調得過強，回測看似改善但實盤不穩。
- 若每次 missed winner 都新增一個例外分類，taxonomy 會膨脹成不可維護的例外表。

QA guardrail：

- 每個新分類必須有最小樣本數門檻，低樣本只能標示 `insufficient_evidence`，不得用來改 BUY 門檻。
- 報告必須分 train / validation 時段，不能只用同一段歷史同時設計分類與驗證分類。
- 每次策略門檻調整必須輸出 before / after：信號數、勝率、MFE、MAE、相對報酬、錯失強勢股比例、最大回撤惡化幅度。
- 旺宏只能作為 seed case，不能作為驗收唯一樣本。

### 未來資料洩漏風險

這是 v20 最大 blocker 風險。Tech 已提到 `published_at / effective_date / ingested_at`，但 QA 認為仍需升級為硬性資料契約：

- 外部新聞、營收、法說、注意股、法人籌碼必須保存 `source_time`、`published_at`、`market_effective_at`、`ingested_at`、`source_url`。
- 回測特徵只能使用 signal time 當下已發布且已入庫資料；不能使用晚間才公告、隔日才整理、或事後修訂的資料。
- 注意股 / 處置原因常在盤後公告，若用於當日盤中策略，必須標記不可用；若用於收盤後隔日計畫，才可使用。
- 財報 / 營收有公告時間與市場可交易時間差，不能只用 `event_date`。
- outcome metrics 必須與 feature snapshots 分表，且查詢層要明確禁止 feature generation join future outcome。

QA 要求：v20.0 開發前，TASK 必須明確定義 point-in-time rule。任何無時間戳或無來源 URL 的外部事件只能進 audit 備註，不得進策略特徵或分類績效計算。

### 外部資料噪音風險

PM 外部研究證明旺宏不是弱勢，但新聞 / 題材資料也可能高度噪音：

- 新聞標題常有情緒偏差，且利多新聞可能出現在股價已反映之後。
- CMoney、媒體快訊、社群評論可能重複轉載同一事件，若不 dedupe，`impact_score` 會被放大。
- 題材標籤會快速變動，同一股票可能同時屬於記憶體、半導體、AI、低價轉機等多個主題，權重不清會造成分類不穩。
- 法人買賣超有日頻延遲，短線可能與價格反向，不能單獨視為強弱證據。
- 注意股是風險標籤，不是看多或看空標籤；若錯誤使用，會把「高波動強勢」誤判為「不能碰」或「一定會續漲」。

QA guardrail：

- 外部資料第一版只能進 `audit / display / research`，不得直接推動 `decision=BUY`、`is_tradeable=True`、`action_pct`。
- `market_events` 必須有 dedupe_key、source_name、confidence / reliability、event_type，且同一事件多來源不能重複加分。
- 題材分數必須可追溯到 constituent / source / valid_from / valid_to，不可只保存一個不可解釋的 theme_score。

### DB 膨脹與資料治理風險

Tech 建議分表是正確方向，但 v20 有明顯 DB 膨脹風險：

- 如果把完整 K 線、新聞全文、raw_result、外部事件、outcome path 全塞進正式報文表，會拖慢每日任務與 QA。
- 若 `strategy_feature_snapshots` 每次改策略版本都全量重算並保留，資料量會快速膨脹。
- 若新聞 `summary` 保存過長或未去重，`market_events` 會變成不可維護的內容倉庫。
- 若缺少 retention / partition / archive 規則，後續 backfill 與測試成本會失控。

QA 要求：

- 研究資料層與正式報文層必須分離；正式 Telegram / signal path 不應依賴大型新聞表即時查詢。
- `market_daily_bars` 和 outcome 表應有 unique key：`stock_id + trade_date + source` 或 `snapshot_id + horizon_days`，避免重跑 backfill 重複寫入。
- 外部新聞第一版只保存摘要、URL、標籤與時間戳，不保存全文。
- v20 TASK 必須包含資料量預估、索引設計、重跑冪等性、backfill dry-run 策略。

### 指標不可驗證風險

Tech 指標方向完整，但部分指標若不定義公式，會變成不可驗證：

- `best_entry_gap_pct` 必須定義「更好買點」是價格更低、RR 更好、回撤更小，還是觸發價更接近。
- `hit_stop_like_drawdown` 必須定義 stop-like 門檻來自策略停損、ATR、固定百分比，或持倉風控線。
- `relative_return_pct` 必須定義相對對象：12 檔 watchlist、TWSE 加權、同族群、或候選池。
- `outcome_label` 的 win / loss / late_win / whipsaw 必須可由數學規則產生，不可人工主觀標記。
- `impact_score` / `sentiment` 若來自 LLM 或人工，必須保存模型版本或評分規則，否則不可回測。

QA 要求：v20.0 第一版只接受可用 deterministic formula 驗證的指標。不可驗證的外部 sentiment / impact score 只能作為展示或 audit note，不能作為策略調參依據。

### 分類仍會誤導使用者的風險

目前 Findings 已識別 `淘汰` 太粗，但 taxonomy 重構仍可能造成新誤導：

- `高波動觀察` 可能被使用者誤讀為「值得追」而忽略注意股 / 不追價。
- `強題材等降溫` 可能被誤讀為「一定會再漲，只是等便宜」。
- `等RR修復` 若沒有觸發價 / 失效價，使用者不知道明天該看什麼。
- `弱勢淘汰` 若仍和 `不可買追蹤` 混在一起，使用者仍分不清「不值得看」和「不能買但值得追蹤」。
- 若摘要壓縮只顯示分類，不顯示主要 blocker，會把風控理由藏起來。

QA guardrail：

- 新 taxonomy 必須拆成兩層：`market_strength` 與 `execution_permission`。例如「題材強 / 高波動」不能自動等於「可買」。
- 報文必須明確區分 `可執行`、`僅追蹤`、`淘汰不追`。
- 每個 `僅追蹤` 類別必須有下一步：等回測價、等 RR、等量能、等注意股解除、等隔日確認。
- `注意股 / 高波動 / 不追價` 必須在摘要與詳情都可見，不能只藏在詳情。

### QA 反證摘要

- PM 是否漏需求：PM 已抓到「不買合理但弱勢淘汰誤導」；但還缺少 taxonomy 使用者誤讀防線與下一步顯示契約。
- Tech 是否漏同步：Tech 架構覆蓋 DB / outcome / 外部事件 / taxonomy；但需要把 point-in-time、指標公式、資料治理寫成開發硬契約，而不是風險提醒。
- Architect 結論是否可進開發：可進 v20.0 Strategy Evidence Foundation，但第一版範圍應限於證據層與分類報告，不應同時改 BUY / SELL 門檻。
- 是否足以避免旺宏類錯殺：目前足以識別與量化，不足以保證避免；需 Phase 3 taxonomy 重構與後續前後對照驗證。

### QA 建議給 Architect 的開發門檻

v20.0 TASK 若要交給 Tech，QA 建議至少包含以下不可省略項：

1. point-in-time 資料契約：所有外部事件必須有 published / effective / ingested time。
2. deterministic 指標公式：MFE、MAE、relative return、best entry、whipsaw 必須定義清楚。
3. 資料層分離：研究表不得拖慢正式 Telegram / signal path。
4. 冪等 backfill：所有新表需 unique key 與重跑不重複寫入。
5. 分類報告：至少能按原分類輸出 1 / 3 / 5 / 10 日 outcome 分布。
6. taxonomy 不改 BUY：第一版只建立證據與 audit，不直接放寬買入門檻。
7. 使用者語意防線：任何新分類都要同時標出可執行 / 僅追蹤 / 淘汰不追。

QA 結論：conditional approval。建議 Architect 允許進入 v20.0「策略證據資料層」開發規劃，但必須把上述 guardrail 寫入 TASK；若下一步直接改策略門檻或直接把外部新聞接入 BUY，QA 應阻塞。

## Architect Conclusion

Architect 最終收口：

- v20 必須先做「策略證據層」，不是直接改買賣門檻。
- 目前策略不是完全單日，但資料仍偏內部技術面，缺少外部事件、族群、法人、注意股與事後路徑驗證。
- 旺宏案例的核心不是「應不應買」，而是分類 taxonomy 失真：`不追價合理` 不應被壓成 `弱勢淘汰`。
- 若直接修改 `services/analysis.py` 或放寬 RR / 過熱門檻，風險是用單一案例調參，會產生過度擬合。
- 正確起手式是先建立可驗證的資料與報告，讓每個策略分類都能被 1/3/5/10 日後續表現反證。
- 所有設計必須保持「定時任務可跑、報文可讀、TG 可交付」；任何資料層或驗證層都只是支撐報文，不是另做產品。

v20 建議拆四階段：

1. Phase 1：策略證據資料層
   - 補完整多日 OHLCV 研究倉庫。
   - 補 outcome path metrics：MFE、MAE、relative return、是否給更好買點。
   - 保存穩定 strategy feature snapshots 與 watch category taxonomy。
   - 先產出可被每日任務引用的分類績效摘要，不改 BUY / SELL。

2. Phase 2：外部事件與市場相對層
   - 注意股 / 處置 / 漲跌停。
   - 法人買賣超。
   - 族群 / 題材強度。
   - 新聞 / 營收 / 法說事件標籤。
   - 先作為 audit / 報文顯示 / 追蹤輔助，不直接觸發 BUY。

3. Phase 3：策略分類 taxonomy 重構
   - 把 `淘汰` 拆成 `弱勢淘汰`、`高波動不追`、`強題材等降溫`、`RR不足等修復`、`量能不足等確認`。
   - 優先解決「分類誤導」與「錯殺可追蹤標的」，仍不直接放寬買入門檻。

4. Phase 4：策略門檻回測後調整
   - 只對有統計證據的分類調整門檻。
   - 每次調整必須給前後對照：信號數、勝率、MFE、MAE、相對報酬、錯失強勢股比例。

建議第一個 v20 開發任務不是「改策略」，而是：

```text
v20.0 Strategy Evidence Foundation
建立策略證據資料層與分類績效報告
```

第一版驗收目標：

- 能回答 `淘汰` 後 1/3/5/10 日是否經常大漲。
- 能回答 `等回測` 是否真的等到更好風報。
- 能回答 `RR不足` 是否真的比追價安全。
- 能回答 `弱勢淘汰` 是否混入高波動強題材標的。
- 能在定時任務中產出簡短策略證據摘要，並整合回 Telegram 報文；不要求 Owner 打開新平台。

QA 已完成反證，結論為 conditional approval。Architect 接受此結論：

- 可以進入 v20.0 `Strategy Evidence Foundation` 正式 TASK。
- v20.0 第一版只做策略證據資料層與分類績效報告。
- 不直接改 BUY / SELL 門檻。
- 不把外部新聞、題材、法人資料直接接入 `decision=BUY`、`is_tradeable=True` 或 `action_pct`。
- 所有資料與報告必須支撐「定時執行 -> Telegram 報文」交付，不做獨立平台。

v20.0 TASK 必須包含 QA guardrails：

1. Point-in-time 資料契約：外部事件需有 published / effective / ingested time。
2. Deterministic 指標公式：MFE、MAE、relative return、best entry、whipsaw 必須明確。
3. 資料層分離：研究表不得拖慢正式 Telegram / signal path。
4. 冪等 backfill：新表需 unique key 與重跑不重複寫入。
5. 分類報告：至少按原分類輸出 1 / 3 / 5 / 10 日 outcome 分布。
6. Taxonomy 不改 BUY：第一版只建立證據與 audit，不放寬買入門檻。
7. 使用者語意防線：新分類需標出可執行 / 僅追蹤 / 淘汰不追。

## Next Action

- PM：旺宏外部資料研究已完成。
- Tech：全策略層多日資料、DB、回測與外部事件資料框架研究已完成。
- QA：v20 架構反證完成，conditional approval。
- PM：下一步撰寫 v20.0 `Strategy Evidence Foundation` 正式 `TASK.md`。
