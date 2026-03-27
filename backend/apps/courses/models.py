import uuid
from django.db import models
from django.conf import settings


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    classroom = models.ForeignKey(
        "classroom.Classroom", on_delete=models.CASCADE, related_name="courses"
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses_created",
    )
    thumbnail = models.ImageField(upload_to="course_thumbnails/", null=True, blank=True)
    order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    xp_reward = models.IntegerField(default=10)
    coin_reward = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses_course"
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def lesson_count(self):
        return self.lessons.filter(is_published=True).count()

    @property
    def completed_count(self):
        return self.lessons.filter(
            is_published=True, progress__is_completed=True
        ).count()


class Lesson(models.Model):
    LESSON_TYPES = [
        ("text", "Matn"),
        ("video", "Video"),
        ("interactive", "Interaktiv"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default="text")
    video_url = models.URLField(max_length=500, blank=True, null=True)
    video_duration_seconds = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=10)
    order = models.IntegerField(default=0)
    xp_reward = models.IntegerField(default=5)
    coin_reward = models.IntegerField(default=2)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses_lesson"
        verbose_name = "Dars"
        verbose_name_plural = "Darslar"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class LessonProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="progress"
    )
    is_completed = models.BooleanField(default=False)
    time_spent_seconds = models.IntegerField(default=0)
    progress_percentage = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses_lessonprogress"
        verbose_name = "Dars progressi"
        verbose_name_plural = "Dars progresslari"
        unique_together = ["student", "lesson"]

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"


class CourseCompletion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_completions",
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="completions"
    )
    xp_earned = models.IntegerField(default=0)
    coin_earned = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "courses_coursecompletion"
        verbose_name = "Kurs yakunlash"
        verbose_name_plural = "Kurs yakunlashlar"
        unique_together = ["student", "course"]

    def __str__(self):
        return f"{self.student.username} completed {self.course.title}"
