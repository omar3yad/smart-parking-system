import cv2
import pickle
import numpy as np
import time
import requests
import os
from ultralytics import YOLO

# --- إعدادات الاتصال والمسارات ---
# تأكد من مطابقة الكود السري الموجود في Django (permissions.py)
DJANGO_API_URL = "http://127.0.0.1:8000/api/slots/update/"
HEADERS = {'X-Camera-Key': 'my_ultra_secure_camera_token_2026'} 

# إعدادات الموديل
model = YOLO('yolov8n.pt') 

# تحميل إحداثيات الأماكن
try:
    with open('CarParkPos', 'rb') as f:
        polygons = pickle.load(f)
except FileNotFoundError:
    print("Error: 'CarParkPos' file not found.")
    polygons = []

# إعداد الفيديو (أو الكاميرا)
cap = cv2.VideoCapture('../videos/D13.mp4')

def run_ai_service():
    """
    الدالة الرئيسية لمعالجة الفيديو وإرسال الحالة لـ Django
    """
    print("AI Parking Monitoring Service Started...")
    
    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            time.sleep(1)
            continue

        # معالجة الموديل
        results = model.predict(frame, conf=0.5, classes=[2, 7], verbose=False)
        detections = results[0].boxes.data.tolist()
        car_centers = [(int((d[0] + d[2]) / 2), int((d[1] + d[3]) / 2)) for d in detections]

        # تجهيز البيانات
        django_payload = []
        for entry in polygons:
            slot_id = str(entry['id'])
            poly_points = np.array(entry['points'], np.int32)
            is_occupied = False

            for center in car_centers:
                if cv2.pointPolygonTest(poly_points, center, False) >= 0:
                    is_occupied = True
                    break
            
            django_payload.append({
                "slot_id": slot_id, 
                "is_occupied": is_occupied
            })
        
        # إرسال البيانات لـ Django Backend
        try:
            response = requests.post(
                DJANGO_API_URL, 
                json=django_payload, 
                headers=HEADERS,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"[SUCCESS] Updated {len(django_payload)} slots.")
            else:
                print(f"[WARNING] Server returned status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Could not connect to Django: {e}")

        # انتظار 5 ثوانٍ قبل التحديث القادم
        time.sleep(5)

if __name__ == "__main__":
    try:
        run_ai_service()
    except KeyboardInterrupt:
        print("\nAI Service stopped by user.")
    finally:
        cap.release()