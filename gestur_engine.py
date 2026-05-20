# ============================================================
# MANDOR AI v2.0 — GESTURE ENGINE (GOD MODE V2.2)
# Pendekatan: Velocity Spike + Dynamic ROI Scaling + Euclidean
# Fitur Baru: Shaka Toggle Laser + One Euro Filter Cursor
# ============================================================

import cv2
import mediapipe as mp
import time
import math
import pyautogui
from collections import deque
from config import *

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


# ============================================================
# ONE EURO FILTER — Adaptive Low-Pass Filter untuk Cursor
# Referensi: Casiez et al., CHI 2012
# ============================================================
class OneEuroFilter:
    """Filter adaptif yang tenang saat diam, responsif saat bergerak."""

    def __init__(self, t0, x0, min_cutoff=1.0, beta=0.01, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = x0
        self.dx_prev = 0.0
        self.t_prev = t0

    def __call__(self, t, x):
        dt = t - self.t_prev
        if dt <= 0:
            return self.x_prev

        # Hitung turunan (kecepatan) dan smoothing-nya
        dx = (x - self.x_prev) / dt
        alpha_d = self._alpha(dt, self.d_cutoff)
        edx = alpha_d * dx + (1.0 - alpha_d) * self.dx_prev

        # Cutoff adaptif: makin cepat gerak, makin tinggi cutoff (makin responsif)
        cutoff = self.min_cutoff + self.beta * abs(edx)

        # Filter nilai utama
        alpha = self._alpha(dt, cutoff)
        rx = alpha * x + (1.0 - alpha) * self.x_prev

        # Update state
        self.t_prev = t
        self.x_prev = rx
        self.dx_prev = edx
        return rx

    def _alpha(self, dt, cutoff):
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)


