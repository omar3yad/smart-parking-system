from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import status

from .serializers import VehicleEntrySerializer, VehicleExitSerializer, SlotDisplaySerializer # تأكد من إضافة الـ Exit هنا لو موجودة
from .permissions import IsCameraNode, IsOwnerOrAdmin, IsCameraNode
from .models import ParkingSlot, VehicleLog, Reservation
from django.db.models import Count
from django.utils import timezone
from decimal import Decimal

class VehicleEntryAPIView(APIView):
    permission_classes = [IsCameraNode]
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
    permission_classes = [IsCameraNode]
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
            
            log.total_fee = hours * Decimal(25.00) 
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
    permission_classes = [IsCameraNode]
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
    permission_classes = [permissions.IsAdminUser]
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

class ParkingSlotListAPIView(ListAPIView):
    """
    هذا الـ API يخدم تطبيق الموبايل.
    يعرض قائمة بكل الـ Slots مع إمكانية الفلترة حسب الحالة أو النوع.
    """
    serializer_class = SlotDisplaySerializer

    def get_queryset(self):
        queryset = ParkingSlot.objects.all().order_by('slot_number')
        
        # إمكانية الفلترة: /api/slots/?status=available
        status_param = self.request.query_params.get('status')
        type_param = self.request.query_params.get('type')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if type_param:
            queryset = queryset.filter(slot_type=type_param)
            
        return queryset

class CreateReservationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ReservationSerializer(data=request.data)
        if serializer.is_valid():
            slot = serializer.validated_data['slot']
            
            # 1. إنشاء الحجز وتوليد كود عشوائي
            reservation = serializer.save(
                user=request.user, # يفترض أن المستخدم مسجل دخول
                reservation_code=str(uuid.uuid4())[:8].upper()
            )
            
            # 2. تغيير حالة الـ Slot فوراً إلى محجوز
            slot.status = 'reserved'
            slot.save()
            
            return Response({
                "message": "تم الحجز بنجاح. يرجى الوصول خلال ساعة.",
                "reservation_code": reservation.reservation_code,
                "slot": slot.slot_number
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
