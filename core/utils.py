import os

# Runtime duplicate-send guard.

def sent_tag_exists(tag):
    path = f"/tmp/{tag}"
    return os.path.exists(path)


def mark_sent(tag):
    path = f"/tmp/{tag}"
    open(path, "w").close()


def already_sent(tag):
    # Backward-compatible helper: check only. Call mark_sent() after the
    # protected action succeeds so failed delivery can retry.
    return sent_tag_exists(tag)
