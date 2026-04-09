# AI交易系統架構（不可破壞）

## 🔥 核心原則
1. 統一決策：所有買賣只由 strategy() 決定
2. AI只做輔助，不可影響 decision
3. 時間權重會影響全局，不影響個股 decision
4. 風險控制優先於報酬

## 📦 模組分工

### analysis.py
- 唯一決策核心
- 輸出：decision / buy / stop / position
- 不可被其他模組覆蓋

### ai.py
- 僅做解釋與驗證
- 不可改變決策

### generate.py
- 負責整合輸出
- 包含：
  - 時間權重
  - 全局判斷
  - 最佳標的選擇

## ⚠️ 禁止事項
- 不可新增第二套決策邏輯
- 不可讓AI覆蓋strategy
- 不可移除風控條件