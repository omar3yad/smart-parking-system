from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.utils import timezone
from django.db.models import Count
from decimal import Decimal

from .serializers import VehicleEntrySerializer, VehicleExitSerializer # تأكد من إضافة الـ Exit هنا لو موجودة
from .models import VehicleLog  # تأكد أن اسم الموديل عندك هو VehicleLog
from .models import ParkingSlot


class VehicleEntryAPIView(APIView):
    """
    هذا الـ Endpoint مخصص لكاميرا الدخول فقط.
    يستقبل صورة ورقم اللوحة ويقوم بفتح سجل جديد.
    """
    def post(self, request, *args, **kwargs):
        serializer = VehicleEntrySerializer(data=request.data)
        
        if serializer.is_valid():
            # حفظ البيانات في PostgreSQL (رقم اللوحة، الصورة، الوقت تلقائياً)
            vehicle_log = serializer.save()
            
            return Response({
                "status": "success",
                "message": "Vehicle entry recorded",
                "log_id": vehicle_log.id,
                "entry_time": vehicle_log.entry_time
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VehicleExitAPIView(APIView):
    def post(self, request):
        serializer = VehicleExitSerializer(data=request.data)
        if serializer.is_valid():
            plate = serializer.validated_data['license_plate']
            image = serializer.validated_data['exit_image']

            # 1. البحث عن آخر سجل دخول لهذه العربة ولم يخرج بعد
            log = VehicleLog.objects.filter(license_plate=plate, exit_time__isnull=True).last()

            if not log:
                return Response({"error": "Vehicle not found in garage"}, status=status.HTTP_404_NOT_FOUND)

            # 2. تسجيل وقت الخروج وصورة الخروج
            log.exit_time = timezone.now()
            log.exit_image = image

            # 3. حساب التكلفة (مثال: 10 جنيه لكل ساعة أو جزء منها)
            duration = log.exit_time - log.entry_time
            hours = Decimal(duration.total_seconds() / 3600).quantize(Decimal('1.00'))
            if hours < 1: hours = 1 # الحد الأدنى ساعة
            
            log.total_fee = hours * Decimal(10.00) 
            log.is_paid = True # نفترض الدفع عند المخرج حالياً
            log.save()

            return Response({
                "status": "success",
                "entry_time": log.entry_time,
                "exit_time": log.exit_time,
                "duration_hours": hours,
                "total_fee": log.total_fee
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BulkSlotUpdateAPIView(APIView):
    """
    هذا الـ API يستقبل بيانات من كاميرات الـ Slots الـ 6.
    كل كاميرا تبعت لستة بالـ slots اللي هي شايفاها وحالتهم.
    """
    def post(self, request):
        # نتوقع استقبال List من الأماكن
        data = request.data # مثال: [{"slot_id": "A1", "is_occupied": True}, ...]
        
        if not isinstance(data, list):
            return Response({"error": "Expected a list of slots"}, status=400)

        updated_slots = []
        for item in data:
            slot_no = item.get('slot_id')
            occupied = item.get('is_occupied')
            
            # تحديث الحالة في الداتا بيز
            new_status = 'occupied' if occupied else 'available'
            
            # احترافية: لا نغير الحالة لو كانت 'reserved' (محجوزة من التطبيق) 
            # إلا لو العربية فعلاً ركنت (بناءً على بزنس لوجيك مشروعك)
            count = ParkingSlot.objects.filter(slot_number=slot_no).update(status=new_status)
            if count > 0:
                updated_slots.append(slot_no)

        return Response({
            "status": "success",
            "updated_slots": updated_slots,
            "message": f"Successfully updated {len(updated_slots)} slots"
        })

class ParkingStatusAPIView(APIView):
    """
    هذا الـ API يعطي ملخص كامل لحالة الجراج:
    العدد الكلي، المتاح، المشغول، والمحجوز.
    """
    def get(self, request):
        # 1. جلب إحصائيات الحالات من الداتا بيز مباشرة
        stats = ParkingSlot.objects.values('status').annotate(total=Count('status'))
        
        # 2. تجهيز قاموس بالقيم الافتراضية
        summary = {
            "total_slots": ParkingSlot.objects.count(),
            "available": 0,
            "occupied": 0,
            "reserved": 0
        }
        
        # 3. ملء البيانات بناءً على نتيجة الداتا بيز
        for item in stats:
            if item['status'] == 'available':
                summary['available'] = item['total']
            elif item['status'] == 'occupied':
                summary['occupied'] = item['total']
            elif item['status'] == 'reserved':
                summary['reserved'] = item['total']
        
        return Response(summary)