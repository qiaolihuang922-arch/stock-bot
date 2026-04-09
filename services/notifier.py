import requests
import time
from config import TOKEN, CHAT_ID

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    if len(msg) > 3500:
        msg = msg[:3500] + "\n\n⚠ 訊息過長已截斷"

    for i in range(3):
        try:
            r = requests.post(url, data={
                "chat_id": CHAT_ID,
                "text": msg
            }, timeout=10)

            if r.status_code == 200:
                print("✅ 發送成功")
                return
            else:
                print("❌ 發送失敗", r.text)

        except Exception as e:
            print("❌ 發送錯誤", e)

        time.sleep(2)