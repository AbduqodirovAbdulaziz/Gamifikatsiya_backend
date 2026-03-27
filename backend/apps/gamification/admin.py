from django.contrib import admin
from .models import (
    Badge,
    UserBadge,
    XPTransaction,
    Streak,
    DailyQuest,
    LevelTitle,
    LeaderboardEntry,
)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "badge_type",
        "condition_type",
        "condition_value",
        "xp_bonus",
        "rarity",
    ]
    list_filter = ["badge_type", "rarity", "is_active"]


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ["student", "badge", "earned_at", "is_displayed"]
    list_filter = ["badge", "is_displayed"]


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "amount",
        "transaction_type",
        "description",
        "created_at",
    ]
    list_filter = ["transaction_type"]
    search_fields = ["student__username"]


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ["student", "current_streak", "longest_streak", "last_activity_date"]


@admin.register(DailyQuest)
class DailyQuestAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "quest_type",
        "target_count",
        "current_count",
        "is_completed",
        "date",
    ]
    list_filter = ["quest_type", "is_completed", "date"]


@admin.register(LevelTitle)
class LevelTitleAdmin(admin.ModelAdmin):
    list_display = ["level", "title", "min_xp", "max_xp"]
    ordering = ["level"]
