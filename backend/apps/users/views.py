import logging

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import models

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
from .permissions import IsOwner, IsParent

User = get_user_model()
logger = logging.getLogger(__name__)


def get_parent_children_queryset(parent_user):
    return User.objects.filter(parent=parent_user, role="student").distinct()


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


class ParentChildListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsParent]
    serializer_class = UserPublicSerializer

    def get_queryset(self):
        return get_parent_children_queryset(self.request.user)

    def list(self, request, *args, **kwargs):
        from apps.gamification.services import GamificationService

        children = self.get_queryset()
        children_data = []

        for child in children:
            try:
                profile = child.student_profile
                xp_progress = GamificationService.get_xp_progress(profile.xp_points)
                children_data.append(
                    {
                        "id": str(child.id),
                        "username": child.username,
                        "avatar": child.avatar.url if child.avatar else None,
                        "level": profile.level,
                        "xp_points": profile.xp_points,
                        "level_title": xp_progress["title"],
                        "streak_days": profile.streak_days,
                        "total_quizzes": profile.total_quizzes_completed,
                    }
                )
            except StudentProfile.DoesNotExist:
                children_data.append(
                    {
                        "id": str(child.id),
                        "username": child.username,
                        "avatar": child.avatar.url if child.avatar else None,
                        "level": 1,
                        "xp_points": 0,
                        "level_title": "Yangi Talaba",
                        "streak_days": 0,
                        "total_quizzes": 0,
                    }
                )

        return Response(children_data)


class ParentChildDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsParent]
    serializer_class = UserSerializer

    def get_object(self):
        child_id = self.kwargs.get("child_id")
        return get_object_or_404(
            get_parent_children_queryset(self.request.user), id=child_id
        )

    def retrieve(self, request, *args, **kwargs):
        child = self.get_object()
        from apps.gamification.services import GamificationService
        from apps.gamification.models import Streak

        try:
            profile = child.student_profile
        except StudentProfile.DoesNotExist:
            profile = None

        xp_progress = GamificationService.get_xp_progress(
            profile.xp_points if profile else 0
        )

        try:
            streak = child.streak
        except Streak.DoesNotExist:
            streak = None

        from apps.quizzes.models import QuizAttempt

        recent_attempts = QuizAttempt.objects.filter(
            student=child, is_completed=True
        ).order_by("-started_at")[:5]

        data = {
            "id": str(child.id),
            "username": child.username,
            "first_name": child.first_name,
            "last_name": child.last_name,
            "avatar": child.avatar.url if child.avatar else None,
            "profile": {
                "xp_points": profile.xp_points if profile else 0,
                "level": profile.level if profile else 1,
                "level_title": xp_progress["title"],
                "coins": profile.coins if profile else 0,
                "streak_days": profile.streak_days if profile else 0,
                "total_quizzes": profile.total_quizzes_completed if profile else 0,
            }
            if profile
            else None,
            "streak": {
                "current_streak": streak.current_streak if streak else 0,
                "longest_streak": streak.longest_streak if streak else 0,
                "last_activity_date": streak.last_activity_date if streak else None,
            }
            if streak
            else None,
            "recent_activity": [
                {
                    "quiz_title": attempt.quiz.title if attempt.quiz else "Noma'lum",
                    "score": attempt.percentage,
                    "completed_at": attempt.completed_at,
                }
                for attempt in recent_attempts
            ],
        }

        return Response(data)


class ParentChildProgressView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsParent]

    def get(self, request, child_id):
        child = get_object_or_404(get_parent_children_queryset(request.user), id=child_id)

        from apps.gamification.services import GamificationService

        # Use shared progress summary service
        progress = GamificationService.get_progress_summary(child_id)
        
        return Response({
            "child_id": str(child.id),
            "username": child.username,
            **progress,  # Include all shared progress data
        })


class ChildSearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsParent]
    serializer_class = UserPublicSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "child_search"

    def get_queryset(self):
        # Backward compatible query support for mobile/web clients.
        query = (
            self.request.query_params.get("q")
            or self.request.query_params.get("search")
            or ""
        ).strip()

        if len(query) < 3:
            return User.objects.none()

        # Search only unlinked students not already linked to this parent.
        linked_children = get_parent_children_queryset(self.request.user)
        linked_ids = linked_children.values_list("id", flat=True)
        
        results = (
            User.objects.filter(role="student", parent__isnull=True)
            .exclude(id__in=linked_ids)
            .filter(models.Q(username__istartswith=query))
            .order_by("username")
        )
        
        return results[:20]  # Limit to 20 results


class ChildLinkView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsParent]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "child_link"

    def create(self, request, *args, **kwargs):
        child_id = request.data.get("child_id")
        
        if not child_id:
            return Response(
                {"error": "child_id talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            child = User.objects.get(id=child_id, role="student")
        except User.DoesNotExist:
            return Response(
                {"error": "O'quvchi topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already linked
        if child.parent_id == request.user.id:
            return Response(
                {"error": "Bu o'quvchi allaqachon bog'langan"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Security: block parent takeover of an already linked child.
        if child.parent_id and child.parent_id != request.user.id:
            logger.warning(
                "Blocked child relink attempt: parent=%s child=%s current_parent=%s",
                request.user.id,
                child.id,
                child.parent_id,
            )
            return Response(
                {"error": "Bu o'quvchi boshqa ota-onaga bog'langan"},
                status=status.HTTP_409_CONFLICT,
            )
        
        child.parent = request.user
        child.save()
        
        return Response(
            {
                "message": "O'quvchi muvaffaqiyatli bog'landi",
                "child": UserPublicSerializer(child).data
            },
            status=status.HTTP_201_CREATED
        )


class StudentProgressView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        from apps.gamification.services import GamificationService
        from apps.classroom.models import Enrollment

        student = get_object_or_404(User, id=student_id, role="student")

        # Permission check: teacher must be in student's classroom, or parent
        if request.user.role == "teacher":
            # Check if teacher has this student in any classroom
            has_access = Enrollment.objects.filter(
                student=student,
                classroom__teacher=request.user,
                is_active=True,
                is_approved=True,
            ).exists()
            if not has_access:
                return Response(
                    {"error": "Bu o'quvchiga ruxsat yo'q"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif request.user.role == "parent":
            # Check if this is parent's child
            if student.parent_id != request.user.id:
                return Response(
                    {"error": "Bu o'quvchiga ruxsat yo'q"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            return Response(
                {"error": "Ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get shared progress summary
        progress_data = GamificationService.get_progress_summary(student_id)

        return Response(progress_data)
