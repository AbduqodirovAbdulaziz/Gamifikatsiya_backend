from django.contrib import admin
from django.utils.html import format_html

from .models import Tournament, TournamentParticipant, Challenge, ChallengeAttempt


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "classroom",
        "type_badge",
        "status_badge",
        "participants_count",
        "start_time",
        "end_time",
    ]
    list_filter = ["status", "tournament_type"]
    search_fields = ["title"]
    list_per_page = 25

    @admin.display(description="Turi")
    def type_badge(self, obj):
        return format_html(
            '<span style="background:#6366f1;color:#fff;padding:2px 9px;'
            'border-radius:20px;font-size:11px;font-weight:700;">{}</span>',
            obj.get_tournament_type_display(),
        )

    @admin.display(description="Holat", ordering="status")
    def status_badge(self, obj):
        configs = {
            "upcoming": ("#06b6d4", "Kutilmoqda"),
            "active": ("#10b981", "Faol"),
            "finished": ("#6b7280", "Yakunlandi"),
            "cancelled": ("#ef4444", "Bekor"),
        }
        color, label = configs.get(obj.status, ("#6b7280", obj.status))
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            color,
            label,
        )

    @admin.display(description="Qatnashchilar")
    def participants_count(self, obj):
        count = obj.participants.count()
        max_p = obj.max_participants
        color = "#ef4444" if count >= max_p else "#6366f1"
        return format_html(
            '<span style="color:{};font-weight:700;">{} / {}</span>',
            color,
            count,
            max_p,
        )


@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    list_display = [
        "rank_display",
        "student",
        "tournament",
        "score_display",
        "registered_at",
    ]
    list_filter = ["tournament"]
    search_fields = ["student__username"]
    readonly_fields = ["registered_at"]
    ordering = ["rank_position"]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="#")
    def rank_display(self, obj):
        rank = obj.rank_position
        if rank in {1, 2, 3}:
            return format_html('<span style="font-size:15px;">{}</span>', rank)
        return format_html(
            '<span style="color:#6b7280;font-weight:600;">#{}</span>',
            rank,
        )

    @admin.display(description="Ball")
    def score_display(self, obj):
        return format_html(
            '<span style="color:#6366f1;font-weight:700;">{}</span>',
            obj.score,
        )


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = [
        "challenger",
        "vs_display",
        "quiz",
        "status_badge",
        "xp_stake_display",
        "expires_at",
    ]
    list_filter = ["status"]
    search_fields = ["challenger__username", "opponent__username"]
    list_per_page = 25

    @admin.display(description="Raqib")
    def vs_display(self, obj):
        return format_html(
            '<span style="color:#ef4444;font-weight:700;">{}</span>',
            obj.opponent.username,
        )

    @admin.display(description="Holat")
    def status_badge(self, obj):
        configs = {
            "pending": ("#f59e0b", "Kutilmoqda"),
            "accepted": ("#10b981", "Qabul qilingan"),
            "in_progress": ("#06b6d4", "Davom etmoqda"),
            "completed": ("#6b7280", "Yakunlandi"),
            "declined": ("#ef4444", "Rad etilgan"),
            "expired": ("#9ca3af", "Muddati o'tdi"),
        }
        color, label = configs.get(obj.status, ("#6b7280", obj.status))
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            color,
            label,
        )

    @admin.display(description="XP tikish")
    def xp_stake_display(self, obj):
        return format_html(
            '<span style="color:#f59e0b;font-weight:700;">{} XP</span>',
            obj.xp_stake,
        )


@admin.register(ChallengeAttempt)
class ChallengeAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "challenge",
        "student",
        "score_display",
        "started_at",
    ]
    readonly_fields = ["started_at", "completed_at"]
    ordering = ["-started_at"]
    list_per_page = 30

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Ball")
    def score_display(self, obj):
        return format_html(
            '<span style="color:#6366f1;font-weight:700;">{}</span>',
            obj.score,
        )
