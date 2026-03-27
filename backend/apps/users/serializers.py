from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import StudentProfile, TeacherProfile

User = get_user_model()


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "xp_points",
            "level",
            "coins",
            "streak_days",
            "last_activity",
            "total_quizzes_completed",
            "total_correct_answers",
            "rank_position",
            "daily_login_streak",
        ]


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ["subject_expertise", "school", "total_students", "is_verified"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=["student", "teacher"], default="student")

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "password_confirm",
            "role",
            "first_name",
            "last_name",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Parollar mos kelmadi"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        role = validated_data.pop("role", "student")
        user = User.objects.create_user(**validated_data)
        user.role = role
        user.save()

        if role == "student":
            StudentProfile.objects.create(user=user)
        elif role == "teacher":
            TeacherProfile.objects.create(user=user)

        return user


class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "avatar",
            "date_of_birth",
            "bio",
            "phone",
            "student_profile",
            "teacher_profile",
            "is_online",
            "last_seen",
        ]
        read_only_fields = ["id", "email", "role", "is_online", "last_seen"]


class UserPublicSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "avatar", "role", "student_profile"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "avatar", "date_of_birth", "bio", "phone"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto'g'ri")
        return value


class FCMTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField(max_length=500)
