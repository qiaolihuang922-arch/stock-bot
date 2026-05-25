from core.generator import generate_report
from services.notifier import send_many
from core.utils import already_sent
from datetime import datetime
import pytz

tz = pytz.timezone("Asia/Taipei")

if __name__ == "__main__":
    tag = datetime.now(tz).strftime("%Y%m%d%H%M")

    if not already_sent(tag):
        messages, reply_markup = generate_report()
        if not send_many(messages, reply_markup=reply_markup):
            # 中文註釋：v19.1.3 發送失敗要讓排程失敗，方便從 GitHub Actions 直接看出問題。
            raise SystemExit(1)
