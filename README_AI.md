# 🔥 AI交易系統守則（FINAL v4｜精簡完整版）

本文件為最高規範  
任何修改必須遵守  

---

# 🧠 一、核心原則

## 1️⃣ 唯一決策

所有交易只能來自：

👉 strategy()

輸出：
- decision  
- buy  
- stop  
- position  

---

❌ 禁止：

- 第二 decision  
- AI 改 decision  
- score 決策  
- generator 做判斷  

---

## 2️⃣ 決策優先級

strategy > 風控 > 時間 > score > AI  

---

## 3️⃣ AI定位

AI = 解釋  

❌ 不可：

- 決策  
- 改買點  
- 改停損  

👉 BUY / WAIT / NO  
只是「文字分類」

---

## 4️⃣ 資料流（不可逆）

stock_api → analysis → ai → generator → learning  

---

## 5️⃣ 風控（強制）

- stop < buy  
- risk ≤ 8%  
- RR ≥ 1.2  

---

# 📦 二、所有檔案職責（🔥完整）

---

## 📁 services/analysis.py

👉 唯一決策核心  

包含：
- volume_model  
- trend_model  
- support_resistance  
- strategy  

❌ 禁止依賴：
AI / score / learning  

---

## 📁 services/ai.py

👉 解釋用  

輸出：
- BUY / WAIT / NO  

❌ 禁止影響交易  

---

## 📁 services/learning.py

👉 記錄資料  

只做：
- record_trade  
- update_trade_result  

❌ 禁止：
- 影響 decision  
- 回寫策略  

---

## 📁 services/stock_api.py

👉 只提供市場資料  

❌ 禁止：
- 分析  
- 判斷  

---

## 📁 services/notifier.py

👉 發送訊息  

❌ 禁止參與任何邏輯  

---

## 📁 core/generator.py

👉 系統中樞  

只做：
- 呼叫 strategy  
- 整理輸出  
- 呼叫 AI  
- 呼叫 learning  

---

❌ 禁止：

- 改 decision  
- 改 buy / stop  
- 做交易判斷  

---

## 📁 core/utils.py

👉 工具函數  

---

## 📄 main.py

👉 程式入口  

只做：

- 呼叫 generator  
- 輸出結果  

❌ 禁止：
- 寫策略  
- 寫邏輯  

---

## 📄 app.py

👉 部署入口（API / Web）  

只做：

- 接收請求  
- 呼叫 main / generator  

❌ 禁止：
- 交易邏輯  

---

## 📄 config.py

👉 設定  

包含：

- API KEY  
- DB  
- 參數  

❌ 禁止寫邏輯  

---

## 📄 render.yaml

👉 部署設定  

---

## 📄 requirements.txt

👉 套件列表  

---

# 📦 三、資料來源

唯一：

👉 Supabase（trades）

---

❌ 禁止：

- JSON  
- 本地資料  
- 雙資料源  

---

# 📊 四、資料規則

狀態：

- pending  
- closed  
- invalid  

---

## 使用

❌ 禁止：
使用 pending  

✅ 必須：
status = closed  

---

# 🧠 五、資料寫入

record_trade：

- buy > stop  
- price = buy  

---

update_trade_result：

只能：

- 停損  
- 停利  
- 結束  

---

❌ 禁止：

- 當日寫結果  
- 未來資料  

---

# 🧠 六、防污染

## 1️⃣ 唯一鍵

(stock, trade_date)

---

## 2️⃣ JSON限制

data 不可含：

- 未來價格  
- result  
- price_after  

---

## 3️⃣ learning隔離

❌ 不得影響 strategy  

---

# 🚫 七、紅線

禁止：

1. 多 decision  
2. AI 決策  
3. score 取代 strategy  
4. generator 決策  
5. 移除停損  
6. 放寬風控  
7. learning 影響策略  
8. 使用 pending  
9. 本地資料  

---

# 🧠 八、修改前檢查

任何修改必須確認：

- 是否影響 strategy  
- 是否影響風控  
- 是否新增 decision  

👉 有 → 禁止  

---

# 🔥 九、核心總結

strategy 決定一切  
AI 只負責說明  
generator 只負責整理  
learning 只負責記錄  

---

# 🚀 十、最終原則

👉 系統可以變強  
👉 但架構不能