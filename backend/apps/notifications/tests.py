from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from apps.classroom.models import Classroom, Enrollment
from apps.users.models import StudentProfile, TeacherProfile
from .views import BroadcastNotificationView, BulkNotificationCreateView


User = get_user_model()


def create_user(username, role, password="testpass123", **extra):
    email = extra.pop("email", f"{username}@example.com")
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        **extra,
    )
    if role == "student":
        StudentProfile.objects.get_or_create(user=user)
    elif role == "teacher":
        TeacherProfile.objects.get_or_create(user=user)
    return user


class NotificationAuthorizationTests(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.teacher = create_user("teacher_notif", "teacher")
        self.other_teacher = create_user("teacher_other_notif", "teacher")
        self.student = create_user("student_notif", "student")
        self.classroom = Classroom.objects.create(
            name="Notif Test Class",
            teacher=self.teacher,
            subject="Math",
        )
        Enrollment.objects.create(
            student=self.student,
            classroom=self.classroom,
            is_active=True,
            is_approved=True,
        )

    def test_bulk_notification_requires_recipient_ids(self):
        view = BulkNotificationCreateView.as_view({"post": "create"})
        request = self.factory.post(
            "/api/v1/notifications/bulk/",
            {
                "notification_type": "system",
                "title": "Hello",
                "message": "World",
            },
            format="json",
        )
        force_authenticate(request, user=self.teacher)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_cannot_broadcast_to_foreign_classroom(self):
        foreign_classroom = Classroom.objects.create(
            name="Foreign Class",
            teacher=self.other_teacher,
            subject="Science",
        )
        view = BroadcastNotificationView.as_view({"post": "create"})
        request = self.factory.post(
            "/api/v1/notifications/broadcast/",
            {
                "notification_type": "broadcast",
                "title": "Alert",
                "message": "Forbidden",
                "classroom_id": str(foreign_classroom.id),
            },
            format="json",
        )
        force_authenticate(request, user=self.teacher)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_canonical_notification_url_returns_200(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.get("/api/v1/notifications/unread_count/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_legacy_notification_url_still_returns_200(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.get("/api/v1/unread_count/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
