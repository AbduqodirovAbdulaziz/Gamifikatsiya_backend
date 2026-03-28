from django.contrib import admin
from django.utils.html import format_html
from .models import Course, Lesson, LessonProgress, CourseCompletion


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ["title", "lesson_type", "order", "xp_reward", "is_published"]
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title", "classroom", "teacher",
        "lessons_count", "published_badge",
    ]
    list_filter = ["is_published", "classroom"]
    search_fields = ["title", "teacher__username"]
    inlines = [LessonInline]
    list_per_page = 25

    @admin.display(description="Holat", ordering="is_published")
    def published_badge(self, obj):
        if obj.is_published:
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:2px 10px;'
                'border-radius:20px;font-size:11px;font-weight:700;">✓ Nashr qilingan</span>'
            )
        return format_html(
            '<span style="background:#e5e7eb;color:#6b7280;padding:2px 10px;'
            'border-radius:20px;font-size:11px;font-weight:700;">Qoralama</span>'
        )

    @admin.display(description="Darslar")
    def lessons_count(self, obj):
        count = obj.lessons.count()
        return format_html(
            '<span style="color:#6366f1;font-weight:700;">📚 {}</span>', count
        )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "title", "course", "type_badge",
        "order", "xp_reward_display", "published_badge",
    ]
    list_filter = ["lesson_type", "is_published"]
    search_fields = ["title", "course__title"]
    ordering = ["course", "order"]
    list_per_page = 30

    @admin.display(description="Turi")
    def type_badge(self, obj):
        colors = {
            "video":    ("#ef4444", "🎬"),
            "text":     ("#6366f1", "📝"),
            "quiz":     ("#10b981", "❓"),
            "task":     ("#f59e0b", "📋"),
            "resource": ("#06b6d4", "📎"),
        }
        color, icon = colors.get(obj.lesson_type, ("#6b7280", "📄"))
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{} {}</span>',
            color, icon, obj.get_lesson_type_display()
        )

    @admin.display(description="XP mukofot")
    def xp_reward_display(self, obj):
        return format_html(
            '<span style="color:#f59e0b;font-weight:700;">⭐ {}</span>', obj.xp_reward
        )

    @admin.display(description="Holat")
    def published_badge(self, obj):
        if obj.is_published:
            return format_html('<span style="color:#10b981;font-weight:700;">✓ Faol</span>')
        return format_html('<span style="color:#9ca3af;">— Qoralama</span>')


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        "student", "lesson", "progress_bar",
        "completion_status", "completed_at",
    ]
    list_filter = ["is_completed", "lesson__course"]
    search_fields = ["student__username"]
    readonly_fields = ["created_at", "completed_at"]
    ordering = ["-created_at"]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Progress")
    def progress_bar(self, obj):
        pct = obj.progress_percentage or 0
        color = "#10b981" if obj.is_completed else "#6366f1"
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:80px;background:#e5e7eb;border-radius:4px;height:7px;">'
            '<div style="width:{}%;background:{};border-radius:4px;height:7px;"></div>'
            '</div>'
            '<span style="font-size:12px;color:#6b7280;">{}%</span>'
            '</div>',
            pct, color, pct
        )

    @admin.display(description="Holat")
    def completion_status(self, obj):
        if obj.is_completed:
            return format_html('<span style="color:#10b981;font-weight:700;">✓ Yakunlandi</span>')
        return format_html('<span style="color:#f59e0b;">⏳ Jarayonda</span>')


@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "xp_earned_display", "completed_at"]
    list_filter = ["course"]
    search_fields = ["student__username"]
    readonly_fields = ["completed_at"]
    ordering = ["-completed_at"]
    list_per_page = 25

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Olingan XP")
    def xp_earned_display(self, obj):
        return format_html(
            '<span style="color:#f59e0b;font-weight:700;">⭐ {} XP</span>',
            obj.xp_earned
        )
