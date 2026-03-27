import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("badge_earned", "Badge olindi"),
        ("level_up", "Level oshdi"),
        ("challenge_received", "Challenge keldi"),
        ("challenge_result", "Challenge natijasi"),
        ("tournament_start", "Turnir boshlandi"),
        ("tournament_result", "Turnir natijasi"),
        ("rank_changed", "Reyting o'zgardi"),
        ("streak_reminder", "Streak eslatmasi"),
        ("quiz_result", "Test natijasi"),
        ("daily_quest", "Kunlik vazifa"),
        ("message", "Xabar"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_sent_push = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_notification"
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username}: {self.title}"


class PushNotificationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "notifications_pushlog"
        verbose_name = "Push xatolari"
        verbose_name_plural = "Push xatolari"
