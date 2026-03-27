import uuid
import random
import string
from django.db import models
from django.conf import settings


def generate_class_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


class Classroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True, default=generate_class_code)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="classrooms_teaching",
    )
    subject = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    academic_year = models.CharField(max_length=9, default="2024-2025")
    is_active = models.BooleanField(default=True)
    max_students = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "classroom_classroom"
        verbose_name = "Sinfxona"
        verbose_name_plural = "Sinfxonalar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"

    @property
    def student_count(self):
        return self.enrollments.filter(is_active=True).count()


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name="enrollments"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        db_table = "classroom_enrollment"
        verbose_name = "Ro'yxatga olish"
        verbose_name_plural = "Ro'yxatga olishlar"
        unique_together = ["student", "classroom"]
        ordering = ["-joined_at"]

    def __str__(self):
        return f"{self.student.username} - {self.classroom.name}"


class ClassroomInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(
        Classroom, on_delete=models.CASCADE, related_name="invitations"
    )
    code = models.CharField(max_length=10, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(default=0)
    use_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "classroom_invitation"
        verbose_name = "Sinfxona taklifi"
        verbose_name_plural = "Sinfxona takliflari"