# ============================================================
# GESTURE ENGINE — Mesin Utama Deteksi Gestur
# ============================================================
class GestureEngine:
    def __init__(self, callback, cursor_callback=None):
        self.callback = callback
        self.cursor_callback = cursor_callback
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

        # --- State Laser Pointer ---
        self.laser_active = False
        self.shaka_intent_start = None
        self.shaka_toggled = False       # Cegah toggle berulang saat pose ditahan
        self.filter_x = None
        self.filter_y = None
        self.last_cursor_x = None
        self.last_cursor_y = None
        self.screen_w, self.screen_h = pyautogui.size()

        print("✅ GestureEngine v2.2 (God Mode + Laser) siap!")

    # ========================================================
    # UTILITAS DASAR
    # ========================================================
    def _in_cooldown(self):
        now = time.time() * 1000
        return (now - self.last_action_time) < self.current_cooldown

    def _trigger_action(self, action, cooldown_ms):
        self.last_action_time = time.time() * 1000
        self.current_cooldown = cooldown_ms
        self.last_action_name = action
        print(f"🎯 AKSI DIEKSEKUSI: {action.upper()}")
        self.callback(action)

    @staticmethod
    def _calc_dist(p1, p2, w, h):
        """Euclidean distance dua landmark, diskalakan ke pixel."""
        return math.hypot((p1.x - p2.x) * w, (p1.y - p2.y) * h)

    # ========================================================
    # DETEKSI TANGAN TERBUKA (untuk Swipe — tidak diubah)
    # ========================================================
    def _is_hand_open(self, landmarks, frame_w, frame_h):
        """
        GERBANG 1: Menggunakan Euclidean Distance.
        Kebal terhadap rotasi! Jari lurus jika jarak ujung jari 
        ke pergelangan > jarak sendi tengah ke pergelangan.
        """
        wrist = landmarks[0]
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        open_count = 0

        for tip, pip in zip(finger_tips, finger_pips):
            dist_tip = self._calc_dist(wrist, landmarks[tip], frame_w, frame_h)
            dist_pip = self._calc_dist(wrist, landmarks[pip], frame_w, frame_h)
            if dist_tip > dist_pip:
                open_count += 1
                
        return open_count >= 3

    # ========================================================
    # DETEKSI SHAKA POSE 🤙 (Jempol + Kelingking terbuka)
    # ========================================================
    def _is_shaka_pose(self, landmarks, w, h):
        """
        Deteksi Pose Shaka (🤙): Jempol & Kelingking terbuka, 
        Telunjuk, Tengah, Manis menekuk.
        """
        wrist = landmarks[0]
        d = self._calc_dist  # alias singkat

        # Jempol harus terbuka (tip > MCP dari wrist)
        thumb_open = d(wrist, landmarks[4], w, h) > d(wrist, landmarks[2], w, h)
        # Kelingking harus terbuka (tip > PIP dari wrist)
        pinky_open = d(wrist, landmarks[20], w, h) > d(wrist, landmarks[18], w, h)

        # Telunjuk, tengah, manis harus menekuk (tip < PIP dari wrist)
        index_curled = d(wrist, landmarks[8], w, h) < d(wrist, landmarks[6], w, h)
        middle_curled = d(wrist, landmarks[12], w, h) < d(wrist, landmarks[10], w, h)
        ring_curled = d(wrist, landmarks[16], w, h) < d(wrist, landmarks[14], w, h)

        return thumb_open and pinky_open and index_curled and middle_curled and ring_curled

    # ========================================================
    # DETEKSI TELUNJUK SAJA ☝️ (Index Finger Pointing)
    # ========================================================
    def _is_index_pointing(self, landmarks, w, h):
        """
        Deteksi Pose Telunjuk Saja (☝️):
        Telunjuk tegak/terbuka.
        Jempol, tengah, manis, kelingking harus menekuk/curled.
        """
        wrist = landmarks[0]
        d = self._calc_dist

        # Telunjuk harus terbuka (tip > PIP dari wrist)
        index_open = d(wrist, landmarks[8], w, h) > d(wrist, landmarks[6], w, h)

        # Jari-jari lainnya (tengah, manis, kelingking) harus menekuk (tip < PIP dari wrist)
        middle_curled = d(wrist, landmarks[12], w, h) < d(wrist, landmarks[10], w, h)
        ring_curled = d(wrist, landmarks[16], w, h) < d(wrist, landmarks[14], w, h)
        pinky_curled = d(wrist, landmarks[20], w, h) < d(wrist, landmarks[18], w, h)

        # Jempol ditekuk (tip (4) ke wrist (0) kurang dari 1.15 kali jarak sendi IP (3) ke wrist (0))
        thumb_curled = d(wrist, landmarks[4], w, h) < d(wrist, landmarks[3], w, h) * 1.15

        return index_open and middle_curled and ring_curled and pinky_curled and thumb_curled

    # ========================================================
    # TOGGLE LASER POINTER (State Machine)
    # ========================================================
    def _detect_laser_toggle(self, landmarks, area_w, area_h):
        """Deteksi Shaka yang ditahan → toggle laser on/off."""
        is_shaka = self._is_shaka_pose(landmarks, area_w, area_h)

        if is_shaka:
            if self.shaka_intent_start is None:
                self.shaka_intent_start = time.time()
            elif not self.shaka_toggled and (time.time() - self.shaka_intent_start >= INTENT_SHAKA_SEC):
                # Toggle state
                self.laser_active = not self.laser_active
                self.shaka_toggled = True  # Cegah re-toggle selama masih ditahan

                # Reset filter setiap kali toggle
                self.filter_x = None
                self.filter_y = None
                self.last_cursor_x = None
                self.last_cursor_y = None

                if self.laser_active:
                    print("🔴 LASER MODE: AKTIF")
                    self._trigger_action("laser_on", COOLDOWN_LASER_TOGGLE_MS)
                else:
                    print("⚫ LASER MODE: NONAKTIF")
                    self._trigger_action("laser_off", COOLDOWN_LASER_TOGGLE_MS)
        else:
            # Pose dilepas → reset intent & izinkan toggle berikutnya
            self.shaka_intent_start = None
            self.shaka_toggled = False

    # ========================================================
    # TRACKING KURSOR DENGAN TELUNJUK (One Euro Filter)
    # ========================================================
    def _track_index_finger(self, landmarks, area_w, area_h):
        """Pindahkan kursor layar mengikuti ujung telunjuk, dihaluskan 1€ Filter."""
        if not self.cursor_callback:
            return

        # Koordinat normalized (0.0–1.0) ujung telunjuk dalam area proses
        raw_x = landmarks[8].x
        raw_y = landmarks[8].y

        # Remap dari Interaction Box ke rentang 0.0–1.0
        box_w = LASER_BOX_X_MAX - LASER_BOX_X_MIN
        box_h = LASER_BOX_Y_MAX - LASER_BOX_Y_MIN
        norm_x = (raw_x - LASER_BOX_X_MIN) / box_w
        norm_y = (raw_y - LASER_BOX_Y_MIN) / box_h
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        # Map ke koordinat layar
        screen_x = norm_x * self.screen_w
        screen_y = norm_y * self.screen_h

        # Inisialisasi filter pada frame pertama
        now = time.time()
        if self.filter_x is None:
            self.filter_x = OneEuroFilter(now, screen_x, LASER_MIN_CUTOFF, LASER_BETA, LASER_D_CUTOFF)
            self.filter_y = OneEuroFilter(now, screen_y, LASER_MIN_CUTOFF, LASER_BETA, LASER_D_CUTOFF)
            self.last_cursor_x = screen_x
            self.last_cursor_y = screen_y

        # Jalankan filter
        filtered_x = self.filter_x(now, screen_x)
        filtered_y = self.filter_y(now, screen_y)

        # Deadzone: abaikan gerakan sub-pixel agar laser diam sempurna
        dx = abs(filtered_x - self.last_cursor_x)
        dy = abs(filtered_y - self.last_cursor_y)
        if dx < LASER_DEADZONE_PX and dy < LASER_DEADZONE_PX:
            return

        self.last_cursor_x = filtered_x
        self.last_cursor_y = filtered_y
        self.cursor_callback(int(filtered_x), int(filtered_y))

    # ========================================================
    # DETEKSI SWIPE (TIDAK DIUBAH dari v2.1)
    # ========================================================
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

    # ========================================================
    # PROCESS FRAME — Pipeline Utama (Routing berdasarkan Mode)
    # ========================================================
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

                lm = hand_landmarks.landmark

                # === SELALU: Cek Shaka untuk toggle laser ===
                self._detect_laser_toggle(lm, area_w, area_h)

                # === ROUTING BERDASARKAN MODE ===
                if self.laser_active:
                    # Mode Laser: hanya gerak kursor jika gestur telunjuk ☝️ terdeteksi
                    if self._is_index_pointing(lm, area_w, area_h):
                        self._track_index_finger(lm, area_w, area_h)
                    else:
                        # Jika tidak ☝️, kursor diam dan filter di-reset untuk mencegah loncatan
                        self.filter_x = None
                        self.filter_y = None
                        self.last_cursor_x = None
                        self.last_cursor_y = None
                else:
                    # Mode Normal: deteksi swipe slide
                    if not self._in_cooldown():
                        self._detect_swipe(hand_label, lm, area_w, area_h)
                    else:
                        self.position_buffer[hand_label].clear()

        return frame

    # ========================================================
    # STATUS (untuk Frontend & Debug)
    # ========================================================
    def get_status(self):
        if self.laser_active:
            return "🔴 Laser Pointer Aktif"
        if self._in_cooldown():
            sisa = int(self.current_cooldown - (time.time()*1000 - self.last_action_time))
            return f"Cooldown... ({sisa}ms)"
        return "Siap"


