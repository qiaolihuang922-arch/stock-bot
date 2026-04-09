def ai_analysis(name, price, change, ma5, ma20, volume, trend, decision, buy, stop):

    prompt = f"""
你是頂級短線交易員，請用專業角度快速判斷：

【股票】{name}
【現價】{price}
【漲跌】{change}%
【MA5】{ma5}
【MA20】{ma20}
【量能】{volume}
【趨勢】{trend}
【策略】{decision}
【買點】{buy}
【停損】{stop}

請嚴格輸出（不要廢話）：

1️⃣ 是否該進場（YES / NO / WAIT）
2️⃣ 原因（一句）
3️⃣ 操作（怎麼做）

限制：50字內
"""

    try:
        r = requests.post(
            "https://api.openai.com/v1/responses",  # ✅ 新API（關鍵修復）
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4.1-mini",
                "input": prompt,
                "temperature": 0.3
            },
            timeout=12
        )

        # ===== DEBUG（你可以保留）=====
        print("AI STATUS:", r.status_code)
        print("AI RAW:", r.text[:200])

        if r.status_code == 200:
            data = r.json()

            # ✅ 新API解析方式（重點）
            if "output" in data and len(data["output"]) > 0:
                content = data["output"][0]["content"]

                if content and "text" in content[0]:
                    text = content[0]["text"]

                    # ✅ 真AI判斷（防空、防亂碼、防假回）
                    if text and len(text.strip()) > 10 and "ERROR" not in text:
                        return text.strip(), True

    except Exception as e:
        print("AI error:", e)

    # ===== 🔥 fallback（保留你原本 + 強化）=====
    if "主升" in trend and "進場" in decision:
        return "YES｜主升延續｜小量追", False

    if "突破" in decision:
        return "WAIT｜假突破風險｜等回踩", False

    if "回檔" in decision:
        return "YES｜支撐區｜分批布局", False

    if "轉強" in decision:
        return "YES｜轉多初期｜試單", False

    if "觀望" in decision:
        return "NO｜位置差｜等待", False

    return "WAIT｜訊號不明｜觀察", False