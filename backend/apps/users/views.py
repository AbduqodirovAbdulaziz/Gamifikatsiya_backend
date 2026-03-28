from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import StudentProfile, TeacherProfile
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserPublicSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    FCMTokenSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
)
from .permissions import IsOwner

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get("username") or attrs.get("email")
        password = attrs.get("password")

        if not username or not password:
            raise InvalidToken("Username va parol talab qilinadi")

        user = User.objects.filter(username=username).first()

        if not user:
            raise InvalidToken("Username yoki parol noto'g'ri")

        if not user.check_password(password):
            raise InvalidToken("Username yoki parol noto'g'ri")

        if not user.is_active:
            raise InvalidToken("Bu foydalanuvchi faol emas")

        refresh = self.get_token(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Ro'yxatdan muvaffaqiyatli o'tdingiz",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserProfileUpdateSerializer
        return UserSerializer


class UserPublicView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserPublicSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(User, id=self.kwargs["pk"])


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"message": "Parol muvaffaqiyatli o'zgartirildi"})


class AvatarUploadView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if "avatar" not in request.FILES:
            return Response(
                {"error": "Rasm yuklanmadi"}, status=status.HTTP_400_BAD_REQUEST
            )

        request.user.avatar = request.FILES["avatar"]
        request.user.save()
        return Response(
            {
                "message": "Avatar muvaffaqiyatli yuklandi",
                "avatar_url": request.user.avatar.url,
            }
        )


class FCMTokenView(generics.UpdateAPIView):
    serializer_class = FCMTokenSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.fcm_token = serializer.validated_data["fcm_token"]
        request.user.save()
        return Response({"message": "FCM token saqlandi"})


class StudentProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_object(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return profile


class TeacherProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_object(self):
        profile, _ = TeacherProfile.objects.get_or_create(user=self.request.user)
        return profile
