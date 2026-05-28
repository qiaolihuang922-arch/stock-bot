# RESEARCH.md

本文件保存最新研究任務的高信號摘要，不保留完整聊天紀錄。

## Latest Research

- task_id: `20260528_120657_23719_online_research_pair`
- 日期：2026-05-28
- 狀態：CAO online PM / QA research ready，等待 Architect 吸收結論
- 來源輸出：`/Users/liveroom/stock-bot-agent-context/outputs/20260528_120657_23719_online_research_pair.md`

## Question

Owner 指出：目前 v20.0.12 只補了市場主線與執行態度的保護邏輯 / 文案橋接，真正的市場 / 題材證據鏈尚未建立。請做研究，不要改產品代碼。研究問題：如何為 Telegram 報文建立可追溯的市場主線 / 題材證據鏈？需回答：1) 產品上要證明什麼，哪些詞句需要證據才可出現，例如 AI/電子供應鏈仍偏多、題材仍可追蹤、不代表看空產業；2) 可用證據來源有哪些：watchlist 內部價格/量能/分類、類股或指數、外部新聞/法人/產業資料、既有 strategy_evidence / snapshot；3) 證據等級與 fallback：confirmed/weak/absent/stale，資料缺失時報文怎麼降級；4) 技術方案：是否需要 schema / cache / provider / scheduler / payload 欄位 / formatter contract；5) QA 如何反證：避免無證據硬寫主線、證據過期、非 AI 場景誤寫 AI、方向偏多被誤讀成可買；6) 不做 live Supabase write、正式 backfill、live Telegram，不改策略決策。請 PM/Tech/QA 分別在 RESEARCH.md 輸出摘要，Architect 最後收口。

## Evidence

- 本輪由 Architect 本地 runner 觸發 CAO online read-only PM / QA。
- Online agent 工作目錄：`/Users/liveroom/stock-bot-agent-context/online_research`。
- Online agent 可查公開網路資料，但不直接讀真實 repo、不改代碼、不寫固定 8 份 Markdown。
- Tech 自動寫碼仍未啟用；若研究結論需要開發，需由 Architect 轉成 `TASK.md` 後交給 Tech。

## PM Findings

• 我會先只讀工作目錄內的摘要文件，確認目前專案脈絡與既有研究狀態；接著查公開來源，最後用 PM 角度整理成可交給 Architect 收口的研究結論，不改任何檔案。

• Ran pwd && rg --files -g '*.md'
  └ /Users/liveroom/stock-bot-agent-context/online_research
    DISPATCH.md
    … +3 lines (ctrl + t to view transcript)
    README.md
    CURRENT_STATE.md

• Explored
  └ Read DISPATCH.md, RESEARCH.md, TASK.md, CURRENT_STATE.md

◦ Searching the web

• Searched Taiwan Stock Exchange sector indices official data industry index TWSE electronics semiconductor ...

• Searching the web

• Searched MOPS Taiwan company monthly revenue official English ...

• Searching the web

• Searched https://www.twse.com.tw/en/indices/indices/series.html

◦ Searching the web

