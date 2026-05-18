# ============================================================
# MANDOR AI v2.0 — GESTURE ENGINE (v1.1 - Anti False Positive)
# ============================================================

import cv2
import mediapipe as mp
import time
import numpy as np
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
        self.position_buffer = {
            "Left": deque(maxlen=7),
            "Right": deque(maxlen=7)
        }
        self.last_action_time = 0
        self.current_cooldown = 0
        self.last_action_name = ""
        print("✅ GestureEngine siap!")

    def _in_cooldown(self):
        now = time.time() * 1000
        return (now - self.last_action_time) < self.current_cooldown

    def _trigger_action(self, action, cooldown_ms):
        self.last_action_time = time.time() * 1000
        self.current_cooldown = cooldown_ms
        self.last_action_name = action
        print(f"🎯 AKSI: {action}")
        self.callback(action)

    def _is_hand_open(self, landmarks):
        """
        Filter C: Cek apakah tangan terbuka (bukan mengepal).
        Caranya: ujung jari harus lebih jauh dari pangkal jari
        dibanding sendi tengah jari.
        Return True jika minimal 3 dari 4 jari terbuka.
        """
        # Pasangan: (ujung jari, sendi tengah, pangkal)
        finger_tips =  [8, 12, 16, 20]   # telunjuk, tengah, manis, kelingking
        finger_pips =  [6, 10, 14, 18]   # sendi tengah
        finger_mcps =  [5,  9, 13, 17]   # pangkal

        open_count = 0
        for tip, pip, mcp in zip(finger_tips, finger_pips, finger_mcps):
            # Jari dianggap terbuka jika ujungnya lebih tinggi dari sendi tengah
            # (nilai Y lebih kecil = lebih atas di koordinat gambar)
            if landmarks[tip].y < landmarks[pip].y:
                open_count += 1

        return open_count >= 3  # minimal 3 jari terbuka

    def _is_hand_in_chest_zone(self, landmarks, frame_height):
        """
        Filter B: Cek apakah tangan berada di zona dada
        (antara 25% - 80% tinggi frame).
        Mencegah deteksi saat tangan di atas kepala atau di bawah pinggang.
        """
        # Gunakan landmark 9 (pangkal jari tengah) sebagai posisi tangan
        hand_y = landmarks[9].y  # nilai 0.0 (atas) sampai 1.0 (bawah)
        return 0.25 <= hand_y <= 0.80

    def _detect_swipe(self, hand_label, landmarks, frame_width, frame_height):
        # 1. Kita matikan sementara zona dada untuk testing, 
        # dan HAPUS buffer.clear() agar ingatan tidak gampang amnesia!
        # if not self._is_hand_in_chest_zone(landmarks, frame_height):
        #     return 

        lm9 = landmarks[9]
        x_now = lm9.x * frame_width
        y_now = lm9.y * frame_height
        now = time.time() * 1000

        buffer = self.position_buffer[hand_label]
        
        # Bersihkan jika format lama masih nyangkut
        if len(buffer) > 0 and len(buffer[0]) == 2:
            buffer.clear()

        # Masukkan posisi sekarang ke memori
        buffer.append((x_now, y_now, now))

        # Tunggu sampai ingatan penuh 7 frame (sekitar 0.2 detik pergerakan)
        if len(buffer) < 7:
            return

        # Ambil memori paling ujung (7 frame yang lalu)
        oldest_x, oldest_y, oldest_time = buffer[0]

        delta_x = x_now - oldest_x
        delta_y = y_now - oldest_y

        # === LAPIS 1: Syarat Jarak Tempuh ===
        if abs(delta_x) < SWIPE_THRESHOLD_PX:
            return
            
        # === LAPIS 2: Syarat Ayunan (Lebih Toleran) ===
        # Gerakan X (Kanan-Kiri) HARUS lebih besar dari gerakan Y (Atas-Bawah).
        # Tapi ayunan melengkung dari bahu tetep bakal lolos di sini!
        if abs(delta_y) > abs(delta_x): 
            return

        # === EKSEKUSI ===
        if delta_x > 0 and hand_label == "Right":
            self._trigger_action("next", COOLDOWN_SWIPE_MS)
            buffer.clear()
        elif delta_x < 0 and hand_label == "Left":
            self._trigger_action("prev", COOLDOWN_SWIPE_MS)
            buffer.clear()

    def process_frame(self, frame, roi=None):
        # if self._in_cooldown():
        #     return frame

        h, w = frame.shape[:2]

        if roi:
            x1, y1, x2, y2 = roi
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            # --- eror handling kalau eror/kosong ---
            if x1 >= x2 or y1 >= y2:
                return frame  # Kalau kotaknya error/kosong, skip proses frame ini
                
            process_area = frame[y1:y2, x1:x2]
            area_w = x2 - x1
            area_h = y2 - y1
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

                # Gambar landmark
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

                # --- UBAH BAGIAN INI ---
                # Cek cooldown di sini! Jadi tangan tetep kelacak dan digambar, 
                # tapi deteksi kibasannya aja yang di-pause sebentar.
                if not self._in_cooldown():
                    self._detect_swipe(hand_label, hand_landmarks.landmark, area_w, area_h)
                else:
                    # Bersihkan ingatan memori biar gak numpuk pas cooldown kelar
                    self.position_buffer[hand_label].clear()

        return frame

    def get_status(self):
        if self._in_cooldown():
            sisa = int(self.current_cooldown - (time.time()*1000 - self.last_action_time))
            return f"Cooldown... ({sisa}ms)"
        return "Siap"


# ============================================================
# TEST MANDIRI
# ============================================================
if __name__ == "__main__":
    def on_gesture(action):
        if action == "next":
            print("👉 NEXT SLIDE")
        elif action == "prev":
            print("👈 PREV SLIDE")

    engine = GestureEngine(callback=on_gesture)
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    print("=" * 45)
    print("🤖 TEST GESTURE ENGINE v1.1")
    print("Kibas tangan KANAN ke kanan = NEXT")
    print("Kibas tangan KIRI  ke kiri  = PREV")
    print("Tekan Q untuk keluar")
    print("=" * 45)

    # Variabel untuk flash notifikasi di layar
    notif_text = ""
    notif_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # Garis zona dada (visual helper untuk tuning)
        zona_atas = int(h * 0.25)
        zona_bawah = int(h * 0.80)
        cv2.line(frame, (0, zona_atas), (w, zona_atas), (0, 255, 255), 1)
        cv2.line(frame, (0, zona_bawah), (w, zona_bawah), (0, 255, 255), 1)
        cv2.putText(frame, "ZONA AKTIF", (10, zona_atas - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        frame = engine.process_frame(frame)

        # Notifikasi aksi
        if engine.last_action_name and time.time() - engine.last_action_time/1000 < 1.0:
            label = "👉 NEXT" if engine.last_action_name == "next" else "👈 PREV"
            cv2.putText(frame, label, (w//2 - 60, h//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)

        # Status bar
        status = engine.get_status()
        cv2.rectangle(frame, (0, h-40), (w, h), (0, 0, 0), -1)
        cv2.putText(frame, f"Status: {status}", (10, h-15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        cv2.imshow("Mandor AI v2 - Test Gesture", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()