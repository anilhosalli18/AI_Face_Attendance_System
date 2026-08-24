// =============================================================================
// AI Face Attendance System — Frontend JavaScript Application
// =============================================================================

let currentTab = 'scanner';
let videoStream = null;
let scanInterval = null;
let isProcessingFrame = false;
let currentPendingFace = null;

// Clock updates
function updateClock() {
    const el = document.getElementById('digital-clock');
    if (el) {
        const now = new Date();
        el.innerText = now.toLocaleTimeString('en-US', { hour12: true });
    }
}
setInterval(updateClock, 1000);
updateClock();

// Speech Synthesis Helper
function speakMessage(text) {
    const bannerText = document.getElementById('voice-message');
    if (bannerText) bannerText.innerText = text;

    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    }
}

// Health Check & DB Status
async function checkHealth() {
    try {
        const res = await fetch('/api/health');
        const data = await res.json();
        const badge = document.getElementById('db-status-badge');
        const text = document.getElementById('db-status-text');

        if (data.database === 'connected') {
            text.innerText = 'MongoDB Connected';
            badge.style.color = '#00ff88';
        } else {
            text.innerText = 'DB Offline';
            badge.style.color = '#ff3366';
        }
    } catch (e) {
        const text = document.getElementById('db-status-text');
        if (text) text.innerText = 'API Offline';
    }
}
setInterval(checkHealth, 10000);
checkHealth();

// Tab Navigation
function switchTab(tabId) {
    currentTab = tabId;
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

    const btn = document.getElementById(`btn-tab-${tabId}`);
    const tab = document.getElementById(`tab-${tabId}`);

    if (btn) btn.classList.add('active');
    if (tab) tab.classList.add('active');

    // Title changes
    const titles = {
        'scanner': ['Live Face Recognition Scanner', 'Real-time automated check-in & check-out'],
        'dashboard': ['Admin Analytics Dashboard', 'Daily employee attendance breakdown'],
        'register': ['Employee Face Registration', 'Add new employees to AI face encoding registry'],
        'logs': ['System Audit Logs', 'Real-time security and operational events']
    };

    if (titles[tabId]) {
        document.getElementById('current-page-title').innerText = titles[tabId][0];
        document.getElementById('current-page-subtitle').innerText = titles[tabId][1];
    }

    if (tabId === 'scanner') {
        startWebcam();
    } else {
        stopWebcam();
    }

    if (tabId === 'dashboard') {
        loadDashboardData();
    } else if (tabId === 'logs') {
        loadLogsData();
    } else if (tabId === 'register') {
        startRegisterWebcam();
    }
}

// Live Camera Initialization
async function startWebcam() {
    const video = document.getElementById('webcam');
    const statusPill = document.getElementById('camera-status');

    try {
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 1280, height: 720, facingMode: 'user' }
        });
        video.srcObject = videoStream;
        statusPill.innerText = 'Camera Active';
        statusPill.style.borderColor = 'rgba(0, 255, 136, 0.4)';
        statusPill.style.color = '#00ff88';

        // Start scanning loop
        if (scanInterval) clearInterval(scanInterval);
        scanInterval = setInterval(captureAndRecognize, 500);

    } catch (err) {
        console.error("Camera access error:", err);
        statusPill.innerText = 'Camera Permission Error';
        statusPill.style.color = '#ff3366';
    }
}

function stopWebcam() {
    if (scanInterval) clearInterval(scanInterval);
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

function toggleCamera() {
    if (videoStream) {
        stopWebcam();
        document.getElementById('camera-status').innerText = 'Camera Stopped';
    } else {
        startWebcam();
    }
}

// Frame Capture & Recognition API Request
async function captureAndRecognize() {
    if (isProcessingFrame || currentTab !== 'scanner') return;

    const video = document.getElementById('webcam');
    const canvas = document.getElementById('overlay-canvas');
    if (!video || video.readyState !== 4) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');

    // Create temporary offscreen canvas to capture JPEG frame
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
    const frameData = tempCanvas.toDataURL('image/jpeg', 0.8);

    isProcessingFrame = true;

    try {
        const res = await fetch('/api/recognize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: frameData })
        });
        const data = await res.json();

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (data.faces && data.faces.length > 0) {
            data.faces.forEach(face => {
                drawBoundingBox(ctx, face, canvas.width, canvas.height);
                updateRecognitionUI(face);
            });
        } else {
            resetRecognitionUI();
        }

    } catch (err) {
        console.error("Recognition API error:", err);
    } finally {
        isProcessingFrame = false;
    }
}

