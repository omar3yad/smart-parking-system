import cv2 as cv
import pickle
import numpy as np



try:
    with open('CarParkPos', 'rb') as f:
        posList = pickle.load(f)
except:
    posList = []

current_polygon = []
NVR_RTSP_URL = "rtsp://admin:password123@192.168.1.64:554/ch1/main"
#cap = cv.VideoCapture(NVR_RTSP_URL)
cap = cv.VideoCapture("../videos/D13.MP4")
ret, frame = cap.read()

if ret:
    cv.imwrite("frame/park1.png", frame)

cap.release()
def mouseClick(event, x, y, flags, param):
    global current_polygon, posList

    # كليك شمال: رسم نقطة جديدة
    if event == cv.EVENT_LBUTTONDOWN:
        current_polygon.append((x, y))

    # كليك يمين: مسح مضلع كامل تم حفظه
    elif event == cv.EVENT_RBUTTONDOWN:
        for i, slot in enumerate(posList):
            pts = np.array(slot["points"], np.int32)
            # التأكد إذا كان مكان الضغطة داخل المضلع
            dist = cv.pointPolygonTest(pts, (x, y), False)
            if dist >= 0:
                posList.pop(i)  # مسح المضلع من القائمة
                # تحديث ملف الـ pickle فوراً
                with open('CarParkPos', 'wb') as f:
                    pickle.dump(posList, f)
                break


img = cv.imread('frame/park1.png')

cv.namedWindow('Img', cv.WINDOW_NORMAL)
cv.resizeWindow('Img', 1100, 750)
cv.setMouseCallback('Img', mouseClick)

while True:
    img_copy = img.copy()

    # رسم الـ Slots المحفوظة
    for slot in posList:
        pts = np.array(slot["points"], np.int32)
        cv.polylines(img_copy, [pts], True, (255, 0, 255), 2)

    # Draw Slot ID
        cv.putText(img_copy,
               slot["id"],
               tuple(slot["points"][0]),
               cv.FONT_HERSHEY_SIMPLEX,
               0.7,
               (255, 0, 255),
               2)

    # رسم المضلع الحالي اللي لسه بيترسم
    if len(current_polygon) > 1:
        pts = np.array(current_polygon, np.int32)
        cv.polylines(img_copy, [pts], False, (0, 255, 0), 2)

    # رسم النقط اللي بنحطها حالياً
    for p in current_polygon:
        cv.circle(img_copy, p, 4, (0, 255, 0), -1)

    cv.imshow('Img', img_copy)

    key = cv.waitKey(1) & 0xFF

    if key == ord('z'):  # تراجع عن آخر نقطة
        if current_polygon:
            current_polygon.pop()

    elif key == ord('r'):  # مسح الشكل الحالي (قبل الحفظ)
        current_polygon.clear()

    elif key == ord('s'):  # حفظ الشكل
        if len(current_polygon) > 2:

            slot_id = f"A{len(posList)+1}"

            posList.append({
            "id": slot_id,
            "points": current_polygon.copy()
        })

        with open('CarParkPos', 'wb') as f:
            pickle.dump(posList, f)

        current_polygon.clear()
        print(f"Slot {slot_id} Saved!")

    elif key == ord('q') or key == 27:
        break

cv.destroyAllWindows()