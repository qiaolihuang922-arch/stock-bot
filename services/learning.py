import logging
from datetime import datetime
import pytz

from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

# ===== 初始化 =====
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

tz = pytz.timezone("Asia/Taipei")

# ===== logger =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ================================
# 🔥 入庫（v7最終版）
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

    try:
        # ===== 基本驗證 =====
        if buy in ["-", None] or stop in ["-", None]:
            logging.warning(f"[SKIP] {name} 無效買賣點")
            return False

        if buy <= stop:
            logging.warning(f"[SKIP] {name} buy <= stop")
            return False

        today = datetime.now(tz).strftime("%Y-%m-%d")

        # ===== 主資料 =====
        data = {
            "stock": name,
            "trade_date": today,
            "action": action,
            "price": float(buy),   # 規則：price = buy
            "buy": float(buy),
            "stop": float(stop),
            "ma5": float(ma5),
            "ma20": float(ma20),
            "volume": str(volume),
            "trend": str(trend),
            "status": "pending",
            "created_at": datetime.now(tz).isoformat()
        }

        # ================================
        # 🔥 extra_data（核心升級）
        # ================================
        clean_extra = {}

        if extra_data:
            for k, v in extra_data.items():

                # ❌ 禁止污染欄位
                if k in ["result", "future_price", "price_after"]:
                    continue

                # ❌ 忽略 None
                if v is None:
                    continue

                # ✅ 型別統一
                if isinstance(v, (int, float, str)):
                    clean_extra[k] = v
                else:
                    clean_extra[k] = str(v)

        # ===== 強制補齊（v7關鍵）=====
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

        # ===== 寫入 extra_data =====
        data["extra_data"] = clean_extra

        # ===== 寫入資料庫 =====
        res = supabase.table("trades").insert(data).execute()

        # ===== 成功 =====
        if res.data:
            logging.info(f"[SUCCESS] {name} 入庫成功 | buy:{buy} stop:{stop}")
            return True

        # ===== 未知 =====
        logging.warning(f"[UNKNOWN] {name} 無回傳資料")
        return False

    except Exception as e:

        msg = str(e).lower()

        # ===== 重複鍵 =====
        if "duplicate" in msg:
            logging.warning(f"[DUPLICATE] {name} 今日已存在")
            return False

        # ===== 其他錯誤 =====
        logging.error(f"[ERROR] {name} 入庫失敗: {e}")
        return False


# ================================
# 🔥 更新結果（平倉）
# ================================
def update_trade_result(name, trade_date, result):

    try:
        if result not in ["win", "loss", "breakeven"]:
            logging.warning(f"[SKIP] 無效結果 {result}")
            return False

        res = supabase.table("trades") \
            .update({
                "status": "closed",
                "result": result,
                "updated_at": datetime.now(tz).isoformat()
            }) \
            .eq("stock", name) \
            .eq("trade_date", trade_date) \
            .eq("status", "pending") \
            .execute()

        if res.data:
            logging.info(f"[UPDATE] {name} 結果更新: {result}")
            return True

        logging.warning(f"[NOT FOUND] {name} 找不到可更新資料")
        return False

    except Exception as e:
        logging.error(f"[ERROR] 更新失敗: {e}")
        return False