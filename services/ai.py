import requests
import time
from config import OPENAI_API_KEY

AI_ENABLED = True
AI_DISABLED_UNTIL = 0


# ================================
# 🔥 輸出標準化（v6）
# ================================
def normalize_ai_output(text):

    if not text:
        return None

    text = text.strip()

    # 只取第一行
    text = text.split("\n")[0].strip()

    # 避免過長
    return text[:40]


# ================================
# 🔥 fallback（完全對齊 v6）
# ================================
def fallback_ai(decision, decision_type):

    # ===== BUY =====
    if decision == "BUY":
        if decision_type == "breakout":
            reason = "突破成立，動能偏強"
        elif decision_type == "pullback":
            reason = "回踩支撐，風險較低"
        else:
            reason = "結構成立"

    # ===== NO_TRADE =====
    elif decision == "NO_TRADE":
        reason = "結構不佳或風險過高"

    # ===== WAIT =====
    else:
        reason = "尚未出現明確進場訊號"

    return {
        "decision": decision,
        "reason": reason
    }


# ================================
# 🔥 AI分析（v6最終版）
# ================================
def ai_analysis(
    name,
    decision,
    decision_type,
    price,
    change,
    risk,
    rr
):

    global AI_ENABLED, AI_DISABLED_UNTIL

    # ===== 冷卻恢復 =====
    if not AI_ENABLED and time.time() > AI_DISABLED_UNTIL:
        AI_ENABLED = True

    # ===== fallback模式 =====
    if not AI_ENABLED:
        return fallback_ai(decision, decision_type)

    # ===== prompt（嚴格限制🔥）=====
    prompt = f"""
你是交易解釋器，不可改策略。

股票:{name}
價格:{price}（{change}%）
風險:{round(risk,3)}
RR:{rr}

決策:{decision}
類型:{decision_type}

請用一句話說明原因（20字內）
禁止提供建議
"""

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
                "temperature": 0.1
            },
            timeout=8
        )

        # ===== 限流 =====
        if r.status_code == 429:
            AI_ENABLED = False
            AI_DISABLED_UNTIL = time.time() + 60
            return fallback_ai(decision, decision_type)

        if r.status_code != 200:
            return fallback_ai(decision, decision_type)

        data = r.json()

        # ===== 解析 =====
        text = None

        try:
            if "output_text" in data:
                text = data["output_text"]

            elif "output" in data:
                for item in data["output"]:
                    if "content" in item:
                        for c in item["content"]:
                            if "text" in c:
                                text = c["text"]
                                break

        except Exception as e:
            print("AI parse error:", e)

        text = normalize_ai_output(text)

        if text:
            return {
                "decision": decision,
                "reason": text
            }

    except Exception as e:
        print("AI request error:", e)

    return fallback_ai(decision, decision_type)