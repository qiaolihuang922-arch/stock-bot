from core.generator import generate
from services.notifier import send
from core.utils import already_sent
from datetime import datetime
import pytz

tz = pytz.timezone("Asia/Taipei")

if __name__ == "__main__":
    tag = datetime.now(tz).strftime("%Y%m%d%H%M")

    if not already_sent(tag):
        msg = generate()
        send(msg)