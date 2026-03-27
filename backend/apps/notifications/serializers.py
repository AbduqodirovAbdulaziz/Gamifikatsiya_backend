from rest_framework import serializers
from .models import Notification, PushNotificationLog


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "data",
            "is_read",
            "created_at",
        ]


class NotificationCreateSerializer(serializers.ModelSerializer):
    recipient_id = serializers.UUIDField()

    class Meta:
        model = Notification
        fields = ["recipient_id", "notification_type", "title", "message", "data"]
