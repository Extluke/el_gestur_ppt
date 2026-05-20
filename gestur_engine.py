# ============================================================
# MANDOR AI v2.0 — GESTURE ENGINE (GOD MODE V2.1)
# Pendekatan: Velocity Spike + Dynamic ROI Scaling + Euclidean
# ============================================================

import cv2
import mediapipe as mp
import time
import math
from collections import deque
from config import *

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

class GestureEngine:
    def __init__(self, callback):
        self.callback = callback
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=MP_DETECTION_CONFIDENCE,
            min_tracking_confidence=MP_TRACKING_CONFIDENCE
        )
        # Buffer menyimpan (x, y, timestamp)
        self.position_buffer = {
            "Left":  deque(maxlen=20),
            "Right": deque(maxlen=20)
        }
        self.last_action_time = 0
        self.current_cooldown = 0
        self.last_action_name = ""
        print("✅ GestureEngine v2.1 (God Mode) siap!")

    def _in_cooldown(self):
        now = time.time() * 1000
        return (now - self.last_action_time) < self.current_cooldown

    def _trigger_action(self, action, cooldown_ms):
        self.last_action_time = time.time() * 1000
        self.current_cooldown = cooldown_ms
        self.last_action_name = action
        print(f"🎯 AKSI DIEKSEKUSI: {action.upper()}")
        self.callback(action)

    def _is_hand_open(self, landmarks, frame_w, frame_h):
        """
        GERBANG 1: Menggunakan Euclidean Distance.
        Kebal terhadap rotasi! Jari lurus jika jarak ujung jari 
        ke pergelangan > jarak sendi tengah ke pergelangan.
        """
        def calc_dist(p1, p2):
            return math.hypot((p1.x - p2.x) * frame_w, (p1.y - p2.y) * frame_h)

        wrist = landmarks[0]
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        open_count = 0

        for tip, pip in zip(finger_tips, finger_pips):
            dist_tip = calc_dist(wrist, landmarks[tip])
            dist_pip = calc_dist(wrist, landmarks[pip])
            if dist_tip > dist_pip:
                open_count += 1
                
        return open_count >= 3

    def _detect_swipe(self, hand_label, landmarks, frame_w, frame_h):
        # === GERBANG 1: Tangan harus terbuka (Anti-Rotasi) ===
        if not self._is_hand_open(landmarks, frame_w, frame_h):
            self.position_buffer[hand_label].clear()
            return

        # === GERBANG 2: Zona dada proporsional ===
        hand_y = landmarks[9].y
        if not (0.15 <= hand_y <= 0.90):
            self.position_buffer[hand_label].clear()
            return

        x_now = landmarks[9].x * frame_w
        y_now = landmarks[9].y * frame_h
        now_ms = time.time() * 1000

        buf = self.position_buffer[hand_label]
        buf.append((x_now, y_now, now_ms))

        if len(buf) < 4:
            return

        # === GERBANG 3: Hitung Kecepatan (Velocity) ===
        recent = list(buf)[-4:]
        velocities_x = []
        
        for i in range(1, len(recent)):
            dx = recent[i][0] - recent[i-1][0]
            dt = (recent[i][2] - recent[i-1][2]) / 1000.0  # detik
            if dt > 0:
                velocities_x.append(dx / dt)

        if not velocities_x:
            return

        avg_velocity = sum(velocities_x) / len(velocities_x)
        peak_velocity = max(velocities_x, key=abs)
        delta_total = buf[-1][0] - buf[-4][0]

        # === DYNAMIC ROI SCALING (Rahasia Kebal Jarak) ===
        # Mengubah ukuran pixel ke persentase berdasarkan lebar kotak badan lu
        min_dist_px = frame_w * 0.15   # Minimal geser sejauh 15% dari lebar badan
        min_speed_px = frame_w * 0.4   # Minimal kecepatan menempuh 100% lebar badan per detik

        # Cetak Telemetri hanya kalau ada pergerakan signifikan (buat kalibrasi lu)
        if abs(delta_total) > (frame_w * 0.05):
            print(f"[{hand_label}] Geser: {abs(delta_total):.0f}px (Min: {min_dist_px:.0f}) | Speed: {abs(peak_velocity):.0f}px/s (Min: {min_speed_px:.0f})")

        # === GERBANG 4: Kecepatan puncak harus lolos ===
        if abs(peak_velocity) < min_speed_px:
            return

        # === GERBANG 5: Konsistensi Arah (Semua frame harus searah) ===
        arah_total = "kanan" if delta_total > 0 else "kiri"
        arah_puncak = "kanan" if peak_velocity > 0 else "kiri"
        
        if arah_total != arah_puncak:
            return
            
        arah = arah_total

        # === GERBANG 6: Jarak total harus cukup ===
        if abs(delta_total) < min_dist_px:
            return

        # === SEMUA GERBANG LOLOS → EKSEKUSI ===
        if arah == "kanan" and hand_label == "Right":
            self._trigger_action("next", COOLDOWN_SWIPE_MS)
            buf.clear()
        elif arah == "kiri" and hand_label == "Left":
            self._trigger_action("prev", COOLDOWN_SWIPE_MS)
            buf.clear()

    def process_frame(self, frame, roi=None):
        h, w = frame.shape[:2]

        if roi:
            x1, y1, x2, y2 = roi
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if x1 >= x2 or y1 >= y2:
                return frame
            process_area = frame[y1:y2, x1:x2]
            area_w, area_h = x2 - x1, y2 - y1
        else:
            process_area = frame
            area_w, area_h = w, h

        rgb = cv2.cvtColor(process_area, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks, hand_info in zip(
                results.multi_hand_landmarks,
                results.multi_handedness
            ):
                raw_label = hand_info.classification[0].label
                hand_label = "Left" if raw_label == "Right" else "Right"

                if roi:
                    for lm in hand_landmarks.landmark:
                        cx = int(lm.x * area_w) + x1
                        cy = int(lm.y * area_h) + y1
                        cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
                else:
                    mp_draw.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                        mp_styles.get_default_hand_landmarks_style(),
                        mp_styles.get_default_hand_connections_style()
                    )

                if not self._in_cooldown():
                    self._detect_swipe(hand_label, hand_landmarks.landmark, area_w, area_h)
                else:
                    self.position_buffer[hand_label].clear()

        return frame

    def get_status(self):
        if self._in_cooldown():
            sisa = int(self.current_cooldown - (time.time()*1000 - self.last_action_time))
            return f"Cooldown... ({sisa}ms)"
        return "Siap"

