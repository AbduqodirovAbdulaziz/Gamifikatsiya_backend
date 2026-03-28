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
            queryset = Course.objects.filter(teacher=user)
        else:
            queryset = Course.objects.filter(
                is_published=True,
                classroom__enrollments__student=user,
                classroom__enrollments__is_active=True,
            ).distinct()

        queryset = queryset.prefetch_related("lessons")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        return CourseSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user if self.request else None
        if user and user.is_authenticated:
            from django.db.models import Prefetch
            from apps.courses.models import LessonProgress

            context["lessons_progress"] = {
                lp.lesson_id: lp for lp in LessonProgress.objects.filter(student=user)
            }
        return context

    def perform_create(self, serializer):
        classroom_id = self.request.data.get("classroom_id")
        classroom = get_object_or_404(
            Classroom, id=classroom_id, teacher=self.request.user
        )
        serializer.save(teacher=self.request.user, classroom=classroom)

    @action(detail=True, methods=["get"])
    def lessons(self, request, pk=None):
        course = self.get_object()
        lessons = (
            course.lessons.filter(is_published=True)
            .order_by("order")
            .prefetch_related("progress")
        )

        lesson_ids = list(lessons.values_list("id", flat=True))
        progress_map = {}
        if request.user.is_authenticated:
            from apps.courses.models import LessonProgress

            progress_map = {
                lp.lesson_id: lp
                for lp in LessonProgress.objects.filter(
                    student=request.user, lesson_id__in=lesson_ids
                )
            }

        for lesson in lessons:
            if lesson.id in progress_map:
                progress = progress_map[lesson.id]
                lesson._is_completed_cache = progress.is_completed
                lesson._progress_percentage_cache = progress.progress_percentage

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

        xp_earned = 0
        if not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.progress_percentage = 100
            progress.save()

            from apps.gamification.services import GamificationService

            xp_result = GamificationService.award_xp(
                user.id,
                lesson.xp_reward,
                "lesson_complete",
                f"Dars yakunlandi: {lesson.title}",
                related_id=str(lesson.id),
            )
            xp_earned = xp_result.get("xp_earned", 0) if xp_result else 0

            self._check_course_completion(user, lesson.course)

        return Response(
            {
                "message": "Dars muvaffaqiyatli yakunlandi",
                "xp_earned": xp_earned,
                "is_completed": progress.is_completed,
            }
        )

    def _check_course_completion(self, user, course):
        completed_lessons = LessonProgress.objects.filter(
            student=user,
            lesson__course=course,
            lesson__is_published=True,
            is_completed=True,
        ).count()

        total_lessons = course.lessons.filter(is_published=True).count()

        if completed_lessons >= total_lessons and total_lessons > 0:
            existing = CourseCompletion.objects.filter(
                student=user, course=course
            ).exists()
            if not existing:
                CourseCompletion.objects.create(
                    student=user,
                    course=course,
                    xp_earned=course.xp_reward,
                    coin_earned=course.coin_reward,
                )

                from apps.gamification.services import GamificationService

                GamificationService.award_xp(
                    user.id,
                    course.xp_reward,
                    "course_complete",
                    f"Kurs yakunlandi: {course.title}",
                    related_id=str(course.id),
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
