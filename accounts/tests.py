from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, UserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,) # أي حد يقدر يسجل حساب
    serializer_class = RegisterSerializer

# الـ Login بيتم عن طريق TokenObtainPairView الجاهزة من JWT