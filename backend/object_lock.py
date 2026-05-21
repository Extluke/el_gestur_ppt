# ============================================================
# EL PRESENTASI v2.0 — OBJECT LOCK v2.0 (THROTTLED + STABLE)
# Perubahan: YOLO hanya jalan 5x/detik murni (Hemat CPU 80%!)
# Dilengkapi Padding Tangan (Area Luas) & Anti-Ghosting
# ============================================================

import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import time
from config import *

class ObjectLocker:
    # 🚨 MASTER THROTTLE: YOLO jalan tiap 0.2 detik (5 FPS)
    _YOLO_INTERVAL = 0.20  

    def __init__(self):
        print("⏳ Loading YOLOv8 model...")
        self.model = YOLO('yolov8n.pt') 
        
        print("⏳ Setup DeepSORT...")
        self.tracker = DeepSort(
            max_age=int(CAMERA_FPS * 20), # Memori ingatan 20 detik
            max_cosine_distance=0.4,
            n_init=6                      # Anti-hantu (Bayangan diabaikan)
        )
        
        self.locked_id = None
        self.center_timers = {} 
        self.is_active = False 
        self.wants_to_lock = False 
        
        # --- CACHING SYSTEM (Buat Throttling) ---
        self._last_tracks = []
        self._last_yolo_time = 0.0
        self._last_roi = None
        
        print("✅ ObjectLocker siap dalam mode STANDBY!")

    def set_locked_id(self, track_id):
        self.locked_id = str(track_id)
        self.center_timers.clear() 
        self.wants_to_lock = False
        print(f"🔒 PRESENTER TERKUNCI: ID {self.locked_id}")

    def unlock(self):
        self.locked_id = None
        self.center_timers.clear()
        self.wants_to_lock = False
        self._last_roi = None
        print("🔓 PRESENTER DILEPAS")

    def process_frame(self, frame):
        h, w = frame.shape[:2]
        
        if not self.is_active:
            cv2.putText(frame, "EL PRESENTASI - ENGINE STANDBY", (30, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "Nyalakan engine melalui kontrol aplikasi web.", (30, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            return frame, None
        
        now = time.time()
        run_yolo = (now - self._last_yolo_time) >= self._YOLO_INTERVAL

        # ====================================================
        # ⚡ MODE HEMAT DAYA: LEWATI AI, GUNAKAN CACHE
        # ====================================================
        if not run_yolo and self.locked_id and self._last_roi:
            pad_x1, pad_y1, pad_x2, pad_y2 = self._last_roi
            cv2.rectangle(frame, (pad_x1, pad_y1), (pad_x2, pad_y2), (0, 255, 0), 2)
            cv2.putText(frame, f"PRESENTER ID:{self.locked_id} (HEMAT DAYA)", (pad_x1, pad_y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            return frame, self._last_roi

        # ====================================================
        # 🧠 MODE KERJA: JALANKAN YOLO & DEEPSORT (Tiap 0.2s)
        # ====================================================
        if run_yolo:
            results = self.model(frame, classes=[0], conf=0.55, verbose=False)
            detections = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = box.conf[0].item()
                    box_w, box_h = x2 - x1, y2 - y1
                    
                    if box_w < 30 or box_h < 80: continue # Buang deteksi objek super kecil
                    detections.append(([int(x1), int(y1), int(box_w), int(box_h)], conf, 'person'))

            self._last_tracks = self.tracker.update_tracks(detections, frame=frame)
            self._last_yolo_time = now

        tracks = self._last_tracks
        presenter_roi = None
        locked_person_found = False
        
        center_x_min = int(w * 0.35)
        center_x_max = int(w * 0.65)

        if not self.locked_id:
            cv2.line(frame, (center_x_min, 0), (center_x_min, h), (0, 255, 255), 1, cv2.LINE_AA)
            cv2.line(frame, (center_x_max, 0), (center_x_max, h), (0, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, "ZONA SETUP - DIAM 3 DETIK UNTUK KUNCI", (center_x_min - 50, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 3. Analisis Tracks
        for track in tracks:
            if not track.is_confirmed() or track.time_since_update > 10:
                continue
                
            track_id = str(track.track_id)
            ltrb = track.to_ltrb() 
            
            orig_x1 = int(ltrb[0])
            orig_y1 = int(ltrb[1])
            orig_x2 = int(ltrb[2])
            orig_y2 = int(ltrb[3])
            
            # --- LOGIKA KETIKA PRESENTER SUDAH TERKUNCI ---
            if self.locked_id and track_id == self.locked_id:
                locked_person_found = True
                
                box_width = orig_x2 - orig_x1
                box_height = orig_y2 - orig_y1
                
                # 🚨 PADDING: Berikan ruang bernapas untuk lengan agar MediaPipe tidak terpotong
                margin_x = int(box_width * 0.35) 
                margin_y = int(box_height * 0.10)
                
                pad_x1 = max(0, orig_x1 - margin_x)
                pad_y1 = max(0, orig_y1 - margin_y)
                pad_x2 = min(w, orig_x2 + margin_x)
                pad_y2 = min(h, orig_y2 + margin_y)
                
                presenter_roi = (pad_x1, pad_y1, pad_x2, pad_y2)
                self._last_roi = presenter_roi # Simpan ke cache untuk frame selanjutnya
                
                cv2.rectangle(frame, (pad_x1, pad_y1), (pad_x2, pad_y2), (0, 255, 0), 2)
                cv2.putText(frame, f"PRESENTER ID:{track_id}", (pad_x1, pad_y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # --- LOGIKA SETUP & ORANG LAIN ---
            elif not self.locked_id:
                tx1, tx2 = max(0, orig_x1), min(w, orig_x2)
                ty1, ty2 = max(0, orig_y1), min(h, orig_y2)

                if self.wants_to_lock:
                    self.set_locked_id(track_id)
                    break
                    
                cx = (tx1 + tx2) // 2
                if center_x_min < cx < center_x_max:
                    if track_id not in self.center_timers:
                        self.center_timers[track_id] = now
                    else:
                        elapsed = now - self.center_timers[track_id]
                        cv2.putText(frame, f"Locking... {int(elapsed)}s", (tx1, ty1 - 25), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                        if elapsed >= 3.0:
                            self.set_locked_id(track_id)
                            break 
                else:
                    if track_id in self.center_timers:
                        del self.center_timers[track_id]

                cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (200, 200, 200), 1)
                cv2.putText(frame, f"ID:{track_id}", (tx1, ty1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            elif self.locked_id and track_id != self.locked_id:
                tx1, tx2 = max(0, orig_x1), min(w, orig_x2)
                ty1, ty2 = max(0, orig_y1), min(h, orig_y2)
                cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (0, 0, 255), 1)
                cv2.putText(frame, f"ID:{track_id}", (tx1, ty1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        if self.locked_id and not locked_person_found:
            cv2.putText(frame, f"DI LUAR FRAME! (MENUNGGU ID: {self.locked_id})", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            presenter_roi = self._last_roi # Jika nge-blink sesaat, tetap kirimkan ROI terakhir ke MediaPipe

        return frame, presenter_roi

# ============================================================
# TEST MANDIRI (JANGAN DIHAPUS)
# ============================================================
if __name__ == "__main__":
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    
    locker = ObjectLocker()
    locker.is_active = True 
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        frame, roi = locker.process_frame(frame)
        
        cv2.imshow("El Presentasi v2 - Optimized CPU", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == ord('u'): locker.unlock()
        elif ord('1') <= key <= ord('9'): locker.set_locked_id(str(chr(key)))

    cap.release()
    cv2.destroyAllWindows()