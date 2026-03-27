from django.contrib import admin
from .models import Classroom, Enrollment, ClassroomInvitation


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "teacher",
        "subject",
        "student_count",
        "is_active",
        "created_at",
    ]
    list_filter = ["subject", "is_active", "academic_year"]
    search_fields = ["name", "subject", "teacher__username"]
    readonly_fields = ["code", "created_at", "updated_at"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "classroom", "joined_at", "is_active", "is_approved"]
    list_filter = ["is_active", "is_approved", "classroom"]
    search_fields = ["student__username", "classroom__name"]


@admin.register(ClassroomInvitation)
class ClassroomInvitationAdmin(admin.ModelAdmin):
    list_display = ["classroom", "code", "created_by", "use_count", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "classroom__name"]
