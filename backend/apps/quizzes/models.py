import uuid
from django.db import models
from django.conf import settings


class Quiz(models.Model):
    QUIZ_TYPES = [
        ("practice", "Amaliyot"),
        ("exam", "Imtihon"),
        ("challenge", "Challenge"),
        ("tournament", "Turnir"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quizzes",
    )
    classroom = models.ForeignKey(
        "classroom.Classroom", on_delete=models.CASCADE, related_name="quizzes"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes_created",
    )
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES, default="practice")
    time_limit_seconds = models.IntegerField(null=True, blank=True)
    max_attempts = models.IntegerField(default=3)
    pass_percentage = models.IntegerField(default=60)
    xp_reward = models.IntegerField(default=20)
    coin_reward = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    show_answers = models.BooleanField(default=True)
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    randomize_questions = models.BooleanField(default=False)
    randomize_answers = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quizzes_quiz"
        verbose_name = "Test"
        verbose_name_plural = "Testlar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def total_points(self):
        return self.questions.aggregate(total=models.Sum("points"))["total"] or 0


class Question(models.Model):
    QUESTION_TYPES = [
        ("multiple_choice", "Ko'p tanlovli"),
        ("true_false", "Ro'st/Yolg'on"),
        ("short_answer", "Qisqa javob"),
        ("matching", "Moslashtirish"),
        ("ordering", "Tartiblash"),
    ]
    DIFFICULTY_LEVELS = [
        ("easy", "Oson"),
        ("medium", "O'rta"),
        ("hard", "Qiyin"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPES, default="multiple_choice"
    )
    image = models.ImageField(upload_to="question_images/", null=True, blank=True)
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_LEVELS, default="medium"
    )
    points = models.IntegerField(default=1)
    time_limit_seconds = models.IntegerField(null=True, blank=True)
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quizzes_question"
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.quiz.title} - {self.question_text[:50]}"


class AnswerChoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = "quizzes_answerchoice"
        verbose_name = "Javob varianti"
        verbose_name_plural = "Javob variantlari"
        ordering = ["order"]

    def __str__(self):
        return f"{self.choice_text[:50]} - {'Correct' if self.is_correct else 'Wrong'}"


class QuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.IntegerField(default=1)
    score = models.FloatField(default=0)
    total_points = models.IntegerField(default=0)
    earned_points = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    is_passed = models.BooleanField(default=False)
    time_taken_seconds = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    xp_earned = models.IntegerField(default=0)
    coin_earned = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "quizzes_quizattempt"
        verbose_name = "Test urinish"
        verbose_name_plural = "Test urinishlari"
        unique_together = ["student", "quiz", "attempt_number"]
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} (Attempt {self.attempt_number})"


class StudentAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="student_answers"
    )
    selected_choice = models.ForeignKey(
        AnswerChoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_by",
    )
    text_answer = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quizzes_studentanswer"
        verbose_name = "O'quvchi javobi"
        verbose_name_plural = "O'quvchi javoblari"

    def __str__(self):
        return f"{self.attempt.student.username} - Q{self.question.order}"
