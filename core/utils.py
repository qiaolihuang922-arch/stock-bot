import os

def already_sent(tag):
    path = f"/tmp/{tag}"
    if os.path.exists(path):
        return True
    open(path, "w").close()
    return False