# 🔥 AI交易系統守則（FINAL v7｜實戰盈利版）

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

# 🧠 二、決策流程（v7升級）

市場環境 → 結構 → 趨勢 → 量能 → 事件 → Edge篩選 → 風控 → 倉位 → decision  

---

# 🧠 三、市場過濾器（強制）

## market_signal

- STRONG  
- NORMAL  
- WEAK  
- CHOPPY  

---

## 規則（強制）

if market_signal == "WEAK":
    禁止 breakout

if market_signal == "CHOPPY":
    position <= 0.5

if market_signal == "STRONG":
    breakout 優先
    可提高倉位

👉 沒有 market_signal = 禁止 BUY  

---

# 🧠 四、事件定義（強制）

## breakout

- 突破壓力位  
- 收盤確認  
- 成交量放大  

---

## pullback

- 上升趨勢成立  
- 回踩支撐  
- 未跌破結構  

---

👉 沒有事件 = 禁止 BUY  

---

# 🧠 五、Edge 篩選（v7核心）

## breakout（全部成立）

- 突破壓力位  
- 收盤站上  
- 成交量 > 5日均量 × 1.5  
- 盤整 ≥ 3天  
- 非高檔（距離前高 < 5% 禁止）

---

## pullback（全部成立）

- MA20 上升  
- 價格在 MA20 上方  
- 第一次回踩  
- 未跌破前低  

---

👉 未通過 Edge = WAIT  

---

# 🧠 六、風控（強制）

必須全部成立：

- stop < buy  
- risk ≤ 0.08  

---

## RR 規則（v7升級）

if decision_type == "breakout":
    RR ≥ 1.8

if decision_type == "pullback":
    RR ≥ 1.5

---

👉 任一不成立 → NO_TRADE  

---

# 🧠 七、倉位系統（v7新增）

## 基於 risk

if risk <= 0.03:
    position = 1.0

elif risk <= 0.05:
    position = 0.7

elif risk <= 0.08:
    position = 0.5

else:
    NO_TRADE

---

## 市場調整（強制）

if market_signal == "CHOPPY":
    position *= 0.7

if market_signal == "WEAK":
    position = 0

---

# 🧠 八、優先級（不變）

strategy > 風控 > 市場 > 結構 > AI  

---

# 🧠 九、資料流（單向）

stock_api → analysis → strategy → ai → generator → learning  

---

❌ 禁止逆流：

- AI → strategy  
- learning → strategy  
- generator → strategy  

---

# 📦 十、專案結構（不變）

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

# 📄 十一、檔案職責（強制）

## main.py
- 呼叫 generator
- 輸出結果

❌ 禁止邏輯  

---

## app.py
- API入口

❌ 禁止交易邏輯  

---

## config.py
- API KEY
- DB設定

---

## render.yaml
- 排程  

---

## requirements.txt
- requests
- flask
- pytz
- supabase  

---

# 🧠 十二、services 層

## stock_api.py
👉 純資料

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

## strategy()（唯一決策）

輸出：

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

---

## ai.py

👉 解釋 decision

輸出：

- decision  
- reason（單一句）

---

## learning.py

👉 記錄交易

- record_trade  
- update_trade_result  

---

fail-safe：

DB錯誤不可影響主流程  

---

## notifier.py

👉 發送訊息  

---

# 🧠 十三、core 層

## generator.py

流程：

1. 抓資料  
2. strategy  
3. AI  
4. learning  
5. 輸出  

---

❌ 禁止修改 decision  

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

# 🧠 十四、顯示層

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

# 🧠 十五、排序規則

BUY > WAIT > NO_TRADE  

BUY內：

1. breakout優先  
2. RR高優先  
3. risk低優先  

---

# 🧠 十六、learning 限制

資料來源：

Supabase（trades）

---

❌ 禁止：

- pending  
- 未來資料  

---

## 唯一鍵

(stock, trade_date)

---

# 🚫 十七、紅線

1. AI 決策  
2. 多 decision  
3. 無停損  
4. RR 不達標  
5. learning 干預  
6. generator 改 decision  
7. 無市場判斷  

---

# 🧠 十八、修改檢查

修改前必問：

- 是否影響 strategy？  
- 是否改 decision？  
- 是否破壞風控？  

👉 任一 YES → 禁止  

---

# 🚀 十九、最終原則

沒有事件 → 不交易  
沒有 Edge → 不交易  
沒有風控 → 不允許存在  
沒有市場 → 不進場  

decision = 唯一真相  
AI = 只能解釋  

---

# 🔥 v7 本質

不是找股票  
是只做「最容易贏的交易