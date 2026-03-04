from rest_framework import serializers
from .models import VehicleLog

class VehicleEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleLog
        # نحدد الحقول التي سترسلها الكاميرا
        fields = ['license_plate', 'entry_image']
        
    def create(self, validated_data):
        # هنا يمكنك إضافة Logic إضافي قبل الحفظ (مثل التأكد من القوائم السوداء)
        return super().create(validated_data)

class VehicleExitSerializer(serializers.Serializer):
    license_plate = serializers.CharField(max_length=20)
    exit_image = serializers.ImageField()

class SlotStatusUpdateSerializer(serializers.Serializer):
    # قائمة من أرقام الـ slots وحالتها الجديدة
    slot_id = serializers.CharField() 
    is_occupied = serializers.BooleanField() # True = مشغول، False = فاضي