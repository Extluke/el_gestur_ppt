import cv2
import mediapipe as mp
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import time
import csv

print("==================================================")
print("🧪 SELAMAT DATANG DI LAB KALIBRASI GESTUR EL PRESENTASI")
print("==================================================")

# Inisialisasi Model
print("⏳ Loading YOLOv8 & DeepSORT...")
yolo_model = YOLO('yolov8n.pt')
tracker = DeepSort(max_age=30, n_init=3) # Dibuat ringan untuk lab

print("⏳ Setup MediaPipe Hands (Full Frame Context)...")
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=4,        # Deteksi sampai 4 tangan di ruangan
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

locked_id = None
csv_filename = "data_kalibrasi_gestur.csv"

# Siapkan file CSV untuk mencatat data log lu
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Pose", "Sudut_Telunjuk", "Sudut_Tengah", "Sudut_Manis", "Sudut_Kelingking", "Jarak_Jempol_ke_Pusat"])

def calculate_angle(a, b, c):
    """
    Rumus Trigonometri Vektor untuk menghitung sudut engsel jari.
    a, b, c adalah koordinat [x, y]. Sudut dihitung pada titik 'b' (Engsel).
    Jika lurus = ~180 derajat. Jika menekuk = < 90 derajat.
    """
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

def distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))

cap = cv2.VideoCapture(0) # Ganti sesuai CAMERA_INDEX lu

print("✅ LAB SIAP! Buka jendela kamera untuk mulai kalibrasi.")

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    # 1. Yolo & DeepSORT (Mencari Presenter)
    results = yolo_model(frame, classes=[0], conf=0.5, verbose=False)
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            if (x2 - x1) > 40 and (y2 - y1) > 100: # Filter ukuran
                detections.append(([int(x1), int(y1), int(x2-x1), int(y2-y1)], box.conf[0].item(), 'person'))
    
    tracks = tracker.update_tracks(detections, frame=frame)
    presenter_box = None

    for track in tracks:
        if not track.is_confirmed(): continue
        tid = str(track.track_id)
        tx1, ty1, tx2, ty2 = map(int, track.to_ltrb())
        
        # Gambar kotak untuk semua orang
        cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (100, 100, 100), 1)
        
        if not locked_id:
            # Auto-Lock siapa yang ada di tengah (Sederhana untuk Lab)
            cx = (tx1 + tx2) // 2
            if int(w*0.4) < cx < int(w*0.6):
                locked_id = tid
        
        if locked_id == tid:
            presenter_box = (tx1, ty1, tx2, ty2)
            cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (0, 255, 0), 2)
            cv2.putText(frame, "PRESENTER", (tx1, ty1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 2. MediaPipe (Mendeteksi Tangan Secara GLOBAL)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hand_results = hands.process(rgb_frame)

    if hand_results.multi_hand_landmarks and presenter_box:
        px1, py1, px2, py2 = presenter_box
        
        for hand_landmarks in hand_results.multi_hand_landmarks:
            # Ambil koordinat Pergelangan Tangan (Landmark 0)
            wrist_x = int(hand_landmarks.landmark[0].x * w)
            wrist_y = int(hand_landmarks.landmark[0].y * h)
            
            # 🔥 SYARAT 1: FILTER SPASIAL (Hanya proses jika tangan ada di dalam/dekat kotak Presenter)
            margin = 150 # Margin tambahan karena tangan sering merentang ke luar badan
            if not ((px1 - margin) < wrist_x < (px2 + margin) and (py1 - margin) < wrist_y < (py2 + margin)):
                # Gambar titik merah (Tangan Audiens diabaikan)
                cv2.circle(frame, (wrist_x, wrist_y), 8, (0, 0, 255), -1)
                continue
            
            # Jika lolos, ini adalah Tangan Presenter!
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # EKSTRAKSI DATA (Koordinat)
            lm = hand_landmarks.landmark
            pts = [(l.x * w, l.y * h) for l in lm]
            
            # MENGHITUNG SUDUT ENGSEL JARI (Titik 0 -> MCP -> Ujung Jari)
            # Semakin lurus jari, sudut mendekati 180. Semakin menekuk, mendekati 0.
            angle_index = calculate_angle(pts[0], pts[5], pts[8])
            angle_middle = calculate_angle(pts[0], pts[9], pts[12])
            angle_ring = calculate_angle(pts[0], pts[13], pts[16])
            angle_pinky = calculate_angle(pts[0], pts[17], pts[20])
            
            # MENGHITUNG RASIO JEMPOL KE PUSAT TELAPAK
            palm_center = pts[9] # Pangkal jari tengah sebagai pusat
            palm_width = distance(pts[5], pts[17]) + 1e-6
            dist_thumb = distance(pts[4], palm_center) / palm_width # Dinormalisasi
            
            # TAMPILKAN TELEMETRI DI LAYAR
            y_offset = 30
            cv2.putText(frame, f"Telunjuk : {int(angle_index)} deg", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Tengah   : {int(angle_middle)} deg", (10, y_offset+30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Manis    : {int(angle_ring)} deg", (10, y_offset+60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Kelingking: {int(angle_pinky)} deg", (10, y_offset+90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Jempol Rasio: {dist_thumb:.2f}", (10, y_offset+120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # 🚨 SISTEM PENCATATAN DATA BERDASARKAN TOMBOL KEYBOARD
            key = cv2.waitKey(1) & 0xFF
            pose_name = None
            if key == ord('1'): pose_name = "NEXT_SLIDE"
            elif key == ord('2'): pose_name = "PREV_SLIDE"
            elif key == ord('3'): pose_name = "START_PRESENTATION"
            elif key == ord('4'): pose_name = "END_PRESENTATION (KON)"
            elif key == ord('5'): pose_name = "LASER_POINTER"
            
            if pose_name:
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([pose_name, int(angle_index), int(angle_middle), int(angle_ring), int(angle_pinky), round(dist_thumb, 2)])
                print(f"✅ DATA TERSIMPAN: {pose_name} | Telunjuk:{int(angle_index)} | Jempol Rasio:{dist_thumb:.2f}")

    # UI Bantuan
    cv2.putText(frame, "TEKAN TOMBOL UNTUK REKAM DATA:", (w-350, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    cv2.putText(frame, "1:Next | 2:Prev | 3:Start | 4:End(Kon) | 5:Laser", (w-350, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

    cv2.imshow("Lab Kalibrasi Gestur", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"✅ Sesi Lab selesai. Data telah disimpan di {csv_filename}")