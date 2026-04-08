import requests
from datetime import datetime

TOKEN = "8714533132:AAGEAYs-Q-oZJDwwBwwuB0MPb27mqnDtzxs"
CHAT_ID = "7119676798"

def get_stock_report():
    today = datetime.now().strftime("%m/%d")

    msg = f"""【{today} AI股票早報】

📌 緯創
→ 趨勢：觀察量能
→ 建議：不追高

📌 建準
→ 偏弱整理
→ 建議：觀望

📌 智原
→ 有資金回流
→ 建議：可關注

👉 今日結論：
暫不重壓
"""
    return msg

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

if __name__ == "__main__":
    send_telegram(get_stock_report())
