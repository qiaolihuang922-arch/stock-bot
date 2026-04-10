# 🔥 AI交易系統守則（FINAL v6｜完整實作規範）

本文件 = 系統唯一行為來源  
所有模組必須遵守  
違反 = 系統錯誤  

---

# 🧠 一、核心原則（不可違反）

## 1️⃣ 唯一決策

唯一來源：

strategy()

輸出：

- decision
- decision_type
- buy
- stop
- position
- risk
- rr

---

## decision 定義（強制）

- BUY        # 可進場（已觸發）
- WAIT       # 條件未到（可轉BUY）
- NO_TRADE   # 結構錯誤（禁止交易）

---

## decision_type（強制）

- breakout
- pullback
- none

---

❌ 禁止：

- 多 decision  
- AI 決策  
- learning 影響 decision  
- generator 修改 decision  

---

# 🧠 二、決策流程（不可逆）

市場 → 結構 → 趨勢 → 量能 → 事件 → 風控 → decision  

---

## 事件定義（強制）

### breakout
- 突破壓力位
- 成交量放大
- 收盤確認

### pullback
- 上升趨勢成立
- 回踩支撐
- 未跌破結構

👉 沒有事件 = 禁止 BUY  

---

# 🧠 三、風控（內建 strategy）

必須同時成立：

- stop < buy  
- risk ≤ 0.08  
- RR ≥ 1.2  

---

風控失敗：

→ 強制 NO_TRADE  

---

# 🧠 四、優先級

strategy > 風控 > 市場 > 結構 > AI  

---

# 🧠 五、資料流（單向）

stock_api → analysis → strategy → ai → generator → learning  

---

❌ 禁止逆流：

- AI → strategy  
- learning → strategy  
- generator → strategy  

---

# 📦 六、專案結構

project/

- main.py  
- app.py  
- config.py  
- render.yaml  
- requirements.txt  

core/  
- generator.py  
- utils.py  

services/  
- analysis.py  
- ai.py  
- learning.py  
- notifier.py  
- stock_api.py  

---

# 📄 七、檔案職責（強制）

## main.py
- 呼叫 generator
- 輸出結果

❌ 禁止任何邏輯  

---

## app.py
- API入口
- 呼叫 main / generator

❌ 禁止交易邏輯  

---

## config.py
- API KEY
- DB 設定
- flags

❌ 禁止寫邏輯  

---

## render.yaml
- 部署排程
- 定時觸發  

---

## requirements.txt
- requests
- flask
- pytz
- supabase  

---

# 🧠 八、services 層

## stock_api.py
👉 純資料提供

- get_twse
- get_yahoo
- get_realtime_price

❌ 禁止分析  

---

## analysis.py（核心）

包含：

- market_signal
- trend_signal
- volume_signal
- structure_ok
- breakout_event
- pullback_event
- risk_control
- strategy

---

### strategy() 輸出

- decision
- decision_type
- buy
- stop
- position
- risk
- rr

---

❌ 禁止：

- AI
- learning
- score  

---

## ai.py

👉 解釋 decision

輸出：

- decision
- reason（單一句）

❌ 禁止：

- 提供買點
- 提供停損
- 改 decision  

---

## learning.py

👉 記錄交易

- record_trade
- update_trade_result

---

規則：

- price = buy
- buy > stop
- status: pending → closed

---

### fail-safe（強制）

- DB錯誤不可影響主流程  

---

## notifier.py

👉 發送訊息

❌ 禁止決策  

---

# 🧠 九、core 層

## generator.py

流程：

1. 抓資料
2. 跑 strategy
3. 跑 AI
4. 記錄 learning
5. 組輸出

---

❌ 禁止：

- 改 decision
- 做判斷  

---

## 輸出格式（強制）

- name
- price
- decision
- decision_type
- reason
- structure
- event
- buy
- stop
- risk
- rr

---

## utils.py

👉 工具函數

❌ 禁止決策  

---

# 🧠 十、顯示層（交易員模式）

## BUY

【標的】🟢 BUY  
原因：xxx  

進場：xxx  
停損：xxx  

類型：breakout / pullback  
RR：x.x  

---

## WAIT

【標的】🟡 WAIT  
原因：xxx  

關鍵價位：xxx  
觸發條件：xxx  

---

## NO_TRADE

【標的】🔴 NO  
原因：xxx  

---

# 🧠 十一、排序規則

BUY > WAIT > NO_TRADE  

BUY內：

1. breakout優先  
2. RR高優先  
3. risk低優先  

---

# 🧠 十二、learning 限制

資料來源：

👉 Supabase（trades）

---

❌ 禁止：

- 使用 pending  
- 使用未來資料  

---

## 唯一鍵

(stock, trade_date)

---

## extra_data 禁止

- result  
- future_price  

---

# 🚫 十三、紅線

1. 多 decision  
2. AI 決策  
3. learning 影響策略  
4. generator 改 decision  
5. 無停損  
6. RR < 1.2  
7. 使用 pending  
8. 多資料源  

---

# 🧠 十四、修改檢查

修改前必問：

- 是否影響 strategy？
- 是否改 decision？
- 是否破壞風控？

👉 任一 YES → 禁止  

---

# 🚀 十五、最終原則

沒有事件 → 不交易  
沒有風控 → 不允許存在  
decision = 唯一真相  
AI = 只能解釋  

---

# 🔥 v6 本質

不是找股票  
是過濾交易