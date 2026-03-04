from django.urls import path
from .views import VehicleEntryAPIView
from .views import VehicleExitAPIView
from .views import BulkSlotUpdateAPIView
from .views import ParkingStatusAPIView


urlpatterns = [
    path('api/entry/', VehicleEntryAPIView.as_view(), name='vehicle-entry'),
    path('api/exit/', VehicleExitAPIView.as_view(), name='vehicle-exit'),
    path('api/slots/update/', BulkSlotUpdateAPIView.as_view(), name='bulk-slot-update'),
    path('api/status/summary/', ParkingStatusAPIView.as_view(), name='parking-summary'),
]