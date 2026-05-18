# ============================================================
# MANDOR AI v2.0 — KONFIGURASI PUSAT
# Ubah nilai di sini untuk tuning tanpa menyentuh logika utama
# ============================================================

# --- KAMERA ---
CAMERA_INDEX = 0          # 0 = kamera utama/webcam bawaan
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# --- GESTUR: KIBASAN (Next/Prev Slide) ---
SWIPE_THRESHOLD_PX = 50      # Min delta X untuk dianggap kibasan

SWIPE_MAX_DURATION_MS = 1000  # Max durasi kibasan (ms), lebih lambat = bukan kibas
SWIPE_MIN_SPEED = 150  # Kecepatan minimum kibasan (pixel per detik)

# --- GESTUR: ANCANG-ANCANG (durasi dalam detik) ---
INTENT_FIST_SEC = 0.8     # Kepalan untuk Start Presentation
INTENT_CROSS_SEC = 1.0    # Kedua tangan di dada untuk Close
INTENT_GUN_SEC = 0.8      # Pose pistol untuk Laser Pointer

# --- GESTUR: FINGER SNAP (Blackout/Whiteout) ---
SNAP_DISTANCE_CLOSED = 20  # Jarak jempol-jari tengah saat menempel (px)
SNAP_DISTANCE_OPEN = 80    # Jarak jempol-jari tengah setelah snap (px)
SNAP_MAX_FRAMES = 3        # Max frame untuk transisi snap

# --- COOLDOWN (dalam milidetik) ---
COOLDOWN_SWIPE_MS = 500
COOLDOWN_START_MS = 2000
COOLDOWN_CLOSE_MS = 2000
COOLDOWN_SNAP_MS = 1500
COOLDOWN_LASER_MS = 0      # Laser tidak butuh cooldown (mode kontinu)

# --- OBJECT LOCKING ---
YOLO_CONFIDENCE = 0.5
LOCK_LOST_SEC = 3          # Toleransi presenter hilang dari frame

# --- MEDIAPIPE ---
MP_DETECTION_CONFIDENCE = 0.7
MP_TRACKING_CONFIDENCE = 0.7