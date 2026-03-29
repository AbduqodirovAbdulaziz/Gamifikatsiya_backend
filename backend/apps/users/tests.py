from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.classroom.models import Classroom, Enrollment
from apps.competition.models import Challenge, ChallengeAttempt, Tournament, TournamentParticipant
from apps.courses.models import Course, Lesson
from apps.gamification.models import DailyQuest, Streak, XPTransaction
from apps.quizzes.models import AnswerChoice, Question, Quiz, QuizAttempt
from apps.users.models import StudentProfile, TeacherProfile


User = get_user_model()


def create_user(username, role, password="testpass123", **extra):
    email = extra.pop("email", f"{username}@example.com")
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        **extra,
    )
    if role == "student":
        StudentProfile.objects.get_or_create(user=user)
    elif role == "teacher":
        TeacherProfile.objects.get_or_create(user=user)
    return user


def create_classroom_with_student(teacher, student):
    classroom = Classroom.objects.create(
        name="Test sinf",
        teacher=teacher,
        subject="Matematika",
    )
    Enrollment.objects.create(student=student, classroom=classroom)
    return classroom


class AdminSmokeTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )
        create_user("teacher_admin_page", "teacher")

    def test_custom_user_admin_changelist_loads(self):
        self.client.force_login(self.admin_user)
        response = self.client.get("/admin/users/customuser/")
        self.assertEqual(response.status_code, 200)

    def test_teacher_profile_admin_changelist_loads(self):
        self.client.force_login(self.admin_user)
        response = self.client.get("/admin/users/teacherprofile/")
        self.assertEqual(response.status_code, 200)


class ApiRegressionTests(APITestCase):
    def setUp(self):
        self.teacher = create_user("teacher", "teacher")
        self.student = create_user("student", "student")
        self.classroom = create_classroom_with_student(self.teacher, self.student)

    def test_student_cannot_update_classroom(self):
        self.client.force_authenticate(self.student)
        response = self.client.patch(
            f"/api/v1/classrooms/{self.classroom.id}/",
            {"name": "Buzilgan nom"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_quiz_duplicate_answers_are_scored_once(self):
        quiz = Quiz.objects.create(
            title="Quiz",
            classroom=self.classroom,
            created_by=self.teacher,
            quiz_type="practice",
            pass_percentage=50,
        )
        question = Question.objects.create(
            quiz=quiz,
            question_text="2+2?",
            question_type="multiple_choice",
            points=5,
        )
        correct = AnswerChoice.objects.create(
            question=question,
            choice_text="4",
            is_correct=True,
        )
        AnswerChoice.objects.create(question=question, choice_text="5", is_correct=False)

        self.client.force_authenticate(self.student)
        start_response = self.client.post(f"/api/v1/quizzes/{quiz.id}/start/")
        self.assertEqual(start_response.status_code, 200)

        submit_response = self.client.post(
            f"/api/v1/quizzes/{quiz.id}/submit/",
            {
                "answers": [
                    {
                        "question_id": str(question.id),
                        "selected_choice_id": str(correct.id),
                        "time_taken_seconds": 5,
                    },
                    {
                        "question_id": str(question.id),
                        "selected_choice_id": str(correct.id),
                        "time_taken_seconds": 3,
                    },
                ],
                "time_taken_seconds": 20,
            },
            format="json",
        )

        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data["correct_count"], 1)
        self.assertEqual(submit_response.data["attempt"]["earned_points"], 5)

    def test_tournament_score_comes_from_verified_quiz_attempt(self):
        quiz = Quiz.objects.create(
            title="Tournament Quiz",
            classroom=self.classroom,
            created_by=self.teacher,
            quiz_type="tournament",
        )
        tournament = Tournament.objects.create(
            title="Tournament",
            classroom=self.classroom,
            quiz=quiz,
            created_by=self.teacher,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
        )
        participant = TournamentParticipant.objects.create(
            tournament=tournament,
            student=self.student,
        )
        attempt = QuizAttempt.objects.create(
            student=self.student,
            quiz=quiz,
            attempt_number=1,
            score=72,
            total_points=10,
            earned_points=7,
            percentage=72,
            is_passed=True,
            is_completed=True,
            completed_at=timezone.now(),
        )

        self.client.force_authenticate(self.student)
        response = self.client.post(
            f"/api/v1/tournaments/{tournament.id}/submit_score/",
            {"score": 999, "attempt_id": str(attempt.id)},
            format="json",
        )

        participant.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["score"], 72)
        self.assertEqual(participant.score, 72)

    def test_challenge_result_comes_from_verified_quiz_attempt(self):
        opponent = create_user("opponent", "student")
        Enrollment.objects.create(student=opponent, classroom=self.classroom)
        quiz = Quiz.objects.create(
            title="Challenge Quiz",
            classroom=self.classroom,
            created_by=self.teacher,
            quiz_type="challenge",
        )
        challenge = Challenge.objects.create(
            challenger=self.student,
            opponent=opponent,
            quiz=quiz,
            status="accepted",
            xp_stake=10,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        attempt = QuizAttempt.objects.create(
            student=self.student,
            quiz=quiz,
            attempt_number=1,
            score=88,
            total_points=10,
            earned_points=9,
            percentage=88,
            is_passed=True,
            is_completed=True,
            completed_at=timezone.now(),
        )

        self.client.force_authenticate(self.student)
        response = self.client.post(
            f"/api/v1/challenges/{challenge.id}/submit_result/",
            {"score": 999, "attempt_id": str(attempt.id)},
            format="json",
        )

        challenge.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(challenge.challenger_score, 88)
        self.assertTrue(
            ChallengeAttempt.objects.filter(
                challenge=challenge,
                student=self.student,
                quiz_attempt=attempt,
            ).exists()
        )

    def test_daily_quests_generate_and_negative_price_cannot_mint_coins(self):
        profile = self.student.student_profile
        profile.coins = 50
        profile.save(update_fields=["coins"])

        self.client.force_authenticate(self.student)
        quests_response = self.client.get("/api/v1/quests/")
        self.assertEqual(quests_response.status_code, 200)
        self.assertEqual(DailyQuest.objects.filter(student=self.student).count(), 4)

        freeze_response = self.client.post(
            "/api/v1/buy-streak-freeze/",
            {"price": -100},
            format="json",
        )

        profile.refresh_from_db()
        streak = Streak.objects.get(student=self.student)
        self.assertEqual(freeze_response.status_code, 200)
        self.assertEqual(profile.coins, 0)
        self.assertEqual(streak.streak_freeze_count, 1)

    def test_course_completion_creates_course_complete_transaction(self):
        course = Course.objects.create(
            title="Course",
            classroom=self.classroom,
            teacher=self.teacher,
            is_published=True,
            xp_reward=20,
        )
        lesson = Lesson.objects.create(
            course=course,
            title="Lesson",
            lesson_type="text",
            is_published=True,
            xp_reward=5,
        )

        self.client.force_authenticate(self.student)
        response = self.client.post(f"/api/v1/lessons/{lesson.id}/complete/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            XPTransaction.objects.filter(
                student=self.student,
                transaction_type="course_complete",
            ).exists()
        )

    def test_parent_progress_endpoint_works_with_parent_relationship(self):
        parent = create_user("parent", "parent")
        child = create_user("child", "student", parent=parent)

        self.client.force_authenticate(parent)
        response = self.client.get(f"/api/v1/children/{child.id}/progress/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["child_id"], str(child.id))
