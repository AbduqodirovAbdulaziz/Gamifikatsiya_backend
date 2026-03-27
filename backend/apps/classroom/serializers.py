from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Classroom, Enrollment, ClassroomInvitation
from apps.users.serializers import UserPublicSerializer

User = get_user_model()


class ClassroomSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    is_joined = serializers.SerializerMethodField()

    class Meta:
        model = Classroom
        fields = [
            "id",
            "name",
            "code",
            "teacher",
            "teacher_name",
            "subject",
            "description",
            "academic_year",
            "is_active",
            "max_students",
            "student_count",
            "is_joined",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "code", "teacher", "created_at", "updated_at"]

    def get_is_joined(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if user and user.is_authenticated:
            return obj.enrollments.filter(student=user, is_active=True).exists()
        return False


class ClassroomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ["name", "subject", "description", "academic_year", "max_students"]


class ClassroomUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ["name", "subject", "description", "is_active", "max_students"]


class EnrollmentSerializer(serializers.ModelSerializer):
    student = UserPublicSerializer(read_only=True)
    classroom = ClassroomSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "student", "classroom", "joined_at", "is_active", "is_approved"]
        read_only_fields = ["id", "joined_at"]


class JoinClassroomSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=10)


class ClassroomStudentListSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()

    class Meta:
        model = Classroom
        fields = ["id", "name", "students"]

    def get_students(self, obj):
        enrollments = obj.enrollments.filter(is_active=True, is_approved=True)
        return EnrollmentSerializer(enrollments, many=True).data


class ClassroomLeaderboardSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    student = UserPublicSerializer()
    xp_points = serializers.IntegerField()
    level = serializers.IntegerField()
