🔥 AI交易系統守則（FINAL v8.5｜精簡可維護版）

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

二、決策流程（不可變）

市場 → 結構 → 趨勢 → 量能 → 事件 → Edge → 風控 → 倉位 → decision

任一階段不成立 → 停止流程

--------------------------------------------------

三、交易成立條件（核心）

必須同時成立：

1. 市場正確（market ≠ WEAK）
2. 有事件（event_breakout 或 event_pullback）
3. 有Edge（對應條件成立）
4. 風控合格（risk / RR）

缺一不可 → 不交易

--------------------------------------------------

四、風控（強制）

risk = (buy - stop) / buy

條件：
- stop < buy
- risk ≤ 0.08

RR：
- breakout ≥ 1.8
- pullback ≥ 1.5

不成立 → NO_TRADE

--------------------------------------------------

五、倉位系統

risk ≤ 0.03 → 1.0
risk ≤ 0.05 → 0.7
risk ≤ 0.08 → 0.5
> 0.08 → NO_TRADE

市場調整：
- CHOPPY → ×0.7
- WEAK → 0

--------------------------------------------------

六、條件引擎（只做映射）

用途：
將 strategy 結果轉為條件狀態

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

禁止：
- 推論 decision
- 新增策略
- 修改 decision

--------------------------------------------------

七、顯示層（給人用）

BUY：
- 顯示：進場 / 停損 / RR
- 顯示：是否接近進場點

WAIT：
- 顯示：缺少條件（轉人話）
- 最多顯示 3 個

NO_TRADE：
- 顯示：禁止原因（轉人話）

禁止：
- 顯示層自行做決策
- 使用策略邏輯判斷

--------------------------------------------------

八、資料流（不可逆）

stock_api → analysis → strategy → condition_engine → generator → learning

禁止逆流：
- AI → strategy
- learning → strategy
- generator → strategy

--------------------------------------------------

九、專案結構（固定）

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

十、檔案職責（重點）

analysis.py：
- 計算市場 / 趨勢 / 結構 / 量能
- 判斷 event（breakout / pullback）
- 拆解 edge
- 計算 risk / RR / position
→ 輸出 strategy 結果

condition_engine.py：
- 將結果轉為條件 True/False
→ 用於顯示

generator.py：
- 顯示結果（人話）
→ 不參與決策

learning.py：
- 記錄交易資料（Supabase）
→ 不影響策略

stock_api.py：
- 提供價格 / MA / 量能

ai.py：
- 解釋 decision（單一句）
→ 不參與決策

main.py / app.py：
- 控制流程與排程

--------------------------------------------------

十一、結果驗證（強制）

每次輸出必須符合：

- BUY 必須有 buy / stop / rr
- stop < buy
- NO_TRADE 不得有 buy

否則 → 系統錯誤

--------------------------------------------------

十二、訊號冷卻

同一標的：

- BUY 後 3 日禁止再次 BUY
- 未平倉前禁止再次 BUY

--------------------------------------------------

十三、訊號失效

WAIT 狀態下：

若出現：
- 跌破支撐
- trend = DOWN
- volume = DISTRIBUTION

→ 強制 NO_TRADE

--------------------------------------------------

十四、總風險控制

sum(risk × position) ≤ 0.06

超過 → 禁止新增 BUY

--------------------------------------------------

十五、紅線（最嚴格）

- 無停損
- RR不達標
- 無市場
- 無事件
- 無Edge
- AI決策
- 修改 decision

--------------------------------------------------

十六、最終原則

沒有市場 → 不交易
沒有事件 → 不交易
沒有Edge → 不交易
沒有風控 → 不允許存在

--------------------------------------------------

🔥 v8.5 本質：

不是找股票  
是只做「已經站在你這邊的交易」