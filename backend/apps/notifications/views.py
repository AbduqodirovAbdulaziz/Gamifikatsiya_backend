from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer


class NotificationService:
    @staticmethod
    def create_notification(recipient_id, notification_type, title, message, data=None):
        notification = Notification.objects.create(
            recipient_id=recipient_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data,
        )

        NotificationService.send_websocket_notification(recipient_id, notification)

        return notification

    @staticmethod
    def send_websocket_notification(user_id, notification):
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {
                    "type": "notification_message",
                    "notification": {
                        "id": str(notification.id),
                        "type": notification.notification_type,
                        "title": notification.title,
                        "message": notification.message,
                        "data": notification.data,
                        "created_at": notification.created_at.isoformat(),
                    },
                },
            )
        except:
            pass


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin" or user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(recipient=user)

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in ["GET", "HEAD", "OPTIONS"]:
            if obj.recipient != request.user and not request.user.is_staff:
                self.permission_denied(request)

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"count": count})

    @action(detail=True, methods=["patch"])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"message": "O'qilgan deb belgilandi"})

    @action(detail=False, methods=["patch"])
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"message": "Barchasi o'qilgan deb belgilandi"})

    @action(detail=True, methods=["delete"])
    def dismiss(self, request, pk=None):
        notification = self.get_object()
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BulkNotificationCreateView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationCreateSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipient_ids = serializer.validated_data.get("recipient_ids", [])
        notification_type = serializer.validated_data["notification_type"]
        title = serializer.validated_data["title"]
        message = serializer.validated_data["message"]
        data = serializer.validated_data.get("data")

        notifications = []
        for recipient_id in recipient_ids:
            notification = NotificationService.create_notification(
                recipient_id, notification_type, title, message, data
            )
            notifications.append(notification)

        return Response(
            {
                "message": f"{len(notifications)} ta bildirishnoma yuborildi",
                "count": len(notifications),
            },
            status=status.HTTP_201_CREATED,
        )
