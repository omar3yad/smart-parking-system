import cv2
import torch
from ultralytics import YOLO
from collections import deque
import os

# ================= GPU CHECK =================
device = "cuda" if torch.cuda.is_available() else "cpu"
# Load model on GPU
model = YOLO("Models/car_detection/yolov8m.pt")
model.to(device)

# ================= VIDEO =================
video_path = r"D:\garage\v4.mp4"
cap = cv2.VideoCapture(video_path)

fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# ================= SETTINGS =================
pre_seconds = 3
post_seconds = 3

pre_frames = fps * pre_seconds
post_frames = fps * post_seconds

frame_buffer = deque(maxlen=pre_frames)

save_folder = "car_clips"
os.makedirs(save_folder, exist_ok=True)

# ================= ROI =================
start_left = (50, 1153)
end_left = (1181, 745)
start_right = (2021, 1773)
end_right = (2285, 876)

xmin = min(start_left[0], end_left[0], start_right[0], end_right[0])
xmax = max(start_left[0], end_left[0], start_right[0], end_right[0])
ymin = min(start_left[1], end_left[1], start_right[1], end_right[1])
ymax = max(start_left[1], end_left[1], start_right[1], end_right[1])

print(f"ROI: xmin={xmin}, xmax={xmax}, ymin={ymin}, ymax={ymax}")

# ================= RECORDING =================
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
recording = False
frames_after_detection = 0
video_number = 0
out = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_buffer.append(frame.copy())

    # Crop ROI
    roi = frame[ymin:ymax, xmin:xmax]

    results = model(roi, verbose=False)

    car_detected = False

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]
            if label == "car":
                car_detected = True
                break

    # ================= IF CAR DETECTED =================
    if car_detected:

        frames_after_detection = post_frames

        if not recording:
            video_number += 1
            filename = os.path.join(save_folder, f"car_{video_number}.mp4")
            out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
            recording = True

            # write 3 sec before detection
            for buffered_frame in frame_buffer:
                out.write(buffered_frame)

            print(f"Started Recording: {filename}")

    # ================= IF RECORDING =================
    if recording:
        out.write(frame)

        if not car_detected:
            frames_after_detection -= 1

        if frames_after_detection <= 0:
            print(f"Stopped Recording: {filename}")
            recording = False
            out.release()
            out = None

cap.release()
if out:
    out.release()

print("Done ✅")