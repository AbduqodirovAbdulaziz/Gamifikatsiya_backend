from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClassroomViewSet, MyClassroomsView

router = DefaultRouter()
router.register(r"classrooms", ClassroomViewSet, basename="classroom")

urlpatterns = [
    path("", include(router.urls)),
    path("my-classrooms/", MyClassroomsView.as_view(), name="my-classrooms"),
]
