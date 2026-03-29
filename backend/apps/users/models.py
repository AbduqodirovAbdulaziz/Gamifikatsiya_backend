import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    STUDENT = "student", "O'quvchi"
    TEACHER = "teacher", "O'qituvchi"
    PARENT = "parent", "Ota-ona"
    ADMIN = "admin", "Administrator"


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20, choices=UserRole.choices, default=UserRole.STUDENT
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        limit_choices_to={"role": UserRole.PARENT},
    )
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    fcm_token = models.CharField(max_length=500, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users_customuser"
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.username} ({self.role})"


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="student_profile"
    )
    xp_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    coins = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=0)
    last_activity = models.DateField(null=True, blank=True)
    total_quizzes_completed = models.IntegerField(default=0)
    total_correct_answers = models.IntegerField(default=0)
    rank_position = models.IntegerField(null=True, blank=True)
    daily_login_streak = models.IntegerField(default=0)
    total_points_earned = models.IntegerField(default=0)

    class Meta:
        db_table = "users_studentprofile"
        verbose_name = "O'quvchi profili"
        verbose_name_plural = "O'quvchi profillari"

    def __str__(self):
        return f"{self.user.username} - Level {self.level}"

    def save(self, *args, **kwargs):
        if self.xp_points is not None and self.level == 1:
            self.level = self.calculate_level(self.xp_points)
        elif self.xp_points is not None:
            self.level = self.calculate_level(self.xp_points)
        super().save(*args, **kwargs)

    @staticmethod
    def calculate_level(total_xp):
        import math

        return math.floor(math.sqrt(total_xp / 100)) + 1


class TeacherProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="teacher_profile"
    )
    subject_expertise = models.CharField(max_length=200, blank=True)
    school = models.CharField(max_length=200, blank=True)
    total_students = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = "users_teacherprofile"
        verbose_name = "O'qituvchi profili"
        verbose_name_plural = "O'qituvchi profillari"

    def __str__(self):
        return f"{self.user.username} - {self.subject_expertise}"
