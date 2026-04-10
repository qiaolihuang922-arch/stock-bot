import requests
import time
from config import OPENAI_API_KEY

AI_ENABLED = True
AI_DISABLED_UNTIL = 0  # 🔥 冷卻時間（新增）


# ================================
# 🔥 格式修正（強化版）
# ================================
def normalize_ai_output(text):

    if not text:
        return None

    text = text.strip()

    # 🔥 清理常見雜訊
    text = text.replace("：", "｜").replace(":", "｜")

    # 只保留第一行
    text = text.split("\n")[0]

    # ===== 嚴格開頭匹配 =====
    for prefix in ["BUY｜", "WAIT｜", "NO｜"]:
        if text.startswith(prefix):
            return text[:30]  # 限長（避免失控）

    return None


# ================================
# 🔥 fallback（強化對齊 strategy）
# ================================
def fallback_ai(decision):

    # ===== 觀望 =====
    if "觀望" in decision:

        if "市場" in decision:
            return "WAIT｜市場偏弱"

        if "未回踩" in decision:
            return "WAIT｜尚未回踩"

        if "追高" in decision:
            return "WAIT｜接近壓力"

        if "過熱" in decision:
            return "WAIT｜短線過熱"

        if "未到買點" in decision:
            return "WAIT｜尚未到點"

        if "報酬不足" in decision:
            return "WAIT｜報酬不足"

        if "風險過大" in decision:
            return "WAIT｜風險偏高"

        if "結構未確認" in decision:
            return "WAIT｜結構未穩"

        if "空間不足" in decision:
            return "WAIT｜空間不足"

        if "弱勢" in decision:
            return "NO｜結構偏弱"

        return "WAIT｜策略觀望"

    # ===== 進場（語意標籤）=====
    if "進場🔥" in decision:
        return "BUY｜強勢結構"

    if "進場" in decision:
        return "BUY｜結構成立"

    if "試單" in decision:
        return "BUY｜轉強觀察"

    # ===== 風險 =====
    if "風險" in decision:
        return "NO｜風險偏高"

    return "WAIT｜訊號不足"


# ================================
# 🔥 AI分析（穩定版）
# ================================
def ai_analysis(
    name,
    price,
    change,
    ma5,
    ma20,
    volume,
    trend,
    decision,
    buy,
    stop,
    decision_type=None  # 🔥 新增（可選）
):

    global AI_ENABLED, AI_DISABLED_UNTIL

    # ===== 冷卻恢復 =====
    if not AI_ENABLED and time.time() > AI_DISABLED_UNTIL:
        AI_ENABLED = True

    prompt = f"""
你是交易分析助手，只能解釋策略，不可做決策。

⚠️ BUY / WAIT / NO 只是分類標籤
⚠️ 不代表交易建議，不可影響決策

股票：{name}
現價：{price}（{change}%）
MA5：{ma5} MA20：{ma20}
量能：{volume}
趨勢：{trend}

策略決策：
{decision}
"""

    # 👉 若有 decision_type，補充但不影響
    if decision_type:
        prompt += f"\n決策類型：{decision_type}"

    prompt += """

請輸出（只能選一種）：

BUY｜解釋原因（20字內）
WAIT｜解釋原因（20字內）
NO｜解釋原因（20字內）

⚠️禁止提供：
- 買點
- 停損
- 倉位
- 交易建議
"""

    # ===== fallback模式 =====
    if not AI_ENABLED:
        return fallback_ai(decision), False

    try:
        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4.1-mini",
                "input": prompt,
                "temperature": 0.2
            },
            timeout=10
        )

        # ===== 限流 =====
        if r.status_code == 429:
            AI_ENABLED = False
            AI_DISABLED_UNTIL = time.time() + 60  # 🔥 冷卻60秒
            return fallback_ai(decision), False

        if r.status_code != 200:
            return fallback_ai(decision), False

        data = r.json()

        # ===== 🔥 多層解析 =====
        try:
            # 新格式
            if "output" in data:
                for item in data["output"]:
                    if "content" in item:
                        for c in item["content"]:
                            if "text" in c:
                                text = normalize_ai_output(c["text"])
                                if text:
                                    return text, True

            # 舊格式
            if "output_text" in data:
                text = normalize_ai_output(data["output_text"])
                if text:
                    return text, True

        except Exception as e:
            print("AI parse error:", e)

    except Exception as e:
        print("AI request error:", e)

    return fallback_ai(decision), False