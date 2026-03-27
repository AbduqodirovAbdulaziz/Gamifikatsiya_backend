import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Tournament(models.Model):
    TOURNAMENT_TYPES = [
        ("single_elimination", "Yakkalik"),
        ("round_robin", "Round Robin"),
        ("time_attack", "Vaqtga intilish"),
    ]
    STATUS_CHOICES = [
        ("upcoming", "Kutilmoqda"),
        ("active", "Faol"),
        ("finished", "Yakunlangan"),
        ("cancelled", "Bekor qilingan"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    classroom = models.ForeignKey(
        "classroom.Classroom", on_delete=models.CASCADE, related_name="tournaments"
    )
    quiz = models.ForeignKey(
        "quizzes.Quiz", on_delete=models.CASCADE, related_name="tournaments"
    )
    tournament_type = models.CharField(
        max_length=30, choices=TOURNAMENT_TYPES, default="time_attack"
    )
    description = models.TextField(blank=True)
    max_participants = models.IntegerField(default=16)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    first_prize_xp = models.IntegerField(default=100)
    second_prize_xp = models.IntegerField(default=50)
    third_prize_xp = models.IntegerField(default=25)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tournaments_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "competition_tournament"
        verbose_name = "Turnir"
        verbose_name_plural = "Turnirlar"
        ordering = ["-start_time"]

    def __str__(self):
        return self.title

    @property
    def participant_count(self):
        return self.participants.filter(is_active=True).count()


class TournamentParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="participants"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tournament_participations",
    )
    score = models.FloatField(default=0)
    rank_position = models.IntegerField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "competition_tournamentparticipant"
        verbose_name = "Turnir ishtirokchisi"
        verbose_name_plural = "Turnir ishtirokchilari"
        unique_together = ["tournament", "student"]

    def __str__(self):
        return f"{self.student.username} - {self.tournament.title}"


class Challenge(models.Model):
    STATUS_CHOICES = [
        ("pending", "Kutilmoqda"),
        ("accepted", "Qabul qilingan"),
        ("in_progress", "Davom etmoqda"),
        ("completed", "Yakunlangan"),
        ("declined", "Rad etilgan"),
        ("expired", "Muddati o'tgan"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenges_sent",
    )
    opponent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenges_received",
    )
    quiz = models.ForeignKey(
        "quizzes.Quiz", on_delete=models.CASCADE, related_name="challenges"
    )
    classroom = models.ForeignKey(
        "classroom.Classroom",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="challenges",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    challenger_score = models.FloatField(null=True, blank=True)
    opponent_score = models.FloatField(null=True, blank=True)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="challenges_won",
    )
    xp_stake = models.IntegerField(default=10)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "competition_challenge"
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.challenger.username} vs {self.opponent.username}"


class ChallengeAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="attempts"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenge_attempts",
    )
    quiz_attempt = models.ForeignKey(
        "quizzes.QuizAttempt",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="challenge_attempts",
    )
    score = models.FloatField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "competition_challengeattempt"
        verbose_name = "Challenge Urinish"
        verbose_name_plural = "Challenge Urinishlar"
        unique_together = ["challenge", "student"]
