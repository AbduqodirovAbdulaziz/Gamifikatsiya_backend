from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Max
from django.core.cache import cache

from .models import Quiz, Question, AnswerChoice, QuizAttempt, StudentAnswer
from .serializers import (
    QuizListSerializer,
    QuizDetailSerializer,
    QuizCreateSerializer,
    QuestionSerializer,
    QuestionCreateSerializer,
    QuizAttemptSerializer,
    QuizAttemptListSerializer,
    QuizStartSerializer,
    QuizSubmitSerializer,
    StudentAnswerSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "teacher":
            return Quiz.objects.filter(created_by=user)
        return Quiz.objects.filter(
            is_active=True,
            classroom__enrollments__student=user,
            classroom__enrollments__is_active=True,
        ).distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return QuizListSerializer
        elif self.action == "create":
            return QuizCreateSerializer
        return QuizDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        quiz = self.get_object()
        user = request.user

        attempt_count = quiz.attempts.filter(student=user).count()
        if attempt_count >= quiz.max_attempts:
            return Response(
                {"error": f"Maksimal {quiz.max_attempts} ta urinishga ruxsat bor"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quiz.available_from and timezone.now() < quiz.available_from:
            return Response(
                {"error": "Test hali boshlanmagan"}, status=status.HTTP_400_BAD_REQUEST
            )

        if quiz.available_until and timezone.now() > quiz.available_until:
            return Response(
                {"error": "Test muddati tugagan"}, status=status.HTTP_400_BAD_REQUEST
            )

        attempt_number = attempt_count + 1
        attempt = QuizAttempt.objects.create(
            student=user,
            quiz=quiz,
            attempt_number=attempt_number,
            total_points=quiz.total_points,
        )

        return Response(
            {
                "attempt_id": str(attempt.id),
                "attempt_number": attempt_number,
                "question_count": quiz.question_count,
                "total_points": quiz.total_points,
                "time_limit_seconds": quiz.time_limit_seconds,
                "started_at": attempt.started_at,
            }
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers_data = serializer.validated_data["answers"]
        time_taken = serializer.validated_data["time_taken_seconds"]

        attempt = (
            quiz.attempts.filter(student=user, is_completed=False)
            .order_by("-started_at")
            .first()
        )
        if not attempt:
            return Response(
                {"error": "Test boshlanmagan"}, status=status.HTTP_400_BAD_REQUEST
            )

        earned_points = 0
        correct_count = 0

        for answer_data in answers_data:
            question_id = answer_data.get("question_id")
            selected_choice_id = answer_data.get("selected_choice_id")
            time_on_question = answer_data.get("time_taken_seconds", 0)

            try:
                question = quiz.questions.get(id=question_id)
            except Question.DoesNotExist:
                continue

            student_answer = StudentAnswer.objects.create(
                attempt=attempt, question=question, time_taken_seconds=time_on_question
            )

            if selected_choice_id:
                try:
                    choice = AnswerChoice.objects.get(
                        id=selected_choice_id, question=question
                    )
                    student_answer.selected_choice = choice
                    if choice.is_correct:
                        student_answer.is_correct = True
                        student_answer.points_earned = question.points
                        earned_points += question.points
                        correct_count += 1
                except AnswerChoice.DoesNotExist:
                    pass

            student_answer.save()

        attempt.earned_points = earned_points
        attempt.percentage = (
            (earned_points / quiz.total_points * 100) if quiz.total_points > 0 else 0
        )
        attempt.is_passed = attempt.percentage >= quiz.pass_percentage
        attempt.time_taken_seconds = time_taken
        attempt.completed_at = timezone.now()
        attempt.is_completed = True
        attempt.save()

        xp_earned = 0
        coin_earned = 0
        if attempt.is_passed:
            if attempt.percentage == 100:
                xp_earned = quiz.xp_reward * 2
                coin_earned = quiz.coin_reward * 2
            elif attempt.percentage >= 80:
                xp_earned = quiz.xp_reward
                coin_earned = quiz.coin_reward
            else:
                xp_earned = quiz.xp_reward // 2
                coin_earned = quiz.coin_reward // 2

            from apps.gamification.services import GamificationService

            GamificationService.award_xp(
                user.id,
                xp_earned,
                "quiz_complete",
                f"Test yakunlandi: {quiz.title}",
                related_id=str(quiz.id),
            )

            attempt.xp_earned = xp_earned
            attempt.coin_earned = coin_earned
            attempt.save()

        return Response(
            {
                "message": "Test yakunlandi",
                "attempt": QuizAttemptSerializer(attempt).data,
                "xp_earned": xp_earned,
                "coin_earned": coin_earned,
                "correct_count": correct_count,
                "total_questions": quiz.question_count,
            }
        )

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        attempts = quiz.attempts.filter(student=user, is_completed=True).order_by(
            "-started_at"
        )
        serializer = QuizAttemptListSerializer(attempts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def leaderboard(self, request, pk=None):
        quiz = self.get_object()
        attempts = (
            quiz.attempts.filter(is_completed=True)
            .select_related("student", "student__student_profile")
            .order_by("-percentage", "time_taken_seconds")[:20]
        )

        leaderboard = []
        for rank, attempt in enumerate(attempts, 1):
            profile = attempt.student.student_profile
            leaderboard.append(
                {
                    "rank": rank,
                    "student_id": str(attempt.student.id),
                    "username": attempt.student.username,
                    "avatar": attempt.student.avatar.url
                    if attempt.student.avatar
                    else None,
                    "percentage": attempt.percentage,
                    "time_taken": attempt.time_taken_seconds,
                    "xp_earned": attempt.xp_earned,
                    "level": profile.level if profile else 1,
                }
            )

        return Response(leaderboard)

    @action(detail=True, methods=["get"])
    def attempt_detail(self, request, pk=None, attempt_id=None):
        quiz = self.get_object()
        user = request.user
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, quiz=quiz, student=user)
        return Response(QuizAttemptSerializer(attempt).data)


class QuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "teacher":
            return Question.objects.filter(quiz__created_by=user)
        return Question.objects.filter(quiz__is_active=True, is_active=True)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return QuestionCreateSerializer
        return QuestionSerializer

    def perform_create(self, serializer):
        quiz_id = self.request.data.get("quiz_id")
        quiz = get_object_or_404(Quiz, id=quiz_id, created_by=self.request.user)
        serializer.save(quiz=quiz)


class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizAttemptSerializer

    def get_queryset(self):
        return QuizAttempt.objects.filter(student=self.request.user, is_completed=True)
