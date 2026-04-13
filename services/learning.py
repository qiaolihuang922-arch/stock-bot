import logging
from datetime import datetime
import pytz

from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

# ================================
# 🔧 初始化
# ================================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
tz = pytz.timezone("Asia/Taipei")

# ================================
# 📊 logger（強化版）
# ================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def log_block(title, data=None):
    logging.info(f"\n========== {title} ==========")
    if data:
        for k, v in data.items():
            logging.info(f"{k}: {v}")
    logging.info("================================\n")


# ================================
# 🔍 DB欄位檢查（防呆）
# ================================
REQUIRED_COLUMNS = [
    "stock", "trade_date", "decision",
    "price", "buy", "stop",
    "ma5", "ma20",
    "volume", "trend",
    "status", "created_at", "extra_data"
]


def validate_payload(data):
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in data:
            missing.append(col)

    if missing:
        logging.error(f"[SCHEMA ERROR] 缺少欄位: {missing}")
        return False

    return True


# ================================
# 🔥 入庫（V8最終版）
# ================================
def record_trade(
    name,
    action,
    price,
    buy,
    stop,
    ma5,
    ma20,
    volume,
    trend,
    extra_data=None
):

    log_block("🚀 嘗試入庫", {
        "stock": name,
        "action": action,
        "price": price,
        "buy": buy,
        "stop": stop
    })

    try:
        # =========================
        # ❌ 基本防呆
        # =========================
        if buy in ["-", None] or stop in ["-", None]:
            logging.warning(f"[SKIP] {name} 買賣點無效")
            return False

        if float(buy) <= float(stop):
            logging.warning(f"[SKIP] {name} buy <= stop")
            return False

        # =========================
        # 📅 時間
        # =========================
        now = datetime.now(tz)
        today = now.strftime("%Y-%m-%d")

        # =========================
        # 🔧 extra_data清洗
        # =========================
        clean_extra = {}

        if extra_data:
            for k, v in extra_data.items():

                if k in ["result", "future_price", "price_after"]:
                    logging.warning(f"[FILTER] 移除污染欄位: {k}")
                    continue

                if v is None:
                    continue

                if isinstance(v, (int, float, str)):
                    clean_extra[k] = v
                else:
                    clean_extra[k] = str(v)

        # ===== 強制欄位 =====
        required_keys = [
            "rr",
            "decision_type",
            "market",
            "structure_state",
            "momentum_state",
            "breakout_quality",
            "pullback_type"
        ]

        for k in required_keys:
            if k not in clean_extra:
                clean_extra[k] = None

        # =========================
        # 📦 組裝資料（修正版）
        # =========================
        data = {
            "stock": name,
            "trade_date": today,
            "decision": action,           # ✅ 修正
            "price": float(price),        # ✅ 修正
            "buy": float(buy),
            "stop": float(stop),
            "ma5": float(ma5),
            "ma20": float(ma20),
            "volume": str(volume),
            "trend": str(trend),
            "status": "pending",
            "created_at": now.isoformat(),
            "extra_data": clean_extra
        }

        # =========================
        # 🔍 schema檢查
        # =========================
        if not validate_payload(data):
            logging.error(f"[ABORT] {name} schema錯誤，停止入庫")
            return False

        log_block("📦 最終寫入資料", data)

        # =========================
        # 💾 寫入DB
        # =========================
        res = supabase.table("trades").insert(data).execute()

        # =========================
        # ✅ 成功
        # =========================
        if res.data:
            logging.info(f"[SUCCESS] ✅ {name} 入庫成功")
            return True

        # =========================
        # ⚠ 未知狀態
        # =========================
        logging.warning(f"[UNKNOWN] ⚠ {name} 無回傳資料")
        logging.warning(f"Response: {res}")
        return False

    except Exception as e:

        msg = str(e).lower()

        # =========================
        # ❗ 重複資料
        # =========================
        if "duplicate" in msg:
            logging.warning(f"[DUPLICATE] {name} 今日已存在")
            return False

        # =========================
        # ❗ 欄位錯誤
        # =========================
        if "column" in msg:
            logging.error(f"[SCHEMA ERROR] 欄位錯誤: {e}")
            return False

        # =========================
        # ❗ 其他錯誤
        # =========================
        logging.error(f"[ERROR] ❌ 入庫失敗: {e}")
        return False


# ================================
# 🔥 更新交易結果（平倉）
# ================================
def update_trade_result(name, trade_date, result):

    log_block("🔄 更新交易結果", {
        "stock": name,
        "date": trade_date,
        "result": result
    })

    try:
        if result not in ["win", "loss", "breakeven"]:
            logging.warning(f"[SKIP] 無效結果: {result}")
            return False

        res = supabase.table("trades") \
            .update({
                "status": "closed",
                "result": result
            }) \
            .eq("stock", name) \
            .eq("trade_date", trade_date) \
            .eq("status", "pending") \
            .execute()

        if res.data:
            logging.info(f"[SUCCESS] ✅ {name} 更新成功 → {result}")
            return True

        logging.warning(f"[NOT FOUND] 找不到可更新資料")
        return False

    except Exception as e:
        logging.error(f"[ERROR] ❌ 更新失敗: {e}")
        return False