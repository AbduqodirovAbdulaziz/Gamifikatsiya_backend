from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from .models import Classroom, Enrollment, ClassroomInvitation
from .serializers import (
    ClassroomSerializer,
    ClassroomCreateSerializer,
    ClassroomUpdateSerializer,
    EnrollmentSerializer,
    JoinClassroomSerializer,
    ClassroomStudentListSerializer,
)
from apps.users.models import StudentProfile
from apps.users.permissions import IsTeacher


class ClassroomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy", "remove_student"}:
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin" or user.is_staff:
            return Classroom.objects.all()
        if user.role == "teacher":
            return Classroom.objects.filter(teacher=user)
        if user.role == "parent":
            return Classroom.objects.filter(
                enrollments__student__parent=user,
                enrollments__is_active=True,
            ).distinct()
        return Classroom.objects.filter(
            enrollments__student=user, enrollments__is_active=True
        ).distinct()

    def get_serializer_class(self):
        if self.action == "create":
            return ClassroomCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ClassroomUpdateSerializer
        return ClassroomSerializer

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        from rest_framework.pagination import PageNumberPagination

        query = request.query_params.get("q", "")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        page_size = min(page_size, 50)

        queryset = (
            Classroom.objects.filter(is_active=True)
            .filter(
                models.Q(name__icontains=query) | models.Q(subject__icontains=query)
            )
            .distinct()
        )

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        paginated = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginated, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["post"])
    def join(self, request):
        serializer = JoinClassroomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"].upper()
        classroom = get_object_or_404(Classroom, code=code, is_active=True)

        if classroom.student_count >= classroom.max_students:
            return Response(
                {"error": "Sinfxona to'lgan"}, status=status.HTTP_400_BAD_REQUEST
            )

        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user, classroom=classroom, defaults={"is_approved": True}
        )

        if not created:
            if enrollment.is_active:
                return Response(
                    {"error": "Siz allaqachon bu sinfxonaga qo'shilgansiz"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            enrollment.is_active = True
            enrollment.save()

        return Response(
            {
                "message": "Sinfxonaga muvaffaqiyatli qo'shildingiz",
                "classroom": ClassroomSerializer(
                    classroom, context={"request": request}
                ).data,
            }
        )

    @action(detail=True, methods=["get"])
    def students(self, request, pk=None):
        classroom = self.get_object()
        enrollments = classroom.enrollments.filter(is_active=True, is_approved=True)
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["delete"])
    def leave(self, request, pk=None):
        classroom = self.get_object()

        if classroom.teacher == request.user:
            return Response(
                {"error": "Sinf rahbari sinfdan chiqa olmaydi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment = get_object_or_404(
            Enrollment, student=request.user, classroom=classroom
        )
        enrollment.is_active = False
        enrollment.save()

        return Response({"message": "Sinfxonadan chiqdingiz"})

    @action(detail=True, methods=["delete"])
    def remove_student(self, request, pk=None):
        classroom = self.get_object()
        user = request.user

        if classroom.teacher != user and not user.is_staff:
            return Response(
                {"error": "Faqat sinf rahbari o'quvchini chiqarishi mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        student_id = request.data.get("student_id")
        if not student_id:
            return Response(
                {"error": "student_id talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            enrollment = Enrollment.objects.get(
                student_id=student_id, classroom=classroom
            )
            enrollment.is_active = False
            enrollment.save()
        except Enrollment.DoesNotExist:
            return Response(
                {"error": "Bu o'quvchi sinfхонада topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"message": "O'quvchi chiqarildi"})

    @action(detail=True, methods=["get"])
    def leaderboard(self, request, pk=None):
        classroom = self.get_object()
        enrollments = classroom.enrollments.filter(is_active=True).select_related(
            "student__student_profile"
        )

        leaderboard_data = []
        for rank, enrollment in enumerate(
            enrollments.order_by("-student__student_profile__xp_points"), 1
        ):
            profile = enrollment.student.student_profile
            leaderboard_data.append(
                {
                    "rank": rank,
                    "student_id": str(enrollment.student.id),
                    "username": enrollment.student.username,
                    "avatar": enrollment.student.avatar.url
                    if enrollment.student.avatar
                    else None,
                    "xp_points": profile.xp_points,
                    "level": profile.level,
                }
            )

        return Response(leaderboard_data)


class MyClassroomsView(generics.ListAPIView):
    serializer_class = ClassroomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin" or user.is_staff:
            return Classroom.objects.filter(is_active=True)
        if user.role == "teacher":
            return Classroom.objects.filter(teacher=user, is_active=True)
        if user.role == "parent":
            return Classroom.objects.filter(
                enrollments__student__parent=user,
                enrollments__is_active=True,
                is_active=True,
            ).distinct()
        return Classroom.objects.filter(
            enrollments__student=user, enrollments__is_active=True, is_active=True
        )
