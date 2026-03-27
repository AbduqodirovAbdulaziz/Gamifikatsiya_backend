from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Course, Lesson, LessonProgress, CourseCompletion
from .serializers import (
    CourseSerializer,
    CourseListSerializer,
    LessonSerializer,
    LessonProgressSerializer,
    CourseCompletionSerializer,
)
from apps.classroom.models import Classroom, Enrollment


class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "teacher":
            return Course.objects.filter(teacher=user)
        return Course.objects.filter(
            is_published=True,
            classroom__enrollments__student=user,
            classroom__enrollments__is_active=True,
        ).distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        return CourseSerializer

    def perform_create(self, serializer):
        classroom_id = self.request.data.get("classroom_id")
        classroom = get_object_or_404(
            Classroom, id=classroom_id, teacher=self.request.user
        )
        serializer.save(teacher=self.request.user, classroom=classroom)

    @action(detail=True, methods=["get"])
    def lessons(self, request, pk=None):
        course = self.get_object()
        lessons = course.lessons.filter(is_published=True).order_by("order")
        serializer = LessonSerializer(lessons, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def my_courses(self, request):
        user = request.user
        if user.role == "teacher":
            courses = Course.objects.filter(teacher=user, is_published=True)
        else:
            courses = Course.objects.filter(
                is_published=True,
                classroom__enrollments__student=user,
                classroom__enrollments__is_active=True,
            ).distinct()
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = LessonSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "teacher":
            return Lesson.objects.filter(course__teacher=user)
        return Lesson.objects.filter(
            is_published=True,
            course__classroom__enrollments__student=user,
            course__classroom__enrollments__is_active=True,
        ).distinct()

    def perform_create(self, serializer):
        course_id = self.request.data.get("course_id")
        course = get_object_or_404(Course, id=course_id, teacher=self.request.user)
        serializer.save(course=course)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        lesson = self.get_object()
        user = request.user

        progress, created = LessonProgress.objects.get_or_create(
            student=user, lesson=lesson, defaults={"progress_percentage": 100}
        )

        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.progress_percentage = 100
            progress.save()

            from apps.gamification.services import GamificationService

            GamificationService.award_xp(
                user.id,
                lesson.xp_reward,
                "lesson_complete",
                f"Dars yakunlandi: {lesson.title}",
                related_id=str(lesson.id),
            )

        return Response(
            {
                "message": "Dars muvaffaqiyatli yakunlandi",
                "xp_earned": lesson.xp_reward if not created else 0,
                "is_completed": progress.is_completed,
            }
        )

    @action(detail=True, methods=["post"])
    def update_progress(self, request, pk=None):
        lesson = self.get_object()
        user = request.user
        percentage = request.data.get("progress_percentage", 0)

        progress, _ = LessonProgress.objects.get_or_create(
            student=user, lesson=lesson, defaults={"progress_percentage": percentage}
        )

        progress.progress_percentage = min(percentage, 100)
        progress.time_spent_seconds = request.data.get(
            "time_spent_seconds", progress.time_spent_seconds
        )
        progress.save()

        return Response(LessonProgressSerializer(progress).data)

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        lesson = self.get_object()
        user = request.user

        progress = LessonProgress.objects.filter(student=user, lesson=lesson).first()
        if not progress:
            return Response(
                {
                    "is_completed": False,
                    "progress_percentage": 0,
                    "time_spent_seconds": 0,
                }
            )

        return Response(LessonProgressSerializer(progress).data)


class CourseCompletionView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CourseCompletionSerializer

    def get_queryset(self):
        return CourseCompletion.objects.filter(student=self.request.user)
