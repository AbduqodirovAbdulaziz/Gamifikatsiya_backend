from django.contrib import admin
from django.utils.html import format_html

from .models import Classroom, Enrollment, ClassroomInvitation


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "teacher",
        "subject",
        "students_count",
        "code_display",
        "active_status",
        "created_at",
    ]
    list_filter = ["subject", "is_active", "academic_year"]
    search_fields = ["name", "subject", "teacher__username"]
    readonly_fields = ["code", "created_at", "updated_at"]
    list_per_page = 25

    @admin.display(description="Holat")
    def active_status(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:2px 10px;'
                'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
                "Faol",
            )
        return format_html(
            '<span style="background:#e5e7eb;color:#6b7280;padding:2px 10px;'
            'border-radius:20px;font-size:11px;">{}</span>',
            "Nofaol",
        )

    @admin.display(description="Sinf kodi")
    def code_display(self, obj):
        return format_html(
            '<code style="background:#f3f4f6;padding:2px 8px;border-radius:4px;'
            'font-size:12px;color:#374151;font-family:monospace;">{}</code>',
            obj.code,
        )

    @admin.display(description="O'quvchilar")
    def students_count(self, obj):
        count = obj.enrollments.filter(is_active=True).count()
        return format_html(
            '<span style="color:#6366f1;font-weight:700;">{}</span>',
            count,
        )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "classroom",
        "joined_at",
        "active_badge",
        "approved_badge",
    ]
    list_filter = ["is_active", "is_approved", "classroom"]
    search_fields = ["student__username", "classroom__name"]
    readonly_fields = ["joined_at"]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Faol")
    def active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#10b981;font-weight:700;">{}</span>',
                "Ha",
            )
        return format_html(
            '<span style="color:#9ca3af;">{}</span>',
            "Yo'q",
        )

    @admin.display(description="Tasdiqlangan")
    def approved_badge(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="color:#6366f1;font-weight:700;">{}</span>',
                "Tasdiqlangan",
            )
        return format_html(
            '<span style="color:#f59e0b;">{}</span>',
            "Kutilmoqda",
        )


@admin.register(ClassroomInvitation)
class ClassroomInvitationAdmin(admin.ModelAdmin):
    list_display = [
        "classroom",
        "code_display",
        "created_by",
        "use_count",
        "max_uses_display",
        "active_badge",
        "created_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["code", "classroom__name"]
    readonly_fields = ["created_at"]
    list_per_page = 25

    @admin.display(description="Taklif kodi")
    def code_display(self, obj):
        return format_html(
            '<code style="background:#eef2ff;color:#6366f1;padding:3px 10px;'
            'border-radius:6px;font-size:13px;font-weight:700;font-family:monospace;">{}</code>',
            obj.code,
        )

    @admin.display(description="Foydalanish")
    def max_uses_display(self, obj):
        if obj.max_uses:
            pct = min(int((obj.use_count / obj.max_uses) * 100), 100)
            color = "#ef4444" if pct >= 80 else "#6366f1"
            return format_html(
                '<span style="color:{};">{} / {}</span>',
                color,
                obj.use_count,
                obj.max_uses,
            )
        return format_html(
            '<span style="color:#6b7280;">{} / inf</span>',
            obj.use_count,
        )

    @admin.display(description="Holat")
    def active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#10b981;font-weight:700;">{}</span>',
                "Faol",
            )
        return format_html(
            '<span style="color:#9ca3af;">{}</span>',
            "Nofaol",
        )
