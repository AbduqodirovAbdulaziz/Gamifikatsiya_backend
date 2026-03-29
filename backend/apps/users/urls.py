from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    UserProfileView,
    UserPublicView,
    ChangePasswordView,
    AvatarUploadView,
    FCMTokenView,
    StudentProfileView,
    TeacherProfileView,
    ParentChildListView,
    ParentChildDetailView,
    ParentChildProgressView,
)

urlpatterns = [
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/student/", StudentProfileView.as_view(), name="student-profile"),
    path("profile/teacher/", TeacherProfileView.as_view(), name="teacher-profile"),
    path("<uuid:pk>/public/", UserPublicView.as_view(), name="user-public"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("avatar/", AvatarUploadView.as_view(), name="avatar-upload"),
    path("fcm-token/", FCMTokenView.as_view(), name="fcm-token"),
    path("children/", ParentChildListView.as_view(), name="parent-children"),
    path(
        "children/<uuid:child_id>/",
        ParentChildDetailView.as_view(),
        name="parent-child-detail",
    ),
    path(
        "children/<uuid:child_id>/progress/",
        ParentChildProgressView.as_view(),
        name="parent-child-progress",
    ),
]
