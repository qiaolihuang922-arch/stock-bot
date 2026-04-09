# 🔥 AI交易系統（不可破壞架構｜FINAL v2）

本文件為本專案最高規範  
所有 AI / 人工修改 必須遵守  

違反本文件 = 錯誤修改  

---

# 🧠 一、核心原則（最高優先）

## 1️⃣ 統一決策（唯一來源）

所有交易決策 **只能來自 strategy()**

唯一輸出：

- decision  
- buy  
- stop  
- position  

---

### ❌ 嚴禁：

- 第二套 decision  
- AI 覆蓋 decision  
- score 決定買賣  
- generator 自行判斷進出場  
- learning / training 影響即時決策  

---

## 2️⃣ 決策優先級（不可違反）

strategy > 風控 > 時間 > score > AI  

---

### 🔒 補充（強制）

learning / training 不在決策鏈內  

---

## 3️⃣ 資料流（不可逆）

stock_api → analysis → ai → generator → notifier  

---

### 🔒 規則：

- 不可逆流  
- 不可回寫 decision  
- 不可修改上游結果  

---

## 4️⃣ AI 角色（嚴格限制）

AI只允許：

- 解釋（WHY）  
- 輔助判斷  
- 輸出文字  

---

### ❌ AI禁止：

- 改 decision  
- 改 buy  
- 改 stop  
- 改 position  
- 建立交易邏輯  

---

AI = 語言層，不是決策層  

---

## 5️⃣ 時間權重（市場節奏）

時間只影響：

- global_decision()  
- score_stock()  

---

### ❌ 禁止：

- 影響 strategy()  
- 影響個股 decision  

---

## 6️⃣ 風險優先（強制）

必須存在：

- stop < buy  
- 最大風險 ≤ 8%  
- RR ≥ 1.2  

---

### ❌ 嚴禁：

- 移除停損  
- 放寬風控  
- 忽略 RR  

---

# 📦 二、模組職責（不可混用）

---

## 📁 services/analysis.py（🔥唯一決策核心）

負責：

- volume_model()  
- trend_model()  
- support_resistance()  
- strategy()  

---

### ⚠️ 規則：

- strategy = 唯一決策來源  
- 不可被覆蓋  
- 不可拆分決策  
- 不可依賴 AI / score / time / learning  

---

## 📁 services/ai.py（AI輔助）

負責：

- ai_analysis()  
- fallback_ai()  

---

### ⚠️ 規則：

- 只輸出 BUY / WAIT / NO  
- 不可影響交易結果  
- 不可控制倉位  
- 不可計算買點  

---

## 📁 services/learning.py（🔥資料收集層｜完全隔離）

負責：

- record_trade()  
- update_trade_result()  
- 資料儲存  

---

### 🔒 核心定位

learning = 離線系統  
learning ≠ 決策系統  

---

### ❌ 嚴禁：

- 影響 strategy  
- 影響 decision  
- 影響 buy / stop / position  
- 即時訓練模型  
- 回寫任何決策模組  

---

### ✅ 只允許：

- 收集 RAW 資料  
- 記錄結果（win / loss）  
- 產生 CLEAN 資料  

---

### 🔥 防污染規則（強制）

RAW → CLEAN →（未來）→ TRAIN  

---

### ❌ 禁止：

RAW → 直接影響 strategy  
RAW → 即時訓練  

---

## 📁 services/stock_api.py（資料層）

負責：

- 市場數據  

---

### ⚠️ 規則：

- 不可分析  
- 不可決策  

---

## 📁 services/notifier.py（輸出層）

負責：

- 發送訊息  

---

### ⚠️ 規則：

- 不可改邏輯  
- 不可參與決策  

---

## 📁 core/generator.py（🔥整合中樞）

負責：

- 呼叫 strategy  
- 呼叫 AI  
- 輸出訊息  
- 全局判斷  

包含：

- global_decision()  
- score_stock()  
- 預備買點  
- 最佳標的  

---

### ⚠️ 核心限制：

❌ 不可：

- 做交易決策  
- 覆蓋 strategy  
- 修改 buy / stop  

---

### ✅ 只能：

- 整理  
- 排序  
- 顯示  

---

## 📁 core/utils.py

- 工具函數  

---

## 📄 main.py

- 程式入口  

---

## 📄 app.py

- 部署入口  

---

## 📄 config.py

- 設定檔  

---

## 📄 render.yaml

- 部署設定  

---

## 📄 requirements.txt

- 套件依賴  

---

# 📂 三、資料結構（強制）

data/

- trades.json（舊資料｜不可用於訓練）  
- raw_trades.json（原始資料）  
- clean_trades.json（訓練資料）  

---

### 🔒 定義：

- raw → 未驗證  
- clean → 已驗證  

---

### ❌ 嚴禁：

- raw 作為策略依據  
- raw 直接進模型  
- trades.json 作為訓練資料  

---

# 🔄 四、系統流程（不可更改）

stock_api → analysis(strategy) → ai → generator → notifier  

---

# 🧠 五、Learning 流（完全獨立）

record_trade → raw_data  
update_result → clean_data  

---

### 🔒 永久限制：

learning 不得進入主流程  
learning 不得影響即時決策  

---

# 🔥 六、決策模型（strategy 必備）

必須同時包含：

- 趨勢（MA / 結構）  
- 動能  
- 量能  
- 位置  
- 風控  

---

# 🔥 七、全局決策（市場層）

輸出：

- 🔴 禁止交易  
- 🟡 試單  
- 🟢 可進場  

---

# 🔥 八、評分系統（僅排序）

用途：

👉 選「最佳標的」

---

### ❌ 禁止：

- score 決定買賣  
- score 覆蓋 decision  

---

# 🚫 九、禁止修改清單（紅線）

1. 多一個 decision  
2. AI 影響交易結果  
3. score 取代 strategy  
4. generator 做決策  
5. 移除停損  
6. 移除風控  
7. 拆分 strategy  
8. 多決策來源  
9. learning 影響 strategy  
10. raw_data 進模型  
11. 使用 trades.json 作為訓練  

---

# 🧠 十、AI修改前必讀（強制）

AI在修改任何程式碼前，必須確認：

- 是否改動 strategy？  
- 是否新增 decision？  
- 是否影響風控？  
- 是否破壞單一決策？  
- 是否讓 learning 影響決策？  

👉 任一為是 → 禁止修改  

---

# 🔥 十一、核心總結（最重要）

strategy 決定交易  
AI 不得干預  
generator 不得決策  
風控不可動  
learning 不得污染  

---

# 🚀 十二、最終原則

AI只能強化系統  
不能改變系統  