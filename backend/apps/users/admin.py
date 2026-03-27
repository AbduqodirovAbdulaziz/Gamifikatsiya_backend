from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, StudentProfile, TeacherProfile


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "role", "is_active", "is_online"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Qo'shimcha ma'lumot",
            {
                "fields": (
                    "role",
                    "avatar",
                    "date_of_birth",
                    "bio",
                    "phone",
                    "fcm_token",
                )
            },
        ),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "level",
        "xp_points",
        "coins",
        "streak_days",
        "rank_position",
    ]
    list_filter = ["level"]
    search_fields = ["user__username", "user__email"]


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "subject_expertise",
        "school",
        "total_students",
        "is_verified",
    ]
    list_filter = ["is_verified"]
    search_fields = ["user__username", "subject_expertise", "school"]
