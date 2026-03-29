from django.contrib import admin
from django.utils.html import format_html

from .models import Quiz, Question, AnswerChoice, QuizAttempt, StudentAnswer


class AnswerChoiceInline(admin.TabularInline):
    model = AnswerChoice
    extra = 4
    fields = ["choice_text", "is_correct"]


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ["question_text", "question_type", "difficulty", "points"]
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "classroom",
        "created_by",
        "type_badge",
        "questions_count",
        "active_status",
    ]
    list_filter = ["quiz_type", "is_active", "classroom"]
    search_fields = ["title", "created_by__username"]
    inlines = [QuestionInline]
    list_per_page = 25

    @admin.display(description="Turi")
    def type_badge(self, obj):
        colors = {
            "practice": "#6366f1",
            "exam": "#ef4444",
            "challenge": "#f59e0b",
            "tournament": "#a855f7",
        }
        color = colors.get(obj.quiz_type, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
            color,
            obj.get_quiz_type_display(),
        )

    @admin.display(description="Faol")
    def active_status(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:#10b981;font-weight:700;">{}</span>',
                "Faol",
            )
        return format_html(
            '<span style="color:#9ca3af;">{}</span>',
            "Nofaol",
        )

    @admin.display(description="Savollar")
    def questions_count(self, obj):
        return format_html(
            '<span style="color:#6366f1;font-weight:700;">{}</span>',
            obj.questions.count(),
        )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "short_text",
        "quiz",
        "type_badge",
        "difficulty_badge",
        "points",
    ]
    list_filter = ["question_type", "difficulty", "quiz"]
    search_fields = ["question_text"]
    inlines = [AnswerChoiceInline]
    list_per_page = 30

    @admin.display(description="Savol")
    def short_text(self, obj):
        text = obj.question_text
        return text[:60] + "..." if len(text) > 60 else text

    @admin.display(description="Turi")
    def type_badge(self, obj):
        colors = {
            "multiple_choice": "#6366f1",
            "true_false": "#10b981",
            "short_answer": "#f59e0b",
            "matching": "#06b6d4",
            "ordering": "#a855f7",
        }
        color = colors.get(obj.question_type, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
            color,
            obj.get_question_type_display(),
        )

    @admin.display(description="Qiyinlik")
    def difficulty_badge(self, obj):
        configs = {
            "easy": ("#10b981", "Oson"),
            "medium": ("#f59e0b", "O'rta"),
            "hard": ("#ef4444", "Qiyin"),
        }
        color, label = configs.get(obj.difficulty, ("#6b7280", obj.difficulty))
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            color,
            label,
        )


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "quiz",
        "attempt_number",
        "score_display",
        "passed_badge",
        "started_at",
    ]
    list_filter = ["is_passed", "quiz"]
    search_fields = ["student__username"]
    readonly_fields = ["started_at", "completed_at"]
    ordering = ["-started_at"]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Ball", ordering="percentage")
    def score_display(self, obj):
        pct = obj.percentage or 0
        color = "#10b981" if pct >= 70 else ("#f59e0b" if pct >= 50 else "#ef4444")
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:60px;background:#e5e7eb;border-radius:4px;height:7px;">'
            '<div style="width:{}%;background:{};border-radius:4px;height:7px;"></div>'
            '</div>'
            '<span style="color:{};font-weight:700;font-size:12px;">{}%</span>'
            '</div>',
            pct,
            color,
            color,
            pct,
        )

    @admin.display(description="Natija")
    def passed_badge(self, obj):
        if obj.is_passed:
            return format_html(
                '<span style="background:#10b981;color:#fff;padding:2px 10px;'
                'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
                "O'tdi",
            )
        return format_html(
            '<span style="background:#ef4444;color:#fff;padding:2px 10px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
            "O'tmadi",
        )


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = [
        "attempt",
        "short_question",
        "correct_badge",
        "points_earned",
    ]
    list_filter = ["is_correct"]
    readonly_fields = [
        "attempt",
        "question",
        "selected_choice",
        "is_correct",
        "points_earned",
    ]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Savol")
    def short_question(self, obj):
        text = str(obj.question)
        return text[:50] + "..." if len(text) > 50 else text

    @admin.display(description="To'g'ri")
    def correct_badge(self, obj):
        if obj.is_correct:
            return format_html(
                '<span style="color:#10b981;font-weight:700;font-size:15px;">{}</span>',
                "Ha",
            )
        return format_html(
            '<span style="color:#ef4444;font-weight:700;font-size:15px;">{}</span>',
            "Yo'q",
        )
