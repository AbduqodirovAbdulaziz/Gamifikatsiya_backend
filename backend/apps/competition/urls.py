from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TournamentViewSet, ChallengeViewSet

router = DefaultRouter()
router.register(r"tournaments", TournamentViewSet, basename="tournament")
router.register(r"challenges", ChallengeViewSet, basename="challenge")

urlpatterns = [
    path("", include(router.urls)),
]