• Searched NVIDIA Taiwan supply chain AI demand official press release 2026 ...

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• ## 1. 公開證據與來源

  - TWSE 官方指數可作市場/類股證據：TAIEX 衡量 TWSE 整體上市股票表現；TWSE 也有 Electronics 相關指數與 FTSE TWSE Taiwan Technology Index，可作「電子 / 科技主線」的市場層證據。來源：TWSE Index Series。(twse.com.tw
    (https://www.twse.com.tw/en/indices/indices/series.html))
  - TWSE 官方入口列出個股日成交量/成交值、外資與其他法人每日交易彙總等資料，可作價格、量能、法人流向來源。(twse.com.tw (https://www.twse.com.tw/en/focus/investing.html))
  - 政府開放資料有「三大法人 / 外資持股比率」資料集，欄位包含產業、總股數、外資持股、持股比例，更新頻率每日，可作法人結構證據。(data.gov.tw (https://data.gov.tw/en/datasets/11655))
  - FinMind 提供台股資料 API，文件明確支援 TaiwanStockPrice 等資料集，並有 request limit；適合作為非官方但結構化的備援資料源。(finmind.github.io (https://finmind.github.io/v3/quickstart/))
  - TSMC 官方月營收頁可作 AI / 半導體基本面佐證之一，例如 2026 Jan-Apr 合併營收年增 29.9%，但這只能支持「供應鏈基本面仍有證據」，不能直接推出「今天可買」。(investor.tsmc.com
    (https://investor.tsmc.com/english/monthly-revenue/2026))
  - TSMC 2026/05/08 官方新聞稿列出 2026 Apr 營收年增 17.5%、Jan-Apr 年增 29.9%，可作具時間戳的外部公司證據。(pr.tsmc.com (https://pr.tsmc.com/english/news/3305))
  - NVIDIA 官方財報新聞稿顯示資料中心收入與 AI 平台需求仍強，可作全球 AI demand 的外部佐證；但它不是台股個股買點證據。(investor.nvidia.com
    (https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2026/default.aspx?utm_source=openai))
  - SEMICON Taiwan 官方描述其覆蓋晶圓製造、設備材料、IC 設計、系統應用與 AI x semiconductor，適合作為題材分類 taxonomy 參考，不適合作即時方向判斷。(semicontaiwan.org (https://www.semicontaiwan.org/en/?utm_source=openai))

  ## 2. 產品結論

  Telegram 不能再用單一句「AI / 電子供應鏈仍偏多」當黑盒結論。產品上要證明三件事：

  - 市場層：大盤 / 電子 / 科技或半導體相關指數是否支持偏多。
  - 題材層：watchlist 內 AI / 電子供應鏈標的是否多數維持強勢、量能、分類未惡化。
  - 執行層：即使市場或題材偏多，個股買點、RR、回測、冷卻與風控是否已成立。

  需要證據才可出現的詞句：

  - AI / 電子供應鏈仍偏多
  - 市場主線仍在
  - 題材仍可追蹤
  - 不代表看空產業
  - 市場偏多但買點未成立
  - 主線持倉保留
  - 電子供應鏈仍在主線內

  缺證據時必須降級為：

  - 市場證據不足，僅依策略分類追蹤
  - 題材未確認，等待價格與量能證據
  - 本輪技術條件未成立，不推論產業方向
  - 新倉：無有效進場

  ## 3. 建議需求 / TASK.md 重點

  本輪建議先定義為研究後的 major/minor 前置任務，不直接開發。

  核心需求：

  - 建立 market_theme_evidence 輸出契約，讓 formatter 每一句市場 / 題材文字都能追溯到來源、時間、樣本與等級。
  - 證據來源分四層：
      - internal watchlist：價格、量能、分類、strategy_evidence、snapshot。
      - market index：TAIEX、電子、科技 / 半導體相關指數。
      - flow：法人買賣超、外資持股或產業持股比。
      - external industry：TSMC / NVIDIA / SEMI / MOPS 類公開資料，只作題材背景，不作買點。
  - 證據等級：
      - confirmed：至少 internal + market/index 兩類同向，且資料新鮮。
      - weak：只有一類支持，或樣本少。
      - absent：無可用證據。
      - stale：有資料但超過 freshness 門檻。
  - 技術上建議需要 provider + cache + payload 欄位 + formatter contract；DB schema 應等 Owner 確認資料源與 retention 後再決定。
  - 嚴禁把 market/theme evidence 接入策略 decision；只能影響報文文字與證據區塊。

  ## 4. 驗收條件

  - 無 evidence 時，報文不得輸出 AI / 電子供應鏈仍偏多。
  - evidence stale 時，報文必須標示資料過期或降級，不得當 confirmed 寫。
  - 非 AI 題材 fixture 不得出現 AI 主線文案。
  - confirmed market/theme 仍不得讓 新倉 顯示可買，除非原策略買點成立。
  - 每個市場 / 題材句都能追溯到 source_type / source_name / as_of / evidence_level / reason。
  - Telegram 手機第一屏必須清楚分開：市場方向、題材追蹤、今日是否可買。
  - 不改 strategy decision、DB write path、watchlist、live Telegram、正式 backfill、live Supabase write。

  ## 5. 直接消費者與輸出契約

  直接消費者：

  - Owner 手機 Telegram 報文。
  - core/generator.py 或等價 formatter。
  - Telegram message list 產生器。
  - strategy evidence / snapshot 消費者。
  - formatter snapshot / regression tests。
  - 未來可能的 QA fixture 與 replay dry-run。

  建議輸出契約形狀：

  market_theme_evidence:
    as_of: "2026-05-28T13:30:00+08:00"
    level: confirmed | weak | absent | stale
    theme: "AI/electronics_supply_chain"
    market_direction: bullish | neutral | bearish | unknown
    execution_implication: "no_trade_signal"
    sources:
      - source_type: watchlist
        source_name: internal_snapshot
        as_of: "..."
        signal: "8/12 above 20MA, volume expansion 5/12"
      - source_type: index
        source_name: TWSE Electronics Index
        as_of: "..."
        signal: "above MA / relative strength positive"
    formatter_allowed_phrases:
      - "AI / 電子供應鏈仍偏多"
      - "新增買點未成立，先等回測"
    formatter_forbidden_phrases:
      - "今日可追主線買進"

  ## 6. 不確定性

  - TWSE / MOPS 官方資料可用性與 API 穩定性需要 Tech 驗證；PM 只能確認公開來源存在。
  - 外部新聞與公司財報能支持「題材背景」，但不能單獨支持「今日市場偏多」或「個股可買」。
  - AI / 電子供應鏈 taxonomy 需 Owner 確認：哪些 watchlist 股票屬 AI、半導體、伺服器、電源、面板、記憶體。
  - freshness 門檻需 Owner / Architect 確認；PM 建議價格/量能 T+0 或 T+1、法人 T+1、公司營收 45 日內、新聞 7 日內。
  - 若 Owner 要長期留存 evidence history，才需要 schema；否則第一階段可先用 cache / snapshot payload dry-run。

## QA Findings

• 我會只讀線上研究目錄裡的摘要文件，先確認目前任務狀態與既有研究脈絡；接著用公開來源反證「市場主線 / 題材證據鏈」需要哪些外部證據與降級規則。

• Ran pwd && rg --files -g '*.md'
  └ /Users/liveroom/stock-bot-agent-context/online_research
    DISPATCH.md
    … +3 lines (ctrl + t to view transcript)
    README.md
    CURRENT_STATE.md

• Explored
  └ Read DISPATCH.md, TASK.md, RESEARCH.md, CURRENT_STATE.md

◦ Searching the web

• Searched TWSE sector indices official Taiwan stock exchange electronics semiconductor index data ...

◦ Searching the web

• Searched Taiwan MOPS monthly revenue official company data API ...

• Searching the web

• Searched Taiwan export orders AI semiconductor official Ministry Economic Affairs 2026 ...

• Searching the web

• Searched site:moea.gov.tw export orders March 2026 AI Taiwan Ministry of Economic Affairs ...

◦ Searching the web

• Searched https://www.twse.com.tw/en/indices/indices/series.html

◦ Searching the web

• Searched MOPS Market Observation Post System monthly revenue official Taiwan listed companies ...

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

• # QA Findings: 市場主線 / 題材證據鏈研究

  範圍：只做公開資料研究與 QA 反證；未改產品代碼、未寫檔、未做 live Supabase write、正式 backfill 或 live Telegram。

  ## 1. 外部證據

  ┌──────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────┬─────────────────────┬───────────────────────────────────────────────────────────────────┐
  │ 證據                                                             │ 可支持什麼                                                │            證據性質 │ QA 限制                                                           │
  ├──────────────────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┼─────────────────────┼───────────────────────────────────────────────────────────────────┤
  │ TWSE 說明 TAIEX 是台灣證券市場主要 benchmark，並提供電子類等自編 │ 可作「大盤 / 電子類股方向」證據，不足以單獨證明 AI 題材。 │     延遲 / 歷史資料 │ 只能支持市場或類股，不支持個股可買。來源：TWSE Index Series       │
  │ 指數系列。                                                       │                                                           │                     │ (https://www.twse.com.tw/en/indices/indices/series.html)          │
  │ TAIFEX 說明電子類股指數涵蓋 TWSE 上市電子股，含半導體、光電、電  │ 可作「電子供應鏈」市場層證據。                            │     延遲 / 歷史資料 │ 電子類股 ≠ AI；不能把所有電子股都標成 AI 主線。來源：TAIFEX Mini  │
  │ 子零組件等，且是電子股表現的重要指標。                           │                                                           │                     │ Electronics Index Futures PDF (https://www.taifex.com.tw/file/    │
  │                                                                  │                                                           │                     │ taifex/event/enl/ZEF_future/file/ZEF%20QA_ENG.pdf)                │
  │ MOEA 2026-04 外銷訂單年增 48.1%，但同頁明確提醒因海外生產普遍，  │ 可作「產業需求背景」證據。                                │     延遲 / 官方統計 │ 不能直接推論台股今日偏多，也不能直接推論 watchlist 個股可買。來   │
  │ 訂單不一定都從台灣出口。                                         │                                                           │                     │ 源：MOEA Export Orders April 2026 (https://www.moea.gov.tw/Mns/   │
  │                                                                  │                                                           │                     │ english/news/News.aspx?kind=6&menu_id=176&news_id=122750)         │
  │ MOF 2026-04 出口年增 39.0%，附件含主要商品表。                   │ 可作總體出口動能背景。                                    │     延遲 / 官方統計 │ 月資料不適合支撐盤中報文的即時主線判斷。來源：MOF Exports and     │
  │                                                                  │                                                           │                     │ Imports April 2026 (https://www.mof.gov.tw/eng/singlehtml/        │
  │                                                                  │                                                           │                     │ f48d641f159a4866b1d31c0916fbcc71?                                 │
  │                                                                  │                                                           │                     │ cntId=6c6414a2b3fc4dd38f4a3271e213766d)                           │
  │ TSMC 2026-04 營收年增 17.5%，1-4 月累計年增 29.9%。              │ 可作半導體龍頭基本面背景。                                │     延遲 / 公司公告 │ TSMC 強不等於整個 AI / 電子供應鏈都偏多；也不等於今日可買。來源： │
  │                                                                  │                                                           │                     │ TSMC April 2026 Revenue (https://pr.tsmc.com/english/news/3305)   │
  │ TWSE 投資資訊頁列出個股日成交、外資每日交易摘要等官方市場資料入  │ 可作法人 / 量價證據來源候選。                             │ 延遲 / 官方市場資料 │ 法人買超是行為資料，不是買入建議；需搭配價格、量能、分類與時效。  │
  │ 口。                                                             │                                                           │                     │ 來源：TWSE Investing in Taiwan (https://www.twse.com.tw/en/focus/ │
  │                                                                  │                                                           │                     │ investing.html)                                                   │
  │ MOPS 是 TWSE / TPEx 等共同建立的公開資訊平台，提供上市櫃公司公開 │ 可作月營收、重大訊息、財報等公司層證據來源。              │     延遲 / 官方揭露 │ 需記錄揭露日期與資料期別，避免把舊基本面套到今日盤中。來源：TWSE  │
  │ 資訊。                                                           │                                                           │                     │ Market Insights on MOPS (https://wwwc.twse.com.tw/                │
  │                                                                  │                                                           │                     │ market_insights/en/detail/8a8216d6933460a4019348b1beda0086)       │
  └──────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────┴─────────────────────┴───────────────────────────────────────────────────────────────────┘

  ## 2. 產品上要證明什麼

  報文若要出現下列句子，必須有可追溯證據：

  - 市場偏多：至少需要大盤或加權指數、成交量、漲跌家數 / watchlist breadth 支持。
  - 電子供應鏈偏多：至少需要電子類指數、電子族群 watchlist 廣度、量能或法人流向支持。
  - AI 主線偏多：不能只靠單一新聞或單一 TSMC；至少要有 AI 標籤股票群的價格 / 量能 / 分類擴散，加上產業或龍頭證據。
  - 題材仍可追蹤：需要 watchlist 內該題材股票沒有全面破線 / 淘汰，且至少有弱證據顯示仍有相對強勢。
  - 不代表看空產業：需要明確區分「策略技術觸發失效」與「產業基本面轉空」，不能在沒有產業證據時反向宣告產業仍好。
  - 方向偏多但不可買：需要同時呈現兩條證據：市場 / 題材證據偏多，以及策略買點 absent。

  ## 3. 可能的策略盲點

  目前最大盲點是把「文案保護」誤當「證據鏈」。v20.0.12 能避免硬寫 AI，但若沒有 evidence payload，formatter 仍可能只靠股票名稱、分類或 fixture 推論主線。

  建議證據分層：

  - market_evidence：TAIEX、電子類指數、櫃買、成交量、漲跌家數。
  - theme_evidence：watchlist 主題標籤、同題材股票強弱、分類分布、量能擴散。
  - stock_evidence：個股價格、量能、策略分類、法人流向、月營收 / 重大訊息。
  - strategy_evidence：既有 snapshot、strategy_evidence、分類 audit、買點是否成立。
  - external_context：MOEA / MOF / MOPS / 公司公告 / 產業新聞，只能補背景，不能直接產生交易指令。

  證據等級建議：

  - confirmed：至少 2 類來源一致，例如 watchlist AI 群強勢 + 電子類指數偏多；且資料未過期。
  - weak：只有單一來源或樣本太小，只能寫「可追蹤」。
  - absent：沒有足夠證據，只能寫「市場證據不足，依策略分類等待」。
  - stale：資料超過時效，例如盤中量價過舊、月營收跨月未更新；報文必須降級。

  ## 4. 使用者誤讀風險

  - AI / 電子供應鏈仍偏多 很容易被 Owner 讀成「今天可以買 AI 股」。報文必須同屏寫 新倉：無有效進場 / 不追高 / 等回測。
  - 題材仍可追蹤 可能被讀成推薦清單。應避免和 可買、準備 放同一行。
  - 不代表看空產業 如果沒有產業證據，反而是無證據安撫。缺證據時應寫 本輪只是策略條件未通過，未判斷產業多空。
  - 單一龍頭如 TSMC 營收強，不能自動外推到整個 watchlist；否則非半導體或非 AI 場景會被錯貼 AI 標籤。
  - 法人買超、新聞熱度、出口數據都是背景或輔助，不應直接轉成 BUY / SELL。

  ## 5. 技術方案 QA 觀點

  需要 PM / Tech 先定義契約，QA 建議至少包含：

  - schema 或 payload 欄位：evidence_id、source_type、source_name、as_of、freshness、confidence、supports_claims、limitations。
  - cache / provider：TWSE / TPEx / MOPS / MOEA / MOF / company IR 應分 provider，記錄抓取時間與資料期別。
  - scheduler：盤中量價與每日法人可不同頻率；月營收 / 外銷訂單不可拿來支撐盤中即時語句。
  - formatter contract：每句主線文案都要能追溯到 evidence summary；沒有 evidence 時必須降級文案。
  - 不建議第一版直接改策略決策。先讓報文引用 evidence，不讓 evidence 影響買賣分數。

  ## 6. 建議下一步測試

  - 無證據測試：AI watchlist 存在但 provider 全部 absent，報文不得出現 AI 主線偏多。
  - 過期證據測試：外部資料 as_of 過舊，應降級為 市場證據過期，僅依策略分類等待。
  - 非 AI 場景測試：電子類指數偏多但 watchlist AI 標籤不足，不得硬寫 AI，只能寫電子或市場。
  - 方向偏多但不可買測試：confirmed theme evidence + strategy buy absent，summary 必須同屏顯示 不可買 / 不追高。
  - 反向證據測試：TSMC 或出口強，但 watchlist AI 群多數跌破 / 淘汰，報文只能寫 外部背景偏強，但本策略樣本未確認主線。
  - 手機閱讀測試：Owner 第一屏先看到的必須是「證據等級 + 行動限制」，不是先看到主線口號。
  - 來源衝突測試：官方統計偏強、價格 breadth 偏弱時，結論應是 weak / mixed，不得寫 confirmed。

  ## 7. 反向假設 / 反證方向

  反向假設：公開總體與龍頭資料顯示 AI / 半導體需求強，但 stock-bot 的 12 檔 watchlist 可能沒有同步擴散，甚至多數股票已進入等回測、等冷卻或淘汰。因此「產業背景強」不等於「本報文可寫 AI 主線偏多」。

  證據強度：中。官方資料可支持總體與龍頭背景，但目前沒有 live/private watchlist breadth、策略 snapshot、實際分類分布，所以不足以確認報文當日主線。結論必須標記：證據不足，需內部 watchlist 與 strategy_evidence 補足。

## Architect Conclusion

- Owner 判斷正確：`v20.0.12` 只是防止無證據硬寫主線的保護邏輯與文案橋接，不是真正的市場 / 題材證據鏈。
- 不應直接進入完整開發或 DB schema。證據鏈會碰資料來源、freshness、payload contract、formatter contract，屬於 major 前置設計；需先由 PM 產出開發任務卡。
- 第一階段建議做 `evidence payload dry-run`，不 live write：
  - 只產生 `market_theme_evidence` payload / cache，不改策略 decision。
  - 先用內部 watchlist / snapshot / strategy_evidence 建立最低可用證據。
  - 外部 TWSE / MOPS / MOEA / MOF / company IR 只作背景或第二階段 provider。
  - formatter 只能引用有 `source_type / source_name / as_of / level / limitations` 的證據。
- 證據等級先採四級：
  - `confirmed`：至少 2 類來源同向且未過期。
  - `weak`：單一來源或樣本小，只能寫可追蹤。
  - `absent`：不得寫主線偏多，只能寫證據不足。
  - `stale`：必須標示過期並降級。
- 報文硬邊界：
  - `AI / 電子供應鏈仍偏多` 必須有 AI 題材 watchlist 廣度 + 市場 / 類股 / 產業至少一類外部或內部佐證。
  - `不代表看空產業` 若無產業證據，不可寫成安撫句；應寫 `本輪只是策略條件未通過，未判斷產業多空`。
  - 市場 / 題材偏多不得推導成可買；必須同屏顯示買點是否成立。
- QA 將來必須反證：
  - 無證據不得硬寫 AI。
  - 過期資料不得當 confirmed。
  - 非 AI 場景不得誤貼 AI。
  - 產業背景強但 watchlist breadth 弱時只能是 weak / mixed。

## Next Action

- 進入 PM 任務卡階段，建立 `market_theme_evidence` dry-run / payload contract 任務。
- 暫不改 DB schema、策略 decision、live Telegram、live Supabase write、正式 backfill。
