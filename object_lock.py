# ============================================================
# MANDOR AI v2.0 — OBJECT LOCKING (YOLOv8 + DeepSORT)
# ============================================================

import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import time
from config import *

class ObjectLocker:
    def __init__(self):
        print("⏳ Loading YOLOv8 model...")
        self.model = YOLO('yolov8n.pt') 
        
        print("⏳ Setup DeepSORT...")
        # Ubah max_age jadi super panjang (contoh: 30 menit)
        # 30 fps * 60 detik * 30 menit = 54000 frame
        self.tracker = DeepSort(max_age=int(CAMERA_FPS * 60 * 30))
        
        self.locked_id = None
        self.lock_lost_time = 0
        self.center_timers = {} 
        print("✅ ObjectLocker siap!")

    def set_locked_id(self, track_id):
        """Set manual/otomatis ID presenter yang mau dikunci"""
        self.locked_id = str(track_id)
        self.center_timers.clear() # Bersihin timer kalau udah dapet target
        print(f"🔒 PRESENTER TERKUNCI: ID {self.locked_id}")

    def unlock(self):
        """Lepas kuncian (kembali ke Setup Mode)"""
        self.locked_id = None
        self.center_timers.clear()
        print("🔓 PRESENTER DILEPAS")

    def process_frame(self, frame):
        h, w = frame.shape[:2]
        
        # Definisikan "Zona Tengah" (30% area di tengah frame vertikal)
        center_x_min = int(w * 0.35)
        center_x_max = int(w * 0.65)

        # 1. Deteksi semua orang pakai YOLO (class 0 = person)
        results = self.model(frame, classes=[0], conf=YOLO_CONFIDENCE, verbose=False)
        
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                box_w, box_h = x2 - x1, y2 - y1
                detections.append(([x1, y1, box_w, box_h], conf, 'person'))

        # 2. Update tracker DeepSORT
        tracks = self.tracker.update_tracks(detections, frame=frame)
        
        presenter_roi = None
        locked_person_found = False

        # Mode Setup (Visualisasi Zona Tengah)
        if not self.locked_id:
            cv2.line(frame, (center_x_min, 0), (center_x_min, h), (0, 255, 255), 1, cv2.LINE_AA)
            cv2.line(frame, (center_x_max, 0), (center_x_max, h), (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, "ZONA SETUP", (center_x_min + 10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 3. Analisis Tracks
        for track in tracks:
            if not track.is_confirmed():
                continue
                
            track_id = str(track.track_id)
            ltrb = track.to_ltrb() 
            x1, y1, x2, y2 = map(int, ltrb)
            
            # --- LOGIKA KETIKA PRESENTER SUDAH TERKUNCI ---
            if self.locked_id and track_id == self.locked_id:
                locked_person_found = True
                presenter_roi = (x1, y1, x2, y2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"PRESENTER ID:{track_id}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # --- LOGIKA SETUP: CARI PRESENTER (OPSI B) ---
            elif not self.locked_id:
                # Cek apakah titik tengah orang ini ada di zona tengah
                cx = (x1 + x2) // 2
                if center_x_min < cx < center_x_max:
                    if track_id not in self.center_timers:
                        self.center_timers[track_id] = time.time()
                    else:
                        elapsed = time.time() - self.center_timers[track_id]
                        # Tampilkan visual loading lingkaran di dada/kepala
                        cv2.putText(frame, f"Locking... {int(elapsed)}s", (x1, y1 - 25), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                        
                        # Jika sudah diam 3 detik -> KUNCI!
                        if elapsed >= 3.0:
                            self.set_locked_id(track_id)
                else:
                    # Kalau dia keluar dari zona tengah, reset timernya
                    if track_id in self.center_timers:
                        del self.center_timers[track_id]

                # Gambar kotak biasa untuk orang yang belum terkunci
                cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 200, 200), 1)
                cv2.putText(frame, f"ID:{track_id}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # --- ORANG LAIN SAAT PRESENTER SUDAH TERKUNCI ---
            elif self.locked_id and track_id != self.locked_id:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 1)
                cv2.putText(frame, f"ID:{track_id}", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # 4. Handle Lock Lost (Mode Bebal: Gak bakal pernah auto-unlock)
        if self.locked_id and not locked_person_found:
            # Tetap tampilkan peringatan visual supaya lu tau lu lagi di luar frame
            # Tapi KUNCIAN TETAP AMAN (locked_id tidak di-reset)
            cv2.putText(frame, f"DI LUAR FRAME! (MENUNGGU ID: {self.locked_id})", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
        else:
            self.lock_lost_time = 0

        return frame, presenter_roi

# ============================================================
# TEST MANDIRI 
# ============================================================
if __name__ == "__main__":
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    
    locker = ObjectLocker()
    
    print("=" * 45)
    print("🎥 TEST MULTI-LOCKING")
    print("Opsi A (Manual) : Tekan angka 1-9 di keyboard untuk lock ID")
    print("Opsi B (Auto)   : Berdiri di tengah garis kuning selama 3 detik")
    print("Tekan 'u' untuk unlock, 'q' untuk keluar.")
    print("=" * 45)

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        frame, roi = locker.process_frame(frame)
        
        cv2.imshow("Mandor AI v2 - Multi-Locker", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('u'):
            locker.unlock()
        elif ord('1') <= key <= ord('9'):
            # Dummy Opsi A: Eksekusi manual dari user
            locker.set_locked_id(str(chr(key)))

    cap.release()
    cv2.destroyAllWindows()