from django.contrib import admin
from .models import Course, Lesson, LessonProgress, CourseCompletion


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "classroom", "teacher", "is_published", "lesson_count"]
    list_filter = ["is_published", "classroom"]
    search_fields = ["title", "teacher__username"]
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "course",
        "lesson_type",
        "order",
        "is_published",
        "xp_reward",
    ]
    list_filter = ["lesson_type", "is_published"]
    search_fields = ["title", "course__title"]


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "lesson",
        "is_completed",
        "progress_percentage",
        "completed_at",
    ]
    list_filter = ["is_completed", "lesson__course"]


@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "xp_earned", "completed_at"]
    list_filter = ["course"]
