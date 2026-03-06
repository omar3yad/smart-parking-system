from django.contrib.auth.models import User
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer, UserSerializer

# 1. فيو التسجيل (Register)
class RegisterView(generics.CreateAPIView):
    """
    هذا الـ API يسمح للمستخدمين الجدد بإنشاء حساب.
    يستخدم الـ Serializer للتحقق من قوة كلمة المرور وتطابقها.
    """
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,) # مسموح للجميع بالوصول
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserSerializer(user).data,
                "message": "تم إنشاء الحساب بنجاح. يمكنك الآن تسجيل الدخول.",
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 2. فيو الملف الشخصي (Profile)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    هذا الـ API يسمح للمستخدم المسجل فقط برؤية وتعديل بياناته الشخصية.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated] # لا بد من وجود Token

    def get_object(self):
        return self.request.user

# 3. فيو التحقق من التوكن (اختياري - مفيد جداً للموبايل)
class CheckAuthView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({"status": "Authenticated", "user": request.user.username})