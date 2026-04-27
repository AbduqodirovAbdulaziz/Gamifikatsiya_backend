from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    BulkNotificationCreateView,
    BroadcastNotificationView,
)

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notification")

urlpatterns = [
    # Canonical notification routes.
    path(
        "notifications/",
        NotificationViewSet.as_view({"get": "list"}),
        name="notifications-list",
    ),
    path(
        "notifications/unread_count/",
        NotificationViewSet.as_view({"get": "unread_count"}),
        name="notifications-unread-count",
    ),
    path(
        "notifications/read_all/",
        NotificationViewSet.as_view({"patch": "read_all"}),
        name="notifications-read-all",
    ),
    path(
        "notifications/dismiss_all/",
        NotificationViewSet.as_view({"delete": "dismiss_all"}),
        name="notifications-dismiss-all",
    ),
    path(
        "notifications/by_type/",
        NotificationViewSet.as_view({"get": "by_type"}),
        name="notifications-by-type",
    ),
    path(
        "notifications/<uuid:pk>/read/",
        NotificationViewSet.as_view({"patch": "read"}),
        name="notifications-read",
    ),
    path(
        "notifications/<uuid:pk>/dismiss/",
        NotificationViewSet.as_view({"delete": "dismiss"}),
        name="notifications-dismiss",
    ),
    path(
        "notifications/bulk/",
        BulkNotificationCreateView.as_view({"post": "create"}),
        name="notifications-bulk",
    ),
    path(
        "notifications/broadcast/",
        BroadcastNotificationView.as_view({"post": "create"}),
        name="notifications-broadcast",
    ),
    # Backward-compatible legacy routes used by current clients.
    path("", include(router.urls)),
]
