from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
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
from apps.users.permissions import IsTeacher


class QuizViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin" or user.is_staff:
            return Quiz.objects.all()
        if user.role == "teacher":
            return Quiz.objects.filter(created_by=user)
        elif user.role == "parent":
            return Quiz.objects.filter(
                is_active=True,
                classroom__enrollments__student__parent=user,
                classroom__enrollments__is_active=True,
            ).distinct()
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
        classroom = serializer.validated_data["classroom"]
        if self.request.user.role == "teacher" and classroom.teacher != self.request.user:
            raise PermissionDenied("Siz faqat o'zingizga tegishli sinf uchun test yarata olasiz")
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        quiz = self.get_object()
        user = request.user

        if user.role != "student":
            return Response(
                {"error": "Faqat o'quvchilar testni boshlashi mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if quiz.available_from and timezone.now() < quiz.available_from:
            return Response(
                {"error": "Test hali boshlanmagan"}, status=status.HTTP_400_BAD_REQUEST
            )

        if quiz.available_until and timezone.now() > quiz.available_until:
            return Response(
                {"error": "Test muddati tugagan"}, status=status.HTTP_400_BAD_REQUEST
            )

        attempt_count = quiz.attempts.filter(student=user).count()
        if attempt_count >= quiz.max_attempts:
            return Response(
                {"error": f"Maksimal {quiz.max_attempts} ta urinishga ruxsat bor"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        incomplete_attempt = quiz.attempts.filter(
            student=user, is_completed=False
        ).first()
        if incomplete_attempt:
            elapsed = (timezone.now() - incomplete_attempt.started_at).total_seconds()
            if quiz.time_limit_seconds and elapsed > quiz.time_limit_seconds:
                incomplete_attempt.is_completed = True
                incomplete_attempt.completed_at = timezone.now()
                incomplete_attempt.save()
            else:
                remaining = (
                    quiz.time_limit_seconds - elapsed if quiz.time_limit_seconds else None
                )
                return Response(
                    {
                        "attempt_id": str(incomplete_attempt.id),
                        "attempt_number": incomplete_attempt.attempt_number,
                        "question_count": quiz.question_count,
                        "total_points": quiz.total_points,
                        "time_limit_seconds": quiz.time_limit_seconds,
                        "started_at": incomplete_attempt.started_at,
                        "remaining_seconds": int(remaining) if remaining else None,
                        "resumed": True,
                    }
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
                "attempt_number": attempt.attempt_number,
                "question_count": quiz.question_count,
                "total_points": quiz.total_points,
                "time_limit_seconds": quiz.time_limit_seconds,
                "started_at": attempt.started_at,
                "resumed": False,
            }
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        user = request.user

        if user.role != "student":
            return Response(
                {"error": "Faqat o'quvchilar testni topshirishi mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

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

        if quiz.time_limit_seconds:
            elapsed = (timezone.now() - attempt.started_at).total_seconds()
            if elapsed > quiz.time_limit_seconds:
                attempt.is_completed = True
                attempt.completed_at = timezone.now()
                attempt.save()
                return Response(
                    {"error": "Test muddati tugagan", "attempt_id": str(attempt.id)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        earned_points = 0
        correct_count = 0
        unique_answers = {}
        for answer_data in answers_data:
            question_id = answer_data.get("question_id")
            if question_id:
                unique_answers[str(question_id)] = answer_data

        questions_by_id = {
            str(question.id): question
            for question in quiz.questions.filter(id__in=unique_answers.keys())
        }

        for question_id, answer_data in unique_answers.items():
            selected_choice_id = answer_data.get("selected_choice_id")
            time_on_question = answer_data.get("time_taken_seconds", 0)
            question = questions_by_id.get(question_id)
            if not question:
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
                    student_answer.save()
                except AnswerChoice.DoesNotExist:
                    student_answer.save()
            else:
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
            from apps.notifications.services import NotificationService

            GamificationService.award_xp(
                user.id,
                xp_earned,
                "quiz_complete",
                f"Test yakunlandi: {quiz.title}",
                related_id=str(quiz.id),
            )

            GamificationService.award_coins(
                user.id, coin_earned, f"Test yakunlash bonus"
            )

            GamificationService.update_quest_progress(user.id, "quiz")

            NotificationService.notify_quiz_result(
                str(user.id), quiz.title, attempt.percentage, attempt.is_passed
            )

            attempt.xp_earned = xp_earned
            attempt.coin_earned = coin_earned
            attempt.save()

            from apps.users.models import StudentProfile

            try:
                profile = StudentProfile.objects.get(user=user)
                profile.total_quizzes_completed += 1
                profile.total_correct_answers += correct_count
                profile.save()
            except StudentProfile.DoesNotExist:
                pass

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
    def questions(self, request, pk=None):
        quiz = self.get_object()
        user = request.user

        attempt_id = request.query_params.get("attempt_id")
        if not attempt_id:
            return Response(
                {"error": "attempt_id talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempt = get_object_or_404(QuizAttempt, id=attempt_id, quiz=quiz, student=user)

        if attempt.is_completed and not (user.role == "teacher" or quiz.show_answers):
            return Response(
                {"error": "Javoblar yashirilgan"}, status=status.HTTP_403_FORBIDDEN
            )

        questions = quiz.questions.filter(is_active=True)
        if quiz.randomize_questions:
            import random

            questions = list(questions)
            random.shuffle(questions)

        questions_data = []
        for q in questions:
            choices = list(q.choices.all())
            if quiz.randomize_answers:
                import random

                random.shuffle(choices)

            choices_data = []
            for c in choices:
                show_correct = (
                    user.role == "teacher" or attempt.is_completed or quiz.show_answers
                )
                choice_data = {
                    "id": str(c.id),
                    "text": c.choice_text,
                }
                if show_correct:
                    choice_data["is_correct"] = c.is_correct
                choices_data.append(choice_data)

            questions_data.append(
                {
                    "id": str(q.id),
                    "text": q.question_text,
                    "type": q.question_type,
                    "points": q.points,
                    "image": q.image.url if q.image else None,
                    "choices": choices_data,
                }
            )

        return Response(
            {
                "questions": questions_data,
                "show_answers": quiz.show_answers or user.role == "teacher",
            }
        )

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        quiz = self.get_object()
        user = request.user
        attempts = (
            quiz.attempts.filter(student=user, is_completed=True)
            .order_by("-started_at")
            .select_related("quiz")
        )
        serializer = QuizAttemptListSerializer(attempts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def leaderboard(self, request, pk=None):
        quiz = self.get_object()
        user = request.user

        if user.role == "teacher" and quiz.created_by != user:
            return Response(
                {"error": "Bu test liderlarini ko'rish huquqingiz yo'q"},
                status=status.HTTP_403_FORBIDDEN,
            )

        cache_key = f"quiz_leaderboard:{quiz.id}"
        cached_leaderboard = cache.get(cache_key)

        if cached_leaderboard:
            return Response(cached_leaderboard)

        attempts = (
            quiz.attempts.filter(is_completed=True)
            .select_related("student", "student__student_profile")
            .order_by("-percentage", "time_taken_seconds")[:20]
        )

        leaderboard = []
        for rank, attempt in enumerate(attempts, 1):
            profile = getattr(attempt.student, "student_profile", None)
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
                    "is_current_user": attempt.student == user,
                }
            )

        cache.set(cache_key, leaderboard, 300)
        return Response(leaderboard)

    @action(detail=True, methods=["get"])
    def attempt_detail(self, request, pk=None, attempt_id=None):
        quiz = self.get_object()
        user = request.user

        if user.role == "teacher":
            attempt = get_object_or_404(QuizAttempt, id=attempt_id, quiz=quiz)
        else:
            attempt = get_object_or_404(
                QuizAttempt, id=attempt_id, quiz=quiz, student=user
            )

        serializer = QuizAttemptSerializer(attempt)
        data = serializer.data

        if user.role != "teacher" and not quiz.show_answers:
            data.pop("answers", None)

        return Response(data)


class QuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = QuestionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "teacher":
            return Question.objects.filter(quiz__created_by=user).select_related("quiz")
        return Question.objects.filter(quiz__is_active=True, is_active=True)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return QuestionCreateSerializer
        return QuestionSerializer

    def perform_create(self, serializer):
        quiz_id = self.request.data.get("quiz_id")
        quiz = get_object_or_404(Quiz, id=quiz_id, created_by=self.request.user)
        serializer.save(quiz=quiz)

    def perform_update(self, serializer):
        question = self.get_object()
        if question.quiz.created_by != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Siz bu savolni tahrirlashingiz mumkin emas")
        serializer.save()


class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QuizAttemptSerializer

    def get_queryset(self):
        return QuizAttempt.objects.filter(
            student=self.request.user, is_completed=True
        ).select_related("quiz")
