import cv2
import time
import os
from ultralytics import YOLO
import math
from APIClient import APIClient
import numpy as np

class EntranceSystem:

    def __init__(self, source, car_model_path,
                 plate_detection_model_path,
                 plate_recognition_model_path,
                 save_dir="captures"):

        self.cap = cv2.VideoCapture(source)

        self.car_model = YOLO(car_model_path)
        self.plate_model = YOLO(plate_detection_model_path)
        self.plate_recognition = YOLO(plate_recognition_model_path)

        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

        self.processed_ids = set()

        self.line_y_position = 0.2
        self.roi_start_x = 0.18
        self.roi_end_x = 0.70
        self.api = APIClient("backend_url")

        cv2.namedWindow("Entrance System", cv2.WINDOW_NORMAL)

    # =============================
    # Save Cropped Car
    # =============================
    def save_car(self, car_crop, track_id):
        if car_crop.size == 0:
            print("Empty crop ❌")
            return None

        filename = f"{self.save_dir}/car_{track_id}_{int(time.time())}.jpg"
        cv2.imwrite(filename, car_crop)
        print("Saved:", filename)
        return filename

    # =============================
    # Plate Detection + Draw
    # =============================
    def detect_and_draw_plate(self, frame):

        h, w = frame.shape[:2]

        roi_x1 = int(w * self.roi_start_x)
        roi_x2 = int(w * self.roi_end_x)

        plate_results = self.plate_model(frame, verbose=False)

        for r in plate_results:
            for box in r.boxes:

                px1, py1, px2, py2 = map(int, box.xyxy[0])

                if px2 <= px1 or py2 <= py1:
                    continue
                plate_cx = (px1 + px2) // 2
                if plate_cx < roi_x1 or plate_cx > roi_x2:
                    continue

                plate_crop = frame[py1:py2, px1:px2]
                if plate_crop.size == 0:
                    continue
                cv2.rectangle(frame,
                              (px1, py1),
                              (px2, py2),
                              (0, 255, 0), 3)

                plate_text = self.recognize_plate(
                    plate_crop,
                    frame,
                    px1,
                    py1
                )

                if not plate_text:
                    plate_text = "Unknown"
                print("✅ Plate predicted (ROI): "+plate_text)

                return plate_text

        return None
    def recognize_plate(self,plate_crop,frame,abs_x1,abs_y1):
        ocr_results = self.plate_recognition(plate_crop, verbose=False)

        plate_text = ""

        for ocr_res in ocr_results:

            if ocr_res.boxes is None:
                continue

            chars = ocr_res.boxes.data.tolist()
            chars.sort(key=lambda x: x[0])

            for char in chars:
                cls_id = int(char[5])
                plate_text += str(ocr_res.names[cls_id])

        if plate_text:
            cv2.putText(frame,
                        plate_text,
                        (abs_x1, abs_y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 255, 0),
                        2)

        return plate_text

    def get_best_frame(self, num_frames=5):
        best_frame = None
        best_score = 0

        for _ in range(num_frames):
            ret, frame = self.cap.read()
            if not ret:
                break

            score = self.sharpness_score(frame)

            if score > best_score:
                best_score = score
                best_frame = frame.copy()

        print("Best frame sharpness score:", best_score)
        return best_frame

    def crop_car_from_frame(self, frame, x1, y1, x2, y2, pad=0):
        h, w = frame.shape[:2]

        x1_new = max(0, x1 - pad)
        y1_new = max(0, y1 - pad)
        x2_new = min(w, x2 + pad)
        y2_new = min(h, y2 + pad)

        car_crop = frame[y1_new:y2_new, x1_new:x2_new]
        return car_crop
    def sharpness_score(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def is_crossing_line(self, point, line_start, line_end):
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end

        # معادلة الخط
        position = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)

        return position > 0
    # =============================
    # Main
    # =============================

    def run(self):

        while True:

            ret, frame = self.cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]

            start_x = int(w * self.roi_start_x)
            end_x = int(w * self.roi_end_x)
            trigger_line_y = int(h * self.line_y_position)

            start_left = (2, 564)
            end_left = (1696, 364)
            cv2.line(frame, start_left, end_left, (0, 255, 0), 3)
            start_right = (2180, 1668)
            end_right = (2331, 467)
            cv2.line(frame, start_right, end_right, (0, 255, 0), 3)
            start_trigger = (800, 741)
            end_trigger = (2244, 1063)
            cv2.line(frame, start_trigger,
                     end_trigger, (0, 0, 255), 3)

            roi_x1 = int(w * self.roi_start_x)
            roi_x2 = int(w * self.roi_end_x)
            roi_polygon = np.array([
                start_left,
                end_left,
                end_right,
                start_right
            ], dtype=np.int32)
            mask = np.zeros(frame.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [roi_polygon], 255)
            roi_frame = cv2.bitwise_and(frame, frame, mask=mask)
            # ================= TRACKING INSIDE ROI ONLY =================
            results = self.car_model.track(
                roi_frame,
                persist=True,
                classes=[2],
                conf=0.5,
                verbose=False
            )

            if results[0].boxes.id is not None:

                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)

                for box, track_id in zip(boxes, track_ids):

                    x1, y1, x2, y2 = map(int, box)
                    x1 += roi_x1
                    x2 += roi_x1

                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    # if cv2.pointPolygonTest(roi_polygon, (cx, cy), False) < 0:
                    #     continue
                    # if not (roi_x1 <= cx <= roi_x2):
                    #     continue

                    cv2.rectangle(frame,
                                  (x1, y1),
                                  (x2, y2),
                                  (255, 0, 0), 2)
                    if self.is_crossing_line((cx, cy), start_trigger, end_trigger) \
                            and track_id not in self.processed_ids:

                        print(f"\nENTRY Car ID: {track_id}")
                        best_frame = self.get_best_frame()
                        plate_text = self.detect_and_draw_plate(best_frame)
                        best_car_crop = self.crop_car_from_frame(best_frame,x1, y1, x2, y2)

                        cv2.namedWindow("Best Frame - Plate Detection", cv2.WINDOW_NORMAL)
                        cv2.imshow("Best Frame - Plate Detection", best_frame)

                        cv2.waitKey(1)
                        if best_car_crop is None:
                            continue

                        image_path = self.save_car(best_car_crop, track_id)
                        # self.api.send_to_backend(image_path,plate_text)
                        self.processed_ids.add(track_id)

            cv2.imshow("Entrance System", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()