# ============================================================
# TEST MANDIRI — py gestur_engine.py
# ============================================================
if __name__ == "__main__":
    def on_gesture(action):
        if action == "next":   print("👉 NEXT SLIDE")
        elif action == "prev": print("👈 PREV SLIDE")

    engine = GestureEngine(callback=on_gesture)
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    print("=" * 50)
    print("🤖 TEST GESTURE ENGINE v2.1 (GOD MODE)")
    print("Kibas tangan KANAN ke kanan = NEXT")
    print("Kibas tangan KIRI  ke kiri  = PREV")
    print("Tekan Q untuk keluar")
    print("=" * 50)

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        y_atas  = int(h * 0.15)
        y_bawah = int(h * 0.90)
        cv2.line(frame, (0, y_atas),  (w, y_atas),  (0, 255, 255), 1)
        cv2.line(frame, (0, y_bawah), (w, y_bawah), (0, 255, 255), 1)
        cv2.putText(frame, "ZONA AKTIF", (10, y_atas - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        frame = engine.process_frame(frame)

        if engine.last_action_name:
            elapsed = time.time() - engine.last_action_time / 1000
            if elapsed < 1.0:
                label = "NEXT >>" if engine.last_action_name == "next" else "<< PREV"
                cv2.putText(frame, label, (w//2 - 80, h//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)

        status = engine.get_status()
        cv2.rectangle(frame, (0, h-40), (w, h), (0,0,0), -1)
        cv2.putText(frame, f"Status: {status} | Adaptif Skala ROI Aktif",
                    (10, h-12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)

        cv2.imshow("Mandor AI v2 - Gesture Engine v2.1", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()