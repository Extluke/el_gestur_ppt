# ============================================================
# MANDOR AI v2.0 — MAIN SERVER (Flask + PyAutoGUI + CV Pipeline)
# ============================================================

import cv2
import threading
import pyautogui
from flask import Flask, jsonify
from flask_cors import CORS

# Import modul yang udah kita buat
from object_lock import ObjectLocker
from gestur_engine import GestureEngine
from config import *

# Inisialisasi Flask Server
app = Flask(__name__)
CORS(app)

# ==========================================
# 1. CALLBACK GESTURE KE KEYBOARD OS
# ==========================================
def handle_gesture(action):
    """Fungsi ini dipanggil oleh GestureEngine kalau ada gerakan valid"""
    if action == "next":
        print("💻 PyAutoGUI: Menekan tombol KANAN (->)")
        pyautogui.press('right')
    elif action == "prev":
        print("💻 PyAutoGUI: Menekan tombol KIRI (<-)")
        pyautogui.press('left')

# Inisialisasi Sistem Inti
locker = ObjectLocker()
engine = GestureEngine(callback=handle_gesture)

# Matikan failsafe agar mouse tidak error kalau menyentuh sudut layar
pyautogui.FAILSAFE = False

# ==========================================
# 2. MAIN LOOP KAMERA (PIPELINE UTAMA)
# ==========================================
def camera_loop():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    
    print("🎥 Pipeline Kamera mulai merekam...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1)
        
        # --- LAPIS 1: OBJECT LOCKING ---
        # frame_annotated: Frame yang udah digambar kotak YOLO
        # presenter_roi: (x1, y1, x2, y2) dari presenter yang terkunci (jika ada)
        frame_annotated, presenter_roi = locker.process_frame(frame)
        
        # --- LAPIS 2: GESTURE ENGINE ---
        if locker.locked_id and presenter_roi:
            # Lempar ROI ke MediaPipe! CUMA TANGAN PRESENTER YANG DIPROSES
            frame_annotated = engine.process_frame(frame_annotated, roi=presenter_roi)
            
        # Tampilkan visualisasi Backend
        cv2.imshow("Mandor AI v2.0 - Backend Server", frame_annotated)
        
        # Kontrol Keyboard untuk Backend (Debugging / Override Manual)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif ord('1') <= key <= ord('9'):
            locker.set_locked_id(str(chr(key))) # Override Lock manual
            
    cap.release()
    cv2.destroyAllWindows()

# ==========================================
# 3. HTTP ENDPOINT UNTUK FRONTEND
# ==========================================
@app.route('/status', methods=['GET'])
def get_status():
    """Endpoint agar frontend HTML bisa ngecek siapa yang dilock & status cooldown"""
    return jsonify({
        "locked_id": locker.locked_id,
        "gesture_status": engine.get_status()
    })

@app.route('/unlock', methods=['POST'])
def force_unlock():
    """Endpoint untuk tombol unlock manual dari frontend"""
    locker.unlock()
    return jsonify({"message": "Presenter dilepas. Kembali ke Setup Mode."})

if __name__ == '__main__':
    # Jalankan loop kamera di thread terpisah biar server Flask tidak nge-block
    cam_thread = threading.Thread(target=camera_loop, daemon=True)
    cam_thread.start()
    
    # Jalankan Flask Server
    print("🚀 Menjalankan Server Flask di port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)