# ============================================================
# TEST MANDIRI — py gestur_engine.py
# ============================================================
if __name__ == "__main__":
    def on_gesture(action):
        if action == "next":         print("👉 NEXT SLIDE")
        elif action == "prev":       print("👈 PREV SLIDE")
        elif action == "laser_on":   print("🔴 LASER ON")
        elif action == "laser_off":  print("⚫ LASER OFF")

    def on_cursor(x, y):
        print(f"🎯 Cursor → ({x}, {y})")

    engine = GestureEngine(callback=on_gesture, cursor_callback=on_cursor)
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    print("=" * 50)
    print("🤖 TEST GESTURE ENGINE v2.2 (GOD MODE + LASER)")
    print("Kibas tangan KANAN ke kanan = NEXT")
    print("Kibas tangan KIRI  ke kiri  = PREV")
    print("Shaka 🤙 tahan 0.8 detik   = TOGGLE LASER")
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
                if engine.last_action_name == "laser_on":
                    label = "LASER ON"
                elif engine.last_action_name == "laser_off":
                    label = "LASER OFF"
                cv2.putText(frame, label, (w//2 - 80, h//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)

        # Indikator laser mode
        if engine.laser_active:
            cv2.circle(frame, (w - 30, 30), 12, (0, 0, 255), -1)
            cv2.putText(frame, "LASER", (w - 80, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        status = engine.get_status()
        cv2.rectangle(frame, (0, h-40), (w, h), (0,0,0), -1)
        cv2.putText(frame, f"Status: {status} | Adaptif Skala ROI Aktif",
                    (10, h-12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)

        cv2.imshow("Mandor AI v2 - Gesture Engine v2.2", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()