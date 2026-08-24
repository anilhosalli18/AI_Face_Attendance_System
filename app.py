import os
import sys
import base64
import time
import cv2
import numpy as np
import face_recognition
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Body, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

import database
from database import employees, attendance, logs, write_log

# ── App Initialization ────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Face Attendance System API",
    description="REST API & Web Application for AI Face Attendance",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TOLERANCE = 0.50
COOLDOWN_SECS = 5
LATE_AFTER = "09:30:00"

# ── Helper Functions ──────────────────────────────────────────────────────────
def decode_base64_image(b64_str: str) -> np.ndarray:
    """Decodes a base64 data URI image into an OpenCV BGR numpy array."""
    try:
        if "," in b64_str:
            b64_str = b64_str.split(",")[1]
        img_bytes = base64.b64decode(b64_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        raise ValueError(f"Invalid base64 image data: {e}")

def get_known_encodings():
    known_encodings, known_ids, known_names = [], [], []
    if employees is not None:
        for emp in employees.find():
            if "face_encoding" in emp:
                known_encodings.append(np.array(emp["face_encoding"]))
                known_ids.append(emp["emp_id"])
                known_names.append(emp["emp_name"])
    return known_encodings, known_ids, known_names

# ── Static Files & Root Route ─────────────────────────────────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>AI Face Attendance Web API is Running.</h2>")

# ── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    db_status = "connected" if employees is not None else "disconnected"
    return {"status": "ok", "database": db_status, "timestamp": datetime.now().isoformat()}

@app.get("/api/stats")
def get_dashboard_stats():
    """Returns analytics KPI stats for the Web Admin Dashboard."""
    today = datetime.now().strftime("%Y-%m-%d")
    total_emp = employees.count_documents({}) if employees is not None else 0
    
    if attendance is not None:
        today_records = list(attendance.find({"date": today}))
        present_count = len(today_records)
        late_count = sum(
            1 for r in today_records
            if r.get("login_time") and r.get("login_time") > LATE_AFTER
        )
    else:
        present_count = 0
        late_count = 0

    log_count = logs.count_documents({}) if logs is not None else 0

    return {
        "total_employees": total_emp,
        "present_today": present_count,
        "late_today": late_count,
        "absent_today": max(0, total_emp - present_count),
        "total_logs": log_count,
        "date": today
    }

@app.get("/api/attendance")
def get_attendance_records(date: Optional[str] = None):
    """Fetch attendance records, default today."""
    if attendance is None:
        return []
    
    query = {}
    if date:
        query["date"] = date
    else:
        query["date"] = datetime.now().strftime("%Y-%m-%d")
        
    records = list(attendance.find(query, {"_id": 0}).sort("date", -1))
    return records

@app.get("/api/employees")
def get_employee_list():
    """Fetch employee directory."""
    if employees is None:
        return []
    emps = list(employees.find({}, {"_id": 0, "face_encoding": 0}).sort("emp_id", 1))
    return emps

class FramePayload(BaseModel):
    image: str

@app.post("/api/recognize")
def recognize_frame(payload: FramePayload):
    """
    Receives a camera frame base64 string from browser.
    Detects faces, computes encodings, and matches with DB encodings.
    """
    try:
        frame = decode_base64_image(payload.image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    locs = face_recognition.face_locations(rgb)
    encs = face_recognition.face_encodings(rgb, locs)
    
    known_encodings, known_ids, known_names = get_known_encodings()

    results = []

    for face_enc, (top, right, bottom, left) in zip(encs, locs):
        # Coordinates scaled relative to frame width/height (0.0 to 1.0)
        box = {
            "top": round(top / h, 4),
            "left": round(left / w, 4),
            "bottom": round(bottom / h, 4),
            "right": round(right / w, 4)
        }

        if not known_encodings:
            results.append({
                "status": "UNKNOWN",
                "label": "NO REGISTERED EMPLOYEES",
                "confidence": 0,
                "box": box
            })
            continue

        distances = face_recognition.face_distance(known_encodings, face_enc)
        best_idx = int(np.argmin(distances))
        best_dist = distances[best_idx]
        confidence = round((1.0 - best_dist) * 100, 1)

        if best_dist >= TOLERANCE:
            results.append({
                "status": "UNKNOWN",
                "label": "UNKNOWN",
                "confidence": confidence,
                "box": box
            })
        else:
            emp_id = known_ids[best_idx]
            emp_name = known_names[best_idx]
            
            today = datetime.now().strftime("%Y-%m-%d")
            record = attendance.find_one({"emp_id": emp_id, "date": today}) if attendance is not None else None

            if not record:
                action = "LOGIN"
            elif not record.get("logout_time"):
                action = "LOGOUT"
            else:
                action = "COMPLETED"

            results.append({
                "status": "IDENTIFIED",
                "emp_id": emp_id,
                "emp_name": emp_name,
                "confidence": confidence,
                "action": action,
                "box": box
            })

    return {"faces": results, "detected_count": len(locs)}

class ConfirmPayload(BaseModel):
    emp_id: str

@app.post("/api/attendance/confirm")
def confirm_attendance(payload: ConfirmPayload):
    """Confirms and writes attendance for identified employee."""
    if employees is None or attendance is None:
        raise HTTPException(status_code=500, detail="Database unavailable")

    emp_id = payload.emp_id
    emp = employees.find_one({"emp_id": emp_id})
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp_name = emp["emp_name"]
    today = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M:%S")

    record = attendance.find_one({"emp_id": emp_id, "date": today})

    if not record:
        status_type = "On-Time" if now_time <= LATE_AFTER else "Late"
        attendance.insert_one({
            "emp_id": emp_id,
            "emp_name": emp_name,
            "department": emp.get("department", "General"),
            "date": today,
            "login_time": now_time,
            "logout_time": "",
            "status": status_type,
            "method": "Web Face Recognition"
        })
        write_log("LOGIN", f"{emp_name} ({emp_id}) marked login at {now_time}", "SUCCESS")
        return {"success": True, "action": "LOGIN", "message": f"Welcome {emp_name}, Login Recorded!"}

    elif not record.get("logout_time"):
        attendance.update_one(
            {"emp_id": emp_id, "date": today},
            {"$set": {"logout_time": now_time}}
        )
        write_log("LOGOUT", f"{emp_name} ({emp_id}) marked logout at {now_time}", "SUCCESS")
        return {"success": True, "action": "LOGOUT", "message": f"Goodbye {emp_name}, Logout Recorded!"}

    else:
        return {"success": False, "action": "ALREADY_COMPLETED", "message": f"{emp_name} has already completed attendance today."}

class RegisterPayload(BaseModel):
    emp_id: str
    emp_name: str
    department: str = "Engineering"
    email: str = ""
    image: str

@app.post("/api/employees/register")
def register_employee(payload: RegisterPayload):
    """Registers a new employee with face image upload."""
    if employees is None:
        raise HTTPException(status_code=500, detail="Database unavailable")

    if employees.find_one({"emp_id": payload.emp_id}):
        raise HTTPException(status_code=400, detail=f"Employee ID {payload.emp_id} already exists")

    try:
        frame = decode_base64_image(payload.image)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encs = face_recognition.face_encodings(rgb)
        
        if not encs:
            raise HTTPException(status_code=400, detail="No clear face detected in the uploaded image. Please try again.")

        encoding_list = encs[0].tolist()

        employees.insert_one({
            "emp_id": payload.emp_id,
            "emp_name": payload.emp_name,
            "department": payload.department,
            "email": payload.email,
            "face_encoding": encoding_list,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        write_log("REGISTER", f"Registered new employee: {payload.emp_name} ({payload.emp_id})", "SUCCESS")
        return {"success": True, "message": f"Employee {payload.emp_name} registered successfully!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/logs")
def get_system_logs(limit: int = 50):
    if logs is None:
        return []
    res = list(logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    return res

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
