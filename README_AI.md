# 🔥 AI交易系統（不可破壞架構｜FINAL v3）

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
- Supabase 寫入  

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

- 收集 RAW（pending）  
- 轉為 CLEAN（closed）  
- 作為未來訓練資料  

---

### 🔥 防污染規則（強制）

RAW（pending） → CLEAN（closed） → TRAIN  

---

### ❌ 禁止：

- RAW 影響 strategy  
- RAW 即時訓練  

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

工具函數  

---

## 📄 main.py

程式入口  

---

## 📄 app.py

部署入口  

---

## 📄 config.py

設定檔  

---

## 📄 render.yaml

部署設定  

---

## 📄 requirements.txt

套件依賴  

---

# 📦 三、資料層（唯一來源｜Supabase）

## 🚫 已移除

- data/  
- trades.json  
- raw_trades.json  
- clean_trades.json  

---

## ✅ 唯一資料來源

Supabase → trades  

---

## ❌ 嚴禁：

- 本地 JSON  
- 第二資料源  
- 雙寫入  

---

# 🧱 四、資料表結構（不可變更）

## Table：trades

---

### 🔑 基本欄位

- id → bigint（PK）  
- created_at → timestamp  

---

### 📅 時間（核心）

- trade_date → date  

trade_date = 交易判斷時間
created_at = 系統時間

---

### 📈 決策資料

- stock → text  
- decision → text  
- price → numeric  
- buy → numeric  
- stop → numeric  

---

### 📊 特徵資料

- ma5 → numeric  
- ma20 → numeric  
- volume → numeric  
- trend → text  

---

### 🧠 上下文

- data → jsonb  

---

### 📉 結果

- result → text  
- price_after → numeric  

---

### 🔥 狀態（核心）

- status → text  

pending → 未結算
closed → 可用資料
invalid → 無效

---

### 📌 來源

- source → text  
live / paper / manual

---

# 🔄 五、資料流（不可違反）

strategy → learning → Supabase  

---

### 🔒 規則：

- learning 只記錄  
- 不可回寫  
- 不可干預  

---

# 🚨 六、資料使用規範

## ❌ 禁止：

- 使用 pending  
- 使用未結算  

---

## ✅ 必須：

WHERE status = 'closed'

---

# 🧠 七、防污染機制

## 1️⃣ 防重複

stock + trade_date 唯一  

---

## 2️⃣ 連續虧損停止

≥3 → 停止記錄  

---

## 3️⃣ JSON限制

data 不可包含未來資訊  

---

# 🚫 八、禁止修改清單（紅線）

1. 多 decision  
2. AI 影響交易  
3. score 取代 strategy  
4. generator 做決策  
5. 移除停損  
6. 移除風控  
7. 拆分 strategy  
8. 多決策來源  
9. learning 影響 strategy  
10. 使用 pending  
11. 本地資料庫  

---

# 🧠 九、AI修改前必讀

- 是否改 strategy  
- 是否新增 decision  
- 是否影響風控  
- 是否讓 learning 影響決策  

👉 任一為是 → 禁止  

---

# 🔥 十、核心總結

strategy 決定交易  
AI 不得干預  
generator 不得決策  
風控不可動  
learning 完全隔離  
資料只來自 Supabase  

---

# 🚀 十一、最終原則

AI只能強化系統  
不能改變系統  





