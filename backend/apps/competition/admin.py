from django.contrib import admin
from .models import Tournament, TournamentParticipant, Challenge, ChallengeAttempt


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "classroom",
        "status",
        "max_participants",
        "start_time",
        "end_time",
    ]
    list_filter = ["status", "tournament_type"]


@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    list_display = ["student", "tournament", "score", "rank_position"]
    list_filter = ["tournament"]


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = [
        "challenger",
        "opponent",
        "quiz",
        "status",
        "xp_stake",
        "expires_at",
    ]
    list_filter = ["status"]
