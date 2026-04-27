from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer
from .services import NotificationService


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "recipient"
        )

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"count": count})

    @action(detail=True, methods=["patch"])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"message": "O'qilgan deb belgilandi"})

    @action(detail=False, methods=["patch"])
    def read_all(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response(
            {"message": "Barchasi o'qilgan deb belgilandi", "updated_count": updated}
        )

    @action(detail=True, methods=["delete"])
    def dismiss(self, request, pk=None):
        notification = self.get_object()
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["delete"])
    def dismiss_all(self, request):
        deleted_count, _ = self.get_queryset().delete()
        return Response(
            {
                "message": "Barcha bildirishnomalar o'chirildi",
                "deleted_count": deleted_count,
            }
        )

    @action(detail=False, methods=["get"])
    def by_type(self, request):
        notification_type = request.query_params.get("type")
        if not notification_type:
            return Response(
                {"error": "type parametri talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notifications = self.get_queryset().filter(notification_type=notification_type)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)


class BulkNotificationCreateView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationCreateSerializer

    def create(self, request):
        if request.user.role not in ["teacher", "admin"]:
            return Response(
                {"error": "Faqat o'qituvchi yoki admin bildirishnoma yuborishi mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipient_ids = serializer.validated_data.get("recipient_ids", [])
        if not recipient_ids:
            return Response(
                {"error": "recipient_ids talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification_type = serializer.validated_data["notification_type"]
        title = serializer.validated_data["title"]
        message = serializer.validated_data["message"]
        data = serializer.validated_data.get("data")

        notifications = []
        for recipient_id in recipient_ids:
            notification = NotificationService.create_notification(
                str(recipient_id), notification_type, title, message, data
            )
            notifications.append(notification)

        return Response(
            {
                "message": f"{len(notifications)} ta bildirishnoma yuborildi",
                "count": len(notifications),
            },
            status=status.HTTP_201_CREATED,
        )


class BroadcastNotificationView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationCreateSerializer

    def create(self, request):
        if request.user.role not in ["teacher", "admin"]:
            return Response(
                {"error": "Faqat o'qituvchi yoki admin broadcast yuborishi mumkin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        notification_type = request.data.get("notification_type", "broadcast")
        title = request.data.get("title")
        message = request.data.get("message")
        classroom_id = request.data.get("classroom_id")
        data = request.data.get("data")

        if not title or not message:
            return Response(
                {"error": "title va message talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.classroom.models import Enrollment
        from apps.classroom.models import Classroom

        if classroom_id:
            if request.user.role == "teacher":
                has_access = Classroom.objects.filter(
                    id=classroom_id,
                    teacher=request.user,
                ).exists()
                if not has_access:
                    return Response(
                        {"error": "Bu sinfga broadcast yuborish huquqingiz yo'q"},
                        status=status.HTTP_403_FORBIDDEN,
                    )

            enrollments = Enrollment.objects.filter(
                classroom_id=classroom_id,
                is_active=True,
                is_approved=True,
            ).select_related("student")

            notifications = []
            seen_students = set()
            for enrollment in enrollments:
                if enrollment.student_id in seen_students:
                    continue
                seen_students.add(enrollment.student_id)
                notification = NotificationService.create_notification(
                    str(enrollment.student.id), notification_type, title, message, data
                )
                notifications.append(notification)
        else:
            return Response(
                {"error": "classroom_id talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": f"{len(notifications)} ta bildirishnoma yuborildi",
                "count": len(notifications),
            },
            status=status.HTTP_201_CREATED,
        )
