import requests

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
    def send_to_backend(self, image_path, plate_text):

        with open(image_path, "rb") as img:
            files = {
                "car_image": img
            }
            data = {
                "plate_number": plate_text,
                "camera_id": "ENTRANCE_CAM_1"
            }

            response = requests.post(self.base_url, files=files, data=data)

        if response.status_code == 200:
            print("✅ Sent to backend successfully")
        else:
            print("❌ Backend error:", response.text)