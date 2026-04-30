from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.classroom.models import Classroom, Enrollment
from apps.quizzes.models import Quiz, Question, AnswerChoice, QuizAttempt
from apps.users.models import CustomUser, UserRole


class QuizApiRegressionTests(APITestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            username="teacher_a",
            email="teacher@example.com",
            password="Pass1234!",
            role=UserRole.TEACHER,
        )
        self.student = CustomUser.objects.create_user(
            username="student_a",
            email="student@example.com",
            password="Pass1234!",
            role=UserRole.STUDENT,
        )

        self.classroom = Classroom.objects.create(
            name="Math A",
            teacher=self.teacher,
            subject="Math",
            description="Classroom for tests",
        )
        Enrollment.objects.create(student=self.student, classroom=self.classroom)

        self.quiz = Quiz.objects.create(
            title="Algebra quiz",
            classroom=self.classroom,
            created_by=self.teacher,
            is_active=True,
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            question_text="2 + 2 = ?",
            points=10,
            order=1,
        )
        self.correct_choice = AnswerChoice.objects.create(
            question=self.question,
            choice_text="4",
            is_correct=True,
            order=1,
        )
        self.wrong_choice = AnswerChoice.objects.create(
            question=self.question,
            choice_text="5",
            is_correct=False,
            order=2,
        )

    def test_teacher_results_returns_all_attempts_for_own_quiz(self):
        QuizAttempt.objects.create(
            student=self.student,
            quiz=self.quiz,
            attempt_number=1,
            is_completed=True,
            percentage=90,
            earned_points=9,
            total_points=10,
        )

        self.client.force_authenticate(self.teacher)
        url = reverse("quiz-results", kwargs={"pk": self.quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_question_create_rejects_invalid_choice_set(self):
        self.client.force_authenticate(self.teacher)
        url = reverse("question-list")
        payload = {
            "quiz": str(self.quiz.id),
            "question_text": "New question",
            "question_type": "multiple_choice",
            "difficulty": "medium",
            "points": 5,
            "order": 2,
            "choices": [
                {"choice_text": "A", "is_correct": True, "order": 1},
            ],
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("choices", response.data)

    def test_question_create_sets_quiz_from_view_save(self):
        self.client.force_authenticate(self.teacher)
        url = reverse("question-list")
        payload = {
            "quiz": str(self.quiz.id),
            "question_text": "What is 5 + 5?",
            "question_type": "multiple_choice",
            "difficulty": "easy",
            "points": 5,
            "order": 2,
            "choices": [
                {"choice_text": "10", "is_correct": True, "order": 1},
                {"choice_text": "11", "is_correct": False, "order": 2},
            ],
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Question.objects.get(question_text="What is 5 + 5?")
        self.assertEqual(created.quiz_id, self.quiz.id)

    def test_submit_accepts_legacy_choice_id_payload(self):
        attempt = QuizAttempt.objects.create(
            student=self.student,
            quiz=self.quiz,
            attempt_number=1,
            total_points=10,
            is_completed=False,
        )

        self.client.force_authenticate(self.student)
        url = reverse("quiz-submit", kwargs={"pk": self.quiz.id})
        payload = {
            "time_taken_seconds": 30,
            "answers": [
                {
                    "question_id": str(self.question.id),
                    "choice_id": str(self.correct_choice.id),
                }
            ],
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        attempt.refresh_from_db()
        self.assertTrue(attempt.is_completed)
