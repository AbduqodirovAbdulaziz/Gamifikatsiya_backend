import uuid
from django.db import models
from django.conf import settings


class Badge(models.Model):
    BADGE_TYPES = [
        ("streak", "Streak"),
        ("quiz", "Test"),
        ("lesson", "Dars"),
        ("social", "Ijtimoiy"),
        ("special", "Maxsus"),
    ]
    CONDITION_TYPES = [
        ("count", "Soni"),
        ("streak", "Streak"),
        ("percentage", "Foiz"),
        ("custom", "Maxsus"),
    ]
    RARITIES = [
        ("common", "Oddiy"),
        ("rare", "Kam uchraydigan"),
        ("epic", "Epik"),
        ("legendary", "Legendar"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.ImageField(upload_to="badges/", null=True, blank=True)
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES)
    condition_value = models.IntegerField(default=1)
    xp_bonus = models.IntegerField(default=0)
    coin_bonus = models.IntegerField(default=0)
    rarity = models.CharField(max_length=20, choices=RARITIES, default="common")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_badge"
        verbose_name = "Badge"
        verbose_name_plural = "Badges"

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges"
    )
    badge = models.ForeignKey(
        Badge, on_delete=models.CASCADE, related_name="user_badges"
    )
    earned_at = models.DateTimeField(auto_now_add=True)
    is_displayed = models.BooleanField(default=True)

    class Meta:
        db_table = "gamification_userbadge"
        verbose_name = "Foydalanuvchi Badgesi"
        verbose_name_plural = "Foydalanuvchi Badgelari"
        unique_together = ["student", "badge"]

    def __str__(self):
        return f"{self.student.username} - {self.badge.name}"


class XPTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("quiz_complete", "Test yakunlandi"),
        ("lesson_complete", "Dars yakunlandi"),
        ("badge_earn", "Badge olindi"),
        ("streak_bonus", "Streak bonus"),
        ("challenge_win", "Challenge g'alabasi"),
        ("challenge_lose", "Challenge mag'lubiyati"),
        ("daily_bonus", "Kunlik bonus"),
        ("penalty", "Jarima"),
        ("tournament_win", "Turnir g'alabasi"),
        ("referral", "Do'st taklifi"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="xp_transactions",
    )
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=200)
    related_object_id = models.UUIDField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gamification_xptransaction"
        verbose_name = "XP Tranzaksiya"
        verbose_name_plural = "XP Tranzaksiyalari"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.username}: {self.amount} XP - {self.description}"


class LeaderboardEntry(models.Model):
    PERIODS = [
        ("daily", "Kunlik"),
        ("weekly", "Haftalik"),
        ("monthly", "Oylik"),
        ("all_time", "Umumiy"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leaderboard_entries",
    )
    classroom = models.ForeignKey(
        "classroom.Classroom",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="leaderboard_entries",
    )
    period = models.CharField(max_length=20, choices=PERIODS, default="weekly")
    xp_points = models.IntegerField(default=0)
    rank_position = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gamification_leaderboardentry"
        verbose_name = "Leaderboard Entry"
        verbose_name_plural = "Leaderboard Entries"
        unique_together = ["student", "classroom", "period"]

    def __str__(self):
        return f"{self.student.username} - Rank {self.rank_position}"


class Streak(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="streak"
    )
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    streak_freeze_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gamification_streak"
        verbose_name = "Streak"
        verbose_name_plural = "Streaks"

    def __str__(self):
        return f"{self.student.username}: {self.current_streak} days"


class DailyQuest(models.Model):
    QUEST_TYPES = [
        ("lesson", "Dars o'qish"),
        ("quiz", "Test yechish"),
        ("social", "Do'stga challenge"),
        ("streak", "Kunlik kirish"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_quests"
    )
    quest_type = models.CharField(max_length=20, choices=QUEST_TYPES)
    target_count = models.IntegerField(default=1)
    current_count = models.IntegerField(default=0)
    xp_reward = models.IntegerField(default=10)
    is_completed = models.BooleanField(default=False)
    date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "gamification_dailyquest"
        verbose_name = "Kunlik vazifa"
        verbose_name_plural = "Kunlik vazifalar"
        unique_together = ["student", "quest_type", "date"]

    def __str__(self):
        return f"{self.student.username} - {self.get_quest_type_display()}"


class LevelTitle(models.Model):
    level = models.IntegerField(unique=True)
    title = models.CharField(max_length=100)
    min_xp = models.IntegerField()
    max_xp = models.IntegerField()
    icon = models.ImageField(upload_to="level_icons/", null=True, blank=True)

    class Meta:
        db_table = "gamification_leveltitle"
        verbose_name = "Level Unvoni"
        verbose_name_plural = "Level Unvonlari"
        ordering = ["level"]

    def __str__(self):
        return f"Level {self.level}: {self.title}"
