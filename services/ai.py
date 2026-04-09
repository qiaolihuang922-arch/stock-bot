import requests
from config import OPENAI_API_KEY

def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop, resistance):

    if "觀望" in decision:
        base = "不建議進場"
    elif "主升" in decision:
        base = "可進場（主升）"
    else:
        base = "可進場"

    prompt = f"""
股票：{name}
現價：{price}
MA20：{ma20}
壓力：{resistance}
量能：{volume}
趨勢：{trend}
決策：{decision}
40字內
"""

    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4.1-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            },
            timeout=10
        )

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]

    except:
        pass

    return base