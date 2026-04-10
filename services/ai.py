import requests
import time
from config import OPENAI_API_KEY

AI_ENABLED = True
AI_DISABLED_UNTIL = 0


# ================================
# 🔥 輸出標準化（強化版）
# ================================
def normalize_ai_output(text):

    if not text:
        return None

    text = text.strip().upper()

    # 清理符號
    text = text.replace("：", "｜").replace(":", "｜")

    # 只取第一行
    text = text.split("\n")[0].strip()

    # 強制格式
    valid_prefix = ["BUY｜", "WAIT｜", "NO｜"]

    for p in valid_prefix:
        if text.startswith(p):
            return text[:30]

    return None


# ================================
# 🔥 fallback（完全對齊 strategy🔥）
# ================================
def fallback_ai(decision, decision_type=None):

    # ===== BUY =====
    if decision == "BUY":

        mapping = {
            "BREAKOUT": "BUY｜突破成立",
            "PULLBACK": "BUY｜回踩支撐",
        }

        return mapping.get(decision_type, "BUY｜結構成立")

    # ===== NO =====
    if decision == "NO":

        mapping = {
            "TREND_DOWN": "NO｜空頭趨勢",
            "DISTRIBUTION": "NO｜出貨訊號",
            "FAKE_BREAKOUT": "NO｜假突破",
            "RISK_TOO_HIGH": "NO｜風險過大",
            "RR_LOW": "NO｜報酬不足",
            "NO_SPACE": "NO｜空間不足",
        }

        return mapping.get(decision_type, "NO｜不符合條件")

    # ===== WAIT =====
    if decision == "WAIT":

        mapping = {
            "NO_VOLUME": "WAIT｜量能不足",
            "STRUCTURE_BAD": "WAIT｜結構不穩",
            "MARKET_WEAK": "WAIT｜市場偏弱",
            "NO_BREAKOUT": "WAIT｜未突破",
            "NO_SIGNAL": "WAIT｜無明確機會",
        }

        return mapping.get(decision_type, "WAIT｜觀望")

    return "WAIT｜觀望"


# ================================
# 🔥 AI分析（最終穩定版）
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
    decision_type=None
):

    global AI_ENABLED, AI_DISABLED_UNTIL

    # ===== 冷卻恢復 =====
    if not AI_ENABLED and time.time() > AI_DISABLED_UNTIL:
        AI_ENABLED = True

    # ===== prompt（極簡，避免失控）=====
    prompt = f"""
你是交易解釋器，不可改策略。

股票:{name}
價格:{price}({change}%)
趨勢:{trend}
量能:{volume}

決策:{decision}
類型:{decision_type}

輸出格式：
BUY｜原因
WAIT｜原因
NO｜原因

限制：
- 20字內
- 不可提供建議
"""

    # ===== fallback模式 =====
    if not AI_ENABLED:
        return fallback_ai(decision, decision_type), False

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
            return fallback_ai(decision, decision_type), False

        if r.status_code != 200:
            return fallback_ai(decision, decision_type), False

        data = r.json()

        # ===== 解析 =====
        try:
            if "output" in data:
                for item in data["output"]:
                    if "content" in item:
                        for c in item["content"]:
                            if "text" in c:
                                text = normalize_ai_output(c["text"])
                                if text:
                                    return text, True

            if "output_text" in data:
                text = normalize_ai_output(data["output_text"])
                if text:
                    return text, True

        except Exception as e:
            print("AI parse error:", e)

    except Exception as e:
        print("AI request error:", e)

    return fallback_ai(decision, decision_type), False