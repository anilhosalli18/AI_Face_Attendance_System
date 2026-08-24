import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pymongo import MongoClient
from datetime import datetime

# ==========================================
# DATABASE.PY — MongoDB Dynamic Connection
# ==========================================

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    db         = client["face_attendance"]
    employees  = db["employees"]
    attendance = db["attendance"]
    logs       = db["system_logs"]

    employees.create_index("emp_id", unique=True)
    attendance.create_index([("emp_id", 1), ("date", 1)])
    logs.create_index([("timestamp", -1)])

    print("MongoDB Connected Successfully ✅")

except Exception as e:
    print("MongoDB Connection Failed ❌")
    print(e)
    employees  = None
    attendance = None
    logs       = None


# ── Logging helper ─────────────────────────
def write_log(event: str, detail: str = "", level: str = "INFO"):
    """
    Levels: INFO | SUCCESS | WARNING | ERROR
    """
    if logs is None:
        return
    try:
        logs.insert_one({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "detail": detail,
            "level": level,
        })
    except Exception:
        pass