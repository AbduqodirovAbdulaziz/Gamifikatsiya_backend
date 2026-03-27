from rest_framework import serializers
from .models import Course, Lesson, LessonProgress, CourseCompletion


class LessonSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "content",
            "lesson_type",
            "video_url",
            "video_duration_seconds",
            "duration_minutes",
            "order",
            "xp_reward",
            "coin_reward",
            "is_published",
            "is_completed",
            "progress_percentage",
            "created_at",
            "updated_at",
        ]

    def get_is_completed(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if user and user.is_authenticated:
            return obj.progress.filter(student=user, is_completed=True).exists()
        return False

    def get_progress_percentage(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if user and user.is_authenticated:
            progress = obj.progress.filter(student=user).first()
            return progress.progress_percentage if progress else 0
        return 0


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    course_title = serializers.CharField(source="lesson.course.title", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "lesson",
            "lesson_title",
            "course_title",
            "is_completed",
            "time_spent_seconds",
            "progress_percentage",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["completed_at"]


class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)
    completed_count = serializers.IntegerField(read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "classroom",
            "teacher",
            "teacher_name",
            "thumbnail",
            "order",
            "is_published",
            "xp_reward",
            "coin_reward",
            "lesson_count",
            "completed_count",
            "lessons",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "teacher", "created_at", "updated_at"]


class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)
    lesson_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "thumbnail",
            "teacher_name",
            "order",
            "is_published",
            "xp_reward",
            "coin_reward",
            "lesson_count",
            "created_at",
        ]


class CourseCompletionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    student_name = serializers.CharField(source="student.get_full_name", read_only=True)

    class Meta:
        model = CourseCompletion
        fields = [
            "id",
            "student",
            "student_name",
            "course",
            "course_title",
            "xp_earned",
            "coin_earned",
            "completed_at",
        ]
