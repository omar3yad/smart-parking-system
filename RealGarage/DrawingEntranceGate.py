import cv2

video_path = "videos/v1.mp4"
cap = cv2.VideoCapture(video_path)

ret, frame = cap.read()
if not ret:
    print("مش قادر اقرأ الفيديو")
    exit()

drawing_frame = frame.copy()
points = []

def draw_line(event, x, y, flags, param):
    global points, drawing_frame
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        if len(points) % 2 == 0:
            cv2.line(drawing_frame, points[-2], points[-1], (0,255,0), 2)
        cv2.imshow("Draw Gate", drawing_frame)

cv2.namedWindow("Draw Gate", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Draw Gate", draw_line)

while True:
    cv2.imshow("Draw Gate", drawing_frame)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()

print("Points")
for i, pt in enumerate(points):
    print(f"Point {i+1}: {pt}")