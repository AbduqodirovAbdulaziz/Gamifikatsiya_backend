from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import CustomUser, StudentProfile, TeacherProfile


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = [
        "username", "email", "role_badge", "full_name",
        "phone", "online_status", "is_active", "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "is_online"]
    search_fields = ["email", "username", "first_name", "last_name", "phone"]
    ordering = ["-date_joined"]
    list_per_page = 25
    date_hierarchy = "date_joined"
    autocomplete_fields = ["parent"]

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Qo'shimcha ma'lumot",
            {
                "fields": (
                    "role", "parent", "avatar", "date_of_birth",
                    "bio", "phone", "fcm_token",
                    "is_online", "last_seen",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Rol", ordering="role")
    def role_badge(self, obj):
        colors = {
            "student": ("#6366f1", "#e0e7ff", "O'quvchi"),
            "teacher": ("#10b981", "#ecfdf5", "O'qituvchi"),
            "parent":  ("#f59e0b", "#fffbeb", "Ota-ona"),
            "admin":   ("#ef4444", "#fef2f2", "Admin"),
        }
        bg, text_bg, label = colors.get(obj.role, ("#6b7280", "#f3f4f6", obj.role))
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
            bg, label
        )

    @admin.display(description="To'liq ism")
    def full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name or "—"

    @admin.display(description="Holat", boolean=False)
    def online_status(self, obj):
        if obj.is_online:
            return format_html(
                '<span style="color:#10b981;font-weight:600;">'
                '<i class="fas fa-circle" style="font-size:8px;"></i> {}</span>',
                "Online",
            )
        return format_html(
            '<span style="color:#9ca3af;font-size:12px;">{}</span>',
            "Offline",
        )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user", "level_badge", "xp_bar", "coins_display",
        "streak_display", "rank_position", "total_quizzes_completed",
    ]
    list_filter = ["level"]
    search_fields = ["user__username", "user__email"]
    ordering = ["-xp_points"]
    list_per_page = 25
    readonly_fields = ["xp_points", "level", "coins", "streak_days", "rank_position",
                       "total_quizzes_completed", "total_correct_answers", "total_points_earned"]

    @admin.display(description="Daraja", ordering="level")
    def level_badge(self, obj):
        level_colors = {
            range(1, 6):   "#6b7280",
            range(6, 11):  "#10b981",
            range(11, 21): "#6366f1",
            range(21, 50): "#f59e0b",
        }
        color = "#ef4444"
        for r, c in level_colors.items():
            if obj.level in r:
                color = c
                break
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;'
            'border-radius:20px;font-size:12px;font-weight:700;">Lv {}</span>',
            color, obj.level
        )

    @admin.display(description="XP")
    def xp_bar(self, obj):
        xp = obj.xp_points
        next_level_xp = ((obj.level) ** 2) * 100
        pct = min(int((xp / max(next_level_xp, 1)) * 100), 100)
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:80px;background:#e5e7eb;border-radius:4px;height:7px;">'
            '<div style="width:{}%;background:#6366f1;border-radius:4px;height:7px;"></div>'
            '</div>'
            '<span style="font-size:12px;color:#6b7280;">{} XP</span>'
            '</div>',
            pct, xp
        )

    @admin.display(description="Tangalar")
    def coins_display(self, obj):
        return format_html(
            '<span style="color:#f59e0b;font-weight:600;">'
            '<i class="fas fa-coins"></i> {}</span>',
            obj.coins
        )

    @admin.display(description="Seriya")
    def streak_display(self, obj):
        if obj.streak_days >= 7:
            color = "#ef4444"
            icon = "🔥"
        elif obj.streak_days >= 3:
            color = "#f59e0b"
            icon = "⚡"
        else:
            color = "#6b7280"
            icon = "📅"
        return format_html(
            '<span style="color:{};font-weight:600;">{} {} kun</span>',
            color, icon, obj.streak_days
        )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user", "subject_expertise", "school",
        "total_students", "verified_badge",
    ]
    list_filter = ["is_verified"]
    search_fields = ["user__username", "subject_expertise", "school"]
    list_per_page = 25

    @admin.display(description="Tasdiqlangan", ordering="is_verified")
    def verified_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="color:#10b981;font-weight:700;">'
                '<i class="fas fa-check-circle"></i> {}</span>',
                "Tasdiqlangan",
            )
        return format_html(
            '<span style="color:#9ca3af;">'
            '<i class="fas fa-clock"></i> {}</span>',
            "Kutilmoqda",
        )
