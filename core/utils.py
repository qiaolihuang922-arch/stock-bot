import os

# Runtime duplicate-send guard.

def already_sent(tag):
    path = f"/tmp/{tag}"

    # 中文註釋：同一個 tag 只允許送一次，避免排程重入造成重複通知。
    if os.path.exists(path):
        return True

    open(path, "w").close()
    return False
