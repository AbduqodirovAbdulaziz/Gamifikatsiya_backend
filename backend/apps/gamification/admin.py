from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Badge, UserBadge, XPTransaction,
    Streak, DailyQuest, LevelTitle, LeaderboardEntry,
)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = [
        "name", "badge_type_badge", "rarity_badge",
        "condition_type", "xp_bonus", "active_status",
    ]
    list_filter = ["badge_type", "rarity", "is_active"]
    search_fields = ["name"]
    list_per_page = 25

    @admin.display(description="Turi")
    def badge_type_badge(self, obj):
        colors = {
            "achievement": "#6366f1",
            "streak":      "#ef4444",
            "quiz":        "#10b981",
            "course":      "#06b6d4",
            "social":      "#f59e0b",
        }
        color = colors.get(obj.badge_type, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_badge_type_display()
        )

    @admin.display(description="Noyoblik")
    def rarity_badge(self, obj):
        colors = {
            "common":    "#6b7280",
            "rare":      "#6366f1",
            "epic":      "#a855f7",
            "legendary": "#f59e0b",
        }
        color = colors.get(obj.rarity, "#6b7280")
        return format_html(
            '<span style="color:{};font-weight:700;">⬟ {}</span>',
            color, obj.get_rarity_display()
        )

    @admin.display(description="Holat", boolean=False)
    def active_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#10b981;font-weight:700;">✓ Faol</span>')
        return format_html('<span style="color:#ef4444;">✗ Nofaol</span>')


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ["student", "badge", "earned_at", "displayed_status"]
    list_filter = ["badge", "is_displayed"]
    readonly_fields = ["earned_at"]
    list_per_page = 25

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Ko'rsatilgan")
    def displayed_status(self, obj):
        if obj.is_displayed:
            return format_html('<span style="color:#10b981;">👁 Ha</span>')
        return format_html('<span style="color:#9ca3af;">— Yo\'q</span>')


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ["student", "amount_display", "transaction_type_badge", "created_at"]
    list_filter = ["transaction_type"]
    search_fields = ["student__username"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Miqdor")
    def amount_display(self, obj):
        color = "#10b981" if obj.amount >= 0 else "#ef4444"
        sign = "+" if obj.amount >= 0 else ""
        return format_html(
            '<span style="color:{};font-weight:700;font-size:13px;">{}{} XP</span>',
            color, sign, obj.amount
        )

    @admin.display(description="Turi")
    def transaction_type_badge(self, obj):
        colors = {
            "quiz":    "#6366f1",
            "lesson":  "#10b981",
            "streak":  "#ef4444",
            "badge":   "#f59e0b",
            "manual":  "#6b7280",
        }
        color = colors.get(obj.transaction_type, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 9px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_transaction_type_display()
        )


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = [
        "student", "streak_display", "longest_streak", "last_activity_date"
    ]
    search_fields = ["student__username"]
    ordering = ["-current_streak"]
    list_per_page = 25

    @admin.display(description="Joriy seriya", ordering="current_streak")
    def streak_display(self, obj):
        n = obj.current_streak
        icon = "🔥" if n >= 7 else ("⚡" if n >= 3 else "📅")
        color = "#ef4444" if n >= 7 else ("#f59e0b" if n >= 3 else "#6b7280")
        return format_html(
            '<span style="color:{};font-weight:700;">{} {} kun</span>',
            color, icon, n
        )


@admin.register(DailyQuest)
class DailyQuestAdmin(admin.ModelAdmin):
    list_display = [
        "student", "quest_type", "progress_bar",
        "completion_badge", "date",
    ]
    list_filter = ["quest_type", "is_completed", "date"]
    search_fields = ["student__username"]
    readonly_fields = ["student", "quest_type", "target_count",
                       "current_count", "is_completed", "date"]

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Progress")
    def progress_bar(self, obj):
        pct = min(int((obj.current_count / max(obj.target_count, 1)) * 100), 100)
        color = "#10b981" if obj.is_completed else "#6366f1"
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:80px;background:#e5e7eb;border-radius:4px;height:7px;">'
            '<div style="width:{}%;background:{};border-radius:4px;height:7px;"></div>'
            '</div>'
            '<span style="font-size:12px;color:#6b7280;">{}/{}</span>'
            '</div>',
            pct, color, obj.current_count, obj.target_count
        )

    @admin.display(description="Holat")
    def completion_badge(self, obj):
        if obj.is_completed:
            return format_html(
                '<span style="color:#10b981;font-weight:700;">✓ Bajarildi</span>'
            )
        return format_html(
            '<span style="color:#f59e0b;">⏳ Jarayonda</span>'
        )


@admin.register(LevelTitle)
class LevelTitleAdmin(admin.ModelAdmin):
    list_display = ["level_badge", "title", "min_xp", "max_xp"]
    ordering = ["level"]
    list_per_page = 50

    @admin.display(description="Daraja", ordering="level")
    def level_badge(self, obj):
        level_colors = [
            (5,  "#6b7280"), (10, "#10b981"),
            (20, "#6366f1"), (50, "#f59e0b"),
        ]
        color = "#ef4444"
        for max_l, c in level_colors:
            if obj.level <= max_l:
                color = c
                break
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:20px;font-weight:700;">Lv {}</span>',
            color, obj.level
        )


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = [
        "rank_display", "student", "classroom",
        "period", "xp_points", "updated_at",
    ]
    list_filter = ["period", "classroom"]
    search_fields = ["student__username"]
    readonly_fields = ["updated_at"]
    ordering = ["rank_position"]
    list_per_page = 25

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="#", ordering="rank_position")
    def rank_display(self, obj):
        rank = obj.rank_position
        if rank == 1:
            return format_html('<span style="color:#f59e0b;font-size:16px;font-weight:900;">🥇 1</span>')
        elif rank == 2:
            return format_html('<span style="color:#9ca3af;font-size:15px;font-weight:900;">🥈 2</span>')
        elif rank == 3:
            return format_html('<span style="color:#b45309;font-size:15px;font-weight:900;">🥉 3</span>')
        return format_html('<span style="color:#6b7280;font-weight:600;">#{}</span>', rank)
