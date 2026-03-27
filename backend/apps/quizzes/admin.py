from django.contrib import admin
from .models import Quiz, Question, AnswerChoice, QuizAttempt, StudentAnswer


class AnswerChoiceInline(admin.TabularInline):
    model = AnswerChoice
    extra = 4


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "classroom",
        "created_by",
        "quiz_type",
        "is_active",
        "question_count",
    ]
    list_filter = ["quiz_type", "is_active", "classroom"]
    search_fields = ["title", "created_by__username"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "quiz",
        "question_text",
        "question_type",
        "difficulty",
        "points",
        "order",
    ]
    list_filter = ["question_type", "difficulty", "quiz"]
    search_fields = ["question_text"]
    inlines = [AnswerChoiceInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "quiz",
        "attempt_number",
        "percentage",
        "is_passed",
        "started_at",
    ]
    list_filter = ["is_passed", "quiz"]


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ["attempt", "question", "is_correct", "points_earned"]
    list_filter = ["is_correct"]
