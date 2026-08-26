# 🤖 AI Face Attendance System

An **AI-powered Face Recognition Attendance System** built using **Python, OpenCV, Face Recognition, MongoDB, and CustomTkinter**.
The system automatically detects and recognizes employees' faces and records **login and logout attendance** with **voice feedback**.

**Live Demo** : https://ai-face-attendance-1k4q.onrender.com 

---

# 🚀 Features

✅ **AI Face Recognition**

* Detects and recognizes employee faces using the `face_recognition` library.

✅ **Automatic Attendance Marking**

* Records **login and logout time** automatically in MongoDB.

✅ **Anti-Spoof Detection**

* Detects fake attempts (photo/video) by checking face movement.

✅ **Voice Assistant**

* Provides **offline voice feedback** using `pyttsx3`.

Example:

* "Welcome Darshan. Attendance marked successfully."
* "Goodbye Darshan. Logout recorded."

✅ **Confidence-Based Recognition**

* Shows recognition confidence percentage.

Example:

DARSHAN (97.4%)

Press ENTER to confirm

✅ **Employee Registration System**

* Capture employee face and generate **128-dimension face encoding**.

✅ **MongoDB Database Storage**
Stores:

* Employee information
* Attendance records
* System logs

✅ **Modern GUI**

* Built with **CustomTkinter**
* Professional UI for Admin and Employee panels.

---

# 🧠 Technologies Used

| Technology       | Purpose                   |
| ---------------- | ------------------------- |
| Python           | Core programming language |
| OpenCV           | Camera & image processing |
| face_recognition | AI face recognition       |
| dlib             | Face detection model      |
| MongoDB          | Database storage          |
| CustomTkinter    | Modern GUI interface      |
| pyttsx3          | Offline voice assistant   |

---

# 📂 Project Structure

```
face_attendance/
│
├── main.py              # Application entry point
├── attendance.py        # Face recognition attendance logic
├── register.py          # Employee face registration
├── database.py          # MongoDB connection
├── voice.py             # AI voice assistant
│
├── faces/               # Saved employee face images
├── ui/                  # GUI components
│
├── requirements.txt     # Python dependencies
└── README.md
```

---

# ⚙️ Installation

### 1️⃣ Clone the Repository

```
git clone https://github.com/spdarshan46/ai-attendace.git
cd ai-attendace
```

---

### 2️⃣ Create Virtual Environment

```
python -m venv env
```

Activate:

Windows

```
env\Scripts\activate
```

---

### 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

### 4️⃣ Start MongoDB

Make sure MongoDB is running locally:

```
mongodb://localhost:27017
```

Database name:

```
face_attendance
```

---

# ▶️ Running the Project

Run the main application:

```
python main.py
```

For standalone attendance testing:

```
python attendance.py
```

---

# 📊 Attendance Workflow

1️⃣ Employee registers face
2️⃣ Face encoding stored in database
3️⃣ Camera scans face
4️⃣ System identifies employee
5️⃣ Employee presses **ENTER**
6️⃣ Login/Logout recorded in MongoDB
7️⃣ Voice confirmation played

---

# 🔐 Security Features

✔ Face encoding authentication
✔ Anti-spoof detection
✔ Cooldown system to prevent duplicate entries
✔ Confidence-based recognition

---

# 📸 Example Output
<img width="1365" height="722" alt="image" src="https://github.com/user-attachments/assets/b100cf06-b65b-4a89-b4ef-a4fc269ca9b9" />
<img width="1350" height="670" alt="image" src="https://github.com/user-attachments/assets/381e9c53-d9c2-407c-bf24-7efcb3212a84" />
<img width="1365" height="717" alt="image" src="https://github.com/user-attachments/assets/432a964a-eb07-4920-a4b8-566fd5286f54" />
<img width="1365" height="720" alt="image" src="https://github.com/user-attachments/assets/11696238-908d-4422-8e46-1624aebdf659" />

---

# 👨‍💻 Author

**S P Darshan**

Computer Science Engineering Student
Interested in **AI, Cybersecurity, and Full Stack Development**

GitHub:
https://github.com/spdarshan46
