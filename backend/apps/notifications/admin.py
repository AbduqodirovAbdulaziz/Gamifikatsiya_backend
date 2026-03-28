from django.contrib import admin
from .models import Notification, PushNotificationLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "notification_type", "title", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read"]
    search_fields = ["recipient__username", "title"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(admin.ModelAdmin):
    list_display = ["notification", "sent_at", "success"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
