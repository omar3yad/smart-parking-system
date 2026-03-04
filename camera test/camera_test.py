import requests

# عنوان الـ API (تأكد أن السيرفر يعمل: python manage.py runserver)
URL = "http://127.0.0.1:8000/api/entry/"

def simulate_camera_entry(image_path, plate_number):
    try:
        # فتح الصورة بنظام البايت (Binary Mode)
        with open(image_path, 'rb') as img:
            # تجهيز البيانات المرسلة (الرقم + الصورة)
            data = {
                "license_plate": plate_number
            }
            files = {
                "entry_image": img
            }

            print(f"[*] Sending data for vehicle: {plate_number}...")
            
            # إرسال طلب الـ POST
            response = requests.post(URL, data=data, files=files)

            # فحص النتيجة
            if response.status_code == 201:
                print("[+] Success!")
                print("Server Response:", response.json())
            else:
                print(f"[-] Failed! Status Code: {response.status_code}")
                print("Error Details:", response.text)

    except FileNotFoundError:
        print("[-] Error: Image file not found.")
    except requests.exceptions.ConnectionError:
        print("[-] Error: Could not connect to the server. Is it running?")

def simulate_camera_exit(image_path, plate_number):
    URL_EXIT = "http://127.0.0.1:8000/api/exit/"
    with open(image_path, 'rb') as img:
        data = {"license_plate": plate_number}
        files = {"exit_image": img}
        response = requests.post(URL_EXIT, data=data, files=files)
        print(response.json())

def simulate_slots_camera(camera_slots_data):
    URL = "http://127.0.0.1:8000/api/slots/update/"
    # البيانات المرسلة من كاميرا واحدة تغطي 3 أماكن مثلاً
    response = requests.post(URL, json=camera_slots_data)
    print(response.json())

# تجربة: الكاميرا شافت إن A1 و A2 مشغولين، و A3 فضي
camera_1_view = [
    {"slot_id": "1", "is_occupied": True},
    {"slot_id": "3", "is_occupied": True},
    {"slot_id": "2", "is_occupied": False},
]

# simulate_slots_camera(camera_1_view)
# جرب تشغله بعد ما تكون عملت Entry لنفس الرقم
if __name__ == "__main__":
    # محاكاة دخول عربة بلوحة "Cairo 123"
    # simulate_camera_entry("car.jpg", "Cairo 123")
    # simulate_camera_exit("car_exit.jpg", "Cairo 123")
    simulate_slots_camera(camera_1_view)