// Draw bounding box overlay on canvas
function drawBoundingBox(ctx, face, width, height) {
    const box = face.box;
    const left = box.left * width;
    const top = box.top * height;
    const right = box.right * width;
    const bottom = box.bottom * height;
    const w = right - left;
    const h = bottom - top;

    const color = (face.status === 'IDENTIFIED') ? '#00ff88' : '#ff3366';

    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(left, top, w, h);

    // Corner highlights
    ctx.fillStyle = color;
    ctx.fillRect(left - 2, top - 2, 12, 4);
    ctx.fillRect(left - 2, top - 2, 4, 12);
    ctx.fillRect(right - 10, top - 2, 12, 4);
    ctx.fillRect(right - 2, top - 2, 4, 12);

    // Label tag
    ctx.fillStyle = 'rgba(10, 15, 30, 0.85)';
    ctx.fillRect(left, top - 32, w, 28);

    ctx.fillStyle = color;
    ctx.font = '600 14px Outfit';
    ctx.fillText(`${face.emp_name || face.label} (${face.confidence}%)`, left + 8, top - 12);
}

// Update Right-side Recognition UI Panel
function updateRecognitionUI(face) {
    const emptyState = document.getElementById('empty-state');
    const identifiedState = document.getElementById('identified-state');

    if (face.status === 'IDENTIFIED') {
        emptyState.classList.add('hidden');
        identifiedState.classList.remove('hidden');

        document.getElementById('id-name').innerText = face.emp_name;
        document.getElementById('id-emp-id').innerText = face.emp_id;
        document.getElementById('id-confidence').innerText = `${face.confidence}%`;
        document.getElementById('action-tag').innerText = `→ ${face.action}`;

        currentPendingFace = face;
    } else {
        emptyState.classList.remove('hidden');
        identifiedState.classList.add('hidden');
        currentPendingFace = null;
    }
}

function resetRecognitionUI() {
    const emptyState = document.getElementById('empty-state');
    const identifiedState = document.getElementById('identified-state');
    if (emptyState) emptyState.classList.remove('hidden');
    if (identifiedState) identifiedState.classList.add('hidden');
    currentPendingFace = null;
}

// Confirm Attendance Button Trigger
async function confirmSelectedFace() {
    if (!currentPendingFace) return;

    try {
        const res = await fetch('/api/attendance/confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emp_id: currentPendingFace.emp_id })
        });
        const data = await res.json();

        if (data.success) {
            speakMessage(data.message);
            alert(data.message);
        } else {
            speakMessage(data.message);
            alert(data.message);
        }
    } catch (e) {
        alert("Failed to record attendance: " + e.message);
    }
}

// Admin Dashboard Data Fetching
async function loadDashboardData() {
    try {
        const statsRes = await fetch('/api/stats');
        const stats = await statsRes.json();

        document.getElementById('stat-total').innerText = stats.total_employees;
        document.getElementById('stat-present').innerText = stats.present_today;
        document.getElementById('stat-late').innerText = stats.late_today;
        document.getElementById('stat-absent').innerText = stats.absent_today;

        const recordsRes = await fetch('/api/attendance');
        const records = await recordsRes.json();

        const tbody = document.getElementById('attendance-table-body');
        if (records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center">No attendance records logged today.</td></tr>`;
            return;
        }

        tbody.innerHTML = records.map(r => `
            <tr>
                <td><strong>${r.emp_id}</strong></td>
                <td>${r.emp_name}</td>
                <td>${r.department || 'General'}</td>
                <td>${r.date}</td>
                <td>${r.login_time || '--'}</td>
                <td>${r.logout_time || '--'}</td>
                <td>
                    <span class="badge-status ${r.status === 'On-Time' ? 'on-time' : 'late'}">
                        ${r.status}
                    </span>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

// System Logs Data Fetching
async function loadLogsData() {
    try {
        const res = await fetch('/api/logs');
        const logs = await res.json();
        const tbody = document.getElementById('logs-table-body');

        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center">No system logs found.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(l => `
            <tr>
                <td>${l.timestamp}</td>
                <td><strong>${l.event}</strong></td>
                <td><span class="badge-status ${l.level === 'SUCCESS' ? 'on-time' : 'late'}">${l.level}</span></td>
                <td>${l.detail}</td>
            </tr>
        `).join('');

    } catch (e) {
        console.error("Logs fetch error:", e);
    }
}

// Registration Camera
let regStream = null;
async function startRegisterWebcam() {
    const video = document.getElementById('reg-webcam');
    try {
        regStream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = regStream;
    } catch (e) {
        console.error("Register camera error:", e);
    }
}

async function handleRegisterSubmit(e) {
    e.preventDefault();

    const empId = document.getElementById('reg-emp-id').value.trim();
    const empName = document.getElementById('reg-emp-name').value.trim();
    const dept = document.getElementById('reg-dept').value;
    const email = document.getElementById('reg-email').value.trim();

    const video = document.getElementById('reg-webcam');
    const canvas = document.getElementById('reg-canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageB64 = canvas.toDataURL('image/jpeg', 0.9);

    try {
        const res = await fetch('/api/employees/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                emp_id: empId,
                emp_name: empName,
                department: dept,
                email: email,
                image: imageB64
            })
        });

        const data = await res.json();
        if (data.success) {
            alert(data.message);
            document.getElementById('register-form').reset();
            switchTab('dashboard');
        } else {
            alert("Error: " + (data.detail || data.message));
        }
    } catch (err) {
        alert("Registration failed: " + err.message);
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    switchTab('scanner');
});
