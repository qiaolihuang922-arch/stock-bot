🔥 AI交易系統守則（FINAL v8｜完整最終版）

本文件 = 系統唯一行為來源  
所有模組必須遵守  
違反 = 系統錯誤  

--------------------------------------------------

一、核心原則（不可違反）

唯一決策來源：
strategy()

輸出：
- decision
- decision_type
- buy
- stop
- position
- risk
- rr

decision：
- BUY = 已觸發（允許進場）
- WAIT = 未觸發（不可進場）
- NO_TRADE = 禁止交易

decision_type：
- breakout
- pullback
- none

禁止：
- 多 decision
- AI 參與決策
- learning 影響 decision
- generator 修改 decision

--------------------------------------------------

二、決策流程（v8）

市場 → 結構 → 趨勢 → 量能 → 事件 → Edge → 風控 → 倉位 → decision

任一階段不成立 → 停止流程

--------------------------------------------------

三、市場系統（強制）

market_signal：
- STRONG
- NORMAL
- CHOPPY
- WEAK

規則：
- WEAK → 禁止 BUY
- CHOPPY → position ≤ 0.5
- STRONG → breakout 優先

核心原則：
市場錯 → 全部錯

--------------------------------------------------

四、事件系統（嚴格）

event 必須由 analysis 明確輸出  
不得由 decision 反推  

breakout_event（全部成立）：
- price > resistance
- 收盤站上
- volume > avg5 × 1.5

pullback_event（全部成立）：
- 回踩支撐
- 未破支撐
- 出現反彈

沒有 event → 禁止 BUY

--------------------------------------------------

五、Edge系統（核心）

edge 必須拆解，不可簡化  

breakout_edge：
- consolidation_ok
- not_high_zone
- no_fake_breakout

pullback_edge：
- ma20_up
- first_pullback
- structure_hold

未通過 → WAIT

--------------------------------------------------

六、風控（強制）

- stop < buy
- risk ≤ 0.08

RR：
- breakout ≥ 1.8
- pullback ≥ 1.5

不成立 → NO_TRADE

--------------------------------------------------

七、倉位系統

risk ≤ 0.03 → 1.0  
risk ≤ 0.05 → 0.7  
risk ≤ 0.08 → 0.5  
> 0.08 → NO_TRADE  

市場調整：
CHOPPY → ×0.7  
WEAK → 0  

--------------------------------------------------

八、條件引擎（核心）

用途：
拆解條件狀態

不可：
- 改 decision
- 新增邏輯
- 反推 decision

輸出：

{
 "market": True/False,
 "structure": True/False,
 "trend": True/False,
 "volume": True/False,
 "event": True/False,
 "edge": True/False,
 "risk": True/False,
 "rr": True/False
}

條件來源必須來自 analysis：

- event_breakout
- event_pullback
- edge_consolidation
- edge_fake_breakout
- edge_first_pullback
- edge_ma20_trend

--------------------------------------------------

九、條件顯示規則

BUY：
顯示 OK 條件

WAIT：
顯示 缺少條件

NO_TRADE：
只顯示致命條件

優先順序：
market → trend → volume

--------------------------------------------------

十、評分系統

範圍：
0 ~ 100

來源：
- market
- trend
- structure
- momentum
- rr

禁止影響 decision

--------------------------------------------------

十一、AI系統

只做解釋

輸出：
- decision
- reason（單一句）

禁止：
- 建議
- 價格
- 改 decision

--------------------------------------------------

十二、learning系統

資料來源：
Supabase（trades）

必須紀錄：
- buy
- stop
- rr
- decision_type
- market
- structure
- momentum
- edge

禁止：
- 未來資料
- pending 影響策略

--------------------------------------------------

十三、資料流（不可逆）

stock_api → analysis → strategy → condition_engine → ai → generator → learning

禁止逆流：
- AI → strategy
- learning → strategy
- generator → strategy

--------------------------------------------------

十四、專案結構

project/

 main.py
 app.py
 config.py
 render.yaml
 requirements.txt

 core/
  generator.py
  condition_engine.py
  utils.py

 services/
  analysis.py
  ai.py
  learning.py
  notifier.py
  stock_api.py

--------------------------------------------------

十五、檔案職責

analysis.py：
唯一決策來源

condition_engine.py：
條件拆解

generator.py：
流程控制

ai.py：
解釋

learning.py：
紀錄

stock_api.py：
資料來源

--------------------------------------------------

十六、顯示層

BUY：
顯示進場 / 停損 / RR

WAIT：
顯示缺什麼條件

NO_TRADE：
顯示禁止原因

--------------------------------------------------

十七、排序

BUY > WAIT > NO_TRADE

BUY排序：
1 breakout
2 RR
3 risk

--------------------------------------------------

十八、訊號冷卻（強制）

同一標的：

BUY 後 3 日內禁止再次 BUY

未平倉前：
禁止重複 BUY

--------------------------------------------------

十九、訊號失效（強制）

WAIT 狀態下：

若出現：

- 跌破支撐
- trend 轉 DOWN
- volume 出現 DISTRIBUTION

→ 強制 NO_TRADE

--------------------------------------------------

二十、總風險控制（強制）

總持倉風險：

sum(risk × position) ≤ 0.06

超過 → 禁止新增 BUY

--------------------------------------------------

二十一、結果驗證（強制）

每次 strategy 輸出必須檢查：

- BUY 必須有 buy / stop / rr
- stop < buy
- NO_TRADE 不得有 buy

否則 → 系統錯誤

--------------------------------------------------

二十二、紅線（最嚴格）

- 無停損
- RR不達標
- 無市場
- 無事件
- AI決策
- 修改 decision

--------------------------------------------------

二十三、最終原則

沒有市場 → 不交易  
沒有事件 → 不交易  
沒有Edge → 不交易  
沒有風控 → 不允許存在  

decision = 唯一真相  
AI = 只能解釋  

--------------------------------------------------

🔥 v8本質：

不是找股票  
是只做「最容易贏的交易」